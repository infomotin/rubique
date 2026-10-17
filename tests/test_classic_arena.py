"""Classic Suite arena tests: seats, validation, escrow and coin settlement.

Covers the server-side store in ``models/classic_arena.py`` plus the
``/cards/classic`` routes: solo-vs-bot games, group lobby tables, illegal
move rejection, stake escrow / payout / refund and ledger integrity.
"""

import json
import unittest
import uuid

from app import create_app
from models.db import init_database
from models.user_model import UserModel
from models import classic_arena as arena
from models.card_club import economy
from models.card_club.errors import CardClubError, IllegalMove


class ClassicArenaBase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key_classic'
        self.client = self.app.test_client()
        with self.app.app_context():
            init_database()
        self.run = uuid.uuid4().hex[:8]

    # ------------------------------------------------------------- helpers
    def api(self, method, url, body=None, client=None):
        cli = client or self.client
        fn = cli.post if method == 'POST' else cli.get
        res = fn(url, json=body or {})
        try:
            return res.status_code, json.loads(res.data)
        except Exception:
            return res.status_code, {}

    def register(self, client=None, prefix='classic'):
        cli = client or self.app.test_client()
        name = f'{prefix}_{self.run}'
        code = cli.post('/register', data={
            'username': name, 'email': f'{name}@test.club',
            'password': 'password123', 'confirm_password': 'password123',
            'date_of_birth': '1995-04-12', 'device_fp': f'device-{name}',
        }).status_code
        self.assertIn(code, (200, 302))
        with self.app.app_context():
            uid = self.user_id(name)
        return name, uid, cli

    def user_id(self, username):
        from models.db import query_one
        row = query_one("SELECT id FROM users WHERE username = %s",
                        "SELECT id FROM users WHERE username = ?", (username,))
        return int(row[0] if not isinstance(row, dict) else row['id'])

    def login(self, username, client=None):
        cli = client or self.client
        cli.get('/logout')
        return cli.post('/login', data={'username': username,
                                        'password': 'password123'}).status_code

    def grant(self, user_id, amount=500):
        with self.app.app_context():
            economy.replenish_wallet(user_id, amount)

    def balance(self, user_id):
        with self.app.app_context():
            return int(economy.balances_view(user_id)['personal'])

    def drive(self, game_id, limit=400):
        """Play the human's legal moves until the game ends."""
        view, settle, moves = None, None, 0
        while moves < limit:
            code, payload = self.api('GET', f'/cards/classic/state?game_id={game_id}')
            self.assertEqual(code, 200, payload)
            view = payload['state']
            if view.get('over'):
                break
            if not view.get('legal_actions'):
                return view, settle, moves
            code, payload = self.api(
                'POST', '/cards/classic/action',
                {'game_id': game_id, **view['legal_actions'][0]})
            self.assertEqual(code, 200, payload)
            self.assertTrue(payload.get('ok'), payload)
            view, settle = payload['state'], payload.get('settlement')
            moves += 1
        return view, settle, moves


