#!/usr/bin/env python3
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/test_ytdlp_server.py
# Purpose: Test suite for ytdlp_server.py transcript functionality
# NOT for: Production deployment without proper test coverage

import unittest
import json
import requests
import time

class TestYtdlpServer(unittest.TestCase):
    """Test suite for ytdlp_server transcript API"""

    BASE_URL = "http://127.0.0.1:8765"
    TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley

    def setUp(self):
        """Setup test environment"""
        # Verify server is running
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            self.assertEqual(response.status_code, 200)
        except:
            self.fail("ytdlp_server not running on port 8765")

    def test_transcript_returns_title(self):
        """Test that /transcript endpoint returns video title"""
        # RED PHASE: This test should FAIL initially
        response = requests.post(
            f"{self.BASE_URL}/transcript",
            json={"url": self.TEST_VIDEO, "lang": "en"},
            timeout=30
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # These assertions will FAIL if title is missing
        self.assertIn("title", data, "Response should contain 'title' field")
        self.assertIsNotNone(data.get("title"), "Title should not be None")
        self.assertNotEqual(data.get("title"), "", "Title should not be empty")
        self.assertIn("Rick", data.get("title", ""), "Title should contain 'Rick' for Rick Astley video")

    def test_transcript_returns_video_id(self):
        """Test that /transcript endpoint returns video ID"""
        response = requests.post(
            f"{self.BASE_URL}/transcript",
            json={"url": self.TEST_VIDEO, "lang": "en"},
            timeout=30
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check videoId field
        self.assertIn("videoId", data, "Response should contain 'videoId' field")
        self.assertEqual(data.get("videoId"), "dQw4w9WgXcQ", "Video ID should match")

    def test_transcript_structure(self):
        """Test that transcript response has complete structure"""
        response = requests.post(
            f"{self.BASE_URL}/transcript",
            json={"url": self.TEST_VIDEO, "lang": "en"},
            timeout=30
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check all required fields
        required_fields = ["success", "videoId", "transcript", "title", "source"]
        for field in required_fields:
            self.assertIn(field, data, f"Response should contain '{field}' field")

if __name__ == "__main__":
    # Run tests - they should FAIL initially (RED phase)
    unittest.main(verbosity=2)