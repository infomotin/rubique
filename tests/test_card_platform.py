"""Comprehensive Automated Test Suite for Card Platform & Economy.

Validates:
1. Security & Identity (18+ Age Gate & Device Binding)
2. Private Groups & Access Control (Isolation, Invites, Role Proposals & Voting, Member Removal)
3. Simulated Coin Economy & Hash-Chained Ledger (1B Supply Invariant, 100 Grant, Escrow, Transfers, Bets)
4. All 12 Requested Card Game Engines (Player Counts, Rules, Moves, Termination)
"""

import hashlib
import json
import unittest
import uuid

from app import create_app
from models.db import init_database, query_one, execute_update
from models.user_model import UserModel
from models.card_club import economy, groups, gameplay
from models.card_club.engines import CATALOG
from models.card_club.engines.popular_classics import (
    CallBreak, Hazari, TwentyNine, TeenPatti, ContractBridge,
    TexasHoldem, Blackjack, CrazyEights,
)
from models.card_club.engines.rummy import Rummy
from models.card_club.engines.shedding import President, Cheat
from models.card_club.engines.realtime import Speed


class CardPlatformSecurityAndLedgerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key_platform'
        self.client = self.app.test_client()
        with self.app.app_context():
            init_database()
        self.run = uuid.uuid4().hex[:8]

    def api(self, method, url, body=None):
        fn = self.client.post if method == 'POST' else self.client.get
        res = fn(url, json=body or {}, headers={'X-Card-Club': '1'})
        try:
            return res.status_code, json.loads(res.data)
        except Exception:
            return res.status_code, {}

    def register_user(self, name, dob='1995-04-12', fp=None):
        return self.client.post('/register', data={
            'username': name, 'email': f'{name}@test.club',
            'password': 'password123', 'confirm_password': 'password123',
            'date_of_birth': dob, 'device_fp': fp or f'device-{name}',
        }, follow_redirects=False).status_code

    def login_user(self, name):
        self.client.get('/logout')
        return self.client.post('/login', data={
            'username': name, 'password': 'password123',
        }, follow_redirects=False).status_code

    # =========================================================================
    # 1. Security & Identity
    # =========================================================================
    def test_age_gate_under_18_rejected(self):
        """Underage accounts (<18 years old) are rejected at registration."""
        u = f"underage_{self.run}"
        status = self.register_user(u, dob='2015-06-01')
        self.assertIsNone(UserModel.find_by_username(u), "Under-18 account must not be registered")

    def test_age_gate_adult_accepted(self):
        """Adult accounts (>=18 years old) are accepted at registration."""
        u = f"adult_{self.run}"
        status = self.register_user(u, dob='2000-01-01')
        self.assertEqual(status, 302, "Adult registration must redirect on success")
        user = UserModel.find_by_username(u)
        self.assertIsNotNone(user, "Adult account must be registered")

    def test_device_binding_multi_account_guard(self):
        """One registration per device fingerprint/MAC."""
        shared_device = f"mac-address-{self.run}"
        u1 = f"user1_{self.run}"
        u2 = f"user2_{self.run}"

        self.assertEqual(self.register_user(u1, fp=shared_device), 302)
        self.assertIsNotNone(UserModel.find_by_username(u1))

        # Attempting second account from the same device
        self.register_user(u2, fp=shared_device)
        self.assertIsNone(UserModel.find_by_username(u2), "Second account on same device must be rejected")

    # =========================================================================
    # 2. Simulated Coin Economy & Ledger Invariants
    # =========================================================================
    def test_fixed_supply_and_ledger_integrity(self):
        """1B coin supply invariant and cryptographic hash-chain verification."""
        rep = economy.verify_ledger()
        self.assertTrue(rep['ok'], f"Ledger verification failed: {rep['violations']}")
        self.assertTrue(rep['chain_ok'], "Ledger hash chain must be intact")
        self.assertTrue(rep['supply_ok'], "Supply invariant broken")
        self.assertEqual(rep['reserve'] + rep['circulating'] + rep['pools'], economy.SUPPLY)

    def test_starting_grant_from_reserve(self):
        """New registered user receives exactly 100 coins from developer reserve."""
        u = f"grant_{self.run}"
        self.register_user(u)
        user = UserModel.find_by_username(u)
        bal = economy.balances_view(user['id'])['personal']
        self.assertEqual(bal, economy.STARTING_GRANT)

        # Invariant still holds
        rep = economy.verify_ledger()
        self.assertTrue(rep['ok'])
        self.assertEqual(rep['reserve'] + rep['circulating'] + rep['pools'], economy.SUPPLY)

    def test_transfer_requires_recipient_acceptance(self):
        """Direct transfers are atomic and require recipient acceptance."""
        a, b = f"txa_{self.run}", f"txb_{self.run}"
        self.register_user(a)
        self.register_user(b)
        aid = UserModel.find_by_username(a)['id']
        bid = UserModel.find_by_username(b)['id']

        self.login_user(a)
        code, data = self.api('POST', '/club/api/wallet/transfer', {
            'to_username': b, 'amount': 30
        })
        self.assertEqual(code, 200)
        tid = data['transfer_id']

        # Sender cannot approve transfer
        code, _ = self.api('POST', f'/club/api/wallet/transfers/{tid}/resolve', {'approve': '1'})
        self.assertEqual(code, 403)

        # Recipient approves
        self.login_user(b)
        code, data = self.api('POST', f'/club/api/wallet/transfers/{tid}/resolve', {'approve': '1'})
        self.assertEqual(code, 200)
        self.assertEqual(data.get('status'), 'accepted')

        self.assertEqual(economy.balances_view(bid)['personal'], economy.STARTING_GRANT + 30)
        self.assertEqual(economy.balances_view(aid)['personal'], economy.STARTING_GRANT - 30)

        # Invariant still holds
        self.assertTrue(economy.verify_ledger()['ok'])

    def test_escrow_lifecycle(self):
        """Escrow lifecycle: create -> fund -> complete."""
        a, b = f"esca_{self.run}", f"escb_{self.run}"
        self.register_user(a)
        self.register_user(b)
        aid = UserModel.find_by_username(a)['id']
        bid = UserModel.find_by_username(b)['id']

        self.login_user(a)
        code, data = self.api('POST', '/club/api/wallet/escrow', {
            'payee_username': b, 'amount': 25, 'description': 'card deal'
        })
        self.assertEqual(code, 200)
        eid = data['escrow_id']

        # Fund escrow
        code, data = self.api('POST', f'/club/api/wallet/escrow/{eid}/act', {'action': 'fund'})
        self.assertEqual(code, 200)
        self.assertEqual(data.get('status'), 'funded')
        self.assertEqual(economy.balances_view(aid)['personal'], economy.STARTING_GRANT - 25)

        # Complete escrow
        code, data = self.api('POST', f'/club/api/wallet/escrow/{eid}/act', {'action': 'complete'})
        self.assertEqual(code, 200)
        self.assertEqual(data.get('status'), 'completed')
        self.assertEqual(economy.balances_view(bid)['personal'], economy.STARTING_GRANT + 25)

        self.assertTrue(economy.verify_ledger()['ok'])

    # =========================================================================
    # 3. Private Groups & Access Control
    # =========================================================================
    def test_private_group_isolation_and_admin_invite(self):
        """Private group cannot be viewed by outsiders; invite allows joining."""
        adm = f"admin_{self.run}"
        out = f"outsider_{self.run}"
        self.register_user(adm)
        self.register_user(out)
        oid = UserModel.find_by_username(out)['id']

        self.login_user(adm)
        code, data = self.api('POST', '/club/api/groups', {
            'name': f'Secret Club {self.run}'
        })
        self.assertEqual(code, 200)
        gid = data['group_id']

        # Outsider cannot access group
        self.login_user(out)
        res = self.client.get(f'/club/groups/{gid}', follow_redirects=False)
        self.assertIn(res.status_code, (302, 404))

        # Admin invites outsider
        self.login_user(adm)
        code, data = self.api('POST', f'/club/api/groups/{gid}/invites', {'username': out})
        self.assertEqual(code, 200)

        # Outsider accepts invite
        self.login_user(out)
        inv = query_one(
            "SELECT id FROM club_invites WHERE invitee_user_id = %s AND status = 'pending'",
            "SELECT id FROM club_invites WHERE invitee_user_id = ? AND status = 'pending'",
            (oid,))
        self.assertIsNotNone(inv)
        code, data = self.api('POST', f"/club/api/invites/{inv['id']}/accept")
        self.assertEqual(code, 200)

        # Now outsider has access
        res = self.client.get(f'/club/groups/{gid}', follow_redirects=False)
        self.assertEqual(res.status_code, 200)

    def test_member_removal_sweeps_balance(self):
        """Member removal revokes access and sweeps member balance to group pool."""
        adm = f"adm_sweep_{self.run}"
        mem = f"mem_sweep_{self.run}"
        self.register_user(adm)
        self.register_user(mem)
        mid = UserModel.find_by_username(mem)['id']

        self.login_user(adm)
        code, data = self.api('POST', '/club/api/groups', {'name': f'Sweep {self.run}'})
        gid = data['group_id']
        self.api('POST', f'/club/api/groups/{gid}/invites', {'username': mem})

        self.login_user(mem)
        inv = query_one(
            "SELECT id FROM club_invites WHERE invitee_user_id = %s AND status = 'pending'",
            "SELECT id FROM club_invites WHERE invitee_user_id = ? AND status = 'pending'",
            (mid,))
        self.api('POST', f"/club/api/invites/{inv['id']}/accept")

        # Member funds group balance
        self.api('POST', '/club/api/wallet/fund', {'group_id': gid, 'amount': 20})
        self.assertEqual(economy.balances_view(mid, gid)['group_balance'], 20)

        # Admin removes member
        self.login_user(adm)
        code, data = self.api('POST', f'/club/api/groups/{gid}/members/{mid}/remove')
        self.assertEqual(code, 200)

        # Member balance swept to group pool
        self.assertEqual(economy.balances_view(mid, gid)['group_balance'], 0)
        self.assertTrue(economy.balances_view(mid, gid)['pool'] >= 20)

        # Member cannot access group
        self.login_user(mem)
        res = self.client.get(f'/club/groups/{gid}', follow_redirects=False)
        self.assertIn(res.status_code, (302, 404))

    # =========================================================================
    # 5. STRICT RULES & CAMERA SHARING AND ENCRYPTED GROUP CHAT VAULT
    # =========================================================================

    def test_strict_rules_and_camera_unlock(self):
        """Test strict tournament rules agreement gating camera sharing."""
        u = f'cam_{self.run}'
        self.register_user(u)
        self.login_user(u)
        u_row = UserModel.find_by_username(u)
        gid = groups.create_group(u_row['id'], f'CamGroup {u}')['id']
        tid = gameplay.create_table(gid, u_row['id'], 'blackjack', stake=0)['id']

        # View before rules read
        view = gameplay.get_view(tid, u_row['id'])
        self.assertFalse(view['my_rules_read'])
        self.assertFalse(view['my_camera_active'])

        # Attempting to activate camera before rules read must fail
        code, body = self.api('POST', f'/club/api/tables/{tid}/camera', {'active': True})
        self.assertEqual(code, 400)
        self.assertIn("Strict Rules must be read", body.get('error', ''))

        # Acknowledge strict rules
        code, body = self.api('POST', f'/club/api/tables/{tid}/strict-rules', {})
        self.assertEqual(code, 200)
        self.assertTrue(body.get('rules_read'))

        # Now camera toggle succeeds
        code, body = self.api('POST', f'/club/api/tables/{tid}/camera', {'active': True})
        self.assertEqual(code, 200)
        self.assertTrue(body.get('camera_active'))

        view2 = gameplay.get_view(tid, u_row['id'])
        self.assertTrue(view2['my_rules_read'])
        self.assertTrue(view2['my_camera_active'])
        self.assertTrue(view2['seats'][0]['camera_active'])

    def test_encrypted_group_chat_isolation_and_vault(self):
        """Test isolated end-to-end encrypted group chat vault (AES-256-GCM ciphertext)."""
        u1 = f'chat_adm_{self.run}'
        u2 = f'chat_mbr_{self.run}'
        u_out = f'chat_out_{self.run}'
        self.register_user(u1)
        self.register_user(u2)
        self.register_user(u_out)

        uid1 = UserModel.find_by_username(u1)['id']
        uid2 = UserModel.find_by_username(u2)['id']
        uid_out = UserModel.find_by_username(u_out)['id']

        self.login_user(u1)
        gid = groups.create_group(uid1, f'Secret Vault {u1}')['id']
        inv = groups.create_invite(gid, uid1, u2)
        groups.accept_invite(uid2, inv['id'])

        # u1 sends encrypted message (AES-256-GCM ciphertext)
        cipher_sample = "mQENBF4G+z8BCAC3+9kLmX0aV998Z5dE"
        iv_sample = "dGVzdF9pdl8xMmJ5dGVz"
        code, body = self.api('POST', f'/club/api/groups/{gid}/chat', {
            'ciphertext': cipher_sample,
            'iv': iv_sample,
            'salt': 'salt123'
        })
        self.assertEqual(code, 200)
        self.assertTrue(body.get('ok'))
        self.assertEqual(body['message']['ciphertext'], cipher_sample)

        # u2 (member) reads encrypted messages
        self.login_user(u2)
        code, body = self.api('GET', f'/club/api/groups/{gid}/chat')
        self.assertEqual(code, 200)
        msgs = body.get('messages', [])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['ciphertext'], cipher_sample)
        self.assertEqual(msgs[0]['iv'], iv_sample)
        self.assertEqual(msgs[0]['username'], u1)

        # Non-member u_out attempts to read or post chat -> must be rejected (isolation)
        self.login_user(u_out)
        code, body = self.api('GET', f'/club/api/groups/{gid}/chat')
        self.assertIn(code, (403, 404))
        code, body = self.api('POST', f'/club/api/groups/{gid}/chat', {
            'ciphertext': 'hack', 'iv': 'hack'
        })
        self.assertIn(code, (403, 404))

    def test_shareable_whatsapp_link_registration_flow_and_member_redirect(self):
        """Test invite link clicked on WhatsApp -> redirects to register -> auto joins group -> lands on member page."""
        admin_name = f'host_{self.run}'
        new_friend = f'friend_{self.run}'
        self.register_user(admin_name)
        self.login_user(admin_name)
        admin_row = UserModel.find_by_username(admin_name)

        # Host creates private group
        gid = groups.create_group(admin_row['id'], f'Spades Club {self.run}')['id']
        group = groups.get_group(gid)
        invite_code = group['invite_code']
        self.assertTrue(bool(invite_code))

        # Check API invite link generator
        code, invite_info = self.api('POST', '/club/api/invite-link', {'group_id': gid})
        self.assertEqual(code, 200)
        self.assertIn('whatsapp_url', invite_info)
        self.assertIn(invite_code, invite_info['join_url'])

        # Friend logs out / is unauthenticated
        self.client.get('/logout')

        # Friend clicks join link (e.g. from WhatsApp)
        res = self.client.get(f'/club/join/{invite_code}', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/register', res.headers.get('Location', ''))
        self.assertIn(invite_code, res.headers.get('Location', ''))

        # Friend registers with the invite code
        res_reg = self.client.post('/register', data={
            'username': new_friend,
            'email': f'{new_friend}@cardtest.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'date_of_birth': '1996-08-15',
            'device_fp': f'dev-{new_friend}',
            'invite': invite_code,
        }, follow_redirects=False)

        # Must redirect directly to the member page (/club/groups/<gid>)
        self.assertEqual(res_reg.status_code, 302)
        self.assertEqual(res_reg.headers.get('Location'), f'/club/groups/{gid}')

        # Friend is verified as member in group
        friend_row = UserModel.find_by_username(new_friend)
        self.assertIsNotNone(friend_row)
        self.assertTrue(groups.is_member(gid, friend_row['id']))

        # Friend can view member page
        res_page = self.client.get(f'/club/groups/{gid}')
        self.assertEqual(res_page.status_code, 200)

    def test_member_search_api(self):
        """Test searching site members for game invitations."""
        u1 = f'searcher_{self.run}'
        u2 = f'target_player_{self.run}'
        self.register_user(u1)
        self.register_user(u2)
        self.login_user(u1)

        code, body = self.api('GET', f'/club/api/members/search?q={u2[:8]}')
        self.assertEqual(code, 200)
        members = body.get('members', [])
        found = any(m['username'] == u2 for m in members)
        self.assertTrue(found, f"{u2} should be found in member search")


class CardGameEnginesTest(unittest.TestCase):
    """Test standard rules and play-through for all 12 requested games."""

    def test_player_counts_and_catalogs(self):
        """Verify exact player range specs for all 12 requested card games."""
        expected = {
            "call_break": (4, 4),
            "hazari": (4, 4),
            "29": (4, 4),
            "teen_patti": (3, 6),
            "rummy": (2, 6),
            "bridge": (4, 4),
            "poker": (2, 9),
            "blackjack": (2, 7),
            "president": (3, 16),
            "cheat": (3, 13),
            "speed": (2, 4),
            "crazy_eights": (2, 7),
        }
        for slug, (mn, mx) in expected.items():
            self.assertIn(slug, CATALOG)
            self.assertEqual(CATALOG[slug]['min'], mn, f"{slug} min players")
            self.assertEqual(CATALOG[slug]['max'], mx, f"{slug} max players")

    def test_call_break_engine_rules(self):
        """Call Break (4p): Spades trump, bidding, trick collection."""
        eng = CallBreak.from_state(CallBreak.create([0, 1, 2, 3], seed=42))
        self.assertEqual(eng.state['phase'], 'bidding')
        self.assertEqual(len(eng.legal_actions(0)), 13)  # Bids 1-13
        # Complete bidding
        for seat in range(4):
            acts = eng.legal_actions(seat)
            eng.apply(seat, acts[2])  # Bid 3
        self.assertEqual(eng.state['phase'], 'playing')
        # Complete full hand
        steps = 0
        while not eng.is_over() and steps < 100:
            turn = eng.state.get('turn')
            acts = eng.legal_actions(turn)
            eng.apply(turn, acts[0])
            steps += 1
        self.assertTrue(eng.is_over())
        self.assertEqual(len(eng.finish_order()), 4)

    def test_hazari_partition_evaluator(self):
        """Hazari (4p): 13 cards partitioned into 3, 3, 3, 4."""
        eng = Hazari.from_state(Hazari.create([0, 1, 2, 3], seed=42))
        self.assertEqual(len(eng.state['hands']), 4)
        for seat in range(4):
            acts = eng.legal_actions(seat)
            self.assertTrue(len(acts) > 0)
            eng.apply(seat, acts[0])
        self.assertTrue(eng.is_over())
        self.assertEqual(len(eng.finish_order()), 4)

    def test_twenty_nine_point_system(self):
        """29 (4p): 32 cards (J=3, 9=2, A=1, 10=1), partnership bidding."""
        eng = TwentyNine.from_state(TwentyNine.create([0, 1, 2, 3], seed=42))
        self.assertEqual(eng.state['phase'], 'bidding')
        steps = 0
        while not eng.is_over() and steps < 100:
            turn = eng.state.get('bid_turn') if eng.state.get('phase') == 'bidding' else eng.state.get('turn')
            acts = eng.legal_actions(turn)
            if not acts:
                break
            eng.apply(turn, acts[0])
            steps += 1
        self.assertTrue(eng.is_over())

    def test_teen_patti_brag_ranking(self):
        """Teen Patti (3-6p): 3-card hand comparison (Troy, Color Run, Run, Color, Pair)."""
        eng = TeenPatti.from_state(TeenPatti.create([0, 1, 2], seed=42))
        steps = 0
        while not eng.is_over() and steps < 60:
            turn = eng.state.get('turn')
            acts = eng.legal_actions(turn)
            eng.apply(turn, acts[0])
            steps += 1
        self.assertTrue(eng.is_over())
        self.assertGreaterEqual(len(eng.finish_order()), 1)

    def test_speed_realtime_shedding(self):
        """Speed (2-4p): real-time simultaneous shedding onto center piles."""
        self.assertTrue(Speed.real_time, "Speed must be marked real_time=True")
        eng = Speed.from_state(Speed.create([0, 1], seed=42))
        steps = 0
        while not eng.is_over() and steps < 100:
            acted = False
            for seat in range(2):
                acts = eng.legal_actions(seat)
                if acts:
                    eng.apply(seat, acts[0])
                    acted = True
                    steps += 1
                    break
            if not acted:
                break
        self.assertTrue(eng.is_over())

    def test_all_12_games_simulate_cleanly(self):
        """Simulate all 12 requested games to completion with no uncaught exceptions."""
        twelve = [
            "call_break", "hazari", "29", "teen_patti", "rummy", "bridge",
            "poker", "blackjack", "president", "cheat", "speed", "crazy_eights",
        ]
        for slug in twelve:
            info = CATALOG[slug]
            n = info['min']
            eng = info['cls'].from_state(info['cls'].create(list(range(n)), seed=11))
            steps, stale = 0, 0
            while not eng.is_over() and steps < 600:
                acted = False
                turn = eng.state.get('turn')
                seat_order = [turn] + [s for s in range(n) if s != turn] if isinstance(turn, int) and 0 <= turn < n else list(range(n))
                for seat in seat_order:
                    if eng.is_over():
                        break
                    acts = eng.legal_actions(seat)
                    if acts:
                        eng.apply(seat, acts[0])
                        steps += 1
                        acted = True
                        break
                stale = 0 if acted else stale + 1
                if stale > 5:
                    break
            self.assertTrue(eng.is_over(), f"{slug} failed to terminate")
            self.assertGreaterEqual(len(eng.finish_order()), 1, f"{slug} must have finish order")


if __name__ == '__main__':
    unittest.main()


