# ===== services/store_admin/utils.py (매장 관리자 서비스 유틸리티) =====
import json
import os

# 기준값 로드
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CRITERIA_PATH = os.path.join(BASE_DIR, "config", "criteria.json")

try:
    with open(CRITERIA_PATH, "r", encoding="utf-8") as f:
        CRITERIA = json.load(f)
except Exception:
    CRITERIA = {}

def _get_rule(club_id, metric):
    """criteria.json에서 클럽/지표별 기준값 가져오기"""
    cid = (club_id or "").lower()
    club_cfg = CRITERIA.get(cid, {})
    if metric in club_cfg:
        return club_cfg[metric]
    default_cfg = CRITERIA.get("default", {})
    return default_cfg.get(metric)

def score_class(value, good, warn=None):
    """기본 점수 분류"""
    if value is None:
        return "bg-none"
    try:
        v = float(value)
    except:
        return "bg-none"
    if good is None:
        return "bg-none"
    if warn is None:
        return "bg-good" if v >= good else "bg-bad"
    if v <= good:
        return "bg-good"
    elif v <= warn:
        return "bg-warn"
    else:
        return "bg-bad"

def classify_by_criteria(value, club_id, metric, *, fallback_good=None, fallback_warn=None, abs_value=False):
    """criteria.json 기반 색상 클래스 결정"""
    if value is None:
        return "bg-none"
    try:
        v = float(value)
    except Exception:
        return "bg-none"
    if abs_value:
        v = abs(v)
    rule = _get_rule(club_id, metric)
    if rule:
        good = rule.get("good")
        warn = rule.get("warn")
        bad = rule.get("bad")
        if isinstance(good, (list, tuple)) and len(good) == 2:
            low, high = float(good[0]), float(good[1])
            return "bg-good" if (low <= v <= high) else "bg-bad"
        if good is not None and bad is not None:
            g = float(good)
            b = float(bad)
            if v >= g:
                return "bg-good"
            if v <= b:
                return "bg-bad"
            return "bg-warn"
        if good is not None and warn is not None:
            g = float(good)
            w = float(warn)
            if v <= g:
                return "bg-good"
            elif v <= w:
                return "bg-warn"
            else:
                return "bg-bad"
        if good is not None:
            g = float(good)
            return "bg-good" if v >= g else "bg-bad"
    if fallback_good is None:
        return "bg-none"
    return score_class(v, fallback_good, fallback_warn)
