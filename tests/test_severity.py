"""Deterministic prototype severity mapping tests.

Severity derives only from cutoffs already present in the recorded grading
policy. It is a pixel-response prototype label, never physical-damage
severity, calibrated confidence, or an industrial classification.
"""

from copy import deepcopy
import unittest

from forgesight.severity import SEVERITY_MAPPING_VERSION, SEVERITY_QUALIFIER, severity_assessment


POLICY = {
    'policy_id': 'forgegrade-metal-nut-pixel-prototype-v1',
    'source_size_px': [700, 700],
    'image_threshold': 0.2,
    'normal_review_margin_fraction': 0.1,
    'reject_response_area_fraction': 0.01,
    'reject_bbox_diagonal_px': 140.0,
    'critical_zones': [],
}


def record(score=0.5, area=100, regions=None, candidate='ANOMALY_CANDIDATE',
           status='ANALYZED', policy=None):
    if regions is None and area:
        regions = [{'bbox_xywh_px': [10, 10, 10, 10], 'area_px': area,
                    'bbox_diagonal_px': 14.142135623730951}]
    elif regions is None:
        regions = []
    return {
        'status': status,
        'candidate': candidate,
        'score': score,
        'geometry': {'source_size_px': [700, 700], 'total_area_px': area,
                     'regions': regions},
        'decision': {'grade': 'REVIEW',
                     'policy_snapshot': deepcopy(policy if policy is not None else POLICY)},
    }


class SeverityTests(unittest.TestCase):
    def test_no_flagged_response_is_none(self):
        for row in (record(area=0), record(candidate='NORMAL_CANDIDATE'),
                    record(status='ERROR')):
            with self.subTest(row=row['candidate']):
                result = severity_assessment(row)
                self.assertEqual(result['severity'], 'NONE')
                self.assertEqual(result['qualifier'], SEVERITY_QUALIFIER)

    def test_high_from_response_area_fraction(self):
        # 1% of 700*700 is 4900 px.
        self.assertEqual(severity_assessment(record(area=4900))['severity'], 'HIGH')
        below = severity_assessment(record(area=4899))
        self.assertNotEqual(below['severity'], 'HIGH')

    def test_high_from_bbox_diagonal(self):
        row = record(regions=[{'bbox_xywh_px': [0, 0, 100, 100], 'area_px': 500,
                               'bbox_diagonal_px': 141.4213562373095}])
        result = severity_assessment(row)
        self.assertEqual(result['severity'], 'HIGH')
        self.assertTrue(any('diagonal' in basis for basis in result['basis']))

    def test_high_from_critical_zone_overlap(self):
        policy = deepcopy(POLICY)
        policy['critical_zones'] = [{'name': 'bore', 'bbox_xywh_px': [0, 0, 50, 50]}]
        result = severity_assessment(record(policy=policy))
        self.assertEqual(result['severity'], 'HIGH')
        self.assertTrue(any('bore' in basis for basis in result['basis']))

    def test_low_band_just_above_threshold(self):
        # threshold 0.2, margin 10%: borderline band is [0.2, 0.22).
        result = severity_assessment(record(score=0.21))
        self.assertEqual(result['severity'], 'LOW')
        self.assertTrue(any('margin' in basis for basis in result['basis']))

    def test_medium_above_borderline_band(self):
        self.assertEqual(severity_assessment(record(score=0.22))['severity'], 'MEDIUM')
        self.assertEqual(severity_assessment(record(score=0.9))['severity'], 'MEDIUM')

    def test_deterministic_and_uses_recorded_policy_snapshot(self):
        row = record()
        self.assertEqual(severity_assessment(row), severity_assessment(deepcopy(row)))
        result = severity_assessment(row)
        self.assertEqual(result['mapping_version'], SEVERITY_MAPPING_VERSION)
        tougher = deepcopy(POLICY)
        tougher['reject_bbox_diagonal_px'] = 10.0
        self.assertEqual(severity_assessment(row, policy=tougher)['severity'], 'HIGH')

    def test_invalid_evidence_fails_closed(self):
        for mutate in (
                lambda row: row.update(score=float('nan')),
                lambda row: row['geometry'].update(total_area_px=-1),
                lambda row: row['geometry'].update(total_area_px=700 * 700 + 1),
                lambda row: row.update(geometry=None)):
            row = record()
            mutate(row)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                severity_assessment(row)


if __name__ == '__main__':
    unittest.main()