class ClassicArenaTests(ClassicArenaBase):
    # ------------------------------------------------------------------ deals
    def test_solo_table_is_seated_with_bots(self):
        _, uid, _ = self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': '29', 'mode': 'ai'})
        self.assertEqual(code, 200, payload)
        self.assertTrue(payload['ok'], payload)

        state = payload['state']
        self.assertEqual(state['my_seat'], 0)
        self.assertEqual(state['status'], 'active')
        self.assertEqual(len(state['players']), 4)
        bots = [p for p in state['players'] if p['is_bot']]
        self.assertEqual(len(bots), 3)
        self.assertFalse(state['players'][0]['is_bot'])
        self.assertTrue(state['legal_actions'])
        self.assertNotIn('hands', state)
        self.assertEqual(len(state['hand']), state['counts']['0'])

    def test_view_hides_the_other_hands(self):
        _, uid, _ = self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'spades', 'mode': 'ai'})
        state = payload['state']
        self.assertNotIn('hands', state)
        self.assertEqual(sorted(state['counts']), ['0', '1', '2', '3'])
        for seat in ('1', '2', '3'):
            self.assertGreater(int(state['counts'][seat]), 0)
        self.assertTrue(0 < len(state['hand']) <= 13)

    # ------------------------------------------------------------ validation
    def test_illegal_move_is_rejected(self):
        self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': '29', 'mode': 'ai'})
        game_id = payload['game_id']
        before = payload['state']

        code, payload = self.api('POST', '/cards/classic/action',
                                 {'game_id': game_id, 'action': 'play',
                                  'card': 'XX'})
        self.assertEqual(code, 400, payload)
        self.assertFalse(payload['ok'])
        self.assertIn('error', payload)

        code, payload = self.api('GET', f'/cards/classic/state?game_id={game_id}')
        self.assertEqual(payload['state']['phase'], before['phase'])

    def test_stranger_cannot_play_at_someone_elses_table(self):
        _, uid, _ = self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'hearts', 'mode': 'ai'})
        game_id = payload['game_id']

        self.register(prefix='stranger')
        self.login(f'stranger_{self.run}')
        code, payload = self.api('POST', '/cards/classic/action',
                                 {'game_id': game_id, 'action': 'bid',
                                  'value': 20})
        self.assertIn(code, (403, 404), payload)
        self.assertFalse(payload['ok'])

    def test_arena_page_renders_with_lobby(self):
        self.register()
        self.login(f'classic_{self.run}')
        res = self.client.get('/cards/classic')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8', 'replace')
        for token in ('id="name-south"', 'id="classic-lobby-modal"',
                      'restoreState()', 'MY_USER_ID'):
            self.assertIn(token, html)

        code, payload = self.api('GET', '/cards/classic/tables?group_id=0')
        self.assertEqual(code, 200, payload)
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['tables'], [])

        code, payload = self.api('GET', '/club/api/wallet')
        self.assertEqual(code, 200, payload)
        self.assertIn('personal', payload['balances'])

    def test_json_routes_require_login(self):
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': '29', 'mode': 'ai'})
        self.assertEqual(code, 401, payload)
        code, payload = self.api('GET', '/cards/classic/state')
        self.assertEqual(code, 401, payload)
        code, _ = self.api('GET', '/cards/classic')
        self.assertEqual(code, 302)

    # ------------------------------------------------------------- play-out
    def test_solo_game_runs_to_completion(self):
        self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'spades', 'mode': 'ai'})
        self.assertEqual(code, 200, payload)
        game_id = payload['game_id']
        view, settle, moves = self.drive(game_id)
        self.assertTrue(view['over'])
        self.assertGreater(moves, 0)
        self.assertIsNotNone(settle)
        self.assertEqual(settle['kind'], 'refund')
        # a finished table is no longer the player's active table
        code, payload = self.api('GET', '/cards/classic/state')
        self.assertEqual(code, 404, payload)
        with self.app.app_context():
            game = arena.get_game(game_id)
        self.assertEqual(game['status'], 'finished')
        result = game['result']
        if isinstance(result, str):
            result = json.loads(result)
        self.assertEqual(result['kind'], 'refund')

    # ---------------------------------------------------------------- coins
    def test_stake_is_escrowed_and_paid_to_the_winners(self):
        self.register()
        self.login(f'classic_{self.run}')
        uid = self.user_id(f'classic_{self.run}')
        self.grant(uid, 400)
        start = self.balance(uid)

        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'hearts', 'mode': 'ai', 'stake': 25})
        self.assertEqual(code, 200, payload)
        game_id = payload['game_id']
        self.assertEqual(self.balance(uid), start - 25)

        with self.app.app_context():
            stakes = economy.classic_stakes(game_id)
            self.assertEqual(len(stakes), 4)
            self.assertTrue(all(s['amount'] == 25 for s in stakes))

        view, settle, _ = self.drive(game_id)
        self.assertTrue(view['over'])
        self.assertIn(settle['kind'], ('settlement', 'refund'))
        self.assertEqual(settle['pot'], 100)

        if settle['kind'] == 'settlement':
            # the pot went to exactly one seat: owner is unchanged or +75
            self.assertEqual(sum(settle['payouts'].values()), 100)
            self.assertIn(self.balance(uid), (start - 25, start + 75))
        else:
            self.assertEqual(self.balance(uid), start)

        with self.app.app_context():
            self.assertTrue(economy.verify_ledger()['ok'])

    def test_payout_is_exactly_zero_sum_across_the_table(self):
        self.register()
        self.login(f'classic_{self.run}')
        uid = self.user_id(f'classic_{self.run}')
        self.grant(uid, 300)

        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'oh_hell', 'mode': 'ai', 'stake': 30})
        game_id = payload['game_id']
        with self.app.app_context():
            seats = arena.game_seats(game_id)
        wallet = {int(s['user_id']): self.balance(int(s['user_id']))
                  for s in seats}

        view, settle, _ = self.drive(game_id)
        self.assertTrue(view['over'])
        self.assertEqual(settle['kind'], 'settlement')

        after = {u: self.balance(u) for u in wallet}
        # the snapshot above was taken after the stakes were escrowed, so the
        # pot has to be added back to compare against the settled wallets
        self.assertEqual(sum(wallet.values()) + settle['pot'], sum(after.values()))
        payouts = {int(k): int(v) for k, v in settle['payouts'].items()}
        self.assertEqual(sum(payouts.values()), settle['pot'])
        for u, delta in after.items():
            self.assertEqual(delta - wallet[u], payouts.get(u, 0))
        with self.app.app_context():
            self.assertTrue(economy.verify_ledger()['ok'])

    def test_cancelling_a_waiting_table_refunds_the_stake(self):
        self.register()
        self.login(f'classic_{self.run}')
        uid = self.user_id(f'classic_{self.run}')
        self.grant(uid, 200)
        start = self.balance(uid)

        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'spades', 'mode': 'group',
                                  'group_id': 0, 'stake': 40})
        self.assertEqual(code, 200, payload)
        game_id = payload['game_id']
        self.assertEqual(payload['state']['status'], 'waiting')
        self.assertEqual(self.balance(uid), start - 40)

        code, payload = self.api('POST', '/cards/classic/cancel',
                                 {'game_id': game_id})
        self.assertEqual(code, 200, payload)
        self.assertEqual(self.balance(uid), start)
        with self.app.app_context():
            self.assertTrue(economy.verify_ledger()['ok'])

    # ------------------------------------------------------------ group play
    def test_two_humans_share_a_group_table(self):
        self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'spades', 'mode': 'group',
                                  'group_id': 0, 'stake': 0})
        self.assertEqual(code, 200, payload)
        game_id = payload['game_id']
        self.assertEqual(payload['state']['status'], 'waiting')

        name2 = f'buddy_{self.run}'
        cli2 = self.app.test_client()
        cli2.post('/register', data={
            'username': name2, 'email': f'{name2}@test.club',
            'password': 'password123', 'confirm_password': 'password123',
            'date_of_birth': '1995-04-12', 'device_fp': f'device-{name2}',
        })
        self.login(name2, client=cli2)

        code, payload = self.api('POST', '/cards/classic/join',
                                 {'game_id': game_id}, client=cli2)
        self.assertEqual(code, 200, payload)
        self.assertEqual(payload['state']['my_seat'], 1)

        code, payload = self.api('POST', '/cards/classic/start',
                                 {'game_id': game_id})
        self.assertEqual(code, 200, payload)
        state = payload['state']
        self.assertEqual(state['status'], 'active')
        self.assertEqual(state['human_seats'], [0, 1])
        self.assertEqual(state['seat_labels'][0], f'classic_{self.run}')

        # alternate until both players have been on move at least twice
        seen = set()
        for _ in range(60):
            code, p1 = self.api('GET',
                                f'/cards/classic/state?game_id={game_id}')
            code, p2 = self.api('GET',
                                f'/cards/classic/state?game_id={game_id}',
                                client=cli2)
            s1, s2 = p1['state'], p2['state']
            if s1['over']:
                break
            self.assertNotEqual(s1['my_seat'], s2['my_seat'])
            if s1['is_my_turn']:
                seen.add(0)
                self.assertTrue(s1['legal_actions'])
                self.assertFalse(s2['legal_actions'])
                code, r = self.api('POST', '/cards/classic/action',
                                   {'game_id': game_id, **s1['legal_actions'][0]})
                self.assertEqual(code, 200, r)
            elif s2['is_my_turn']:
                seen.add(1)
                self.assertTrue(s2['legal_actions'])
                self.assertFalse(s1['legal_actions'])
                code, r = self.api('POST', '/cards/classic/action',
                                   {'game_id': game_id, **s2['legal_actions'][0]},
                                   client=cli2)
                self.assertEqual(code, 200, r)
            else:
                break
        self.assertEqual(seen, {0, 1}, 'both humans must get the lead')

    def test_bots_fill_every_empty_group_seat_on_start(self):
        self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': '29', 'mode': 'group',
                                  'group_id': 0, 'stake': 0})
        game_id = payload['game_id']
        code, payload = self.api('POST', '/cards/classic/start',
                                 {'game_id': game_id})
        self.assertEqual(code, 200, payload)
        players = payload['state']['players']
        self.assertEqual(len(players), 4)
        self.assertEqual(sum(1 for p in players if p['is_bot']), 3)
        self.assertEqual(payload['state']['human_seats'], [0])
        self.assertTrue(payload['state']['is_my_turn'])

    def test_only_seated_players_can_read_the_table(self):
        self.register()
        self.login(f'classic_{self.run}')
        code, payload = self.api('POST', '/cards/classic/new-game',
                                 {'slug': 'whist', 'mode': 'ai'})
        game_id = payload['game_id']

        self.register(prefix='nosy')
        self.login(f'nosy_{self.run}')
        code, payload = self.api('GET',
                                 f'/cards/classic/state?game_id={game_id}')
        self.assertEqual(code, 404, payload)
        self.assertFalse(payload['ok'])


if __name__ == '__main__':
    unittest.main()
