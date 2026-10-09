"""Card Club controller - private groups, 15 card games, coin economy.

Sits under /club (the /cards prefix belongs to the legacy CyberDeck memory
game). HTML pages render with Jinja; the /club/api/* endpoints are JSON and
share the exact same service functions with the Socket.IO `table_move`
handler, so HTTP polling and websocket play stay consistent.
"""

import json
from functools import wraps

from flask import (Blueprint, render_template, request, session, jsonify,
                   redirect, url_for, flash)

from models.user_model import UserModel
from models.db import query_one, query_all
from models.card_club import economy, groups, gameplay, devices
from models.card_club.engines import CATALOG, ordered_catalog
from models.card_club.errors import (
    CardClubError, NotFoundError, PermissionDenied, AgeGateError,
)
from controllers.auth_controller import login_required

card_club_bp = Blueprint('card_club', __name__, url_prefix='/club')

_socketio = None

DEV_ROLES = ('super_admin', 'developer')


# ------------------------------------------------------------------ helpers

def _current_user():
    uid = session.get('user_id')
    return UserModel.find_by_id(uid) if uid else None


def _user_id():
    return session.get('user_id')


def _wants_json():
    return (request.is_json or request.path.startswith('/club/api/')
            or request.headers.get('X-Card-Club') == '1'
            or (request.accept_mimetypes and
                request.accept_mimetypes.best == 'application/json'))


def _deny(e):
    status = 404 if isinstance(e, NotFoundError) else (
        403 if isinstance(e, PermissionDenied) else 400)
    if _wants_json():
        return jsonify({"ok": False, "error": str(e)}), status
    flash(str(e), 'error')
    return redirect(request.referrer or url_for('card_club.section'))


def age_gate_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        user = _current_user()
        if not user:
            flash('Please log in to access the Card Club.', 'warning')
            return redirect(url_for('auth.login',
                                    next=request.full_path.rstrip('?')))
        status, age = groups.age_gate_status(user)
        if status == 'needs_dob':
            nxt = request.full_path.rstrip('?')
            return redirect(url_for('card_club.age_gate', next=nxt))
        if status == 'underage':
            return render_template('card_club/blocked.html', age=age), 403
        return f(*args, **kwargs)
    return wrapped


