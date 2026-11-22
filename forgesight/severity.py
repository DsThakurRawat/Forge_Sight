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
        decision = record.get('decision')
        policy = decision.get('policy_snapshot') if isinstance(decision, dict) else None
    if not isinstance(policy, dict):
        raise ValueError('Invalid or incomplete severity evidence.')
    try:
        width, height = policy['source_size_px']
        threshold = policy['image_threshold']
        margin = policy['normal_review_margin_fraction']
        reject_area_fraction = policy['reject_response_area_fraction']
        reject_diagonal = policy['reject_bbox_diagonal_px']
        critical_zones = policy['critical_zones']
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Invalid or incomplete severity evidence.') from exc
    score = record.get('score')
    geometry = record.get('geometry')
    if (type(score) not in (int, float) or not math.isfinite(score)
            or type(threshold) not in (int, float) or not math.isfinite(threshold)
            or type(margin) not in (int, float) or not math.isfinite(margin)
            or not isinstance(geometry, dict)):
        raise ValueError('Invalid or incomplete severity evidence.')
    total = geometry.get('total_area_px')
    regions = geometry.get('regions')
    if type(total) is not int or not 0 <= total <= width * height or not isinstance(regions, list):
        raise ValueError('Invalid or incomplete severity evidence.')
    summed = 0
    for region in regions:
        if not isinstance(region, dict):
            raise ValueError('Invalid or incomplete severity evidence.')
        area = region.get('area_px')
        bbox = region.get('bbox_xywh_px')
        diagonal = region.get('bbox_diagonal_px')
        if (type(area) is not int or area <= 0
                or not isinstance(bbox, (list, tuple)) or len(bbox) != 4
                or any(type(v) is not int for v in bbox)
                or type(diagonal) not in (int, float) or not math.isfinite(diagonal)):
            raise ValueError('Invalid or incomplete severity evidence.')
        summed += area
    if summed != total:
        raise ValueError('Region and total areas disagree.')
    if not total:
        return result('NONE', ['no flagged anomaly response'])
    if score < threshold and not math.isclose(score, threshold, rel_tol=1e-9):
        raise ValueError('Score below the recorded image threshold contradicts the flagged anomaly candidate.')

    basis = []
    area_fraction = total / (width * height)
    if area_fraction >= reject_area_fraction:
        basis.append(f'response area fraction {area_fraction:.6f} reaches the recorded reject cutoff')
    longest = max(region['bbox_diagonal_px'] for region in regions)
    if longest >= reject_diagonal:
        basis.append(f'largest region bbox diagonal {longest!r} px reaches the recorded reject cutoff')
    if not isinstance(critical_zones, list):
        raise ValueError('Invalid or incomplete severity evidence.')
    for zone in critical_zones:
        zone_bbox = zone.get('bbox_xywh_px') if isinstance(zone, dict) else None
        if (not isinstance(zone, dict) or not isinstance(zone.get('name'), str)
                or not isinstance(zone_bbox, (list, tuple)) or len(zone_bbox) != 4
                or any(type(v) is not int for v in zone_bbox)):
            raise ValueError('Invalid or incomplete severity evidence.')
    zones = [zone['name'] for zone in critical_zones
             if any(_overlap(region['bbox_xywh_px'], zone['bbox_xywh_px']) for region in regions)]
    for name in zones:
        basis.append(f'response overlaps critical zone {name}')
    if basis:
        return result('HIGH', basis)
    borderline = threshold * (1 + margin)
    if score < borderline and not math.isclose(score, borderline, rel_tol=1e-9):
        return result('LOW', ['score inside the recorded normal review margin band above threshold'])
    return result('MEDIUM', ['anomaly above threshold, below every recorded reject cutoff'])
