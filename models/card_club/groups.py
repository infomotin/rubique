"""Private groups: isolation, admin invitations, majority role votes,
member removal (balance sweep + seat vacate)."""

import secrets
from datetime import date, datetime, timezone

from models.db import query_one, query_all, execute_insert, execute_update
from models.card_club import economy
from models.card_club.errors import (
    CardClubError, NotFoundError, PermissionDenied,
)

DEFAULT_GROUP_ROLES = ("member", "dealer", "scorekeeper")
ADMIN = "admin"

# Role sets proposed must come from the ACTIVE game's role set (spec 2.3).
GAME_ROLE_SETS = {
    "call_break": ("dealer", "bid-master", "member"),
    "hazari": ("dealer", "scorekeeper", "member"),
    "29": ("dealer", "trump-bidder", "member"),
    "teen_patti": ("dealer", "table-host", "member"),
    "bridge": ("dealer", "declarer", "member"),
    "poker": ("dealer", "floor-manager", "member"),
    "blackjack": ("dealer", "pit-boss", "member"),
    "crazy_eights": ("dealer", "caller", "member"),
    "blitz": ("dealer", "caller", "member"),
    "cheat": ("dealer", "caller", "member"),
    "ers": ("dealer", "caller", "member"),
    "fantan": ("dealer", "scorekeeper", "member"),
    "golf": ("marker", "scorekeeper", "member"),
    "gops": ("caller", "scorekeeper", "member"),
    "knockout_whist": ("caller", "trump-caller", "member"),
    "mao": ("dealer", "caller", "member"),
    "palace": ("dealer", "scorekeeper", "member"),
    "president": ("president", "vice-president", "scum", "member"),
    "rantergoround": ("dealer", "scorekeeper", "member"),
    "rummy": ("dealer", "scorekeeper", "member"),
    "scopa": ("dealer", "scorekeeper", "member"),
    "speed": ("dealer", "caller", "member"),
    "spoons": ("dealer", "spoon-master", "member"),
}

# ------------------------------------------------------------------ age gate

def parse_dob(text):
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.strptime(text, "%d/%m/%Y").date()
        except ValueError:
            return None


def age_on(dob, today=None):
    today = today or date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


def is_adult(dob):
    return dob is not None and age_on(dob) >= 18


def age_gate_status(user_row):
    """Returns ('ok', age) | ('needs_dob', None) | ('underage', age)."""
    dob_raw = None
    if isinstance(user_row, dict):
        dob_raw = user_row.get("date_of_birth")
    elif user_row and len(user_row) > 8:
        dob_raw = user_row[8]          # legacy tuple access fallback
    if isinstance(dob_raw, (bytes, bytearray)):
        dob_raw = dob_raw.decode()
    if not dob_raw:
        return "needs_dob", None
    if isinstance(dob_raw, datetime):
        dob = dob_raw.date()
    elif isinstance(dob_raw, date):
        dob = dob_raw
    else:
        dob = parse_dob(str(dob_raw)[:10])
    if dob is None:
        return "needs_dob", None
    age = age_on(dob)
    if age < 18:
        return "underage", age
    return "ok", age


def declare_dob(user_id, dob_text):
    dob = parse_dob(dob_text)
    if dob is None:
        raise CardClubError("Date of birth must be YYYY-MM-DD")
    if not is_adult(dob):
        return False
    execute_update(
        "UPDATE users SET date_of_birth = %s WHERE id = %s",
        "UPDATE users SET date_of_birth = ? WHERE id = ?",
        (dob.isoformat(), user_id))
    return True


# ------------------------------------------------------------------- groups

def create_group(user_id, name, description=""):
    name = (name or "").strip()
    if not name:
        raise CardClubError("Group name is required")
    invite_code = secrets.token_hex(5).upper()
    group_id = execute_insert(
        "INSERT INTO club_groups (name, description, invite_code, created_by) VALUES (%s,%s,%s,%s)",
        "INSERT INTO club_groups (name, description, invite_code, created_by) VALUES (?,?,?,?)",
        (name, description or "", invite_code, user_id))
    execute_insert(
        "INSERT INTO club_group_members (group_id, user_id, role) VALUES (%s,%s,%s)",
        "INSERT INTO club_group_members (group_id, user_id, role) VALUES (?,?,?)",
        (group_id, user_id, ADMIN))
    try:
        economy.allocate_group_pool(group_id)
    except Exception:
        execute_update("DELETE FROM club_groups WHERE id = %s",
                       "DELETE FROM club_groups WHERE id = ?", (group_id,))
        raise
    return get_group(group_id)