def api_required(f):
    """login + age gate, JSON-first errors (for /club/api/*)."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not _user_id():
            return jsonify({"ok": False, "error": "Login required"}), 401
        user = _current_user()
        status, age = groups.age_gate_status(user)
        if status == 'needs_dob':
            return jsonify({"ok": False, "error": "Age verification required",
                            "age_gate": "needs_dob"}), 403
        if status == 'underage':
            return jsonify({"ok": False, "error": "Card Club is 18+ only",
                            "age_gate": "underage"}), 403
        return f(*args, **kwargs)
    return wrapped


# ------------------------------------------------------------------ age gate

@card_club_bp.route('/age-gate', methods=['GET', 'POST'])
@login_required
def age_gate():
    user = _current_user()
    if request.method == 'POST':
        ok = groups.declare_dob(_user_id(), request.form.get('date_of_birth', ''))
        if not ok:
            flash('The Card Club is restricted to members 18 and older.', 'error')
            return render_template('card_club/age_gate.html',
                                   next=request.form.get('next', ''))
        flash('Age verified. Welcome to the Card Club.', 'success')
        nxt = request.form.get('next') or ''
        if nxt.startswith('/') and not nxt.startswith('//'):
            return redirect(nxt)
        return redirect(url_for('card_club.section'))
    return render_template('card_club/age_gate.html',
                           next=request.args.get('next', ''))


# ------------------------------------------------------------------- section

@card_club_bp.route('/', methods=['GET'])
@login_required
@age_gate_required
def section():
    uid = _user_id()
    return render_template(
        'card_club/section.html',
        active_page='card_club',
        user=_current_user(),
        my_groups=groups.list_my_groups(uid),
        invites=groups.list_pending_invites(uid),
        catalog=ordered_catalog(),
        wallet=economy.balances_view(uid),
        transfers=economy.list_transfers(uid),
        escrows=_my_escrows(uid),
        pool_seed=economy.GROUP_POOL_ALLOCATION,
        age_gate='ok')


def _my_escrows(uid):
    rows = query_all(
        """SELECT e.*, fu.username AS payer_name, tu.username AS payee_name
           FROM club_escrow e
           JOIN users fu ON fu.id = e.payer_id
           JOIN users tu ON tu.id = e.payee_id
           WHERE (e.payer_id = %s OR e.payee_id = %s)
             AND e.status IN ('offered','funded')
           ORDER BY e.id DESC""",
        """SELECT e.*, fu.username AS payer_name, tu.username AS payee_name
           FROM club_escrow e
           JOIN users fu ON fu.id = e.payer_id
           JOIN users tu ON tu.id = e.payee_id
           WHERE (e.payer_id = ? OR e.payee_id = ?)
             AND e.status IN ('offered','funded')
           ORDER BY e.id DESC""",
        (uid, uid))
    return rows or []


# --------------------------------------------------------------------- group

@card_club_bp.route('/groups/<int:gid>', methods=['GET'])
@login_required
@age_gate_required
def group_page(gid):
    uid = _user_id()
    try:
        role = groups.require_member(gid, uid)
    except CardClubError as e:
        return _deny(e)
    group = groups.get_group(gid)
    is_admin = role == groups.ADMIN
    slug, role_set = groups.active_role_set(gid)
    active_game = CATALOG.get(slug, {}).get('name') if slug else None
    return render_template(
        'card_club/group.html',
        active_page='card_club',
        user=_current_user(),
        group=group, role=role, is_admin=is_admin,
        members=groups.members(gid),
        invites=(query_all(
            """SELECT i.id, i.token, i.status, i.created_at, u.username
               FROM club_invites i JOIN users u ON u.id = i.invitee_user_id
               WHERE i.group_id = %s AND i.status = 'pending' ORDER BY i.id DESC""",
            """SELECT i.id, i.token, i.status, i.created_at, u.username
               FROM club_invites i JOIN users u ON u.id = i.invitee_user_id
               WHERE i.group_id = ? AND i.status = 'pending' ORDER BY i.id DESC""",
            (gid,)) if is_admin else []),
        proposals=groups.list_proposals(gid),
        role_set=role_set, active_game=active_game,
        tables=gameplay.list_tables(gid, include_finished=True),
        wallet=economy.balances_view(uid, gid),
        catalog=ordered_catalog(),
        max_bet=economy.MAX_BET_LIMIT,
        group_id=gid)


# --------------------------------------------------------------------- table

@card_club_bp.route('/tables/<int:tid>', methods=['GET'])
@login_required
@age_gate_required
def table_page(tid):
    uid = _user_id()
    t = gameplay.get_table(tid)
    if not t:
        flash('Table not found.', 'error')
        return redirect(url_for('card_club.section'))
    gid = int(t['group_id'])
    try:
        groups.require_member(gid, uid)
    except CardClubError as e:
        return _deny(e)
    view = gameplay.get_view(tid, uid)
    info = CATALOG.get(t['game_slug'], {})
    return render_template(
        'card_club/table.html',
        active_page='card_club',
        group=groups.get_group(gid),
        table=t, info=info,
        view_json=json.dumps(view),
        seat=gameplay.seat_index_of(tid, uid),
        group_id=gid)


# -------------------------------------------------------------------- ledger

@card_club_bp.route('/ledger', methods=['GET'])
@login_required
@age_gate_required
def ledger_page():
    uid = _user_id()
    role = session.get('role', 'user')
    full = role in DEV_ROLES
    report = economy.verify_ledger()
    if full:
        entries = query_all(
            """SELECT l.*, u.username FROM club_ledger l
               LEFT JOIN users u ON u.id = l.user_id
               ORDER BY l.seq DESC LIMIT 100""",
            """SELECT l.*, u.username FROM club_ledger l
               LEFT JOIN users u ON u.id = l.user_id
               ORDER BY l.seq DESC LIMIT 100""")
    else:
        entries = query_all(
            """SELECT l.*, u.username FROM club_ledger l
               LEFT JOIN users u ON u.id = l.user_id
               WHERE l.user_id = %s ORDER BY l.seq DESC LIMIT 50""",
            """SELECT l.*, u.username FROM club_ledger l
               LEFT JOIN users u ON u.id = l.user_id
               WHERE l.user_id = ? ORDER BY l.seq DESC LIMIT 50""",
            (uid,))
    return render_template('card_club/ledger.html',
                           active_page='card_club',
                           report=report, entries=entries or [], full=full)


# =========================================================== API: groups ===

@card_club_bp.route('/api/groups', methods=['POST'])
@api_required
def api_create_group():
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    try:
        group = groups.create_group(uid, data.get('name', ''),
                                    data.get('description', ''))
        return jsonify({"ok": True, "group_id": int(group["id"]),
                        "invite_code": group["invite_code"]})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/groups/<int:gid>/invites', methods=['POST'])
@api_required
def api_invite(gid):
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    try:
        inv = groups.create_invite(gid, uid, data.get('username', '').strip())
        return jsonify({"ok": True, "invite": inv})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/invites/<int:iid>/accept', methods=['POST'])
@api_required
def api_accept_invite(iid):
    uid = _user_id()
    try:
        gid = groups.accept_invite(uid, iid)
        return jsonify({"ok": True, "group_id": gid})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/groups/<int:gid>/proposals', methods=['POST'])
@api_required
def api_propose(gid):
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    payload = data.get('payload')
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {"role": payload}
    payload = payload or {"role": data.get('role'),
                          "target_user_id": data.get('target_user_id')}
    try:
        pid = groups.propose_role_change(gid, uid,
                                         data.get('proposal_type', ''),
                                         payload)
        return jsonify({"ok": True, "proposal_id": pid})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/proposals/<int:pid>/vote', methods=['POST'])
@api_required
def api_vote(pid):
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    prop = query_one("SELECT group_id FROM club_role_proposals WHERE id = %s",
                     "SELECT group_id FROM club_role_proposals WHERE id = ?",
                     (pid,))
    if not prop:
        return _deny(NotFoundError("Proposal not found"))
    gid = int(prop["group_id"] if isinstance(prop, dict) else prop[0])
    try:
        result = groups.vote_on_proposal(gid, uid, pid,
                                         data.get('vote', ''))
        return jsonify({"ok": True, **result})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/groups/<int:gid>/members/<int:uid>/remove',
                    methods=['POST'])
@api_required
def api_remove_member(gid, uid):
    actor = _user_id()
    try:
        groups.remove_member(gid, actor, uid)
        return jsonify({"ok": True})
    except CardClubError as e:
        return _deny(e)


# ============================================================ API: wallet ===

@card_club_bp.route('/api/wallet', methods=['GET'])
@api_required
def api_wallet():
    uid = _user_id()
    return jsonify({
        "ok": True,
        "balances": economy.balances_view(uid),
        "transfers": [dict(t) for t in (economy.list_transfers(uid) or [])],
        "escrows": [dict(e) for e in _my_escrows(uid)],
        "limits": {"bet": economy.MAX_BET_LIMIT,
                   "exposure": economy.MAX_OUTSTANDING_EXPOSURE},
    })


@card_club_bp.route('/api/wallet/fund', methods=['POST'])
@api_required
def api_fund():
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    gid = int(data.get('group_id', 0))
    try:
        groups.require_member(gid, uid)
        bal = economy.fund_group_balance(gid, uid, int(data.get('amount', 0)))
        return jsonify({"ok": True, "group_balance": bal})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("Invalid amount"))


@card_club_bp.route('/api/wallet/transfer', methods=['POST'])
@api_required
def api_transfer():
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    try:
        target = UserModel.find_by_username(data.get('to_username', '').strip())
        if not target:
            raise NotFoundError("No such member")
        tid = economy.transfer_create(uid, int(target['id']),
                                      int(data.get('amount', 0)))
        return jsonify({"ok": True, "transfer_id": tid})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("Invalid amount"))


@card_club_bp.route('/api/wallet/transfers/<int:tid>/resolve', methods=['POST'])
@api_required
def api_resolve_transfer(tid):
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    approve = str(data.get('approve', '')).lower() in ('1', 'true', 'yes')
    try:
        result = economy.transfer_resolve(tid, uid, approve)
        return jsonify({"ok": True, **result})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/wallet/escrow', methods=['POST'])
@api_required
def api_escrow_offer():
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    try:
        target = UserModel.find_by_username(data.get('payee_username', '').strip())
        if not target:
            raise NotFoundError("No such member")
        eid = economy.escrow_offer(uid, int(target['id']),
                                   int(data.get('amount', 0)),
                                   data.get('description', ''))
        return jsonify({"ok": True, "escrow_id": eid})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("Invalid amount"))


@card_club_bp.route('/api/wallet/escrow/<int:eid>/act', methods=['POST'])
@api_required
def api_escrow_act(eid):
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    try:
        result = economy.escrow_act(eid, uid, data.get('action', ''))
        return jsonify({"ok": True, **result})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/ledger/verify', methods=['GET'])
@api_required
def api_verify_ledger():
    if session.get('role') not in DEV_ROLES:
        return jsonify({"ok": False,
                        "error": "Ledger verification is for developers"}), 403
    report = economy.verify_ledger()
    return jsonify({"ok": report["ok"], "report": report})


# ========================================================= API: gameplay ===

@card_club_bp.route('/api/groups/<int:gid>/tables', methods=['POST'])
@api_required
def api_create_table(gid):
    uid = _user_id()
    data = request.get_json(silent=True) or request.form
    try:
        t = gameplay.create_table(gid, uid, data.get('game_slug', ''),
                                  int(data.get('stake', 0) or 0),
                                  int(data.get('pool_bonus', 0) or 0),
                                  data.get('name', ''))
        return jsonify({"ok": True, "table_id": int(t["id"])})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("Invalid stake or bonus"))


def _table_context(tid):
    t = gameplay.get_table(tid)
    if not t:
        raise NotFoundError("Table not found")
    gid = int(t["group_id"])
    uid = _user_id()
    groups.require_member(gid, uid)
    return t, gid, uid


@card_club_bp.route('/api/tables/<int:tid>/join', methods=['POST'])
@api_required
def api_join_table(tid):
    try:
        t, gid, uid = _table_context(tid)
        gameplay.join_table(gid, uid, tid)
        _broadcast_table(tid)
        return jsonify({"ok": True, "seat": gameplay.seat_index_of(tid, uid)})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/tables/<int:tid>/leave', methods=['POST'])
@api_required
def api_leave_table(tid):
    try:
        t, gid, uid = _table_context(tid)
        gameplay.leave_table(gid, uid, tid)
        _broadcast_table(tid)
        return jsonify({"ok": True})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/tables/<int:tid>/start', methods=['POST'])
@api_required
def api_start_table(tid):
    try:
        t, gid, uid = _table_context(tid)
        gameplay.start_table(gid, uid, tid)
        _broadcast_table(tid)
        return jsonify({"ok": True})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/tables/<int:tid>/abandon', methods=['POST'])
@api_required
def api_abandon_table(tid):
    try:
        t, gid, uid = _table_context(tid)
        role = groups.require_member(gid, uid)
        if t['status'] == 'waiting':
            gameplay.cancel_waiting_table(gid, uid, tid)
        else:
            if role != groups.ADMIN:
                raise PermissionDenied("Only a group admin can abandon a "
                                       "table in play")
            from models.card_club.gameplay import _abandon_active
            _abandon_active(tid)
        _broadcast_table(tid)
        return jsonify({"ok": True})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/tables/<int:tid>/move', methods=['POST'])
@api_required
def api_move(tid):
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    if not isinstance(action, dict):
        return jsonify({"ok": False, "error": "action object required"}), 400
    try:
        t, gid, uid = _table_context(tid)
        result = _do_move(gid, uid, tid, action)
        return jsonify({"ok": True, **result})
    except CardClubError as e:
        return _deny(e)


@card_club_bp.route('/api/tables/<int:tid>/state', methods=['GET'])
@api_required
def api_table_state(tid):
    try:
        t, gid, uid = _table_context(tid)
        return jsonify({"ok": True,
                        "state": gameplay.get_view(tid, uid)})
    except CardClubError as e:
        return _deny(e)


# ============================================================ play service ===

def _do_move(gid, uid, tid, action):
    result = gameplay.perform_move(gid, uid, tid, action)
    _broadcast_table(tid, result.get('settlement'))
    return result


def _broadcast_table(tid, settlement=None):
    """Push private views to every seated user, public view to watchers."""
    if _socketio is None:
        return
    try:
        t = gameplay.get_table(tid)
        if not t:
            return
        for s in gameplay.seats(tid):
            su = int(s["user_id"])
            _socketio.emit('table_state',
                           gameplay.get_view(tid, su),
                           room=f'user:{su}')
        _socketio.emit('table_spectate', gameplay.get_view(tid),
                       room=f'table:{tid}')
        if settlement:
            for s in gameplay.seats(tid):
                su = int(s["user_id"])
                _socketio.emit('table_settlement',
                               {"table_id": tid, "settlement": settlement},
                               room=f'user:{su}')
            _socketio.emit('table_settlement',
                           {"table_id": tid, "settlement": settlement},
                           room=f'table:{tid}')
    except Exception:
        pass  # broadcast failures must never break the move itself


# ================================================================ socketio ===

def init_socketio(app):
    """Attach Socket.IO to the app and register Card Club live handlers."""
    global _socketio
    from flask_socketio import SocketIO
    _socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading",
                         logger=False, engineio_logger=False)

    @_socketio.on('connect')
    def _on_connect():
        from flask import session as flask_session
        uid = flask_session.get('user_id')
        if uid:
            _socketio.enter_room(f'user:{uid}')

    @_socketio.on('watch_table')
    def _on_watch(data):
        from flask import session as flask_session, request as flask_request
        uid = flask_session.get('user_id')
        if not uid:
            return {"ok": False, "error": "Login required"}
        tid = int((data or {}).get('table_id', 0))
        try:
            t = gameplay.get_table(tid)
            if not t:
                return {"ok": False, "error": "Table not found"}
            groups.require_member(int(t['group_id']), uid)
        except CardClubError as e:
            return {"ok": False, "error": str(e)}
        _socketio.enter_room(f'table:{tid}')
        return {"ok": True, "state": gameplay.get_view(tid, uid)}

    @_socketio.on('unwatch_table')
    def _on_unwatch(data):
        tid = int((data or {}).get('table_id', 0))
        _socketio.leave_room(f'table:{tid}')
        return {"ok": True}

    @_socketio.on('table_move')
    def _on_move(data):
        from flask import session as flask_session
        uid = flask_session.get('user_id')
        if not uid:
            return {"ok": False, "error": "Login required"}
        data = data or {}
        tid = int(data.get('table_id', 0))
        action = data.get('action')
        if not isinstance(action, dict):
            return {"ok": False, "error": "action object required"}
        try:
            t = gameplay.get_table(tid)
            if not t:
                return {"ok": False, "error": "Table not found"}
            gid = int(t['group_id'])
            groups.require_member(gid, uid)
            result = _do_move(gid, uid, tid, action)
            return {"ok": True, "state": result.get('view'),
                    "settlement": result.get('settlement')}
        except CardClubError as e:
            return {"ok": False, "error": str(e)}

    return _socketio
