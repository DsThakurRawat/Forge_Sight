"""Deterministic prototype pixel-response severity from recorded policy cutoffs.

Every label derives only from thresholds already present in the recorded
grading policy (image threshold, normal review margin, reject response area
fraction, reject bbox diagonal, critical zones). The policy itself labels
those cutoffs illustrative rule-engine examples, not manufacturing
tolerances, so every assessment carries SEVERITY_QUALIFIER. Severity here is
never physical-damage severity, calibrated confidence, or an industrial
classification, and the anomaly score is never renamed severity.
"""

import math


SEVERITY_MAPPING_VERSION = 'forgegrade-pixel-prototype-severity-v1'
SEVERITY_QUALIFIER = 'prototype pixel-response severity, not physical-damage severity'


def _overlap(a, b):
    x, y, w, h = a
    xx, yy, ww, hh = b
    return x < xx + ww and xx < x + w and y < yy + hh and yy < y + h


def severity_assessment(record: dict, policy: dict = None) -> dict:
    """Map an analyzed inspection record to NONE/LOW/MEDIUM/HIGH.

    No clock, randomness or model input: identical record and policy yield
    an identical assessment. Malformed evidence fails closed with ValueError
    instead of guessing a label.
    """
    def result(severity, basis):
        return {'severity': severity, 'mapping_version': SEVERITY_MAPPING_VERSION,
                'basis': basis, 'qualifier': SEVERITY_QUALIFIER}

    if (record.get('status') != 'ANALYZED'
            or record.get('candidate') != 'ANOMALY_CANDIDATE'):
        return result('NONE', ['no flagged anomaly response'])
    if policy is None:
        policy = record['decision']['policy_snapshot']
    width, height = policy['source_size_px']
    threshold = policy['image_threshold']
    margin = policy['normal_review_margin_fraction']
    score = record['score']
    geometry = record.get('geometry')
    if (not isinstance(score, (float, int)) or not math.isfinite(score)
            or not isinstance(geometry, dict)):
        raise ValueError('Invalid or incomplete severity evidence.')
    total = geometry['total_area_px']
    regions = geometry['regions']
    if (type(total) is not int or not 0 <= total <= width * height
            or any(type(region['area_px']) is not int or region['area_px'] <= 0
                   for region in regions)):
        raise ValueError('Invalid or incomplete severity evidence.')
    if not total or not regions:
        return result('NONE', ['no flagged anomaly response'])

    basis = []
    area_fraction = total / (width * height)
    if area_fraction >= policy['reject_response_area_fraction']:
        basis.append(f'response area fraction {area_fraction:.6f} reaches the recorded reject cutoff')
    longest = max(region['bbox_diagonal_px'] for region in regions)
    if longest >= policy['reject_bbox_diagonal_px']:
        basis.append(f'largest region bbox diagonal {longest!r} px reaches the recorded reject cutoff')
    zones = [zone['name'] for zone in policy['critical_zones']
             if any(_overlap(region['bbox_xywh_px'], zone['bbox_xywh_px']) for region in regions)]
    for name in zones:
        basis.append(f'response overlaps critical zone {name}')
    if basis:
        return result('HIGH', basis)
    borderline = threshold * (1 + margin)
    if score < borderline and not math.isclose(score, borderline, rel_tol=1e-9):
        return result('LOW', ['score inside the recorded normal review margin band above threshold'])
    return result('MEDIUM', ['anomaly above threshold, below every recorded reject cutoff'])
