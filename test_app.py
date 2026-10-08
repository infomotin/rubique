import unittest
import json
from app import app, init_db

class CubePermutationTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_key'
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_routes_redirect(self):
        # Unauthenticated access to / should redirect to login
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_registration_and_login(self):
        # Register user
        res = self.client.post('/register', data={
            'username': 'maththeorist',
            'email': 'math@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Login user
        res = self.client.post('/login', data={
            'username': 'maththeorist',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Access visualizer
        res = self.client.get('/visualizer')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Rubik's Cube", res.data)

        # Test API Scramble
        res = self.client.get('/api/scramble')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('scramble', data)
        self.assertIn('solution', data)
        print("API Scramble test passed:", data['scramble'])

        # Test API Solve
        res = self.client.post('/api/solve', json={
            'custom_moves': "R U R' U'"
        })
        self.assertEqual(res.status_code, 200)
        solve_data = json.loads(res.data)
        self.assertTrue(solve_data['success'])
        print("API Solve test passed:", solve_data['solution'])

if __name__ == '__main__':
    unittest.main()
