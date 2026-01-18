# ===== services/user/utils.py (유저 서비스 유틸리티) =====
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
    """criteria.json 기반 색상 클래스 결정 (조회 시 화면 표시용)"""
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

def evaluate_shot_by_criteria(shot_data, club_id):
    """
    criteria.json 기준으로 샷 평가 (저장 시 사용)
    
    Returns:
        tuple: (is_valid: bool, score: int)
        - is_valid: 모든 필수 기준을 충족하면 True
        - score: 0-100 점수 (단순 로직: good 기준 충족 개수 기반)
    """
    if not CRITERIA:
        return False, 0
    
    club_id_lower = (club_id or "").lower()
    
    # 드라이버는 smash_factor, face_angle, club_path 3가지만 평가
    if club_id_lower == "driver":
        metrics_to_check = ["smash_factor", "face_angle", "club_path"]
    else:
        # 다른 클럽은 전체 평가
        metrics_to_check = ["smash_factor", "launch_angle", "face_angle", "club_path", 
                          "lateral_offset", "direction_angle", "side_spin", "back_spin"]
    
    good_count = 0
    total_count = 0
    
    for metric_key in metrics_to_check:
        value = shot_data.get(metric_key)
        if value is None:
            continue
        
        try:
            v = float(value)
        except (ValueError, TypeError):
            continue
        
        rule = _get_rule(club_id, metric_key)
        if not rule:
            continue
        
        total_count += 1
        good = rule.get("good")
        warn = rule.get("warn")
        bad = rule.get("bad")
        
        # 절댓값이 필요한 메트릭
        if metric_key in ["face_angle", "club_path", "lateral_offset", "direction_angle"]:
            v = abs(v)
        
        # 기준 충족 여부 확인
        is_good = False
        if isinstance(good, (list, tuple)) and len(good) == 2:
            low, high = float(good[0]), float(good[1])
            is_good = (low <= v <= high)
        elif good is not None and bad is not None:
            g = float(good)
            b = float(bad)
            is_good = (v >= g)
        elif good is not None and warn is not None:
            g = float(good)
            is_good = (v <= g)  # 작을수록 좋은 경우 (lateral_offset, direction_angle 등)
        elif good is not None:
            g = float(good)
            is_good = (v >= g)
        
        if is_good:
            good_count += 1
    
    # is_valid: 모든 필수 기준을 충족해야 함 (단순 로직: 70% 이상 충족)
    is_valid = (total_count > 0) and (good_count / total_count >= 0.7)
    
    # score: 0-100 (기준 충족 비율 * 100)
    score = int((good_count / total_count * 100)) if total_count > 0 else 0
    
    return is_valid, score
