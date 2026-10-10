import unittest
import requests

BASE_URL = 'http://127.0.0.1:5050'

class TestNewsfeedAndPrivacy(unittest.TestCase):

    def setUp(self):
        self.session = requests.Session()
        # Ensure speedcuber logs in
        login_res = self.session.post(
            f"{BASE_URL}/login",
            data={'username': 'speedcuber', 'password': 'user123'},
            allow_redirects=False
        )
        self.login_redirect = login_res.headers.get('Location')

    def test_01_subscriber_login_redirects_to_newsfeed(self):
        self.assertIn('/feed', self.login_redirect, f"Expected /feed redirect, got {self.login_redirect}")

    def test_02_newsfeed_page_renders_with_facebook_elements(self):
        res = self.session.get(f"{BASE_URL}/feed")
        self.assertEqual(res.status_code, 200)
        content = res.text
        self.assertIn("News Feed", content)
        self.assertIn("Direct Inbox", content)
        self.assertIn("Notifications", content)
        self.assertIn("global-search-input", content)
        self.assertIn("What's on your mind", content)
        self.assertIn("Profile Privacy", content)

    def test_03_authenticated_root_redirects_to_feed(self):
        root_res = self.session.get(f"{BASE_URL}/", allow_redirects=False)
        self.assertIn('/feed', root_res.headers.get('Location', ''))

    def test_04_create_post_and_invitation(self):
        # Public community post
        res_post = self.session.post(
            f"{BASE_URL}/feed/post",
            data={
                'title': 'Test Permutation Post',
                'content': 'Discussing cycle notation and commutators in S54.',
                'post_type': 'post',
                'privacy': 'public'
            },
            allow_redirects=False
        )
        self.assertIn(res_post.status_code, (200, 302))

        # Game invitation post
        res_invite = self.session.post(
            f"{BASE_URL}/feed/post",
            data={
                'title': 'Call Break 4-Player Table Invite',
                'content': 'Join our high stakes card table!',
                'post_type': 'card_invite',
                'game_type': 'call_break',
                'invite_code': 'CB-TEST-01',
                'privacy': 'public'
            },
            allow_redirects=False
        )
        self.assertIn(res_invite.status_code, (200, 302))

    def test_05_universal_search(self):
        res = self.session.get(f"{BASE_URL}/feed/api/search?q=Call")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        results = data['results']
        self.assertIn('posts', results)
        self.assertIn('invitations', results)
        self.assertIn('users', results)
        self.assertGreater(len(results['invitations']), 0)

    def test_06_profile_privacy_protection(self):
        # Set profile to private
        priv_res = self.session.post(
            f"{BASE_URL}/feed/privacy-toggle",
            json={'is_private': True}
        )
        self.assertTrue(priv_res.json()['is_private'])

        # Now view from another user's session (admin)
        admin_sess = requests.Session()
        admin_sess.post(f"{BASE_URL}/login", data={'username': 'admin', 'password': 'admin123'})

        # Fetch speedcuber (id=3) info as admin
        user_res = admin_sess.get(f"{BASE_URL}/feed/api/user/3")
        self.assertEqual(user_res.status_code, 200)
        u_info = user_res.json()['user']

        # Strict privacy enforcement check:
        self.assertTrue(u_info['is_private_view'])
        self.assertEqual(u_info['username'], 'speedcuber')
        self.assertIn('Hidden', u_info['email'])
        self.assertIn('Hidden', str(u_info['pb_single']))
        self.assertIn('Hidden', str(u_info['coins_balance']))
        self.assertIn('Private', u_info['bio'])

    def test_07_inbox_messaging(self):
        # Send direct message to admin (id=1)
        dm_res = self.session.post(
            f"{BASE_URL}/feed/api/inbox/send",
            json={'receiver_id': 1, 'message': 'Hey Admin, let us play Call Break!'}
        )
        self.assertEqual(dm_res.status_code, 200)
        self.assertTrue(dm_res.json()['success'])

        # Fetch conversation
        conv_res = self.session.get(f"{BASE_URL}/feed/api/inbox/messages?with_user_id=1")
        self.assertEqual(conv_res.status_code, 200)
        conv_data = conv_res.json()
        self.assertTrue(conv_data['success'])
        self.assertGreater(len(conv_data['messages']), 0)

    def test_08_post_like_and_comment(self):
        # Like first post
        like_res = self.session.post(f"{BASE_URL}/feed/like/1")
        self.assertEqual(like_res.status_code, 200)
        self.assertTrue(like_res.json()['success'])

        # Comment on first post
        cmt_res = self.session.post(
            f"{BASE_URL}/feed/comment/1",
            json={'comment': 'Great post on Rubique!'}
        )
        self.assertEqual(cmt_res.status_code, 200)
        self.assertTrue(cmt_res.json()['success'])
        self.assertEqual(cmt_res.json()['comment']['comment'], 'Great post on Rubique!')

    def test_09_create_image_and_video_posts(self):
        import io
        # 1. Post with Image URL
        img_url = "https://images.unsplash.com/photo-1591994843349-f415893b3a6b?w=800"
        res_img = self.session.post(
            f"{BASE_URL}/feed/post",
            data={
                'title': 'Speedcube Collection Showcase',
                'content': 'Check out my new magnetic 3x3 flagship cube!',
                'post_type': 'post',
                'image_url': img_url,
                'privacy': 'public'
            },
            allow_redirects=True
        )
        self.assertEqual(res_img.status_code, 200)
        self.assertIn('Speedcube Collection Showcase', res_img.text)
        self.assertIn(img_url, res_img.text)
        self.assertIn('Photo', res_img.text)

        # 2. Post with Video URL (YouTube)
        yt_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        res_vid = self.session.post(
            f"{BASE_URL}/feed/post",
            data={
                'title': 'Sub-10 CFOP Walkthrough Video',
                'content': 'Full step-by-step breakdown of cross to F2L transitions.',
                'post_type': 'post',
                'video_url': yt_url,
                'privacy': 'public'
            },
            allow_redirects=True
        )
        self.assertEqual(res_vid.status_code, 200)
        self.assertIn('Sub-10 CFOP Walkthrough Video', res_vid.text)
        self.assertIn('youtube.com/embed/dQw4w9WgXcQ', res_vid.text)
        self.assertIn('Video', res_vid.text)

        # 3. Post with Direct Image File Upload
        fake_image = io.BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        res_upload = self.session.post(
            f"{BASE_URL}/feed/post",
            data={
                'title': 'Uploaded Custom Cube Photo',
                'content': 'Direct binary upload test for feed posts.',
                'post_type': 'post',
                'privacy': 'public'
            },
            files={'image_file': ('cube_photo.png', fake_image, 'image/png')},
            allow_redirects=True
        )
        self.assertEqual(res_upload.status_code, 200)
        self.assertIn('Uploaded Custom Cube Photo', res_upload.text)
        self.assertIn('/static/uploads/feed/', res_upload.text)

if __name__ == '__main__':
    unittest.main()

