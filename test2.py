import unittest
from main import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Academic QA Assistant', response.data)

    def test_process_files_no_upload(self):
        response = self.app.post('/process_files', data={})
        self.assertEqual(response.status_code, 302)  # Redirect due to flash
        # Further assertions can be made by following the redirect

    # Add more tests as needed

if __name__ == '__main__':
    unittest.main()
