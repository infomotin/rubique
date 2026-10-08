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
        self.assertIn(b"Unauthorized", res.data)

if __name__ == '__main__':
    unittest.main()
