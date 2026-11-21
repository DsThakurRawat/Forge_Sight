"""Read-only runs_root reconciliation and low-disk reporting.

Orphan run directories (partial kills, SQLite-unconfirmed records) are
identified and reported, never deleted. Nothing here mutates evidence.
"""

import argparse
import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from forgesight.jetson_live_ui import LiveService
from forgesight.operation_log import operation_logger
from forgesight.storage import InspectionStore


class StorageHealthTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.runs = self.root / "runs"
        self.runs.mkdir()
        self.store = InspectionStore(self.root / "inspections.sqlite3")
        self.service = LiveService.__new__(LiveService)
        self.service.store = self.store
        self.service.args = argparse.Namespace(runs_root=self.runs)
        self.logger = operation_logger()
        self.records = []
        handler = logging.Handler()
        handler.emit = self.records.append
        self.logger.addHandler(handler)
        self.addCleanup(self.logger.removeHandler, handler)

    def make_run(self, name, record=None):
        folder = self.runs / name
        (folder / "result").mkdir(parents=True)
        if record is not None:
            (folder / "result" / "record.json").write_text(json.dumps(record))
        return folder

    def confirmed_record(self):
        record = json.loads(
            Path("manifests/graded_inspection_replay_v1.json").read_text())["records"][0]
        self.store.save_inspection(record)
        return record

    def test_partial_and_unconfirmed_runs_are_orphans_confirmed_is_not(self):
        record = self.confirmed_record()
        self.make_run("replay_confirmed", record)
        self.make_run("part_partial")  # killed before record.json
        unconfirmed = dict(record, inspection_id="11111111-1111-1111-1111-111111111111",
                           part_id="NUT-ORPHAN-1")
        self.make_run("user_upload_unconfirmed", unconfirmed)
        (self.runs / "advice").mkdir()  # not a run dir
        (self.runs / "logs").mkdir()
        health = self.service.storage_health()
        self.assertEqual(health["orphan_count"], 2)
        self.assertEqual(sorted(health["orphan_runs"]),
                         ["part_partial", "user_upload_unconfirmed"])
        self.assertIsInstance(health["disk_free_bytes"], int)
        warnings = [r.getMessage() for r in self.records
                    if r.levelno == logging.WARNING]
        self.assertTrue(any("orphan run dir(s)" in message for message in warnings))

    def test_low_disk_is_flagged_and_logged(self):
        fake = mock.Mock(free=1024)
        with mock.patch("forgesight.jetson_live_ui.shutil.disk_usage",
                        return_value=fake):
            health = self.service.storage_health()
        self.assertTrue(health["low_disk"])
        self.assertEqual(health["disk_free_bytes"], 1024)
        self.assertTrue(any("Low disk space" in r.getMessage()
                            for r in self.records))

    def test_health_is_cached_for_sixty_seconds(self):
        first = self.service.storage_health(now=1000.0)
        self.make_run("part_neworphan")
        again = self.service.storage_health(now=1030.0)
        self.assertIs(again, first)
        refreshed = self.service.storage_health(now=1061.0)
        self.assertEqual(refreshed["orphan_count"], 1)

    def test_locked_store_reports_unavailable_not_zero_orphans(self):
        import sqlite3
        self.make_run("part_consulted",
                      {"inspection_id": "11111111-1111-1111-1111-111111111111"})
        with mock.patch.object(self.store, "get_inspection",
                               side_effect=sqlite3.OperationalError("locked")):
            health = self.service.storage_health()
        self.assertEqual(health["status"], "UNAVAILABLE")
        # A store failure must not masquerade as "no orphans".
        self.assertFalse(health["status"] == "OK" and health["orphan_count"])

    def test_state_survives_store_failure(self):
        import sqlite3
        self.service.lock = __import__("threading").Lock()
        self.service.latest = None
        self.service.busy = False
        self.service.replay_samples = {}
        self.service.local_replay_samples = []
        self.service.advice_state = lambda: {"status": "NOT_CONNECTED", "advisory": None}
        self.service.camera = mock.Mock()
        self.service.camera.state.return_value = {"ready": False, "message": "x"}
        self.make_run("part_consulted",
                      {"inspection_id": "11111111-1111-1111-1111-111111111111"})
        with mock.patch.object(self.store, "get_inspection",
                               side_effect=sqlite3.OperationalError("locked")):
            state = self.service.state()  # must not raise
        self.assertEqual(state["storage"]["status"], "UNAVAILABLE")

    def test_tampered_same_id_record_is_classified_mismatch(self):
        record = self.confirmed_record()
        tampered = dict(record)
        tampered["decision"] = dict(record["decision"], grade="SCRAP")
        self.make_run("replay_tampered", tampered)
        health = self.service.storage_health()
        self.assertEqual(health["orphans"], {"replay_tampered": "mismatch"})

    def test_symlinked_run_dir_is_not_traversed(self):
        outside = self.root / "outside"
        outside.mkdir()
        link = self.runs / "part_link"
        link.symlink_to(outside, target_is_directory=True)
        health = self.service.storage_health()
        self.assertEqual(health["orphan_count"], 0)

    def test_symlinked_result_dir_is_rejected_before_any_read(self):
        outside = self.root / "outside"
        (outside / "result").mkdir(parents=True)
        marker = outside / "result" / "record.json"
        marker.write_text(json.dumps(
            {"inspection_id": "11111111-1111-1111-1111-111111111111"}))
        folder = self.runs / "part_nested"
        folder.mkdir()
        (folder / "result").symlink_to(outside / "result",
                                       target_is_directory=True)
        with mock.patch.object(self.store, "get_inspection") as lookup:
            health = self.service.storage_health()
        self.assertEqual(health["orphans"], {"part_nested": "invalid"})
        lookup.assert_not_called()  # the outside record was never consulted

    def test_entry_scan_is_capped_and_streamed(self):
        for index in range(10):
            (self.runs / ("filler-%02d" % index)).mkdir()
        self.make_run("part_real")
        with mock.patch("forgesight.jetson_live_ui.STORAGE_SCAN_MAX_ENTRIES", 3):
            health = self.service.storage_health()
        self.assertEqual(health["status"], "INCOMPLETE")
        self.assertTrue(health["truncated"])

    def test_scan_is_bounded_and_reports_incomplete(self):
        for index in range(5):
            self.make_run("part_%03d" % index)
        with mock.patch("forgesight.jetson_live_ui.STORAGE_SCAN_MAX_DIRS", 3):
            health = self.service.storage_health()
        self.assertEqual(health["status"], "INCOMPLETE")
        self.assertTrue(health["truncated"])
        self.assertLessEqual(health["orphan_count"], 3)

    def test_state_exposes_storage_health(self):
        self.service.lock = __import__("threading").Lock()
        self.service.latest = None
        self.service.busy = False
        self.service.replay_samples = {}
        self.service.local_replay_samples = []
        self.service.advice_state = lambda: {"status": "NOT_CONNECTED", "advisory": None}
        self.service.camera = mock.Mock()
        self.service.camera.state.return_value = {"ready": False, "message": "x"}
        state = self.service.state()
        self.assertIn("storage", state)
        self.assertEqual(state["storage"]["orphan_count"], 0)


if __name__ == "__main__":
    unittest.main()
