"""The outer UI vision budget must cover a worker hang plus a cold retry.

Before this change the UI killed the vision_edge subprocess at 180s while
the inner pipeline could legitimately consume the worker client budget
(180s) and then a full cold-fallback child budget (180s). A hung worker
therefore produced a killed cold retry, a partial run directory and no
record. The outer budget is now derived from the named inner budgets.
"""

import argparse
import inspect as pyinspect
from pathlib import Path
from threading import Lock
import unittest
from unittest import mock

from forgesight import jetson_live_ui, vision_edge_live_once, vision_edge_replay
from forgesight.jetson_live_ui import LiveService, VISION_OUTER_TIMEOUT_SECONDS


class TimeoutBudgetTests(unittest.TestCase):
    def test_outer_budget_covers_worst_inner_path(self):
        for inner in (vision_edge_live_once, vision_edge_replay):
            with self.subTest(inner=inner.__name__):
                worst = (inner.WORKER_REQUEST_TIMEOUT_SECONDS
                         + inner.CHILD_TIMEOUT_SECONDS)
                self.assertGreater(VISION_OUTER_TIMEOUT_SECONDS, worst)

    def test_inner_modules_use_named_budgets(self):
        from forgesight import vision_edge_worker
        self.assertIn("timeout_seconds=WORKER_REQUEST_TIMEOUT_SECONDS",
                      pyinspect.getsource(vision_edge_worker))
        for inner in (vision_edge_live_once, vision_edge_replay):
            with self.subTest(inner=inner.__name__):
                source = pyinspect.getsource(inner)
                self.assertIn("WORKER_REQUEST_TIMEOUT_SECONDS", source)
                self.assertIn("timeout=CHILD_TIMEOUT_SECONDS", source)

    def test_ui_uses_named_outer_budget_for_all_vision_children(self):
        source = pyinspect.getsource(jetson_live_ui)
        self.assertEqual(
            source.count("text=True, timeout=VISION_OUTER_TIMEOUT_SECONDS"), 3)

    def test_run_replay_passes_outer_budget_to_subprocess(self):
        service = LiveService.__new__(LiveService)
        service.args = argparse.Namespace(
            vision_python=Path("python"), model=Path("model.ts"),
            grade_policy=Path("policy.json"), database=Path("db.sqlite3"),
            dataset_manifest=Path("manifest.json"), vision_worker_socket=None)
        service._publish_result = mock.Mock()
        service.lock = Lock()
        service.busy = True
        sample = {"sha256": "0" * 64, "path": "test/bent/017.png"}
        with mock.patch("forgesight.jetson_live_ui.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            service._run_replay("REPLAY-1", Path("image.png"), sample,
                                Path("/tmp/run-budget-test"))
        self.assertEqual(run.call_args.kwargs["timeout"],
                         VISION_OUTER_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
