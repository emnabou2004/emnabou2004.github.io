import os
import shutil
import unittest

from app import app, POSTS_DIR


class BlogAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def tearDown(self):
        for path in POSTS_DIR.glob('*.md'):
            if path.name.startswith('test-') or path.name.startswith('sample-'):
                path.unlink()

    def test_publish_markdown_creates_post(self):
        response = self.client.post('/api/posts', json={
            'title': 'Test Note',
            'content': '# Hello\n\nThis is a test.'
        })

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertTrue((POSTS_DIR / 'test-note.md').exists())


if __name__ == '__main__':
    unittest.main()