def get_group(group_id):
    return query_one("SELECT * FROM club_groups WHERE id = %s",
                     "SELECT * FROM club_groups WHERE id = ?", (group_id,))


def member_role(group_id, user_id):
    row = query_one(
        "SELECT role FROM club_group_members WHERE group_id = %s AND user_id = %s",
        "SELECT role FROM club_group_members WHERE group_id = ? AND user_id = ?",
        (group_id, user_id))
    if not row:
        return None
    return row["role"] if isinstance(row, dict) else row[0]


def is_member(group_id, user_id):
    return member_role(group_id, user_id) is not None


def require_member(group_id, user_id):
    role = member_role(group_id, user_id)
    if role is None:
        raise NotFoundError("Group not found")     # invisible to outsiders
    return role


def require_admin(group_id, user_id):
    role = require_member(group_id, user_id)
    if role != ADMIN:
        raise PermissionDenied("Group admin only")
    return role


def members(group_id):
    return query_all(
        """SELECT m.user_id, m.role, m.joined_at, u.username
           FROM club_group_members m JOIN users u ON u.id = m.user_id
           WHERE m.group_id = %s ORDER BY m.joined_at ASC""",
        """SELECT m.user_id, m.role, m.joined_at, u.username
           FROM club_group_members m JOIN users u ON u.id = m.user_id
           WHERE m.group_id = ? ORDER BY m.joined_at ASC""",
        (group_id,))


def member_count(group_id):
    row = query_one("SELECT COUNT(*) c FROM club_group_members WHERE group_id = %s",
                    "SELECT COUNT(*) c FROM club_group_members WHERE group_id = ?",
                    (group_id,))
    return int(row["c"] if isinstance(row, dict) else row[0])


def list_my_groups(user_id):
    return query_all(
        """SELECT g.id, g.name, g.description, m.role, g.created_at
           FROM club_groups g JOIN club_group_members m ON m.group_id = g.id
           WHERE m.user_id = %s ORDER BY m.joined_at DESC""",
        """SELECT g.id, g.name, g.description, m.role, g.created_at
           FROM club_groups g JOIN club_group_members m ON m.group_id = g.id
           WHERE m.user_id = ? ORDER BY m.joined_at DESC""",
        (user_id,))


# --------------------------------------------------------------- invitations

def create_invite(group_id, admin_id, username):
    """Admin-only invitations; there is no discovery path for outsiders."""
    require_admin(group_id, admin_id)
    target = query_one("SELECT id FROM users WHERE username = %s",
                       "SELECT id FROM users WHERE username = ?", (username,))
    if not target:
        raise NotFoundError("No such member of the site")
    target_id = int(target["id"] if isinstance(target, dict) else target[0])
    if is_member(group_id, target_id):
        raise CardClubError("Already in this group")
    token = secrets.token_urlsafe(18)
    invite_id = execute_insert(
        "INSERT INTO club_invites (group_id, invitee_user_id, token, created_by) VALUES (%s,%s,%s,%s)",
        "INSERT INTO club_invites (group_id, invitee_user_id, token, created_by) VALUES (?,?,?,?)",
        (group_id, target_id, token, admin_id))
    return {"id": invite_id, "token": token, "invitee": username}


def list_pending_invites(user_id):
    return query_all(
        """SELECT i.id, i.token, i.created_at, g.id AS gid, g.name
           FROM club_invites i JOIN club_groups g ON g.id = i.group_id
           WHERE i.invitee_user_id = %s AND i.status = 'pending'
           ORDER BY i.id DESC""",
        """SELECT i.id, i.token, i.created_at, g.id AS gid, g.name
           FROM club_invites i JOIN club_groups g ON g.id = i.group_id
           WHERE i.invitee_user_id = ? AND i.status = 'pending'
           ORDER BY i.id DESC""",
        (user_id,))


