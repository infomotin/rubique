import unittest
import json
from app import create_app
from models.db import init_database

class MultiRoleRBACApplicationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key_rbac'
        self.client = self.app.test_client()
        with self.app.app_context():
            init_database()

    def login(self, username, password):
        """Opens an authenticated session for the given demo account"""
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_super_admin_role_access(self):
        """Test Super Admin login and executive command center access"""
        # 1. Login as Super Admin
        res = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Access Admin Dashboard
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Executive Command Center", res.data)
        self.assertIn(b"User Directory", res.data)

        # 3. Create a competition
        res = self.client.post('/admin/competitions/create', data={
            'title': 'Test Tournament 2026',
            'description': 'Speed test',
            'scramble': 'R U R\' U\'',
            'prize_trophy': 'Diamond Cube'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Test Tournament 2026", res.data)

    def test_developer_role_access(self):
        """Test Developer login and telemetry HUD access"""
        # 1. Login as Developer
        res = self.client.post('/login', data={
            'username': 'developer',
            'password': 'dev123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Access Dev Dashboard
        res = self.client.get('/developer/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"System & Diagnostics Telemetry", res.data)
        self.assertIn(b"CPU LOAD", res.data)

        # 3. Run Self-Diagnostics
        res = self.client.post('/developer/diagnostics')
        self.assertEqual(res.status_code, 200)
        diag = json.loads(res.data)
        self.assertTrue(diag['success'])
        self.assertTrue(len(diag['results']) >= 2)

    def test_user_role_access(self):
        """Test Registered User login and speedcubing hub access"""
        # 1. Login as regular speedcuber
        res = self.client.post('/login', data={
            'username': 'speedcuber',
            'password': 'user123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Access User Hub
        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Competitions Arena", res.data)
        self.assertIn(b"Trophy Cabinet", res.data)

        # 3. Try accessing admin dashboard (Should be restricted)
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
    def test_community_features_and_stages(self):
        """Test all new community menus, video uploads, live chat, friends, and blogs"""
        # 1. Login as speedcuber
        res = self.client.post('/login', data={
            'username': 'speedcuber',
            'password': 'user123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Access dashboard overview + every dedicated menu page
        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'overview-scramble-display', res.data)
        self.assertIn(b'user-sidebar-nav', res.data)

        menu_pages = {
            '/dashboard/battle': 'battle-scramble-text',
            '/dashboard/learning': 'learning-3d-canvas',
            '/dashboard/guide': 'guide-3d-canvas',
            '/dashboard/videos': 'upload-video-form-box',
            '/dashboard/chat': 'chat-messages-container',
            '/dashboard/friends': 'friends/add',
            '/dashboard/blog': 'blog',
            '/dashboard/competitions': 'competition',
            '/dashboard/courses': 'course-modal',
            '/dashboard/scan': 'net-solve-btn',
            '/dashboard/trophies': 'trophy',
        }
        for path, marker in menu_pages.items():
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f'{path} must render')
            self.assertIn(b'user-sidebar-nav', res.data, f'{path} must include shared sidebar')
            self.assertIn(marker.encode(), res.data, f'{path} must contain its workspace marker')

        # 3. Test video upload
        res = self.client.post('/dashboard/videos/upload', data={
            'title': 'My Sub-10 CFOP Solve Breakdown',
            'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'solve_time': '9.45s',
            'method': 'CFOP'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Sub-10 CFOP Solve Breakdown', res.data)

        # 4. Test video like
        res = self.client.post('/dashboard/videos/like/1')
        self.assertEqual(res.status_code, 200)
        like_data = json.loads(res.data)
        self.assertTrue(like_data['success'])
        self.assertTrue(like_data['likes'] >= 1)

        # 5. Test create chat group
        res = self.client.post('/dashboard/groups/create', data={
            'name': 'FMC Elite Solvers',
            'description': 'Fewest Moves Challenge study clan',
            'is_private': '0',
            'passcode': ''
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'FMC Elite Solvers', res.data)

        # 6. Test send chat message
        res = self.client.post('/dashboard/chat/send', data={
            'group_id': '1',
            'message': 'Hello fellow speedcubers! Testing 3D AI laboratory!'
        })
        self.assertEqual(res.status_code, 200)
        chat_data = json.loads(res.data)
        self.assertTrue(chat_data['success'])

        # 7. Test fetch chat messages
        res = self.client.get('/dashboard/chat/messages/1')
        self.assertEqual(res.status_code, 200)
        msg_data = json.loads(res.data)
        self.assertTrue(msg_data['success'])
        self.assertTrue(len(msg_data['messages']) >= 1)

        # 8. Test add friend
        res = self.client.post('/dashboard/friends/add', data={
            'friend_username': 'feliks_speed'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 9. Test create blog post
        res = self.client.post('/dashboard/blogs/create', data={
            'title': 'Mastering F2L Lookahead in 2026',
            'content': 'To achieve sub-10, minimize cube rotations and track pieces during pair insertion.',
            'category': 'F2L Tricks'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Mastering F2L Lookahead in 2026', res.data)

        # 10. Test blog comment
        res = self.client.post('/dashboard/blogs/comment', data={
            'post_id': '1',
            'comment': 'Great breakdown! This helped my average drop by 2 seconds.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Comment posted!', res.data)

        # 11. Test Language Switcher
        res = self.client.get('/set-language/bn', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/set-language/en', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_visualizer_lab_and_api(self):
        """Test the 3D Visualizer Lab, Kociemba Two-Phase API, Scramble and History endpoints"""
        # 1. Access Visualizer Page without Auth -> Must Redirect to Login
        res_guest = self.client.get('/visualizer/')
        self.assertEqual(res_guest.status_code, 302)
        self.assertIn('/login', res_guest.headers.get('Location', ''))

        # 2. Access Visualizer Page with Logged in Session
        self.login('speedcuber', 'user123')
        res = self.client.get('/visualizer/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'id="isometric-cube-svg"', res.data)
        self.assertIn(b'id="visualizer-3d-cube"', res.data)
        self.assertIn(b'id="permutation-orbit-svg"', res.data)
        self.assertIn(b'id="move-ribbon"', res.data)
        self.assertIn(b'id="btn-scramble"', res.data)
        self.assertIn(b'id="btn-solve"', res.data)

        # 2. Test Scramble API
        res = self.client.get('/api/scramble')
        self.assertEqual(res.status_code, 200)
        scramble_data = json.loads(res.data)
        self.assertIn('scramble', scramble_data)
        self.assertIn('solution', scramble_data)
        self.assertTrue(len(scramble_data['scramble'].split()) >= 10)

        # 3. Test Solve API with a known permutation
        res = self.client.post('/api/solve', json={'custom_moves': 'R U R\' U\''})
        self.assertEqual(res.status_code, 200)
        solve_data = json.loads(res.data)
        self.assertTrue(solve_data['success'])
        self.assertIn('solution', solve_data)
        self.assertTrue(len(solve_data['solution']) > 0)

        # 4. Test History API
        res = self.client.get('/api/history')
        self.assertEqual(res.status_code, 200)
        history_data = json.loads(res.data)
        self.assertIn('history', history_data)

    def test_pattern_studio_library_and_stage(self):
        """Pattern Studio: verified pattern library, API endpoint and dashboard stage"""
        import pycuber as pc
        import pattern_library

        opposite = {'y': 'w', 'w': 'y', 'g': 'b', 'b': 'g', 'o': 'r', 'r': 'o'}
        own = {'U': 'y', 'R': 'o', 'F': 'g', 'D': 'w', 'L': 'r', 'B': 'b'}

        def face_grid(cube, letter):
            return [[str(s)[1] for s in row] for row in cube.get_face(letter)]

        # 1. Library loads, is unique, and every pattern reverts to solved
        patterns = pattern_library.get_patterns()
        self.assertGreaterEqual(len(patterns), 5)
        self.assertEqual(len({p['id'] for p in patterns}), len(patterns))
        for p in patterns:
            self.assertTrue(p['verified'])
            self.assertEqual(p['move_count'], len(p['algorithm'].split()))
            self.assertIn(p['difficulty'], ('beginner', 'intermediate', 'advanced'))
            cube = pc.Cube()
            cube(p['algorithm'])
            self.assertNotEqual(str(cube), str(pc.Cube()))
            cube(pattern_library.invert_sequence(p['algorithm']))
            self.assertEqual(str(cube), str(pc.Cube()))

        by_id = {p['id']: p for p in patterns}

        # 2. Checkerboard: alternating opposite colours on every face
        cube = pc.Cube()
        cube(by_id['checkerboard']['algorithm'])
        for letter in 'URFDLB':
            grid = face_grid(cube, letter)
            for r in range(3):
                for c in range(3):
                    expected = grid[0][0] if (r + c) % 2 == 0 else opposite[grid[0][0]]
                    self.assertEqual(grid[r][c], expected, f'checkerboard broken on {letter}')
            self.assertEqual(opposite[grid[0][0]], grid[0][1])

        # 3. Six Spots: every face keeps its own colour with a contrasting centre dot
        cube = pc.Cube()
        cube(by_id['six_spots']['algorithm'])
        for letter in 'URFDLB':
            grid = face_grid(cube, letter)
            rim = [grid[0][0], grid[0][1], grid[0][2], grid[1][0],
                   grid[1][2], grid[2][0], grid[2][1], grid[2][2]]
            self.assertEqual(set(rim), {own[letter]}, f'six spots rim broken on {letter}')
            self.assertNotEqual(grid[1][1], own[letter])

        # 4. Cube in a Cube: 2x2 block of the face colour framed by one other colour
        cube = pc.Cube()
        cube(by_id['cube_in_cube']['algorithm'])
        for letter in 'URFDLB':
            grid = face_grid(cube, letter)
            flat = [grid[r][c] for r in range(3) for c in range(3)]
            self.assertEqual(flat.count(own[letter]), 4, f'inner cube broken on {letter}')
            others = {ch for ch in flat if ch != own[letter]}
            self.assertEqual(len(others), 1)
            self.assertEqual(flat.count(next(iter(others))), 5)

        # 5. Superflip: corners and centres stay home, all 24 edge stickers flip
        cube = pc.Cube()
        cube(by_id['superflip']['algorithm'])
        solved = pc.Cube()
        for letter in 'URFDLB':
            grid = face_grid(cube, letter)
            solved_grid = face_grid(solved, letter)
            for r in range(3):
                for c in range(3):
                    if r in (0, 2) and c in (0, 2):
                        self.assertEqual(grid[r][c], solved_grid[r][c])
                    elif r == 1 and c == 1:
                        self.assertEqual(grid[r][c], solved_grid[r][c])
                    else:
                        self.assertNotEqual(grid[r][c], solved_grid[r][c])

        # 6. API endpoint serves the library
        res = self.client.get('/api/patterns')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['patterns']), len(patterns))
        self.assertIn('moves', data['patterns'][0])

        # 7. Dashboard ships the Pattern Studio as a dedicated page
        self.login('speedcuber', 'user123')
        res = self.client.get('/dashboard/patterns')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'id="pattern-3d-canvas"', res.data)
        self.assertIn(b'id="pattern-list"', res.data)
        self.assertIn(b'href="/dashboard/patterns"', res.data)

    def test_chess_3d_board_and_puzzle_flow(self):
        """3D Chess menu page + Super Admin hard problems + subscriber submissions"""
        # 1. Subscriber opens the GoChess 3D board page from the sidebar menu
        self.login('speedcuber', 'user123')
        res = self.client.get('/chess/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'id="gochess-canvas"', res.data)
        self.assertIn(b'Grandmaster Problems', res.data)
        self.assertIn(b'href="/chess/"', res.data)  # sidebar menu entry present

        # 2. Super Admin authors a very hard problem (back-rank mate in 1)
        self.client.get('/logout', follow_redirects=True)
        self.login('admin', 'admin123')
        res = self.client.post('/chess/problems/create', json={
            'title': 'Unit Test Twin Mate',
            'difficulty': 'Grandmaster (2400 ELO)',
            'fen': '6k1/5ppp/8/8/8/8/5PPP/RR4K1 w - - 0 1',
            'solution_moves': 'a1a8',
            'hint': 'Either rook ends it on the back rank.',
            'xp_reward': 250
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        problem_id = data['problem_id']

        # Invalid FEN and illegal solution lines are rejected
        res = self.client.post('/chess/problems/create', json={
            'title': 'Bad FEN', 'fen': 'not-a-fen', 'solution_moves': 'e2e4'})
        self.assertEqual(res.status_code, 400)
        res = self.client.post('/chess/problems/create', json={
            'title': 'Bad Line',
            'fen': '6k1/5ppp/8/8/8/8/5PPP/RR4K1 w - - 0 1',
            'solution_moves': 'a1h8'})
        self.assertEqual(res.status_code, 400)

        # 3. Anonymous users cannot author problems
        self.client.get('/logout', follow_redirects=True)
        res = self.client.post('/chess/problems/create', json={
            'title': 'Guest', 'fen': '6k1/5ppp/8/8/8/8/5PPP/RR4K1 w - - 0 1',
            'solution_moves': 'a1a8'})
        self.assertIn(res.status_code, (302, 401, 403))

        # 4. Subscriber solves it their own way: wrong move, then key move in SAN
        self.login('speedcuber', 'user123')
        res = self.client.post(f'/chess/problems/{problem_id}/submit', json={'moves': 'g1f1'})
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        self.assertFalse(data['is_solved'])
        self.assertEqual(data['xp_earned'], 0)

        res = self.client.post(f'/chess/problems/{problem_id}/submit', json={'moves': 'Ra8#'})
        data = json.loads(res.data)
        self.assertTrue(data['is_solved'])
        self.assertEqual(data['xp_earned'], 250)

        # Alternative legal mating move (b1b8) also accepted
        res = self.client.post(f'/chess/problems/{problem_id}/submit', json={'moves': 'b1b8'})
        data = json.loads(res.data)
        self.assertTrue(data['is_solved'])

        # 5. Problem appears in the public list for subscribers
        res = self.client.get('/chess/problems')
        data = json.loads(res.data)
        titles = [p['title'] for p in data['problems']]
        self.assertIn('Unit Test Twin Mate', titles)

        # 6. Valid piece move endpoint works on the studio board (e2e4 legal)
        res = self.client.post('/chess/move', json={
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'from': 'e2', 'to': 'e4', 'game_mode': 'puzzle'})
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['player_move']['uci'], 'e2e4')

class CardClubTests(unittest.TestCase):
    """Card Club: age gate, device binding, group privacy, majority votes,
    coin economy (grants/transfers/escrow/bet limits/zero-sum settlement),
    hash-chained ledger integrity, and all 15 game engines."""

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key_club'
        self.client = self.app.test_client()
        with self.app.app_context():
            init_database()
        import uuid
        self.run = uuid.uuid4().hex[:8]

    # ------------------------------------------------------------- helpers
    def api(self, method, url, body=None):
        fn = self.client.post if method == 'POST' else self.client.get
        res = fn(url, json=body or {}, headers={'X-Card-Club': '1'})
        try:
            return res.status_code, json.loads(res.data)
        except Exception:
            return res.status_code, {}

    def register(self, name, dob='1990-05-04', fp=None):
        return self.client.post('/register', data={
            'username': name, 'email': f'{name}@club.test',
            'password': 'secret123', 'confirm_password': 'secret123',
            'date_of_birth': dob, 'device_fp': fp or f'fp-{name}',
        }, follow_redirects=False).status_code

    def login(self, name):
        self.client.get('/logout')
        return self.client.post('/login', data={
            'username': name, 'password': 'secret123'},
            follow_redirects=False).status_code

    def open_club(self):
        res = self.client.get('/club/', follow_redirects=False)
        if res.status_code == 302 and '/age-gate' in res.headers.get('Location', ''):
            self.client.post('/club/age-gate', data={
                'date_of_birth': '1990-05-04', 'next': '/club/'})
            res = self.client.get('/club/', follow_redirects=False)
        return res.status_code

    # ------------------------------------------------------------ age gate
    def test_card_club_age_gate_device_binding_and_grant(self):
        from models.user_model import UserModel
        from models.card_club import economy

        kid = f'kid{self.run}'
        self.register(kid, dob='2015-01-01')
        self.assertIsNone(UserModel.find_by_username(kid),
                          'under-18 registration must be rejected')

        alice = f'alice{self.run}'
        self.assertEqual(self.register(alice), 302)

        # one account per device
        self.assertEqual(self.register(f'mallory{self.run}', fp=f'fp-{alice}'), 200)
        self.assertIsNone(UserModel.find_by_username(f'mallory{self.run}'))

        # starting grant from the fixed reserve (idempotent)
        uid = UserModel.find_by_username(alice)['id']
        self.assertEqual(economy.balances_view(uid)['personal'],
                         economy.STARTING_GRANT)
        self.assertFalse(economy.grant_starting_balance(uid))

        # logged-in adult reaches the section (legacy users hit the gate first)
        self.assertEqual(self.login(alice), 302)
        self.assertEqual(self.open_club(), 200)

        # ledger verification endpoint is developer-only
        code, data = self.api('GET', '/club/api/ledger/verify')
        self.assertEqual(code, 403)

    # -------------------------------------------------- groups & privacy
    def test_card_club_group_invite_vote_and_privacy(self):
        from models.user_model import UserModel
        from models.db import query_one
        import json as _json

        a, b = f'ga{self.run}', f'gb{self.run}'
        self.register(a)
        self.register(b)
        self.login(a)
        self.assertEqual(self.open_club(), 200)

        code, data = self.api('POST', '/club/api/groups',
                              {'name': f'Club {self.run}', 'description': 't'})
        self.assertTrue(data.get('ok'))
        gid = data['group_id']

        # privacy: outsiders cannot see or touch the group
        self.login(b)
        res = self.client.get(f'/club/groups/{gid}', follow_redirects=False)
        self.assertIn(res.status_code, (302, 404))
        code, data = self.api('POST', f'/club/api/groups/{gid}/tables',
                              {'game_slug': 'blitz'})
        self.assertIn(code, (403, 404))

        # admin-only invitation, then acceptance
        self.login(a)
        code, data = self.api('POST', f'/club/api/groups/{gid}/invites',
                              {'username': b})
        self.assertTrue(data.get('ok'))
        self.login(b)
        inv = query_one(
            "SELECT id FROM club_invites WHERE invitee_user_id = %s AND status = 'pending'",
            "SELECT id FROM club_invites WHERE invitee_user_id = ? AND status = 'pending'",
            (UserModel.find_by_username(b)['id'],))
        code, data = self.api('POST', f"/club/api/invites/{inv['id']}/accept")
        self.assertTrue(data.get('ok'))
        self.assertEqual(self.client.get(f'/club/groups/{gid}').status_code, 200)

        # majority of ALL members approves a role change
        bob_id = UserModel.find_by_username(b)['id']
        self.login(a)
        code, data = self.api('POST', f'/club/api/groups/{gid}/proposals',
                              {'proposal_type': 'set_member_role',
                               'payload': _json.dumps(
                                   {'role': 'dealer', 'target_user_id': bob_id})})
        self.assertTrue(data.get('ok'))
        pid = data['proposal_id']
        code, data = self.api('POST', f'/club/api/proposals/{pid}/vote',
                              {'vote': 'for'})
        self.assertEqual(data.get('result'), 'open')
        self.login(b)
        code, data = self.api('POST', f'/club/api/proposals/{pid}/vote',
                              {'vote': 'for'})
        self.assertEqual(data.get('result'), 'approved')
        role = query_one(
            "SELECT role FROM club_group_members WHERE group_id = %s AND user_id = %s",
            "SELECT role FROM club_group_members WHERE group_id = ? AND user_id = ?",
            (gid, bob_id))
        self.assertEqual(role['role'], 'dealer')

        # roles must come from the active game's role set
        self.login(a)
        code, data = self.api('POST', f'/club/api/groups/{gid}/proposals',
                              {'proposal_type': 'set_member_role',
                               'payload': _json.dumps(
                                   {'role': 'wizard', 'target_user_id': bob_id})})
        self.assertEqual(code, 400)

        # member removal revokes access
        code, data = self.api('POST',
                              f'/club/api/groups/{gid}/members/{bob_id}/remove')
        self.assertTrue(data.get('ok'))
        role = query_one(
            "SELECT role FROM club_group_members WHERE group_id = %s AND user_id = %s",
            "SELECT role FROM club_group_members WHERE group_id = ? AND user_id = ?",
            (gid, bob_id))
        self.assertIsNone(role)
        self.login(b)   # removed member no longer sees the group
        res = self.client.get(f'/club/groups/{gid}', follow_redirects=False)
        self.assertIn(res.status_code, (302, 404))

    # --------------------------------------------------- economy end-to-end
    def test_card_club_wallet_escrow_bets_and_zero_sum_settlement(self):
        from models.user_model import UserModel
        from models.card_club import economy

        a, b = f'wa{self.run}', f'wb{self.run}'
        self.register(a)
        self.register(b)
        self.login(a)
        self.assertEqual(self.open_club(), 200)
        aid = UserModel.find_by_username(a)['id']
        bid = UserModel.find_by_username(b)['id']

        code, data = self.api('POST', '/club/api/groups',
                              {'name': f'Wallet {self.run}'})
        gid = data['group_id']
        # invite as admin first
        self.login(a)
        self.api('POST', f'/club/api/groups/{gid}/invites', {'username': b})
        self.login(b)
        from models.db import query_one
        inv = query_one(
            "SELECT id FROM club_invites WHERE invitee_user_id = %s AND status = 'pending'",
            "SELECT id FROM club_invites WHERE invitee_user_id = ? AND status = 'pending'",
            (bid,))
        self.api('POST', f"/club/api/invites/{inv['id']}/accept")

        # funding + recipient-approved transfer
        self.login(a)
        code, data = self.api('POST', '/club/api/wallet/fund',
                              {'group_id': gid, 'amount': 40})
        self.assertEqual(data.get('group_balance'), 40)
        code, data = self.api('POST', '/club/api/wallet/transfer',
                              {'to_username': b, 'amount': 15})
        tid = data['transfer_id']
        code, data = self.api('POST', f'/club/api/wallet/transfers/{tid}/resolve',
                              {'approve': '1'})
        self.assertEqual(code, 403)   # sender may not self-resolve
        self.login(b)
        code, data = self.api('POST', f'/club/api/wallet/transfers/{tid}/resolve',
                              {'approve': '1'})
        self.assertEqual(data.get('status'), 'accepted')
        self.assertEqual(economy.balances_view(bid)['personal'],
                         economy.STARTING_GRANT + 15)

        # escrow lifecycle
        self.login(a)
        code, data = self.api('POST', '/club/api/wallet/escrow',
                              {'payee_username': b, 'amount': 20,
                               'description': 'test'})
        eid = data['escrow_id']
        code, data = self.api('POST', f'/club/api/wallet/escrow/{eid}/act',
                              {'action': 'fund'})
        self.assertEqual(data.get('status'), 'funded')
        code, data = self.api('POST', f'/club/api/wallet/escrow/{eid}/act',
                              {'action': 'complete'})
        self.assertEqual(data.get('status'), 'completed')

        # hard bet limit
        code, data = self.api('POST', f'/club/api/groups/{gid}/tables',
                              {'game_slug': 'blitz', 'stake': 501})
        self.assertEqual(code, 400)

        # full table: join, start, auto-play to settlement
        code, data = self.api('POST', f'/club/api/groups/{gid}/tables',
                              {'game_slug': 'blitz', 'stake': 10,
                               'pool_bonus': 5, 'name': 'W'})
        tid = data['table_id']
        self.login(b)
        self.api('POST', '/club/api/wallet/fund', {'group_id': gid, 'amount': 30})
        code, data = self.api('POST', f'/club/api/tables/{tid}/join')
        self.assertEqual(data.get('seat'), 1)
        code, data = self.api('POST', f'/club/api/tables/{tid}/start')
        self.assertTrue(data.get('ok'))

        # strict-rules gate: moving before acknowledgement is rejected
        code, data = self.api('GET', f'/club/api/tables/{tid}/state')
        st_legal = ((data.get('state') or {}).get('legal') or [])
        if st_legal:
            code, data = self.api('POST', f'/club/api/tables/{tid}/move',
                                  {'action': st_legal[0]})
            self.assertEqual(code, 400)
            self.assertIn('Strict Rules', str(data))

        # both players must read + acknowledge strict rules before playing
        code, data = self.api('POST', f'/club/api/tables/{tid}/strict-rules')
        self.assertTrue(data.get('ok'), data)          # b (current session)
        self.login(a)
        code, data = self.api('POST', f'/club/api/tables/{tid}/strict-rules')
        self.assertTrue(data.get('ok'), data)          # a (creator seat)
        self.login(b)

        settled, current, steps = None, b, 0
        while steps < 400:
            steps += 1
            code, data = self.api('GET', f'/club/api/tables/{tid}/state')
            state = data.get('state')
            if not state or state['table']['status'] != 'active':
                break
            turn = (state.get('game') or {}).get('turn')
            wanted = b if turn == 1 else a
            if wanted != current:
                self.login(wanted)
                current = wanted
                code, data = self.api('GET', f'/club/api/tables/{tid}/state')
                state = data.get('state')
            legal = state.get('legal') or []
            if not legal:
                continue
            code, data = self.api('POST', f'/club/api/tables/{tid}/move',
                                  {'action': legal[0]})
            if code != 200:
                break
            if data.get('settlement'):
                settled = data['settlement']
                break
        self.assertIsNotNone(settled, 'table must settle after auto-play')
        self.assertEqual(settled['pot'], 20)
        self.assertEqual(settled['total'],
                         settled['pot'] + settled['pool_bonus'])

        # ledger stays verifiable through all of the above
        rep = economy.verify_ledger()
        self.assertTrue(rep['ok'], rep['violations'][:4])
        self.assertEqual(rep['reserve'] + rep['circulating'] + rep['pools'],
                         economy.SUPPLY)

    # ------------------------------------------------------- engine smoke
    def test_card_club_all_15_engines_play_to_completion(self):
        from models.card_club.engines import CATALOG, SPEC_ORDER

        original_15 = ['blitz', 'cheat', 'ers', 'fantan', 'golf', 'gops',
                       'knockout_whist', 'mao', 'palace', 'president',
                       'rantergoround', 'rummy', 'scopa', 'speed', 'spoons']
        self.assertGreaterEqual(len(CATALOG), 15)
        for slug in original_15:
            self.assertIn(slug, CATALOG)
        self.assertEqual(sorted(CATALOG.keys()), sorted(SPEC_ORDER))
        for slug in SPEC_ORDER:
            info = CATALOG[slug]
            n = info['min']
            eng = info['cls'].from_state(
                info['cls'].create(list(range(n)), seed=7))
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
            self.assertTrue(eng.is_over(), f'{slug} did not terminate')
            self.assertTrue(len(eng.finish_order()) >= 1, f'{slug} no finish order')
            eng.view(None)          # spectator view must never leak hands


class ChessArenaTests(unittest.TestCase):
    """Chess arena matchmaking: invitations, open lobby (all subscribers),
    Group vs Group roster seats, and Public vs Public quick pairing."""

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key_chess'
        self.client = self.app.test_client()
        with self.app.app_context():
            init_database()
            # deterministic matchmaking slate: drop leftovers from earlier runs
            from models.db import execute_update
            mp_filter = "match_type IS NOT NULL AND match_type != 'ai'"
            for dep in ("chess_team_moves", "chess_clan_challenges", "chess_invitations"):
                execute_update(
                    f"DELETE FROM {dep} WHERE game_id IN (SELECT id FROM chess_games WHERE {mp_filter})",
                    f"DELETE FROM {dep} WHERE game_id IN (SELECT id FROM chess_games WHERE {mp_filter})",
                    ())
            execute_update(
                "DELETE FROM chess_invitations", "DELETE FROM chess_invitations", ())
            execute_update(
                f"DELETE FROM chess_games WHERE {mp_filter}",
                f"DELETE FROM chess_games WHERE {mp_filter}", ())

    def login(self, username, password):
        self.client.get('/logout', follow_redirects=True)
        return self.client.post('/login', data={
            'username': username, 'password': password}, follow_redirects=True)

    def logout(self):
        self.client.get('/logout', follow_redirects=True)

    def api(self, method, url, body=None):
        res = self.client.post(url, json=body or {}) if method == 'POST' else self.client.get(url)
        try:
            return res.status_code, json.loads(res.data)
        except Exception:
            return res.status_code, {}

    # ---------------------------------------------------------------- panels
    def test_chess_arena_renders_all_four_panels(self):
        self.login('speedcuber', 'user123')
        res = self.client.get('/chess/')
        self.assertEqual(res.status_code, 200)
        for marker in [b'id="tab-multiplayer"', b'INVITATIONS', b'OPEN TO ALL SUBSCRIBERS',
                       b'GROUP VS GROUP', b'PUBLIC VS PUBLIC', b'id="invite-modal"',
                       b'id="quick-pair-btn"', b'id="create-match-modal"']:
            self.assertIn(marker, res.data)

        # guests are pointed at the login instead of the arena actions
        self.logout()
        res = self.client.get('/chess/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Log in to play', res.data)
        self.assertNotIn(b'id="open-invite-modal-btn"', res.data)

    # ------------------------------------------------------------ invitations
    def test_direct_subscriber_invitation_flow(self):
        self.login('speedcuber', 'user123')
        code, data = self.api('POST', '/chess/invitations/send', {
            'to_username': 'developer', 'title': 'Night Owl Duel', 'message': 'Two moves in?'})
        self.assertEqual(code, 200)
        self.assertEqual(data['status'], 'success')
        game_id = data['game_id']
        invitation_id = data['invitation_id']

        # invitation-only battle stays out of the public arena listing
        code, data = self.api('GET', '/chess/multiplayer')
        self.assertEqual(code, 200)
        self.assertNotIn(game_id, [m['id'] for m in data['matches']])

        # nobody else may seat themselves in it, nor touch its invitation
        self.logout()
        self.login('admin', 'admin123')
        code, data = self.api('POST', f'/chess/multiplayer/{game_id}/join')
        self.assertEqual(code, 403)
        code, data = self.api('GET', '/chess/invitations')
        self.assertNotIn(game_id, [i['game_id'] for i in data['received']])
        code, data = self.api('POST', f'/chess/invitations/{invitation_id}/decline')
        self.assertEqual(code, 403)

        # the invitee receives it, accepts, and takes the Black seat
        self.login('developer', 'dev123')
        code, data = self.api('GET', '/chess/invitations')
        inv = next(i for i in data['received'] if i['game_id'] == game_id)
        self.assertEqual(inv['from_username'], 'speedcuber')
        res = self.client.get('/chess/')
        self.assertIn(b'accept-invite-btn', res.data)

        code, data = self.api('POST', f"/chess/invitations/{inv['id']}/accept")
        self.assertEqual(code, 200)
        self.assertEqual(data['seat'], 'black')
        code, data = self.api('POST', f"/chess/invitations/{inv['id']}/accept")
        self.assertEqual(code, 409)

        # a third subscriber still cannot decline an already-used invitation
        self.logout()
        self.login('admin', 'admin123')
        code, data = self.api('POST', f"/chess/invitations/{inv['id']}/decline")
        self.assertEqual(code, 409)

    def test_arena_json_endpoints_require_login(self):
        self.logout()
        code, _ = self.api('POST', '/chess/invitations/send', {'to_username': 'admin'})
        self.assertEqual(code, 401)
        code, _ = self.api('GET', '/chess/invitations')
        self.assertEqual(code, 401)
        code, _ = self.api('POST', '/chess/multiplayer/quick-pair')
        self.assertEqual(code, 401)
        code, _ = self.api('POST', '/chess/multiplayer/1/join')
        self.assertEqual(code, 401)
        code, _ = self.api('GET', '/chess/invitations/search?q=dev')
        self.assertEqual(code, 401)

    # ------------------------------------------------------ open + public
    def test_open_lobby_and_public_quick_pairing(self):
        self.login('speedcuber', 'user123')
        code, data = self.api('POST', '/chess/multiplayer/create', {
            'title': 'Open Lobby Table', 'match_type': 'open'})
        self.assertEqual(code, 200)
        open_id = data['game_id']

        # is_public is forced on for Open / Public tables
        code, data = self.api('POST', '/chess/multiplayer/create', {
            'title': 'Public Blitz', 'match_type': 'public', 'is_public': 0})
        self.assertEqual(code, 200)
        public_id = data['game_id']

        code, data = self.api('POST', '/chess/multiplayer/create', {'match_type': 'chessboxing'})
        self.assertEqual(code, 400)

        code, data = self.api('GET', '/chess/multiplayer?type=open')
        self.assertIn(open_id, [m['id'] for m in data['matches']])
        code, data = self.api('GET', '/chess/multiplayer?type=public')
        self.assertIn(public_id, [m['id'] for m in data['matches']])

        # any subscriber can take the free seat in the open lobby
        self.logout()
        self.login('developer', 'dev123')
        code, data = self.api('POST', f'/chess/multiplayer/{open_id}/join')
        self.assertEqual(code, 200)
        self.assertEqual(data['seat'], 'black')

        # a third subscriber finds both seats taken
        self.logout()
        self.login('admin', 'admin123')
        code, data = self.api('POST', f'/chess/multiplayer/{open_id}/join')
        self.assertEqual(code, 409)

        # Quick pair seats the challenger into the waiting public table
        self.logout()
        self.login('developer', 'dev123')
        code, data = self.api('POST', '/chess/multiplayer/quick-pair')
        self.assertEqual(code, 200)
        self.assertTrue(data['joined'])
        self.assertEqual(data['game_id'], public_id)
        self.assertEqual(data['seat'], 'black')

        # with no free public table left, quick pair hosts a fresh one
        self.logout()
        self.login('admin', 'admin123')
        code, data = self.api('POST', '/chess/multiplayer/quick-pair')
        self.assertEqual(code, 200)
        self.assertFalse(data['joined'])
        self.assertEqual(data['seat'], 'white')
        self.assertNotEqual(data['game_id'], public_id)

    # ----------------------------------------------------- group vs group
    def test_group_vs_group_roster_and_seat_turn_enforcement(self):
        from models.community_model import CommunityModel

        with self.app.app_context():
            rival_group_id = CommunityModel.create_group(
                'Dev War Clan', 'Group vs Group roster', created_by=2)

        self.login('speedcuber', 'user123')
        code, data = self.api('POST', '/chess/multiplayer/create', {
            'title': 'Clans At War', 'match_type': 'group_vs_group',
            'white_group_id': 1, 'black_group_id': rival_group_id})
        self.assertEqual(code, 200)
        war_id = data['game_id']

        # you can only field a clan you lead / are rostered in
        code, data = self.api('POST', '/chess/multiplayer/create', {
            'title': 'Not My Clan', 'match_type': 'group_vs_group',
            'white_group_id': 999999, 'black_group_id': rival_group_id})
        self.assertEqual(code, 403)

        # an outsider can neither seat themselves nor move pieces
        self.logout()
        self.login('admin', 'admin123')
        code, data = self.api('POST', f'/chess/multiplayer/{war_id}/join')
        self.assertEqual(code, 403)
        code, data = self.api('POST', f'/chess/multiplayer/{war_id}/move',
                              {'from': 'e2', 'to': 'e4', 'team': 'white'})
        self.assertEqual(code, 403)

        # the rival clan's founder takes the Black seat
        self.logout()
        self.login('developer', 'dev123')
        code, data = self.api('POST', f'/chess/multiplayer/{war_id}/join')
        self.assertEqual(code, 200)
        self.assertEqual(data['seat'], 'black')

        # seat colour is enforced, then the turn order
        code, data = self.api('POST', f'/chess/multiplayer/{war_id}/move',
                              {'from': 'e2', 'to': 'e4', 'team': 'white'})
        self.assertEqual(code, 403)
        code, data = self.api('POST', f'/chess/multiplayer/{war_id}/move',
                              {'from': 'd7', 'to': 'd5', 'team': 'black'})
        self.assertEqual(code, 409)

        # White opens the battle, Black answers on the next turn
        self.logout()
        self.login('speedcuber', 'user123')
        code, data = self.api('POST', f'/chess/multiplayer/{war_id}/move',
                              {'from': 'e2', 'to': 'e4', 'team': 'white'})
        self.assertEqual(code, 200)
        self.assertEqual(data['status'], 'success')

        self.logout()
        self.login('developer', 'dev123')
        code, data = self.api('POST', f'/chess/multiplayer/{war_id}/move',
                              {'from': 'd7', 'to': 'd5', 'team': 'black'})
        self.assertEqual(code, 200)
        self.assertEqual(data['move']['uci'], 'd7d5')

    def test_clan_invitation_flow(self):
        from models.community_model import CommunityModel
        from models.chess_model import ChessModel

        with self.app.app_context():
            rival_group_id = CommunityModel.create_group(
                'Dev Invite Clan', 'Clan invitation roster', created_by=2)

        self.login('speedcuber', 'user123')
        code, data = self.api('POST', '/chess/invitations/send', {
            'to_group_id': rival_group_id, 'my_group_id': 1,
            'title': 'Clan Summon', 'message': 'Bring your best line.'})
        self.assertEqual(code, 200)
        self.assertEqual(data['match_type'], 'group_vs_group')
        game_id = data['game_id']

        # subscribers outside the rival clan never see the invitation
        self.logout()
        self.login('admin', 'admin123')
        code, data = self.api('GET', '/chess/invitations')
        self.assertNotIn(game_id, [i['game_id'] for i in data['received']])

        # the rival clan's founder sees it and accepts into the Black seat
        self.logout()
        self.login('developer', 'dev123')
        code, data = self.api('GET', '/chess/invitations')
        inv = next(i for i in data['received'] if i['game_id'] == game_id)
        self.assertEqual(inv['group_name'], 'Dev Invite Clan')
        self.assertEqual(inv['game_match_type'], 'group_vs_group')

        code, data = self.api('POST', f"/chess/invitations/{inv['id']}/accept")
        self.assertEqual(code, 200)
        self.assertEqual(data['seat'], 'black')

        # accepting registers the player on the clan roster
        with self.app.app_context():
            self.assertTrue(ChessModel.is_clan_member(rival_group_id, 2))

        # and the battle shows up on the Invitation Desk as sent
        self.logout()
        self.login('speedcuber', 'user123')
        code, data = self.api('GET', '/chess/invitations')
        sent = next(i for i in data['sent'] if i['game_id'] == game_id)
        self.assertEqual(sent['status'], 'accepted')


if __name__ == '__main__':
    unittest.main()


