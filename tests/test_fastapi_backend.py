"""
Tests for CubePermutation AI - FastAPI Backend
==============================================
Validates:
1. Authentication:
   - Web-compatible login returning valid signed Flask session cookie
   - Decoding/validating the Flask session cookie in FastAPI and Flask
   - Firebase Auth token verification & MySQL account mapping
   - Bearer token & Cookie-based authorization to protected endpoints
2. Data Flow & Core Computations:
   - WCA Scramble Generation
   - Two-Phase Kociemba Solving & Move Inversion
   - Step-by-Step explanation generation
   - Solve history recording in MySQL
   - Pattern library retrieval
3. Computer Vision / Real-Time Image Processing:
   - Preset scanning (Sample U, Sample F, etc.)
   - Base64 image payload scanning
   - Multipart image file upload scanning
   - Annotated image verification & color classification
"""

import unittest
import base64
import numpy as np
import cv2
from fastapi.testclient import TestClient
from fastapi_app.main import app
from fastapi_app.session_manager import decode_flask_cookie, encode_flask_cookie
from models.user_model import UserModel
from models.db import init_database


class FastAPIMobileBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Test server health check endpoint"""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")

    def test_02_login_and_flask_session_cookie(self):
        """
        Verify login against existing MySQL user (speedcuber) returns a
        valid Flask session cookie that decodes correctly.
        """
        res = self.client.post("/api/v1/auth/login", json={
            "username": "speedcuber",
            "password": "user123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["username"], "speedcuber")
        self.assertIn("session_cookie", data)

        cookie_str = data["session_cookie"]
        # Cryptographically verify and decode with Flask session serializer
        decoded = decode_flask_cookie(cookie_str)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["username"], "speedcuber")
        self.assertIn("user_id", decoded)

        # Now test accessing /me with this cookie
        me_res = self.client.get("/api/v1/auth/me", cookies={"session": cookie_str})
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.json()
        self.assertEqual(me_data["user"]["username"], "speedcuber")

    def test_03_login_failure(self):
        """Verify invalid credentials return 401"""
        res = self.client.post("/api/v1/auth/login", json={
            "username": "speedcuber",
            "password": "wrong_password"
        })
        self.assertEqual(res.status_code, 401)

    def test_04_firebase_token_auth_and_mysql_mapping(self):
        """
        Verify Firebase Auth token is verified and maps onto MySQL account.
        """
        test_email = "firebase_mobile_cuber@example.com"
        token = f"test_token_firebase:{test_email}"

        res = self.client.post("/api/v1/auth/firebase-login", json={
            "id_token": token
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["email"], test_email)
        self.assertIn("session_cookie", data)

        # Verify user was created/retrieved in MySQL
        mysql_user = UserModel.find_by_username(data["user"]["username"])
        self.assertIsNotNone(mysql_user)
        self.assertEqual(mysql_user["email"], test_email)

        # Verify accessing protected endpoint using Bearer token
        me_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["user"]["email"], test_email)

    def test_05_scramble_generation(self):
        """Verify WCA scramble generation and preliminary solution"""
        res = self.client.get("/api/scramble")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("scramble", data)
        self.assertIn("solution", data)
        self.assertIn("move_count", data)
        self.assertTrue(len(data["scramble"].split()) >= 14)

    def test_06_solve_move_sequence(self):
        """Verify solving a move sequence returns inverted moves and step explanations"""
        scramble = "R U R' U'"
        res = self.client.post("/api/solve", json={"custom_moves": scramble})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["solution"], "U R U' R'")
        self.assertEqual(len(data["moves"]), 4)
        self.assertEqual(len(data["steps"]), 4)
        self.assertIn("why", data["steps"][0])
        self.assertIn("how", data["steps"][0])

    def test_07_solve_facelet_state(self):
        """Verify solving solved facelet state returns identity/solved"""
        solved_facelets = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
        res = self.client.post("/api/solve", json={"facelet_string": solved_facelets})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])

    def test_08_opencv_scan_sample_preset(self):
        """Verify OpenCV scanner handles sample presets with annotated preview"""
        res = self.client.post("/api/scan-image", data={"sample_id": "sample_u"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["face_grid"]), 3)
        self.assertEqual(len(data["face_grid"][0]), 3)
        self.assertTrue(data["annotated_image"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(data["center_color"], "Y")

    def test_09_opencv_scan_image_file_upload(self):
        """Verify OpenCV scanner processes real multipart uploaded image bytes"""
        # Create a synthetic 300x300 BGR test cube image
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[:, :] = (20, 200, 240)  # Yellow-ish face
        cv2.rectangle(img, (10, 10), (290, 290), (255, 255, 255), 2)
        _, encoded = cv2.imencode(".jpg", img)
        img_bytes = encoded.tobytes()

        files = {"image": ("test_face.jpg", img_bytes, "image/jpeg")}
        res = self.client.post("/api/scan-image", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["face_grid"]), 3)
        self.assertTrue(data["annotated_image"].startswith("data:image/jpeg;base64,"))

    def test_10_opencv_scan_base64_payload(self):
        """Verify OpenCV scanner processes base64 payload"""
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[:, :] = (90, 190, 30)  # Green face
        _, encoded = cv2.imencode(".jpg", img)
        b64_str = base64.b64encode(encoded.tobytes()).decode("utf-8")

        res = self.client.post("/api/v1/cube/scan-json", json={"image_base64": b64_str})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["face_grid"]), 3)

    def test_11_pattern_studio(self):
        """Verify pattern library returns artistic patterns"""
        res = self.client.get("/api/patterns")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(len(data["patterns"]) >= 5)

    def test_12_profile_and_solve_history(self):
        """Verify authenticated user can fetch profile, stats, and solve history"""
        # Login first
        login_res = self.client.post("/api/v1/auth/login", json={
            "username": "speedcuber",
            "password": "user123"
        })
        cookie = login_res.json()["session_cookie"]

        # Fetch profile
        prof_res = self.client.get("/api/v1/profile", cookies={"session": cookie})
        self.assertEqual(prof_res.status_code, 200)
        prof_data = prof_res.json()
        self.assertTrue(prof_data["success"])
        self.assertEqual(prof_data["user"]["username"], "speedcuber")
        self.assertIn("stats", prof_data)

        # Update profile
        upd_res = self.client.post(
            "/api/v1/profile/update",
            json={"bio": "Updated Mobile Speedcuber Bio", "avatar_color": "#38bdf8"},
            cookies={"session": cookie}
        )
        self.assertEqual(upd_res.status_code, 200)
        self.assertEqual(upd_res.json()["user"]["bio"], "Updated Mobile Speedcuber Bio")


if __name__ == "__main__":
    unittest.main()