def accept_invite(user_id, invite_id):
    invite = query_one(
        "SELECT id, group_id, invitee_user_id, status FROM club_invites WHERE id = %s AND token IS NOT NULL",
        "SELECT id, group_id, invitee_user_id, status FROM club_invites WHERE id = ?",
        (invite_id,))
    if not invite:
        invite = query_one(
            "SELECT id, group_id, invitee_user_id, status FROM club_invites WHERE token = %s",
            "SELECT id, group_id, invitee_user_id, status FROM club_invites WHERE token = ?",
            (invite_id,))
    if not invite:
        raise NotFoundError("Invite not found")
    iid = int(invite["id"] if isinstance(invite, dict) else invite[0])
    gid = int(invite["group_id"] if isinstance(invite, dict) else invite[1])
    inv_user = invite["invitee_user_id"] if isinstance(invite, dict) else invite[2]
    status = invite["status"] if isinstance(invite, dict) else invite[3]
    if int(inv_user) != int(user_id):
        raise PermissionDenied("This invite is for someone else")
    if status != "pending":
        raise CardClubError(f"Invite is {status}")
    group = get_group(gid)
    default_role = group.get("default_role") or "member" if isinstance(group, dict) else "member"
    try:
        execute_insert(
            "INSERT INTO club_group_members (group_id, user_id, role) VALUES (%s,%s,%s)",
            "INSERT INTO club_group_members (group_id, user_id, role) VALUES (?,?,?)",
            (gid, user_id, default_role))
    except Exception:
        raise CardClubError("Already a member")
    execute_update(
        "UPDATE club_invites SET status = 'accepted', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
        "UPDATE club_invites SET status = 'accepted', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
        (iid,))
    return gid


def get_group_by_invite_code(invite_code):
    """Retrieve group record by its unique public/shareable invite code."""
    if not invite_code:
        return None
    code = str(invite_code).strip().upper()
    return query_one(
        "SELECT * FROM club_groups WHERE UPPER(invite_code) = %s",
        "SELECT * FROM club_groups WHERE UPPER(invite_code) = ?",
        (code,))


def join_group_by_invite_code(invite_code, user_id):
    """Admit a registered user into a private group via shareable invite code.
    Auto-initializes membership and returns the group id."""
    if not invite_code:
        raise NotFoundError("Invite code missing")
    code = str(invite_code).strip().upper()
    group = get_group_by_invite_code(code)
    if not group:
        raise NotFoundError("Invalid or expired invitation link")
    gid = int(group["id"] if isinstance(group, dict) else group[0])
    if is_member(gid, user_id):
        return gid
    default_role = group.get("default_role") if isinstance(group, dict) else "member"
    default_role = default_role or "member"
    try:
        execute_insert(
            "INSERT INTO club_group_members (group_id, user_id, role) VALUES (%s,%s,%s)",
            "INSERT INTO club_group_members (group_id, user_id, role) VALUES (?,?,?)",
            (gid, user_id, default_role))
    except Exception:
        pass
    return gid


# ------------------------------------------------------------ role proposals

def active_role_set(group_id):
    """Role set comes from the active game at the group (spec: proposals use
    the active game's role set); fall back to the default club set."""
    from models.card_club.engines import CATALOG
    row = query_one(
        """SELECT t.game_slug FROM club_tables t
           WHERE t.group_id = %s AND t.status = 'active' ORDER BY t.id DESC LIMIT 1""",
        """SELECT t.game_slug FROM club_tables t
           WHERE t.group_id = ? AND t.status = 'active' ORDER BY t.id DESC LIMIT 1""",
        (group_id,))
    if row:
        slug = row["game_slug"] if isinstance(row, dict) else row[0]
        roles = GAME_ROLE_SETS.get(slug) or DEFAULT_GROUP_ROLES
        return slug, roles
    return None, DEFAULT_GROUP_ROLES


def propose_role_change(group_id, proposer_id, proposal_type, payload):
    require_admin(group_id, proposer_id)
    if proposal_type not in ("set_member_role", "set_default_role"):
        raise CardClubError("Unknown proposal type")
    payload = payload or {}
    role = (payload.get("role") or "").strip()
    slug, roles = active_role_set(group_id)
    if role not in roles:
        raise CardClubError(
            f"Role '{role}' is not in the active game role set: {', '.join(roles)}")
    target = payload.get("target_user_id")
    if proposal_type == "set_member_role":
        if not target or not is_member(group_id, int(target)):
            raise CardClubError("Target must be a member of this group")
        target = int(target)
    else:
        target = None
    pid = execute_insert(
        """INSERT INTO club_role_proposals
           (group_id, proposer_id, target_user_id, proposal_type, payload)
           VALUES (%s,%s,%s,%s,%s)""",
        """INSERT INTO club_role_proposals
           (group_id, proposer_id, target_user_id, proposal_type, payload)
           VALUES (?,?,?,?,?)""",
        (group_id, proposer_id, target, proposal_type, _dumps(payload)))
    return pid


def _dumps(obj):
    import json
    return json.dumps(obj)


def _loads(text):
    import json
    try:
        return json.loads(text or "{}")
    except Exception:
        return {}


