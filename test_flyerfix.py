"""Tests for FlyerFix's non-GUI logic: image prep and the Meta API call.

Runs without a display, a network connection, or an API key: urlopen is
mocked for every compare() test. The Tkinter UI in main() is not covered.
"""

import base64
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import flyerfix
from PIL import Image


def make_image(size=(100, 80), color="red"):
    image = Image.new("RGB", size, color)
    data = io.BytesIO()
    image.save(data, format="PNG")
    data.seek(0)
    return data


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def fake_ok(content):
    return FakeResponse({"choices": [{"message": {"content": content}}]})


class LoadImageTests(unittest.TestCase):
    def test_returns_rgb_and_keeps_small_images(self):
        image = flyerfix.load_image(make_image())
        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (100, 80))

    def test_thumbnails_large_images(self):
        image = flyerfix.load_image(make_image(size=(3000, 2000)))
        self.assertTrue(image.size[0] <= 1800 and image.size[1] <= 1800)


class ImagePartTests(unittest.TestCase):
    def test_data_url_decodes_to_jpeg(self):
        part = flyerfix.image_part(Image.new("RGB", (10, 10), "blue"))
        url = part["image_url"]["url"]
        self.assertTrue(url.startswith("data:image/jpeg;base64,"))
        raw = base64.b64decode(url.split(",", 1)[1])
        self.assertEqual(raw[:2], b"\xff\xd8")  # JPEG magic bytes
        self.assertEqual(Image.open(io.BytesIO(raw)).format, "JPEG")


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.original = Image.new("RGB", (10, 10), "red")
        self.crop = Image.new("RGB", (10, 10), "blue")

    def test_returns_stripped_content(self):
        with patch.object(flyerfix, "urlopen", return_value=fake_ok("  Crop check  ")):
            self.assertEqual(
                flyerfix.compare(self.original, self.crop, "key"), "Crop check"
            )

    def test_401_points_at_the_key(self):
        error = HTTPError("url", 401, "Unauthorized", {}, None)
        with patch.object(flyerfix, "urlopen", side_effect=error):
            with self.assertRaises(ValueError) as caught:
                flyerfix.compare(self.original, self.crop, "bad-key")
        self.assertIn("API key", str(caught.exception))

    def test_429_points_at_rate_limits(self):
        error = HTTPError("url", 429, "Too Many Requests", {}, None)
        with patch.object(flyerfix, "urlopen", side_effect=error):
            with self.assertRaises(ValueError) as caught:
                flyerfix.compare(self.original, self.crop, "key")
        self.assertIn("rate limits", str(caught.exception))

    def test_empty_content_is_rejected(self):
        with patch.object(flyerfix, "urlopen", return_value=fake_ok("   ")):
            with self.assertRaises(ValueError):
                flyerfix.compare(self.original, self.crop, "key")

    def test_non_string_content_is_rejected(self):
        with patch.object(flyerfix, "urlopen", return_value=fake_ok(None)):
            with self.assertRaises(ValueError):
                flyerfix.compare(self.original, self.crop, "key")


if __name__ == "__main__":
    unittest.main()
