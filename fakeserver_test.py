import unittest
import subprocess
import time
import requests

class TestFakeServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_process = subprocess.Popen(['python3', 'fakeserver.py'])
        time.sleep(1)  # Give the server a second to start

    @classmethod
    def tearDownClass(cls):
        cls.server_process.terminate()
        cls.server_process.wait()

    def test_server_starts(self):
        """
        Test that the server starts and listens on the port.
        """
        response = requests.get('http://127.0.0.1:5000/v1/models')
        self.assertEqual(response.status_code, 200)
        self.assertIn("model1", response.json())

    def test_chat_completions(self):
        """
        Test that the server responds to chat completions.
        """
        data = {
            "model": "model1",
            "messages": ["Hello"],
            "stream": False
        }
        response = requests.post('http://127.0.0.1:5000/v1/chat/completions', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("model", response.json())
        self.assertIn("messages", response.json())

if __name__ == '__main__':
    unittest.main()