def list_proposals(group_id):
    rows = query_all(
        """SELECT p.id, p.proposer_id, p.target_user_id, p.proposal_type,
                  p.payload, p.status, p.votes_for, p.votes_against, p.created_at,
                  u.username AS proposer,
                  tu.username AS target
           FROM club_role_proposals p
           JOIN users u ON u.id = p.proposer_id
           LEFT JOIN users tu ON tu.id = p.target_user_id
           WHERE p.group_id = %s ORDER BY p.id DESC""",
        """SELECT p.id, p.proposer_id, p.target_user_id, p.proposal_type,
                  p.payload, p.status, p.votes_for, p.votes_against, p.created_at,
                  u.username AS proposer,
                  tu.username AS target
           FROM club_role_proposals p
           JOIN users u ON u.id = p.proposer_id
           LEFT JOIN users tu ON tu.id = p.target_user_id
           WHERE p.group_id = ? ORDER BY p.id DESC""",
        (group_id,))
    out = []
    for r in rows or []:
        d = dict(r) if isinstance(r, dict) else {}
        payload = _loads(d.get("payload"))
        d["role"] = payload.get("role", "")
        out.append(d)
    return out


def proposal_votes(proposal_id):
    return query_all(
        "SELECT user_id, vote FROM club_role_votes WHERE proposal_id = %s",
        "SELECT user_id, vote FROM club_role_votes WHERE proposal_id = ?",
        (proposal_id,))


