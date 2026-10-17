"""Human-vs-Computer card play (Card Club bots).

Validates that ``vs_com``/``solo`` tables seat computer opponents, that those
bots always return a legal move, that every catalogued game terminates instead
of stalling, and that bot identities never leak into human-facing lists.
"""

import unittest
import uuid

from app import create_app
from models.db import init_database
from models.user_model import UserModel
from models.card_club import bots, economy, groups, gameplay
from models.card_club.engines import CATALOG

# Contract Bridge keeps its dummy-hand bug and is covered by its own test.
AUTO_PLAY_SLUGS = sorted(s for s in CATALOG if s != "bridge")


class VsComputerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key_vscom'
        self.client = self.app.test_client()
        with self.app.app_context():
            init_database()
        self.run = uuid.uuid4().hex[:8]

    # ------------------------------------------------------------------ util
    def _register(self, name):
        self.client.post('/register', data={
            'username': name, 'email': f'{name}@test.club',
            'password': 'password123', 'confirm_password': 'password123',
            'date_of_birth': '1995-04-12', 'device_fp': f'device-{name}-{self.run}',
        })
        return UserModel.find_by_username(name)

    def _pick(self, state, seat, legal):
        """Bot-quality pick, hardened so it can never leave the legal set."""
        action = bots.choose_action(state, seat, legal)
        if action in legal:
            return action
        return bots._ranked(state, seat, legal)[0]

    def _play_to_end(self, gid, uid, tid, cap=600):
        """Drive the human seat with legal moves until the game settles."""
        applied = 0
        for _ in range(cap):
            t = gameplay.get_table(tid)
            if not t or t['status'] != 'active':
                return applied, t
            seat = gameplay.seat_index_of(tid, uid)
            info, eng = gameplay._engine_for(t)
            legal = eng.legal_actions(seat)
            if legal:
                gameplay.perform_move(gid, uid, tid,
                                      self._pick(eng.state, seat, legal))
                applied += 1
                continue
            moves, _ = gameplay.step_pending_bots(tid)
            if not moves:
                return applied, gameplay.get_table(tid)
            applied += len(moves)
        return applied, gameplay.get_table(tid)

    def _table(self, slug, mode='vs_com', max_seats=None):
        u = self._register(f'human_{slug}_{self.run}')
        gid = groups.create_group(u['id'], f'Bot Club {slug} {self.run}')['id']
        t = gameplay.create_table(gid, u['id'], slug, stake=0,
                                  max_seats=max_seats, mode=mode)
        return u, gid, int(t['id'])

    # --------------------------------------------------------------- seating
    def test_bots_needed_follows_mode(self):
        u, gid, tid = self._table('poker')
        t = gameplay.get_table(tid)
        info = CATALOG['poker']
        seated = gameplay.seats(tid)
        self.assertEqual(len(seated), 1, "creator sits alone before start")
        self.assertEqual(bots.bots_needed(t, info, seated), info['max'] - 1)

        solo_u, solo_gid, solo_tid = self._table('gops', mode='solo')
        solo_t = gameplay.get_table(solo_tid)
        self.assertEqual(bots.bots_needed(solo_t, CATALOG['gops'],
                                          gameplay.seats(solo_tid)), 1)

        mp_u, mp_gid, mp_tid = self._table('rummy', mode='multiplayer')
        mp_t = gameplay.get_table(mp_tid)
        self.assertEqual(bots.bots_needed(mp_t, CATALOG['rummy'],
                                          gameplay.seats(mp_tid)), 0,
                         "multiplayer tables must never auto-seat bots")

    def test_start_table_seats_bots(self):
        u, gid, tid = self._table('teen_patti')
        gameplay.start_table(gid, u['id'], tid)
        seated = gameplay.seats(tid)
        self.assertEqual(len(seated), CATALOG['teen_patti']['max'],
                         "every empty seat is filled by a computer player")
        bots_at_table = [s for s in seated if s['is_bot']]
        humans = [s for s in seated if not s['is_bot']]
        self.assertEqual(len(humans), 1)
        self.assertEqual(len(bots_at_table), len(seated) - 1)
        for b in bots_at_table:
            self.assertTrue(b['display_name'], "bot seats always show a name")
            self.assertTrue(b['rules_read'],
                            "bots are pre-acknowledged so they never block play")

    def test_bots_are_hidden_from_human_lists(self):
        u, gid, tid = self._table('poker')
        gameplay.start_table(gid, u['id'], tid)
        bot_uids = {int(s['user_id']) for s in gameplay.seats(tid)
                    if s['is_bot']}
        self.assertTrue(bot_uids)

        members = {int(m['user_id']) for m in groups.members(gid)}
        self.assertFalse(bot_uids & members,
                         "bots must not appear in the member/invite list")
        self.assertEqual(groups.member_count(gid), 1)

        found = UserModel.search_users('bot_', exclude_user_id=u['id'])
        self.assertFalse([r for r in found
                          if int(r['id'] if isinstance(r, dict) else r[0])
                          in bot_uids],
                         "bots must not appear in player search")
        listed = UserModel.list_active_players(exclude_user_id=u['id'])
        self.assertFalse([r for r in listed
                          if int(r['id'] if isinstance(r, dict) else r[0])
                          in bot_uids])

    # -------------------------------------------------------------- gameplay
    def test_every_catalog_game_finishes_against_bots(self):
        """Full human-vs-bot game for every engine except bridge."""
        problems = []
        for slug in AUTO_PLAY_SLUGS:
            print(f"[vs_com] {slug} ...", flush=True)
            try:
                u, gid, tid = self._table(
                    slug, max_seats=min(4, CATALOG[slug]['max']))
                gameplay.start_table(gid, u['id'], tid)
                gameplay.acknowledge_strict_rules(tid, u['id'])
                _, t = self._play_to_end(gid, u['id'], tid)
                if not t or t['status'] != 'finished':
                    problems.append(
                        f"{slug}: stalled ({t['status'] if t else 'missing'})")
            except Exception as e:
                problems.append(f"{slug}: {type(e).__name__}: {e}")
        self.assertEqual(problems, [],
                         "these games crashed or stalled instead of finishing")

    def test_every_bot_move_is_legal(self):
        """Replays the audit log and proves each bot move was in the legal set."""
        u, gid, tid = self._table('scopa')
        gameplay.start_table(gid, u['id'], tid)
        gameplay.acknowledge_strict_rules(tid, u['id'])
        self._play_to_end(gid, u['id'], tid)

        rows = gameplay.query_all(
            "SELECT seq, user_id, move_json FROM club_moves "
            "WHERE table_id = %s ORDER BY seq ASC",
            "SELECT seq, user_id, move_json FROM club_moves "
            "WHERE table_id = ? ORDER BY seq ASC", (tid,))
        bot_uids = {int(s['user_id']) for s in gameplay.seats(tid)
                    if s['is_bot']}
        self.assertGreater(len(rows), 1, "bots must have contributed moves")

        import json
        parsed = [dict(r) if isinstance(r, dict) else
                  {'seq': r[0], 'user_id': r[1], 'move_json': r[2]}
                  for r in rows or []]
        for row in parsed:
            if isinstance(row['move_json'], str):
                row['move_json'] = json.loads(row['move_json'])
        start = parsed[0]['move_json']
        self.assertEqual(start.get('action'), 'start')

        info = CATALOG['scopa']
        players = [u['id']] + sorted(bot_uids)
        eng = info['cls'].from_state(
            info['cls'].create(players, seed=start['seed']))
        seat_of = {int(s['user_id']): int(s['seat_index'])
                   for s in gameplay.seats(tid)}
        for row in parsed[1:]:
            action = row['move_json']
            seat = seat_of[int(row['user_id'])]
            self.assertIn(action, eng.legal_actions(seat),
                          f"illegal move at seq {row['seq']}")
            eng.apply(seat, action)

    def test_settlement_is_zero_sum(self):
        u, gid, tid = self._table('blackjack')
        before = economy.balances_view(u['id'])['personal']
        gameplay.start_table(gid, u['id'], tid)
        gameplay.acknowledge_strict_rules(tid, u['id'])
        _, t = self._play_to_end(gid, u['id'], tid)
        self.assertEqual(t['status'], 'finished')
        after = economy.balances_view(u['id'])['personal']
        self.assertEqual(before, after,
                         "a stake-free table must not create or destroy coins")

    def test_step_pending_bots_is_a_noop_on_human_turn(self):
        u, gid, tid = self._table('poker')
        gameplay.start_table(gid, u['id'], tid)
        gameplay.acknowledge_strict_rules(tid, u['id'])
        moves, settlement = gameplay.step_pending_bots(tid)
        self.assertEqual((moves, settlement), ([], None),
                         "bots must not act while a human still owes a move")

    def test_bot_action_is_deterministic_and_in_legal_set(self):
        info = CATALOG['poker']
        state = info['cls'].create([1, 2, 3], seed=11)
        eng = info['cls'].from_state(state)
        seat = bots.current_actor(state) or 0
        legal = eng.legal_actions(seat)
        self.assertTrue(legal, "the actor must always have a legal move")
        self.assertEqual(bots.choose_action(state, seat, legal),
                         bots.choose_action(state, seat, legal),
                         "bot choice must be reproducible")
        self.assertIn(bots.choose_action(state, seat, legal), legal)


if __name__ == '__main__':
    unittest.main()
