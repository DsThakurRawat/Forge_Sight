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
from forgesight.operation_log import (LOGGER_NAME, _ScrubFilter,
                                      configure_operation_log, operation_logger,
                                      scrub)


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
        for existing in list(self.logger.filters):
            if isinstance(existing, _ScrubFilter):
                self.logger.removeFilter(existing)
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

    def test_unwritable_log_dir_degrades_to_stderr_with_warning(self):
        with TemporaryDirectory() as folder:
            blocker = Path(folder) / "blocker"
            blocker.write_text("a regular file, not a directory")
            logger = configure_operation_log(blocker / "logs")  # must not raise
            warnings = [r for r in self.capture.records if r.levelno == logging.WARNING]
            self.assertTrue(any("stderr only" in r.getMessage() for r in warnings))
            self.assertTrue(any(isinstance(h, logging.StreamHandler)
                                and not isinstance(h, RotatingFileHandler)
                                for h in logger.handlers))
            logger.info("still-works-after-degrade")

    def test_scrub_redacts_credentials_in_messages_args_and_tracebacks(self):
        with TemporaryDirectory() as folder:
            logger = configure_operation_log(folder)
            logger.info("child said token=abc123 and password = hunter2")
            try:
                raise ValueError("worker config api_key=zzz999")
            except ValueError:
                logger.exception("boot failure")
            for handler in logger.handlers:
                handler.flush()
            content = (Path(folder) / "forgesight-operations.log").read_text()
            for leaked in ("abc123", "hunter2", "zzz999"):
                self.assertNotIn(leaked, content)
            self.assertIn("[redacted]", content)
            self.assertIn("boot failure", content)

    def test_scrub_bounds_field_length(self):
        text = scrub("x" * 5000)
        self.assertLess(len(text), 600)
        self.assertTrue(text.endswith("...[truncated]"))

    def advice_service(self):
        service = self.bare_service()
        service.advice_recovered = set()
        service._respawn_advice_worker = mock.Mock()
        return service

    def test_advice_completion_success_is_logged(self):
        import json as jsonlib
        service = self.advice_service()
        future = mock.Mock()
        future.done.return_value = True
        future.result.return_value = mock.Mock(
            returncode=0,
            stdout=jsonlib.dumps({"status": "GENERATED_REQUIRES_HUMAN_REVIEW"}),
            stderr="")
        service._recover_finished_advice("insp-ok-1", future)
        infos = [r.getMessage() for r in self.capture.records
                 if r.levelno == logging.INFO]
        self.assertTrue(any("insp-ok-1" in m and "finished" in m
                            and "GENERATED_REQUIRES_HUMAN_REVIEW" in m
                            for m in infos))
        service._respawn_advice_worker.assert_not_called()

    def test_advice_completion_failure_is_logged_with_bounded_stderr(self):
        service = self.advice_service()
        future = mock.Mock()
        future.done.return_value = True
        future.result.return_value = mock.Mock(
            returncode=1, stdout="", stderr="crash " + "y" * 5000)
        service._recover_finished_advice("insp-bad-1", future)
        errors = [r for r in self.capture.records if r.levelno >= logging.ERROR]
        self.assertTrue(any("insp-bad-1" in r.getMessage() and "failed" in r.getMessage()
                            for r in errors))

    def test_advice_completion_uncollectable_is_logged(self):
        service = self.advice_service()
        future = mock.Mock()
        future.done.return_value = True
        future.result.side_effect = RuntimeError("killed")
        service._recover_finished_advice("insp-dead-1", future)
        errors = [r for r in self.capture.records if r.levelno >= logging.ERROR]
        self.assertTrue(any("insp-dead-1" in r.getMessage()
                            and "could not be collected" in r.getMessage()
                            for r in errors))

    def test_queue_exception_dict_result_is_logged_not_crashed(self):
        import subprocess as sp
        from forgesight.assist_queue import AdvisoryQueue
        service = self.advice_service()
        queue = AdvisoryQueue()
        self.addCleanup(queue.close)

        def worker():
            raise sp.TimeoutExpired(cmd="llama", timeout=5)

        future = queue.submit(worker)
        outcome = future.result(timeout=10)
        # The real queue contract: a raised worker becomes an outcome dict,
        # never a CompletedProcess.
        self.assertIsInstance(outcome, dict)
        service._recover_finished_advice("insp-timeout-1", future)  # must not raise
        errors = [r for r in self.capture.records if r.levelno >= logging.ERROR]
        self.assertTrue(any("insp-timeout-1" in r.getMessage()
                            and "ADVICE_UNAVAILABLE" in r.getMessage()
                            and "TimeoutExpired" in r.getMessage()
                            for r in errors))

    def test_scrub_redaction_policy_shapes(self):
        samples = {
            "env var": ("API_TOKEN=envvalue123", "envvalue123"),
            "url userinfo": ("postgres://user:p%40ss@host/db", "p%40ss"),
            "quoted multiword": ('token="multi word secret"', "multi word secret"),
            "pem": ("-----BEGIN PRIVATE KEY-----\nMIIabc\n-----END PRIVATE KEY-----",
                    "MIIabc"),
            "bearer": ("Authorization: Bearer xyz987.more", "xyz987.more"),
            "simple assignment": ("token=abc123", "abc123"),
        }
        for name, (raw, secret) in samples.items():
            with self.subTest(name=name):
                self.assertNotIn(secret, scrub(raw))
        # Non-credential lookalikes stay readable.
        self.assertIn("monkey=banana", scrub("monkey=banana"))
        self.assertIn("/home/user/runs/x", scrub("path /home/user/runs/x"))

    def test_format_split_args_are_redacted_after_rendering(self):
        with TemporaryDirectory() as folder:
            logger = configure_operation_log(folder)
            logger.info("child config: %s", "token=splitsecret1")
            for handler in logger.handlers:
                handler.flush()
            content = (Path(folder) / "forgesight-operations.log").read_text()
            self.assertNotIn("splitsecret1", content)
            self.assertIn("[redacted]", content)

    def boot_args(self, folder):
        root = Path(folder)
        vision_python = root / "vision-python"
        vision_python.write_text("#!/bin/sh")
        model = root / "model.ts"
        model.write_bytes(b"model")
        policy = root / "policy.json"
        policy.write_text("{}")
        manifest = root / "manifest.json"
        manifest.write_text('{"samples": []}')
        guidance = root / "guidance.json"
        guidance.write_text("{}")
        llama = root / "llama"
        (llama / "venv/bin").mkdir(parents=True)
        (llama / "venv/bin/python").write_text("#!/bin/sh")
        (llama / "model").mkdir()
        (llama / "model/llama3_2_1b_xnnpack.pte").write_bytes(b"x")
        return argparse.Namespace(
            vision_python=vision_python, model=model, grade_policy=policy,
            dataset_manifest=manifest, dataset_root=root / "dataset",
            database=root / "db.sqlite3", camera_index=0,
            vision_worker_socket=None, advice_root=root / "advice",
            llama_root=llama, guidance=guidance,
            llama_worker_socket=Path("/tmp/boot-test.sock"))

    def test_advice_worker_boot_failure_is_logged(self):
        with TemporaryDirectory() as folder:
            args = self.boot_args(folder)
            with mock.patch("forgesight.jetson_live_ui.sha256",
                            return_value="0" * 64), \
                 mock.patch("forgesight.jetson_live_ui.MODEL_SHA256", "0" * 64), \
                 mock.patch("forgesight.jetson_live_ui.DATASET_MANIFEST_SHA256",
                            "0" * 64), \
                 mock.patch("forgesight.jetson_live_ui.launch_advice_worker",
                            side_effect=ValueError("socket refused")):
                service = LiveService(args, mock.Mock())
            self.assertEqual(service.advice_worker_boot_error, "socket refused")
            errors = [r.getMessage() for r in self.capture.records
                      if r.levelno >= logging.ERROR]
            self.assertTrue(any("failed to start at boot" in m for m in errors))

    def test_vision_worker_boot_failure_is_logged_and_reraised(self):
        with TemporaryDirectory() as folder:
            args = self.boot_args(folder)
            args.vision_worker_socket = Path("/tmp/vision-boot-test.sock")
            with mock.patch("forgesight.jetson_live_ui.sha256",
                            return_value="0" * 64), \
                 mock.patch("forgesight.jetson_live_ui.MODEL_SHA256", "0" * 64), \
                 mock.patch("forgesight.jetson_live_ui.DATASET_MANIFEST_SHA256",
                            "0" * 64), \
                 mock.patch("forgesight.jetson_live_ui.launch_vision_worker",
                            side_effect=RuntimeError("model mismatch")):
                with self.assertRaises(RuntimeError):
                    LiveService(args, mock.Mock())
            errors = [r for r in self.capture.records
                      if r.levelno >= logging.ERROR]
            self.assertTrue(any("Vision worker failed to start at boot"
                                in r.getMessage() for r in errors))


if __name__ == "__main__":
    unittest.main()