def vote_on_proposal(group_id, user_id, proposal_id, vote):
    """Simple majority of ALL current members required to take effect."""
    require_member(group_id, user_id)
    if vote not in ("for", "against"):
        raise CardClubError("Vote must be for or against")
    prop = query_one(
        "SELECT id, group_id, proposer_id, target_user_id, proposal_type, payload, status, votes_for, votes_against FROM club_role_proposals WHERE id = %s",
        "SELECT id, group_id, proposer_id, target_user_id, proposal_type, payload, status, votes_for, votes_against FROM club_role_proposals WHERE id = ?",
        (proposal_id,))
    if not prop or int(prop["group_id"] if isinstance(prop, dict) else prop[1]) != group_id:
        raise NotFoundError("Proposal not found")
    p = dict(prop) if isinstance(prop, dict) else {}
    status = p.get("status") or prop[5]
    if status != "open":
        raise CardClubError(f"Proposal is {status}")
    try:
        execute_insert(
            "INSERT INTO club_role_votes (proposal_id, user_id, vote) VALUES (%s,%s,%s)",
            "INSERT INTO club_role_votes (proposal_id, user_id, vote) VALUES (?,?,?)",
            (proposal_id, user_id, vote))
    except Exception:
        raise CardClubError("You already voted")
    inc_for = 1 if vote == "for" else 0
    inc_against = 1 if vote == "against" else 0
    execute_update(
        "UPDATE club_role_proposals SET votes_for = votes_for + %s, votes_against = votes_against + %s WHERE id = %s",
        "UPDATE club_role_proposals SET votes_for = votes_for + ?, votes_against = votes_against + ? WHERE id = ?",
        (inc_for, inc_against, proposal_id))
    fresh = query_one(
        "SELECT votes_for, votes_against FROM club_role_proposals WHERE id = %s",
        "SELECT votes_for, votes_against FROM club_role_proposals WHERE id = ?",
        (proposal_id,))
    votes_for = int(fresh["votes_for"] if isinstance(fresh, dict) else fresh[0])
    votes_against = int(fresh["votes_against"] if isinstance(fresh, dict) else fresh[1])
    total = member_count(group_id)
    result = "open"
    if votes_for * 2 > total:                     # absolute simple majority
        result = "approved"
        _apply_proposal(p, votes_for, votes_against, group_id)
    elif votes_against * 2 >= total:              # mathematically cannot pass
        result = "rejected"
        execute_update(
            "UPDATE club_role_proposals SET status = 'rejected', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
            "UPDATE club_role_proposals SET status = 'rejected', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (proposal_id,))
    return {"result": result, "votes_for": votes_for, "votes_against": votes_against,
            "member_count": total}


def _apply_proposal(p, votes_for, votes_against, group_id):
    execute_update(
        "UPDATE club_role_proposals SET status = 'approved', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
        "UPDATE club_role_proposals SET status = 'approved', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
        (p["id"],))
    payload = _loads(p.get("payload"))
    if p["proposal_type"] == "set_member_role":
        execute_update(
            "UPDATE club_group_members SET role = %s WHERE group_id = %s AND user_id = %s",
            "UPDATE club_group_members SET role = ? WHERE group_id = ? AND user_id = ?",
            (payload.get("role"), group_id, int(p["target_user_id"])))
    else:
        execute_update(
            "UPDATE club_groups SET default_role = %s WHERE id = %s",
            "UPDATE club_groups SET default_role = ? WHERE id = ?",
            (payload.get("role"), group_id))


# ------------------------------------------------------------ member removal

def remove_member(group_id, admin_id, target_user_id):
    """Revokes access, returns remaining balance to the group pool, and
    vacates/settles active table seats."""
    require_admin(group_id, admin_id)
    target_user_id = int(target_user_id)
    if target_user_id == int(admin_id):
        raise CardClubError("Use leave-group for your own membership")
    role = member_role(group_id, target_user_id)
    if role is None:
        raise NotFoundError("Not a member")
    admins = [r for r in members(group_id)
              if (r["role"] if isinstance(r, dict) else r[1]) == ADMIN]
    if role == ADMIN and len(admins) <= 1:
        raise CardClubError("Cannot remove the last admin")
    from models.card_club import gameplay
    gameplay.vacate_member_seats(group_id, target_user_id)
    economy.sweep_member_balance(group_id, target_user_id)
    execute_update(
        "DELETE FROM club_group_members WHERE group_id = %s AND user_id = %s",
        "DELETE FROM club_group_members WHERE group_id = ? AND user_id = ?",
        (group_id, target_user_id))
    execute_update(
        "UPDATE club_invites SET status = 'revoked' WHERE group_id = %s AND invitee_user_id = %s AND status = 'pending'",
        "UPDATE club_invites SET status = 'revoked' WHERE group_id = ? AND invitee_user_id = ? AND status = 'pending'",
        (group_id, target_user_id))
    return True


# ------------------------------------ isolated end-to-end encrypted chat vault

def send_group_encrypted_message(group_id, user_id, ciphertext, iv, salt=None):
    """Stores client-side encrypted ciphertext in the group-isolated vault.
    Strictly isolated: only members can submit.
    Server never receives plaintext ('No one capture or Decrypted it')."""
    require_member(group_id, user_id)
    ciphertext = (ciphertext or "").strip()
    iv = (iv or "").strip()
    salt = (salt or "").strip() if salt else None
    if not ciphertext or not iv:
        raise CardClubError("Ciphertext and IV are required for encrypted message")
    if len(ciphertext) > 65535:
        raise CardClubError("Encrypted payload exceeds size limit")

    mid = execute_insert(
        """INSERT INTO club_group_messages (group_id, user_id, ciphertext, iv, salt)
           VALUES (%s,%s,%s,%s,%s)""",
        """INSERT INTO club_group_messages (group_id, user_id, ciphertext, iv, salt)
           VALUES (?,?,?,?,?)""",
        (group_id, user_id, ciphertext, iv, salt))

    u = query_one(
        "SELECT username FROM users WHERE id = %s",
        "SELECT username FROM users WHERE id = ?",
        (user_id,))
    username = u["username"] if isinstance(u, dict) else u[0]
    return {
        "id": mid,
        "group_id": group_id,
        "user_id": user_id,
        "username": username,
        "ciphertext": ciphertext,
        "iv": iv,
        "salt": salt,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }


def list_group_encrypted_messages(group_id, user_id, limit=50):
    """Retrieves encrypted message stream strictly for group members.
    Completely isolated from non-members and other groups."""
    require_member(group_id, user_id)
    limit = min(max(1, int(limit or 50)), 100)
    rows = query_all(
        """SELECT m.id, m.group_id, m.user_id, m.ciphertext, m.iv, m.salt,
                  m.created_at, u.username
           FROM club_group_messages m
           JOIN users u ON u.id = m.user_id
           WHERE m.group_id = %s
           ORDER BY m.id ASC
           LIMIT %s""",
        """SELECT m.id, m.group_id, m.user_id, m.ciphertext, m.iv, m.salt,
                  m.created_at, u.username
           FROM club_group_messages m
           JOIN users u ON u.id = m.user_id
           WHERE m.group_id = ?
           ORDER BY m.id ASC
           LIMIT ?""",
        (group_id, limit))
    out = []
    for r in rows or []:
        d = dict(r) if isinstance(r, dict) else {
            "id": r[0], "group_id": r[1], "user_id": r[2], "ciphertext": r[3],
            "iv": r[4], "salt": r[5], "created_at": str(r[6]), "username": r[7]
        }
        if "created_at" in d and hasattr(d["created_at"], "strftime"):
            d["created_at"] = d["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        else:
            d["created_at"] = str(d.get("created_at") or "")
        out.append(d)
    return out

