"""The operation log must persist worker failures that used to vanish."""

import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
import time
import unittest
from unittest import mock

from forgesight.jetson_live_ui import LiveService
from forgesight.operation_log import LOGGER_NAME, configure_operation_log, operation_logger


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class OperationLogTests(unittest.TestCase):
    def setUp(self):
        self.logger = operation_logger()
        self.saved_handlers = list(self.logger.handlers)
        self.saved_level = self.logger.level
        self.saved_propagate = self.logger.propagate
        for handler in self.saved_handlers:
            self.logger.removeHandler(handler)
        self.capture = ListHandler()
        self.logger.addHandler(self.capture)
        self.logger.setLevel(logging.INFO)
        self.addCleanup(self.restore)

    def restore(self):
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)
        for handler in self.saved_handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(self.saved_level)
        self.logger.propagate = self.saved_propagate

    def test_configure_writes_one_rotating_file_and_is_idempotent(self):
        with TemporaryDirectory() as folder:
            first = configure_operation_log(folder)
            again = configure_operation_log(folder)
            rotating = [h for h in again.handlers if isinstance(h, RotatingFileHandler)]
            self.assertIs(first, again)
            self.assertEqual(len(rotating), 1)
            self.assertEqual(rotating[0].maxBytes, 1024 * 1024)
            self.assertEqual(rotating[0].backupCount, 5)
            self.assertFalse(again.propagate)
            again.info("test-marker-end-to-end-trace")
            for handler in again.handlers:
                handler.flush()
            content = (Path(folder) / "forgesight-operations.log").read_text()
            self.assertIn("test-marker-end-to-end-trace", content)

    def bare_service(self):
        with mock.patch.object(LiveService, "__init__", lambda self, *a, **k: None):
            service = LiveService()
        service.args = argparse.Namespace(
            vision_python=Path("python"), model=Path("model.ts"),
            grade_policy=Path("policy.json"), database=Path("db.sqlite3"),
            camera_index=0, vision_worker_socket=Path("/tmp/worker.sock"),
            overlay_format="png")
        service.worker_respawning = False
        service.worker_respawn_lock = Lock()
        service.vision_worker = None
        return service

    def wait_respawn(self, service):
        for _ in range(200):
            if not service.worker_respawning and self.capture.records:
                return
            time.sleep(0.01)

    def test_vision_respawn_failure_is_logged_not_swallowed(self):
        service = self.bare_service()
        with mock.patch("forgesight.jetson_live_ui.launch_vision_worker",
                        side_effect=ValueError("model hash mismatch at boot")):
            service._respawn_vision_worker()
            self.wait_respawn(service)
        errors = [r for r in self.capture.records if r.levelno >= logging.ERROR]
        self.assertTrue(any("Vision worker respawn failed" in r.getMessage()
                            for r in errors))
        self.assertTrue(any("model hash mismatch at boot" in (r.exc_text or "")
                            or r.exc_info for r in errors))

    def test_successful_respawn_is_logged(self):
        service = self.bare_service()
        with mock.patch("forgesight.jetson_live_ui.launch_vision_worker",
                        return_value=mock.Mock()):
            service._respawn_vision_worker()
            for _ in range(200):
                if any("Vision worker respawned" in r.getMessage()
                       for r in self.capture.records):
                    break
                time.sleep(0.01)
        self.assertTrue(any("Vision worker respawned" in r.getMessage()
                            for r in self.capture.records))

    def test_cold_fallback_marker_logs_the_inspection_id(self):
        service = self.bare_service()
        service._publish_result = mock.Mock()
        service._respawn_vision_worker = mock.Mock()
        record = {"status": "ANALYZED", "inspection_id": "insp-cold-1",
                  "timings": {"vision_mode": "COLD_PROCESS_AFTER_WORKER_UNAVAILABLE"}}
        with mock.patch("forgesight.vision_edge_live_once.inspect", return_value=record):
            service._inspect_inline(Path("image.png"), "part-t1", Path("/tmp/root-t1"),
                                    dict(mvtec_benchmark_upload=True,
                                         uploaded_image_diagnostic=False,
                                         operator_declared_part=False,
                                         screen_photo_diagnostic=False,
                                         diagnostic_no_part=False))
        self.assertTrue(any("insp-cold-1" in r.getMessage()
                            and r.levelno == logging.WARNING
                            for r in self.capture.records))


if __name__ == "__main__":
    unittest.main()
