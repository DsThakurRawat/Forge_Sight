"""The offline runtime check must not consume held-out evaluation images."""

import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

import numpy as np
from PIL import Image

from forgesight import vision_edge_replay as replay
from forgesight.storage import InspectionStore
from forgesight.vision_edge_replay import select_replay_sample
from tests.test_live_once_worker_mode import fake_cold_vision_child

REPO = Path(__file__).resolve().parent.parent
POLICY = REPO / "configs" / "forgegrade_benchmark_v1.json"
FROZEN_EXPORT_SHA256 = "8766c41a51a5444f57f564134427bbd2d2d95dd6ec5ff08b24698f00f7f55dcd"


class ReplayEvidenceTests(unittest.TestCase):
    """Persisted replays must refuse producer reports that misdeclare the maps."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        image_path = self.root / "dataset" / "test" / "bent" / "017.png"
        image_path.parent.mkdir(parents=True)
        Image.new("RGB", (700, 700), "gray").save(image_path)
        self.image_sha = hashlib.sha256(image_path.read_bytes()).hexdigest()
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({"samples": [
            {"path": "test/bent/017.png", "sha256": self.image_sha,
             "role": "development_preview"}]}))
        self.image = image_path

    def run_replay(self, part_id, mutate=None):
        output = self.root / ("out-" + part_id)
        argv = ["vision_edge_replay.py", "--image", str(self.image),
                "--image-sha256", self.image_sha,
                "--dataset-manifest", str(self.manifest), "--part-id", part_id,
                "--vision-python", "python", "--model", str(self.root / "model.ts"),
                "--model-sha256", FROZEN_EXPORT_SHA256,
                "--grade-policy", str(POLICY),
                "--database", str(self.root / ("db-" + part_id + ".sqlite3")),
                "--output-dir", str(output)]

        def run_child(child_argv):
            if "--tensor" in child_argv and "--output" not in child_argv:
                tensor_path = Path(child_argv[child_argv.index("--tensor") + 1])
                with tensor_path.open("xb") as stream:
                    np.save(stream, np.zeros((1, 3, 256, 256), dtype=np.float32),
                            allow_pickle=False)
            elif "--output" in child_argv:
                tensor = Path(child_argv[child_argv.index("--tensor") + 1])
                report = fake_cold_vision_child(child_argv, tensor,
                                                model_sha=FROZEN_EXPORT_SHA256)
                if mutate:
                    mutate(report)
                    Path(child_argv[child_argv.index("--output") + 1]).write_text(
                        json.dumps(report))
            return 1.0

        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(replay, "run_child", side_effect=run_child), \
                mock.patch("sys.stdout"):
            replay.main()
        return json.loads((output / "record.json").read_text())

    def test_declared_map_hashes_matching_the_saved_maps_pass(self):
        record = self.run_replay("replay-honest")
        self.assertEqual(record["status"], "ANALYZED")
        stored = InspectionStore(self.root / "db-replay-honest.sqlite3", create=False)
        self.assertEqual(stored.get_inspection(record["inspection_id"]), record)

    def test_misdeclared_map_hashes_fail_instead_of_being_blessed(self):
        for name, mutate in (("model-map", lambda r: r.update(map_sha256="0" * 64)),
                             ("source-map", lambda r: r.update(source_map_sha256="0" * 64)),
                             ("missing", lambda r: r.pop("source_map_sha256"))):
            with self.subTest(case=name):
                part_id = "replay-bad-" + name
                with self.assertRaises(SystemExit) as caught:
                    self.run_replay(part_id, mutate)
                self.assertEqual(caught.exception.code, 1)
                record = json.loads(
                    (self.root / ("out-" + part_id) / "record.json").read_text())
                self.assertEqual(record["status"], "ERROR")
                self.assertIn("Inconsistent model inference evidence",
                              record["error"]["message"])
                self.assertEqual(record["decision"]["grade"], "REVIEW")


class ReplayRoleTests(unittest.TestCase):
    def setUp(self):
        self.samples = [
            {"path": "test/bent/017.png", "sha256": "dev", "role": "development_preview"},
            {"path": "train/good/000.png", "sha256": "fit", "role": "fit"},
            {"path": "train/good/001.png", "sha256": "other", "role": "fit"},
            {"path": "test/good/001.png", "sha256": "held", "role": "final_holdout"},
        ]

    def test_development_preview_allowed_by_default(self):
        sample = select_replay_sample(self.samples, "dev", "/data/test/bent/017.png")
        self.assertEqual(sample["role"], "development_preview")

    def test_only_explicit_named_fit_reference_allowed(self):
        with self.assertRaises(ValueError):
            select_replay_sample(self.samples, "fit", "/data/train/good/000.png")
        sample = select_replay_sample(self.samples, "fit", "/data/train/good/000.png", True)
        self.assertEqual(sample["path"], "train/good/000.png")
        with self.assertRaises(ValueError):
            select_replay_sample(self.samples, "other", "/data/train/good/001.png", True)

    def test_holdout_and_wrong_path_rejected(self):
        with self.assertRaises(ValueError):
            select_replay_sample(self.samples, "held", "/data/test/good/001.png", True)
        with self.assertRaises(ValueError):
            select_replay_sample(self.samples, "dev", "/data/test/bent/999.png", True)


if __name__ == "__main__":
    unittest.main()
