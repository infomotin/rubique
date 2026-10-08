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

        # 2. Access dashboard and check all stage containers exist
        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'id="stage-learning"', res.data)
        self.assertIn(b'id="stage-videos"', res.data)
        self.assertIn(b'id="stage-chat"', res.data)
        self.assertIn(b'id="stage-friends"', res.data)
        self.assertIn(b'id="stage-blog"', res.data)
        self.assertIn(b'id="stage-overview"', res.data)
        self.assertIn(b'id="stage-battle"', res.data)
        self.assertIn(b'id="stage-guide"', res.data)

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

if __name__ == '__main__':
    unittest.main()


