"""Respawn backoff and the close-vs-launch race.

Before this change every cold-fallback request could start a fresh respawn
attempt (unthrottled against a permanently broken worker), and close()
could finish while a background respawn was mid-launch, leaving a live
worker process attached to a closed service.
"""

from pathlib import Path
from threading import Event, Lock
import time
import unittest
from unittest import mock

from forgesight.jetson_live_ui import LiveService, WORKER_RESPAWN_MIN_INTERVAL_SECONDS


class RespawnLifecycleTests(unittest.TestCase):
    def bare(self):
        with mock.patch.object(LiveService, "__init__", lambda self, *a, **k: None):
            service = LiveService()
        service.advice_worker_respawn_lock = Lock()
        service.advice_worker_respawning = False
        service.worker_respawn_lock = Lock()
        service.worker_respawning = False
        service.advice_worker = None
        service.vision_worker = None
        service.llama_ready = True
        service.closed = False
        service.args = mock.Mock()
        return service

    def wait_idle(self, service, kind="advice"):
        attr = "advice_worker_respawning" if kind == "advice" else "worker_respawning"
        for _ in range(500):
            if not getattr(service, attr):
                return
            time.sleep(0.005)
        self.fail("respawn thread did not settle")

    def test_respawn_attempts_are_backed_off(self):
        service = self.bare()
        with mock.patch("forgesight.jetson_live_ui.launch_advice_worker",
                        side_effect=ValueError("still broken")) as launch:
            service._respawn_advice_worker()
            self.wait_idle(service)
            service._respawn_advice_worker()
            self.wait_idle(service)
            self.assertEqual(launch.call_count, 1)
            # After the interval a new attempt is allowed again.
            service._advice_respawn_last -= WORKER_RESPAWN_MIN_INTERVAL_SECONDS + 1
            service._respawn_advice_worker()
            self.wait_idle(service)
            self.assertEqual(launch.call_count, 2)

    def test_vision_respawn_attempts_are_backed_off(self):
        service = self.bare()
        with mock.patch("forgesight.jetson_live_ui.launch_vision_worker",
                        side_effect=ValueError("still broken")) as launch:
            service._respawn_vision_worker()
            self.wait_idle(service, "vision")
            service._respawn_vision_worker()
            self.wait_idle(service, "vision")
            self.assertEqual(launch.call_count, 1)

    def test_respawn_after_close_is_skipped(self):
        service = self.bare()
        service.closed = True
        with mock.patch("forgesight.jetson_live_ui.launch_vision_worker") as launch, \
             mock.patch("forgesight.jetson_live_ui.launch_advice_worker") as alaunch:
            service._respawn_vision_worker()
            service._respawn_advice_worker()
            self.assertFalse(service.worker_respawning)
            self.assertFalse(service.advice_worker_respawning)
            launch.assert_not_called()
            alaunch.assert_not_called()

    def test_close_during_launch_terminates_the_new_worker(self):
        service = self.bare()
        entered = Event()
        release = Event()
        new_worker = mock.Mock()
        new_worker.poll.return_value = None

        def slow_launch(args):
            entered.set()
            self.assertTrue(release.wait(timeout=10))
            return new_worker

        with mock.patch("forgesight.jetson_live_ui.launch_advice_worker",
                        side_effect=slow_launch):
            service._respawn_advice_worker()
            self.assertTrue(entered.wait(timeout=10))
            service.closed = True  # close() begins while the launch is blocked
            release.set()
            self.wait_idle(service)
        new_worker.terminate.assert_called_once()
        self.assertIsNone(service.advice_worker)

    def test_close_sets_the_flag_before_terminating(self):
        service = self.bare()
        service.advice_queue = mock.Mock()
        service.close()
        self.assertTrue(service.closed)


if __name__ == "__main__":
    unittest.main()
