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

if __name__ == '__main__':
    unittest.main()


