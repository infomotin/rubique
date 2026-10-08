import unittest
import json
from app import create_app
from models.db import init_database

class CubePermutationMVCTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key_mvc'
        self.client = self.app.test_client()
        with self.app.app_context():
            init_database()

    def test_landing_page(self):
        """Test home landing page renders high-graphic content"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Permutation Network", res.data)
        self.assertIn(b"Abstract Algebra", res.data)

    def test_auth_and_profile_flow(self):
        """Test full user registration, login, profile view and history"""
        import time
        unique_user = f"user_{int(time.time())}"
        
        # 1. Register
        res = self.client.post('/register', data={
            'username': unique_user,
            'email': f'{unique_user}@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Login
        res = self.client.post('/login', data={
            'username': unique_user,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 3. Access Profile
        res = self.client.get('/profile/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(unique_user.encode(), res.data)
        self.assertIn(b"Total Solves", res.data)

        # 4. Access Visualizer
        res = self.client.get('/visualizer/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Rubik's Cube", res.data)

        # 5. Solve and record to MySQL/SQLite
        res = self.client.post('/api/solve', json={
            'custom_moves': "R U R' U' F' U2"
        })
        self.assertEqual(res.status_code, 200)
        solve_data = json.loads(res.data)
        self.assertTrue(solve_data['success'])

        # 6. Verify solve history in Profile
        res = self.client.get('/profile/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"R U R' U' F' U2", res.data)

if __name__ == '__main__':
    unittest.main()
