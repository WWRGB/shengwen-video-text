import json
import sys
import unittest
from unittest.mock import patch
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import main


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class BasicLogicTests(unittest.TestCase):
    def test_language_options_are_nonempty_and_targets_unique(self):
        self.assertGreater(len(main.LANGUAGE_OPTIONS), 70)
        labels = [label for label, _ in main.TARGET_LANGUAGE_OPTIONS]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(main.TARGET_CODE_BY_LABEL["简体中文"], "zh-CN")

    def test_time_format(self):
        self.assertEqual(main.format_time(3661), "01:01:01")
        self.assertEqual(main.SpeechTextApp._srt_time(1.234), "00:00:01,234")

    def test_translation_http_payload_parsing(self):
        payload = {"responseStatus": 200, "responseData": {"translatedText": "你好"}}
        with patch.object(main.urllib.request, "urlopen", return_value=FakeResponse(payload)) as opener:
            result = main.SpeechTextApp._call_mymemory("Hello", "en", "zh-CN")
        self.assertEqual(result, "你好")
        request = opener.call_args.args[0]
        self.assertIn("api.mymemory.translated.net/get?", request.full_url)
        self.assertIn("langpair=en%7Czh-CN", request.full_url)

    def test_translation_errors_raise_instead_of_fabricating_text(self):
        payload = {"responseStatus": 403, "responseDetails": "limit exceeded", "responseData": {"translatedText": ""}}
        with patch.object(main.urllib.request, "urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(RuntimeError):
                main.SpeechTextApp._call_mymemory("Hello", "en", "xx")


if __name__ == "__main__":
    unittest.main()
