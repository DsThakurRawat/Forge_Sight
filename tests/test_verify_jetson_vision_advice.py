"""Host-side pins for the Jetson vision-advice verification script.

No Jetson execution happens here: the script's network helpers are replaced
so verify_case stops immediately after the advice request is captured. This
pins the explicit operator contract choice the script must send - an empty
body would silently mean the composed default and fail on assessed records."""

import json
import unittest
from unittest import mock

import scripts.verify_jetson_vision_advice as script


class StopAfterAdvicePost(Exception):
    pass


class AdviceRequestModeTests(unittest.TestCase):
    def test_advice_request_posts_explicit_vision_choice_mode(self):
        calls = []
        assessment = {"defect_type": "scratch", "severity": {"level": "HIGH"}}
        record = {"inspection_id": "insp-1", "assessment": assessment}
        latest = {"part_id": "scratch", "status": "ANALYZED",
                  "inspection_id": "insp-1", "grade": "REJECT"}
        snapshot = {"latest": latest, "busy": False, "advice": {"status": "NOT_REQUESTED"}}
        store = mock.Mock()
        store.get_inspection.return_value = record
        with mock.patch.object(script, "submit",
                               lambda base, endpoint, payload, headers:
                                   calls.append((endpoint, payload, headers))), \
             mock.patch.object(script, "state", return_value=snapshot), \
             mock.patch.object(script, "wait_for",
                               side_effect=[latest, StopAfterAdvicePost]), \
             self.assertRaises(StopAfterAdvicePost):
            script.verify_case("http://127.0.0.1:8787", None, store,
                               "scratch", "test/scratch/004.png", b"png", "HIGH")
        advice_calls = [call for call in calls if call[0] == "/api/advice"]
        self.assertEqual(len(advice_calls), 1)
        _, payload, headers = advice_calls[0]
        self.assertEqual(json.loads(payload.decode()), {"mode": "vision_choice"})
        self.assertEqual(headers.get("Content-Type"), "application/json")


if __name__ == "__main__":
    unittest.main()
