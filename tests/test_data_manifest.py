"""Test split integrity without viewing the real holdout."""

from copy import deepcopy
import hashlib
from pathlib import Path
import unittest

from forgesight.data_manifest import (
    EXPECTED_COUNTS, assign_roles, encoded_manifest, rank, reject_duplicates,
    safe_path, validate_manifest,
)


def synthetic_manifest():
    rows = []
    for group, count in {"train/good": 220, "test/good": 22, "test/bent": 25,
                         "test/color": 22, "test/flip": 23, "test/scratch": 23}.items():
        split, label = group.split("/")
        for index in range(count):
            path = f"{group}/{index:03}.png"
            digest = hashlib.sha256(path.encode()).hexdigest()
            mask = None if label == "good" else {
                "path": f"ground_truth/{label}/{index:03}_mask.png", "sha256": digest,
                "pixel_sha256": digest, "mode": "L", "size": [700, 700]}
            rows.append({"path": path, "source_split": split, "label": label,
                         "sha256": digest, "pixel_sha256": digest, "mode": "RGB",
                         "size": [700, 700], "mask": mask})
    return {"schema_version": 1, "dataset": "MVTec AD", "category": "metal_nut",
            "policy_version": "forgesight-metal-nut-v1", "seed": 42,
            "source_archive_sha256": "a" * 64, "counts": EXPECTED_COUNTS.copy(),
            "samples": assign_roles(rows)}


class ManifestTests(unittest.TestCase):
    def test_counts_and_one_preview_per_defect(self):
        manifest = synthetic_manifest()
        validate_manifest(manifest)
        preview = [row for row in manifest["samples"] if row["role"] == "development_preview"]
        self.assertEqual({row["label"] for row in preview}, {"bent", "color", "flip", "scratch"})
        self.assertEqual(len(preview), 4)
        self.assertTrue(all(row["source_split"] == "train" for row in manifest["samples"]
                            if row["role"] in {"fit", "validation_normal"}))

    def test_input_order_does_not_change_partition(self):
        rows = synthetic_manifest()["samples"]
        self.assertEqual(assign_roles(rows), assign_roles(list(reversed(rows))))

    def test_ranking_uses_documented_text(self):
        path = "train/good/000.png"
        self.assertEqual(rank(path)[0], hashlib.sha256(
            b"forgesight-metal-nut-v1|42|train/good/000.png").hexdigest())

    def test_count_preserving_role_swap_is_rejected(self):
        manifest = synthetic_manifest()
        fit = next(row for row in manifest["samples"] if row["role"] == "fit")
        validation = next(row for row in manifest["samples"] if row["role"] == "validation_normal")
        fit["role"], validation["role"] = validation["role"], fit["role"]
        with self.assertRaisesRegex(ValueError, "deterministic policy"):
            validate_manifest(manifest)

    def test_duplicate_bytes_and_pixels_are_rejected(self):
        original = synthetic_manifest()["samples"]
        for field in ("sha256", "pixel_sha256"):
            rows = deepcopy(original)
            rows[1][field] = rows[0][field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Duplicate image"):
                reject_duplicates(rows)

    def test_missing_and_mismatched_masks_are_rejected(self):
        for mask in (None, {"path": "ground_truth/scratch/wrong_mask.png"}):
            manifest = synthetic_manifest()
            next(row for row in manifest["samples"] if row["label"] == "scratch")["mask"] = mask
            with self.subTest(mask=mask), self.assertRaisesRegex(ValueError, "mask"):
                validate_manifest(manifest)

    def test_unsafe_relative_paths_are_rejected(self):
        for path in ("../outside.png", "/tmp/outside.png", "C:/outside.png", "test\\good\\a.png"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_path(Path("."), path)

    def test_encoding_is_stable(self):
        original = synthetic_manifest()
        self.assertEqual(encoded_manifest(original), encoded_manifest(deepcopy(original)))


if __name__ == "__main__":
    unittest.main()
