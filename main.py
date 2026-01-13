# ===== main.py (FINAL) =====
import json
import time
import os
import re
import sys
import threading
from datetime import datetime

import requests
import pyautogui
import numpy as np
import cv2
import pytesseract
from openai import OpenAI

# 시스템 트레이 관련
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("경고: pystray가 설치되지 않았습니다. 시스템 트레이 기능을 사용할 수 없습니다.")
    print("설치: pip install pystray pillow")

# =========================
# 설정
# =========================
# 서버 URL은 환경 변수로 설정 가능 (Railway 배포 시 사용)
# 환경 변수가 없으면 Railway 프로덕션 서버 기본값 사용
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://golf-api-production-e675.up.railway.app")
SERVER_URL = f"{DEFAULT_SERVER_URL}/api/save_shot"

# PC 토큰 파일 경로 (register_pc.py와 동일한 위치)
PC_TOKEN_FILE = os.path.join(os.path.dirname(__file__), "pc_token.json")

def load_pc_token():
    """PC 토큰 로드"""
    if os.path.exists(PC_TOKEN_FILE):
        try:
            with open(PC_TOKEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("pc_token")
        except Exception:
            pass
    return None

def save_pc_token(pc_token, server_url):
    """PC 토큰 저장"""
    try:
        data = {
            "pc_token": pc_token,
            "server_url": server_url
        }
        with open(PC_TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"토큰 저장 실패: {e}")
        return False

def get_auth_headers():
    """인증 헤더 생성 (PC 토큰 포함)"""
    pc_token = load_pc_token()
    headers = {}
    if pc_token:
        headers["Authorization"] = f"Bearer {pc_token}"
    return headers

POLL_INTERVAL = 0.05  # 샷 처리 속도 개선 (0.20 -> 0.05)
COOLDOWN_SEC  = 2.0
SPEED_TOL     = 0.25
MIN_CHANGE    = 0.60
MIN_SPEED     = 5.0
MAX_SPEED     = 120.0
# ===== 하이브리드 샷 감지 기준 =====
STABLE_TOL    = 0.25   # 안정 상태 허용 오차
ACTIVE_DELTA  = 1.0    # 샷 시작으로 보는 최소 변화
STABLE_FRAMES = 4      # 안정 복귀 프레임 수
# ===== 런 텍스트 감지 기준 =====
WAITING_POLL_INTERVAL = 0.05    # 대기 상태에서 런 텍스트 체크 간격 (초) - 속도 개선 (0.3 -> 0.05)
RUN_DETECTION_FRAMES = 2        # 런 텍스트가 연속으로 감지되어야 하는 프레임 수
TEXT_REAPPEAR_MIN_TIME = 1.0    # 텍스트가 다시 나타난 후 최소 유지 시간 (초) - 이 시간 이하면 데이터 수집 안함

# =========================
# 로그 제어 (실매장용: DEBUG = False)
# =========================
DEBUG = False

def log(*args):
    """로그 출력 (DEBUG 모드에서만)"""
    if DEBUG:
        print(*args)

# ===== 자동 세션 종료 기준 =====
SESSION_AUTO_LOGOUT_NO_SHOT = 20 * 60  # 20분 동안 샷이 없으면 자동 종료 (초)
SESSION_AUTO_LOGOUT_NO_SCREEN = 5 * 60  # 5분 동안 연습 화면이 아니면 자동 종료 (초)

OCR_TIMEOUT_SEC = 1

# 이 값들을 매장 PC에서 상황에 맞게 변경
DEFAULT_STORE_ID = "gaja"
DEFAULT_BAY_ID   = "01"
DEFAULT_CLUB_ID  = "Driver"

# PC 등록 관련 설정
PC_REGISTRATION_ENABLED = os.environ.get("PC_REGISTRATION_ENABLED", "true").lower() == "true"
PC_STORE_NAME = os.environ.get("PC_STORE_NAME", "")  # 매장명 (등록 시 필요)
PC_BAY_NAME = os.environ.get("PC_BAY_NAME", "")      # 타석명 (등록 시 필요)
PC_NAME = os.environ.get("PC_NAME", "")              # PC 이름 (등록 시 필요)

# PC 고유번호 수집 모듈
try:
    from pc_identifier import get_pc_info
except ImportError:
    # pc_identifier.py가 없으면 기본 함수 정의
    import platform
    import uuid
    import hashlib
    def get_pc_info():
        hostname = platform.node()
        unique_id = hashlib.sha256(f"{hostname}{uuid.getnode()}".encode()).hexdigest()[:32].upper()
        return {"unique_id": unique_id, "hostname": hostname}

# 매장별 좌표 파일 (매장마다 화면 레이아웃이 다를 수 있음)
# 각 매장의 좌표 파일을 regions/ 폴더에 만들어서 사용
# 예: regions/gaja.json, regions/sg_golf.json, regions/golfzone.json 등
REGIONS_FILE = os.path.join("regions", f"{DEFAULT_STORE_ID}.json")
# 매장별 좌표 파일이 없으면 기본 파일 사용
if not os.path.exists(REGIONS_FILE):
    REGIONS_FILE = os.path.join("regions", "test.json")

# 샷 기준표 파일 경로
CRITERIA_FILE = os.path.join("config", "criteria.json")
# 피드백 메시지 파일 경로
FEEDBACK_MESSAGES_FILE = os.path.join("config", "feedback_messages.json")

# 활성 사용자 조회 API
ACTIVE_USER_API = f"{DEFAULT_SERVER_URL}/api/active_user"

# GPT API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # 환경 변수에서만 읽기
GPT_MODEL = "gpt-4o-mini"  # 또는 "gpt-3.5-turbo", "gpt-4" 등
USE_GPT_FEEDBACK = False  # GPT 피드백 사용 여부 (True면 GPT 사용, False면 기존 기준표 방식 사용)

# =========================
# TTS (완전 비활성화)
# =========================
def speak(text: str):
    """TTS 완전 비활성화"""
    pass

# =========================
# 유틸
# =========================
def load_json(path):
    base = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base, path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"좌표 파일을 찾을 수 없습니다: {full_path}")
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 매장별 좌표 파일 로드
try:
    REGIONS = load_json(REGIONS_FILE)["regions"]
    print(f"✅ 좌표 파일 로드 완료: {REGIONS_FILE}")
except FileNotFoundError as e:
    print(f"❌ 오류: {e}")
    print(f"💡 regions/{DEFAULT_STORE_ID}.json 파일을 생성하거나 regions/test.json 파일을 확인하세요.")
    raise

# 샷 기준표 파일 로드
try:
    CRITERIA = load_json(CRITERIA_FILE)
    print(f"✅ 샷 기준표 로드 완료: {CRITERIA_FILE}")
except FileNotFoundError as e:
    print(f"⚠️ 샷 기준표 파일을 찾을 수 없습니다: {e}")
    CRITERIA = {}

# 피드백 메시지 파일 로드
try:
    FEEDBACK_MESSAGES = load_json(FEEDBACK_MESSAGES_FILE)
    print(f"✅ 피드백 메시지 로드 완료: {FEEDBACK_MESSAGES_FILE}")
except FileNotFoundError as e:
    print(f"⚠️ 피드백 메시지 파일을 찾을 수 없습니다: {e}")
    FEEDBACK_MESSAGES = {}

def capture_region_ratio(region):
    sw, sh = pyautogui.size()
    x = int(region["x"] * sw)
    y = int(region["y"] * sh)
    w = int(region["w"] * sw)
    h = int(region["h"] * sh)
    img = pyautogui.screenshot(region=(x, y, w, h))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    gray = cv2.threshold(gray, 145, 255, cv2.THRESH_BINARY)[1]
    return gray

def ocr_number(img):
    """숫자만 빠르게 읽을 때 사용 (볼스피드/클럽스피드 감지용)
    소수점 인식 강화: 이미지 확대 및 여러 전처리 시도
    """
    h, w = img.shape[:2]
    # 소수점 인식을 위해 이미지 확대
    if w < 150 or h < 50:
        scale = max(5.0, 150.0 / w, 50.0 / h)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 여러 threshold 값 시도 (소수점 인식 강화)
    for thresh_val in [145, 150, 140, 135, 155]:
        try:
            thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)[1]
            text = pytesseract.image_to_string(
                thresh,
                lang="eng",
                config="--psm 7 -c tessedit_char_whitelist=0123456789.-",
                timeout=OCR_TIMEOUT_SEC
            ).strip()
            
            if text:
                # 소수점이 있는 숫자를 우선적으로 찾기
                m = re.search(r"-?\d+\.\d+", text)
                if m:
                    return float(m.group())
                # 소수점이 없으면 일반 숫자
                m = re.search(r"-?\d+", text)
                if m:
                    return float(m.group())
        except Exception:
            continue
    
    return None


def ocr_text_region(key):
    """
    숫자 + 부호(+/- 또는 R/L) + 단위 전체가 들어있는 영역을 읽어서
    그대로 문자열로 반환.
    개선: 이미지 전처리 강화 및 여러 threshold 시도
    백스핀 특별 처리: 4자리 숫자 인식 강화
    """
    img = capture_region_ratio(REGIONS[key])
    
    # 백스핀과 사이드스핀은 4자리 숫자가 많아서 더 크게 확대
    # 볼스피드/클럽스피드는 소수점 인식을 위해 더 크게 확대
    h, w = img.shape[:2]
    if key in ["back_spin", "side_spin"]:
        # 백스핀/사이드스핀은 더 크게 확대 (4자리 숫자 인식 강화)
        # 최소 250px 너비로 확대하여 4자리 숫자 전체 인식 (범위를 넓게 잡아서 첫 숫자도 인식)
        if w < 250 or h < 70:
            scale = max(7.0, 250.0 / w, 70.0 / h)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    elif key in ["ball_speed", "club_speed"]:
        # 볼스피드/클럽스피드는 소수점 인식을 위해 더 크게 확대
        # 최소 150px 너비로 확대하여 소수점 포함 숫자 전체 인식
        if w < 150 or h < 50:
            scale = max(5.0, 150.0 / w, 50.0 / h)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    else:
        if w < 100 or h < 40:
            scale = max(4.0, 100.0 / w, 40.0 / h)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 전처리
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 백스핀/사이드스핀은 더 강한 전처리
    if key in ["back_spin", "side_spin"]:
        # 대비 강화 (CLAHE 사용)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
    
    # 방법 1: 정규화 + 블러 + 일반 threshold (가장 빠르고 효과적)
    gray1 = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    gray1 = cv2.GaussianBlur(gray1, (3, 3), 0)
    
    # 백스핀과 사이드스핀은 더 많은 threshold 값 시도
    # 볼스피드/클럽스피드는 소수점 인식을 위해 더 많은 시도
    if key in ["back_spin", "side_spin"]:
        priority_combinations = [
            (gray1, 145, 8),  # PSM 8 (단일 단어) 우선 시도
            (gray1, 150, 8),
            (gray1, 140, 8),
            (gray1, 145, 7),
            (gray1, 150, 7),
            (gray1, 140, 7),
            (gray1, 135, 7),  # 스핀 항목 추가
            (gray1, 155, 7),  # 스핀 항목 추가
            (gray1, 145, 6),  # PSM 6도 시도
            (gray1, 160, 8),  # 추가 threshold
            (gray1, 130, 8),  # 추가 threshold
        ]
        # 여러 결과를 수집하여 가장 정확한 것 선택
        candidate_texts = []
    elif key in ["ball_speed", "club_speed"]:
        # 볼스피드/클럽스피드는 소수점 인식을 위해 더 많은 시도
        priority_combinations = [
            (gray1, 145, 7),  # 가장 일반적인 조합
            (gray1, 150, 7),
            (gray1, 140, 7),
            (gray1, 145, 8),  # PSM 8도 시도
            (gray1, 150, 8),
            (gray1, 140, 8),
            (gray1, 135, 7),  # 추가 threshold
            (gray1, 155, 7),  # 추가 threshold
        ]
    else:
        priority_combinations = [
            (gray1, 145, 7),  # 가장 일반적인 조합
            (gray1, 150, 7),
            (gray1, 140, 7),
            (gray1, 145, 8),  # PSM 8도 시도
        ]
    
    best_text = None
    best_thresh_img = None
    candidate_texts = []  # 백스핀/사이드스핀용 후보 텍스트들
    
    for processed, thresh_val, psm_mode in priority_combinations:
        try:
            thresh = cv2.threshold(processed, thresh_val, 255, cv2.THRESH_BINARY)[1]
            text = pytesseract.image_to_string(
                thresh,
                lang="eng",
                config=f"--psm {psm_mode} -c tessedit_char_whitelist=0123456789.,-RL /mps°",
                timeout=OCR_TIMEOUT_SEC
            ).upper().strip()
            if text and any(c.isdigit() for c in text):
                # 볼스피드/클럽스피드는 소수점이 있는 결과를 우선 선택
                if key in ["ball_speed", "club_speed"]:
                    if "." in text:
                        # 소수점이 있으면 즉시 반환 (디버그 이미지는 샷 감지 시 저장)
                        if best_thresh_img is None:
                            best_thresh_img = thresh
                        return text
                    elif best_text is None:
                        # 소수점이 없어도 일단 저장 (나중에 사용)
                        best_text = text
                        if best_thresh_img is None:
                            best_thresh_img = thresh
                # 백스핀과 사이드스핀은 특별 처리
                elif key == "back_spin":
                    # 백스핀: 4자리 숫자 우선
                    digits = sum(c.isdigit() for c in text)
                    if digits == 4:
                        candidate_texts.append(text)
                    elif digits >= 4:
                        candidate_texts.append(text)
                    elif digits >= 3:
                        candidate_texts.append(text)
                elif key == "side_spin":
                    # 사이드 스핀: 4자리 또는 3자리 숫자 우선 (부호 포함)
                    digits = sum(c.isdigit() for c in text)
                    if digits == 4:
                        # 정확히 4자리면 즉시 반환
                        return text
                    elif digits == 3:
                        # 정확히 3자리면 즉시 반환
                        return text
                    elif digits >= 4:
                        # 4자리 이상이면 후보에 추가 (나중에 파싱에서 앞 4자리만 추출)
                        candidate_texts.append(text)
                    elif digits >= 3:
                        # 3자리 이상이면 후보에 추가 (나중에 파싱에서 앞 3자리만 추출)
                        candidate_texts.append(text)
                    elif digits >= 2:
                        candidate_texts.append(text)
                else:
                    return text  # 즉시 반환 (조기 종료)
        except Exception:
            continue
    
    # 백스핀: 여러 후보 중 가장 정확한 것 선택 (4자리 우선)
    if key == "back_spin" and candidate_texts:
        # 정확히 4자리 숫자가 있는 결과 우선 선택
        for candidate in candidate_texts:
            digits = sum(c.isdigit() for c in candidate)
            if digits == 4:
                return candidate
        # 4자리가 없으면 첫 번째 후보 반환 (파싱에서 처리)
        if candidate_texts:
            return candidate_texts[0]
    
    # 사이드 스핀: 여러 후보 중 가장 정확한 것 선택 (4자리 우선, 그 다음 3자리)
    if key == "side_spin" and candidate_texts:
        # 정확히 4자리 숫자가 있는 결과 우선 선택
        for candidate in candidate_texts:
            digits = sum(c.isdigit() for c in candidate)
            if digits == 4:
                return candidate
        # 4자리가 없으면 3자리 선택
        for candidate in candidate_texts:
            digits = sum(c.isdigit() for c in candidate)
            if digits == 3:
                return candidate
        # 3자리도 없으면 첫 번째 후보 반환 (파싱에서 처리)
        if candidate_texts:
            return candidate_texts[0]
    
    # 볼스피드/클럽스피드는 소수점이 없는 경우에도 반환 (디버그 이미지는 샷 감지 시 저장)
    if key in ["ball_speed", "club_speed"] and best_text:
        return best_text
    
    # 실패 시 적응형 threshold 시도 (1회만)
    try:
        gray2 = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        text = pytesseract.image_to_string(
            gray2,
            lang="eng",
            config="--psm 7 -c tessedit_char_whitelist=0123456789.,-RL /mps°",
            timeout=OCR_TIMEOUT_SEC
        ).upper().strip()
        if text and any(c.isdigit() for c in text):
            if key == "back_spin":
                digits = sum(c.isdigit() for c in text)
                if digits >= 3:
                    return text
            elif key == "side_spin":
                digits = sum(c.isdigit() for c in text)
                if digits >= 2:  # 사이드 스핀은 3자리지만 2자리 이상이면 일단 반환
                    return text
            else:
                return text
    except Exception:
        pass
    
    # 마지막 시도: whitelist 없이
    try:
        thresh = cv2.threshold(gray1, 145, 255, cv2.THRESH_BINARY)[1]
        text = pytesseract.image_to_string(
            thresh,
            lang="eng",
            config="--psm 7",
            timeout=OCR_TIMEOUT_SEC
        ).upper().strip()
        return text
    except Exception:
        return ""


def parse_value(text, mode="plain", key=None):
    """
    text: OCR로 읽은 전체 문자열 (예: "L 3.0°", "10,000 rpm", "-866 rpm", "47.55 m/s", "1662-", "--1070-", "22981")
    mode:
      - "plain"  : 부호 없는 순수 숫자 (볼스피드, 클럽스피드, 발사각 등)
      - "minus"  : '-' 기호 기준 부호 (클럽패스, 사이드스핀, 백스핀 등)
      - "RL"     : R/L 기준 부호 (페이스각, 방향각, 좌우이격 등)
    key: 항목 이름 (back_spin, side_spin 등) - 4자리 숫자 우선 추출용
    
    개선: 쉼표가 포함된 숫자(10,000)도 처리하고, 부호 인식을 더 정확하게
    4자리 숫자도 정확히 추출하도록 개선
    """
    if not text:
        return None

    # OCR 결과에서 불필요한 문자 제거 (뒤에 붙은 '-' 등)
    # 예: "1662-" → "1662", "--1070-" → "-1070"
    text_clean = text.strip()
    
    # 연속된 '-' 정리 (맨 앞의 '-'만 유지)
    if text_clean.startswith("-"):
        # 맨 앞의 '-' 유지하고 나머지 '-' 제거
        text_clean = "-" + text_clean[1:].replace("-", "")
    else:
        # 앞에 '-'가 없으면 모든 '-' 제거
        text_clean = text_clean.replace("-", "")

    # 백스핀: 정확히 4자리 숫자를 우선적으로 찾기
    if key == "back_spin":
        # 모든 숫자 추출 (순서대로)
        all_digits = re.findall(r'\d', text_clean)
        
        if len(all_digits) >= 4:
            # 앞의 4자리 숫자만 사용
            # 예: "22981" → "2298", "2981" → "2981" (이미 4자리)
            num_str = ''.join(all_digits[:4])
            try:
                v = float(num_str)
                return abs(v)  # 백스핀은 부호 없음
            except ValueError:
                pass
        
        # 정규표현식으로도 시도 (기존 방식)
        m = re.search(r"\d{4}(?!\d)", text_clean)  # 4자리 숫자 뒤에 숫자가 없는 경우
        if m:
            num_str = m.group(0).replace(",", "")
            try:
                v = float(num_str)
                return abs(v)
            except ValueError:
                pass
        
        # 4자리 숫자 뒤에 숫자가 있어도 앞의 4자리만 추출 (22981 → 2298)
        m = re.search(r"(\d{4})\d+", text_clean)
        if m:
            num_str = m.group(1)
            try:
                v = float(num_str)
                return abs(v)
            except ValueError:
                pass
    
    # 사이드 스핀: 3자리 또는 4자리 숫자 처리 (부호 포함)
    if key == "side_spin":
        # 원본 텍스트에서 부호 확인 (OCR 오류로 인한 잘못된 부호 제거)
        original_text = text.strip()
        has_minus_sign = False
        
        # 명확한 부호 확인: 텍스트 시작 부분에 "-"가 있고, 그 뒤에 숫자가 오는 경우만
        if original_text.startswith("-") and len(original_text) > 1 and original_text[1].isdigit():
            has_minus_sign = True
        
        # 모든 숫자 추출 (순서대로)
        all_digits = re.findall(r'\d', text_clean)
        
        # 4자리 숫자 우선 처리 (-1070 같은 경우)
        if len(all_digits) >= 4:
            # 앞의 4자리 숫자 사용
            # 예: "10706" → "1070", "1070" → "1070"
            num_str = ''.join(all_digits[:4])
            try:
                v = float(num_str)
                if mode == "minus":
                    # 명확한 부호가 있을 때만 음수로 처리
                    if has_minus_sign:
                        return -abs(v)
                    return abs(v)
                return abs(v)
            except ValueError:
                pass
        
        # 3자리 숫자 처리 (655 같은 경우)
        if len(all_digits) >= 3:
            # 앞의 3자리 숫자만 사용
            # 예: "6556" → "655", "655" → "655"
            num_str = ''.join(all_digits[:3])
            try:
                v = float(num_str)
                if mode == "minus":
                    # 명확한 부호가 있을 때만 음수로 처리
                    if has_minus_sign:
                        return -abs(v)
                    return abs(v)
                return abs(v)
            except ValueError:
                pass
        
        # 정규표현식으로도 시도: 4자리 숫자 우선, 그 다음 3자리
        m = re.search(r"\d{4}(?!\d)", text_clean)  # 4자리 숫자 뒤에 숫자가 없는 경우 (부호 제외)
        if m:
            num_str = m.group(0).replace(",", "")
            try:
                v = float(num_str)
                if mode == "minus":
                    if has_minus_sign:
                        return -abs(v)
                    return abs(v)
                return abs(v)
            except ValueError:
                pass
        
        m = re.search(r"\d{3}(?!\d)", text_clean)  # 3자리 숫자 뒤에 숫자가 없는 경우 (부호 제외)
        if m:
            num_str = m.group(0).replace(",", "")
            try:
                v = float(num_str)
                if mode == "minus":
                    if has_minus_sign:
                        return -abs(v)
                    return abs(v)
                return abs(v)
            except ValueError:
                pass
        
        # 4자리 이상 숫자 뒤에 숫자가 있어도 앞의 4자리만 추출 (10706 → 1070)
        m = re.search(r"(\d{4})\d+", text_clean)  # 부호 제외하고 숫자만
        if m:
            num_str = m.group(1)
            try:
                v = float(num_str)
                if mode == "minus":
                    if has_minus_sign:
                        return -abs(v)
                    return abs(v)
                return abs(v)
            except ValueError:
                pass
        
        # 3자리 숫자 뒤에 숫자가 있어도 앞의 3자리만 추출 (6556 → 655)
        m = re.search(r"(\d{3})\d+", text_clean)  # 부호 제외하고 숫자만
        if m:
            num_str = m.group(1)
            try:
                v = float(num_str)
                if mode == "minus":
                    if has_minus_sign:
                        return -abs(v)
                    return abs(v)
                return abs(v)
            except ValueError:
                pass

    # 숫자 추출 (4자리 이상도 포함, 쉼표 포함 가능, 소수점 포함 가능)
    # 예: "1662", "10,000", "47.55", "60.62", "-1070", "L 3.0", "-4.7" 등
    # 소수점이 있는 숫자를 우선적으로 찾기 (볼스피드/클럽스피드/클럽패스 등)
    # 소수점 인식 강화: 소수점 앞뒤로 숫자가 있는 패턴 우선
    m = re.search(r"-?\d+\.\d+", text_clean)
    if not m:
        # 소수점이 없으면 정수만 찾기
        # 먼저 쉼표 포함 숫자 시도
        m = re.search(r"-?\d{1,3}(?:,\d{3})+", text_clean)
    if not m:
        # 정확히 4자리 숫자 우선 시도 (백스핀용)
        m = re.search(r"-?\d{4}", text_clean)
    if not m:
        # 쉼표 없는 4자리 이상 숫자 시도
        m = re.search(r"-?\d{4,}", text_clean)
    if not m:
        # 일반 숫자 (1자리 이상)
        m = re.search(r"-?\d+", text_clean)
    if not m:
        return None

    # 쉼표 제거 후 숫자 변환
    num_str = m.group(0).replace(",", "")
    
    # 소수점이 있는 경우와 없는 경우를 구분하여 처리
    has_decimal = "." in num_str
    try:
        v = float(num_str)
    except ValueError:
        return None

    if mode == "plain":
        # 부호 없는 순수 숫자 (볼스피드, 클럽스피드 등)
        # 단, 소수점이 있는 경우 원래 값 유지 (음수면 음수, 양수면 양수)
        # 볼스피드/클럽스피드는 항상 양수이므로 abs 사용
        return abs(v)

    if mode == "minus":
        # '-' 기호가 있으면 음수, 없으면 양수
        # 예: "-866 rpm" → -866, "989 rpm" → 989, "-4.7" → -4.7, "4.7" → 4.7
        # 원본 text에서 명확한 부호 확인 (텍스트 시작 부분에 "-"가 있고 그 뒤에 숫자가 오는 경우만)
        original_text = text.strip()
        has_minus_sign = False
        if original_text.startswith("-") and len(original_text) > 1:
            # "-" 뒤에 숫자나 소수점이 오는 경우만 부호로 인정
            next_char = original_text[1]
            if next_char.isdigit() or next_char == ".":
                has_minus_sign = True
        
        # 소수점이 있는 경우: 원본 텍스트의 부호를 정확히 반영
        if has_decimal:
            if has_minus_sign or num_str.startswith("-"):
                return -abs(v)
            return abs(v)
        
        # 소수점이 없는 경우: 기존 로직
        if has_minus_sign or num_str.startswith("-"):
            return -abs(v)
        return abs(v)

    if mode == "RL":
        # R/L 기준 부호 (L이 우선, 그다음 R)
        # 예: "L 3.0°" → -3.0, "R 5.31 m" → 5.31
        text_upper = text.upper()
        if "L" in text_upper:
            return -abs(v)
        if "R" in text_upper:
            return abs(v)
        # 부호가 없으면 원래 값 반환 (음수면 음수, 양수면 양수)
        return v

    return v

# =========================
# 픽셀 감지 (자동 보정)
# =========================
def detect_symbol_by_ratio(img, min_ratio=0.02):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )
    black = cv2.countNonZero(bw)
    total = bw.shape[0] * bw.shape[1]
    return (black / total) >= min_ratio

def apply_sign(value, *, is_left=False, is_minus=False):
    if value is None:
        return None
    if is_left or is_minus:
        return -abs(value)
    return abs(value)

# =========================
# 안정화 (이전값 재사용)
# =========================
class StableValue:
    def __init__(self):
        self.last = None
    def update(self, v):
        if v is not None:
            self.last = v
        return self.last

def read_value(key):
    """숫자 감지용 간단 리더 (볼스피드/클럽스피드 샷 감지에만 사용)"""
    img = capture_region_ratio(REGIONS[key])
    return ocr_number(img)

def detect_text_presence():
    """텍스트 존재 여부 감지 (샷 시작/종료 판단용)
    Returns: True if text/pixels are detected in the region, False otherwise
    """
    if "run_text" not in REGIONS:
        return None
    
    img = capture_region_ratio(REGIONS["run_text"])
    
    # 픽셀 비율로 텍스트 존재 여부 확인 (더 빠르고 안정적)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 적응형 threshold로 텍스트 영역 감지
    bw = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )
    
    # 검은 픽셀(텍스트) 비율 계산
    black_pixels = cv2.countNonZero(bw)
    total_pixels = bw.shape[0] * bw.shape[1]
    text_ratio = black_pixels / total_pixels if total_pixels > 0 else 0
    
    # 텍스트가 있다고 판단하는 임계값 (2% 이상이면 텍스트 존재)
    has_text = text_ratio >= 0.02
    
    return has_text


def read_metrics():
    """
    실제 DB에 저장할 항목들 + 스매쉬팩터 계산.
    필요한 키(모두 숫자+부호+단위 포함 영역):
      - total_distance, carry (총거리, 캐리)
      - ball_speed, club_speed, launch_angle, back_spin
      - club_path, lateral_offset, direction_angle, side_spin, face_angle
    """
    # 총거리, 캐리
    td_txt  = ocr_text_region("total_distance")
    cr_txt  = ocr_text_region("carry")
    
    bs_txt  = ocr_text_region("ball_speed")
    cs_txt  = ocr_text_region("club_speed")
    la_txt  = ocr_text_region("launch_angle")
    bk_txt  = ocr_text_region("back_spin")

    cp_txt  = ocr_text_region("club_path")
    lo_txt  = ocr_text_region("lateral_offset")
    da_txt  = ocr_text_region("direction_angle")
    ss_txt  = ocr_text_region("side_spin")
    fa_txt  = ocr_text_region("face_angle")

    # 총거리, 캐리 파싱
    total_distance = parse_value(td_txt, mode="plain")
    carry = parse_value(cr_txt, mode="plain")

    # 디버그: OCR 텍스트 결과 출력
    if bs_txt:
        print(f"🔍 [ball_speed] OCR 텍스트: '{bs_txt}'")
        ball_speed = parse_value(bs_txt, mode="plain")
        print(f"   → 파싱 결과: {ball_speed}")
    else:
        ball_speed = None
        
    if cs_txt:
        print(f"🔍 [club_speed] OCR 텍스트: '{cs_txt}'")
        club_speed = parse_value(cs_txt, mode="plain")
        print(f"   → 파싱 결과: {club_speed}")
    else:
        club_speed = None
    launch_angle = parse_value(la_txt, mode="plain")

    # 스핀류: 백스핀은 부호 없음, 사이드스핀은 '-' 부호 가능 (4자리 숫자 우선 추출)
    back_spin    = parse_value(bk_txt, mode="plain", key="back_spin")
    side_spin    = parse_value(ss_txt, mode="minus", key="side_spin")

    # 각도/이격 : R/L 로 방향 결정
    club_path    = parse_value(cp_txt, mode="minus")
    lateral      = parse_value(lo_txt, mode="RL")
    direction    = parse_value(da_txt, mode="RL")
    face_angle   = parse_value(fa_txt, mode="RL")

    smash_factor = None
    try:
        if ball_speed is not None and club_speed not in (None, 0, 0.0):
            smash_factor = round(ball_speed / club_speed, 2)
    except Exception:
        smash_factor = None

    return {
        "total_distance":   total_distance,
        "carry":            carry,
        "ball_speed":       ball_speed,
        "club_speed":       club_speed,
        "launch_angle":     launch_angle,
        "back_spin":        back_spin,
        "club_path":        club_path,
        "lateral_offset":   lateral,
        "direction_angle":  direction,
        "side_spin":        side_spin,
        "face_angle":       face_angle,
        "smash_factor":     smash_factor,
    }

# =========================
# 감지 보조
# =========================
def safe_number(value, default=None):
    """안전한 숫자 변환 (None 방어)"""
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def is_valid_speed(v):
    try:
        v = float(v)
    except:
        return False
    return MIN_SPEED <= v <= MAX_SPEED

def approx_equal(a, b, tol):
    return abs(a - b) <= tol

def changed_enough(new, old):
    return abs(new - old) >= MIN_CHANGE

# =========================
# GPT API 초기화
# =========================
gpt_client = None
if USE_GPT_FEEDBACK and OPENAI_API_KEY:
    try:
        gpt_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ GPT API 초기화 완료")
    except Exception as e:
        print(f"⚠️ GPT API 초기화 실패: {e}")
        gpt_client = None

# =========================
# 샷 평가 및 음성 안내
# =========================
def get_criteria_rule(club_id, metric):
    """criteria.json에서 클럽/지표별 기준값 가져오기"""
    cid = (club_id or "").lower()
    club_cfg = CRITERIA.get(cid, {})
    if metric in club_cfg:
        return club_cfg[metric]
    default_cfg = CRITERIA.get("default", {})
    return default_cfg.get(metric)

def evaluate_shot(metrics, club_id="Driver"):
    """샷 데이터를 기준표와 비교하여 평가"""
    if not CRITERIA:
        return []
    
    evaluations = []
    
    # 드라이버는 3가지만 평가: 스매시팩터, 페이스각도, 클럽패스
    if club_id.lower() == "driver":
        metric_names = {
            "smash_factor": "스매시팩터",
            "face_angle": "페이스각도",
            "club_path": "클럽패스",
        }
    else:
        # 다른 클럽은 전체 평가
        metric_names = {
            "smash_factor": "스매시팩터",
            "launch_angle": "발사각",
            "face_angle": "페이스각",
            "club_path": "클럽패스",
            "lateral_offset": "좌우이격",
            "direction_angle": "방향각",
            "side_spin": "사이드스핀",
            "back_spin": "백스핀",
            "ball_speed": "볼스피드",
        }
    
    for metric_key, metric_name in metric_names.items():
        value = metrics.get(metric_key)
        if value is None:
            continue
        
        try:
            v = float(value)
        except (ValueError, TypeError):
            continue
        
        rule = get_criteria_rule(club_id, metric_key)
        if not rule:
            continue
        
        good = rule.get("good")
        bad = rule.get("bad")
        warn = rule.get("warn")
        
        # 범위값 처리 (예: [12, 16])
        if isinstance(good, (list, tuple)) and len(good) == 2:
            low, high = float(good[0]), float(good[1])
            if low <= v <= high:
                evaluations.append({"metric": metric_name, "value": v, "status": "good", "priority": 1, "metric_key": metric_key})
            else:
                if v < low:
                    evaluations.append({"metric": metric_name, "value": v, "status": "bad", "message": f"{metric_name} {v:.1f}, 낮습니다. {low:.1f} 이상이 좋습니다.", "priority": _get_priority(metric_key), "metric_key": metric_key, "target": low})
                else:
                    evaluations.append({"metric": metric_name, "value": v, "status": "bad", "message": f"{metric_name} {v:.1f}, 높습니다. {high:.1f} 이하가 좋습니다.", "priority": _get_priority(metric_key), "metric_key": metric_key, "target": high})
            continue
        
        # good/bad 기준 처리
        if good is not None and bad is not None:
            g = float(good)
            b = float(bad)
            if v >= g:
                evaluations.append({"metric": metric_name, "value": v, "status": "good", "priority": 1, "metric_key": metric_key})
            elif v <= b:
                evaluations.append({"metric": metric_name, "value": v, "status": "bad", "message": f"{metric_name} {v:.1f}, 낮습니다. {g:.2f} 이상이 좋습니다.", "priority": _get_priority(metric_key), "metric_key": metric_key, "target": g})
            else:
                evaluations.append({"metric": metric_name, "value": v, "status": "warn", "priority": _get_priority(metric_key), "metric_key": metric_key})
            continue
        
        # good/warn 기준 처리 (절대값 기준)
        if good is not None and warn is not None:
            g = float(good)
            w = float(warn)
            abs_v = abs(v)
            if abs_v <= g:
                evaluations.append({"metric": metric_name, "value": v, "status": "good", "priority": 1, "metric_key": metric_key})
            elif abs_v <= w:
                evaluations.append({"metric": metric_name, "value": v, "status": "warn", "message": f"{metric_name} {v:.1f}, 주의하세요. {g:.1f} 이하가 좋습니다.", "priority": _get_priority(metric_key), "metric_key": metric_key, "target": g})
            else:
                evaluations.append({"metric": metric_name, "value": v, "status": "bad", "message": f"{metric_name} {v:.1f}, 높습니다. {g:.1f} 이하가 좋습니다.", "priority": _get_priority(metric_key), "metric_key": metric_key, "target": g})
            continue
        
        # good만 있는 경우
        if good is not None:
            g = float(good)
            if v >= g:
                evaluations.append({"metric": metric_name, "value": v, "status": "good", "priority": 1, "metric_key": metric_key})
            else:
                evaluations.append({"metric": metric_name, "value": v, "status": "bad", "message": f"{metric_name} {v:.1f}, 낮습니다. {g:.1f} 이상이 좋습니다.", "priority": _get_priority(metric_key), "metric_key": metric_key, "target": g})
    
    return evaluations

def _get_priority(metric_key):
    """드라이버 평가 우선순위: 스매시팩터(1) > 페이스각도(2) > 클럽패스(3)"""
    priority_map = {
        "smash_factor": 1,
        "face_angle": 2,
        "club_path": 3,
    }
    return priority_map.get(metric_key, 99)

def get_gpt_feedback(metrics, club_id="Driver"):
    """GPT API를 사용하여 샷 피드백 생성"""
    if not gpt_client:
        return None
    
    try:
        # 드라이버는 3가지만 평가
        if club_id.lower() == "driver":
            shot_data = {
                "스매시팩터": metrics.get("smash_factor"),
                "페이스각도": metrics.get("face_angle"),
                "클럽패스": metrics.get("club_path"),
            }
        else:
            shot_data = {
                "스매시팩터": metrics.get("smash_factor"),
                "발사각": metrics.get("launch_angle"),
                "페이스각": metrics.get("face_angle"),
                "클럽패스": metrics.get("club_path"),
                "좌우이격": metrics.get("lateral_offset"),
                "방향각": metrics.get("direction_angle"),
                "사이드스핀": metrics.get("side_spin"),
                "백스핀": metrics.get("back_spin"),
                "볼스피드": metrics.get("ball_speed"),
            }
        
        # None 값 제거
        shot_data = {k: v for k, v in shot_data.items() if v is not None}
        
        # 기준표 정보 가져오기
        criteria_info = ""
        if club_id.lower() == "driver" and CRITERIA.get("driver"):
            driver_criteria = CRITERIA["driver"]
            criteria_info = f"""
드라이버 기준:
- 스매시팩터: {driver_criteria.get('smash_factor', {}).get('good', 'N/A')} 이상이 좋음
- 페이스각도: {driver_criteria.get('face_angle', {}).get('good', 'N/A')} 범위가 좋음
- 클럽패스: {driver_criteria.get('club_path', {}).get('good', 'N/A')} 범위가 좋음
"""
        
        prompt = f"""당신은 골프 전문 코치입니다. 골프 샷 데이터를 분석하여 간단하고 명확한 피드백을 제공해주세요.

샷 데이터:
{json.dumps(shot_data, ensure_ascii=False, indent=2)}
{criteria_info}

요구사항:
1. 드라이버 샷의 경우 스매시팩터, 페이스각도, 클럽패스 3가지만 평가
2. 가장 좋은 점 하나와 가장 안 좋은 점 하나만 언급
3. 모두 안 좋으면 우선순위(스매시팩터 > 페이스각도 > 클럽패스)에 따라 가장 안 좋은 것 하나만 언급
4. 간결하고 자연스러운 한국어로 응답 (30자 이내)
5. 수치를 언급할 때는 구체적인 값 포함

예시:
- "스매시팩터 좋습니다. 페이스각도 3.5도, 높습니다."
- "스매시팩터 1.30, 낮습니다. 1.48 이상이 좋습니다."
- "페이스각도 좋습니다. 클럽패스 5.0도, 높습니다."

피드백:"""
        
        response = gpt_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "당신은 골프 전문 코치입니다. 간결하고 명확한 피드백을 제공합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        feedback = response.choices[0].message.content.strip()
        return feedback
        
    except Exception as e:
        print(f"⚠️ GPT 피드백 생성 실패: {e}")
        return None

def generate_voice_feedback(evaluations):
    """평가 결과를 바탕으로 음성 안내 메시지 생성
    - 가장 좋은 것 하나
    - 가장 안 좋은 것 하나
    - 다 안 좋으면 우선순위에 따라 가장 안 좋은 것 하나만
    """
    if not evaluations:
        return None
    
    good_items = [e for e in evaluations if e["status"] == "good"]
    bad_items = [e for e in evaluations if e.get("message")]  # 메시지가 있는 나쁜 항목만
    
    messages = []
    
    # 다 안 좋으면 우선순위에 따라 가장 안 좋은 것 하나만
    if not good_items and bad_items:
        # 우선순위 순으로 정렬 (낮은 숫자가 높은 우선순위)
        bad_items.sort(key=lambda x: x.get("priority", 99))
        messages.append(bad_items[0]["message"])
    else:
        # 좋은 점 하나 (가장 좋은 것)
        if good_items:
            # 우선순위가 높은 것부터 (스매시팩터 > 페이스각도 > 클럽패스)
            good_items.sort(key=lambda x: x.get("priority", 99))
            messages.append(f"{good_items[0]['metric']} 좋습니다.")
        
        # 나쁜 점 하나 (가장 나쁜 것)
        if bad_items:
            # 우선순위가 높은 것부터 (스매시팩터 > 페이스각도 > 클럽패스)
            bad_items.sort(key=lambda x: x.get("priority", 99))
            messages.append(bad_items[0]["message"])
    
    if messages:
        return " ".join(messages)
    return None

# =========================
# 서버 전송
# =========================
def send_to_server(payload):
    try:
        headers = get_auth_headers()
        r = requests.post(SERVER_URL, json=payload, headers=headers, timeout=2)
        print("✅ 서버:", r.status_code, r.text[:200])
    except Exception as e:
        print("❌ 서버 전송 실패:", e)

# =========================
# 활성 사용자 조회
# =========================
def get_active_user(store_id, bay_id):
    """
    DB에서 현재 로그인한 사용자 조회
    """
    try:
        r = requests.get(
            ACTIVE_USER_API,
            params={"store_id": store_id, "bay_id": bay_id},
            timeout=1
        )
        if r.status_code == 200:
            data = r.json()
            user_id = data.get("user_id")
            if user_id:
                print(f"👤 현재 활성 사용자: {user_id}")
                return user_id
        return None
    except Exception as e:
        print(f"⚠️ 활성 사용자 조회 실패: {e}")
        return None

def clear_active_session(store_id, bay_id):
    """
    활성 세션 삭제 (자동 로그아웃)
    """
    try:
        headers = get_auth_headers()
        r = requests.post(
            f"{DEFAULT_SERVER_URL}/api/clear_session",
            json={"store_id": store_id, "bay_id": bay_id},
            headers=headers,
            timeout=1
        )
        if r.status_code == 200:
            print(f"✅ 자동 세션 종료: {store_id}/{bay_id}")
            return True
        return False
    except Exception as e:
        print(f"⚠️ 세션 종료 실패: {e}")
        return False

# =========================
# 중복 샷 차단
# =========================
last_shot_signature = None

def is_same_shot(shot_data):
    """중복 샷 차단 (ball_speed, club_speed, launch_angle 비교)"""
    global last_shot_signature
    sig = (
        shot_data.get("ball_speed"),
        shot_data.get("club_speed"),
        shot_data.get("launch_angle"),
    )
    if sig == last_shot_signature:
        return True
    last_shot_signature = sig
    return False

# =========================
# 메인 루프 (런 텍스트 기반 샷 감지)
# =========================
def check_pc_approval():
    """PC 승인 상태 확인"""
    try:
        pc_info = get_pc_info()
        pc_unique_id = pc_info.get("unique_id")
        
        # STEP 3: API URL 확인 (진단용)
        api_url = f"{DEFAULT_SERVER_URL}/api/check_pc_status"
        print(f"🔍 PC STATUS CHECK URL: {api_url}")
        
        headers = get_auth_headers()
        response = requests.post(
            api_url,
            json={"pc_unique_id": pc_unique_id},
            headers=headers,
            timeout=10
        )
        
        # STEP 2: 실제 응답 로그 출력 (진단용)
        print(f"🔍 PC STATUS RESPONSE STATUS: {response.status_code}")
        try:
            response_data = response.json()
            print(f"🔍 PC STATUS RESPONSE DATA: {response_data}")
        except:
            print(f"🔍 PC STATUS RESPONSE TEXT: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("allowed"):
                return True, data.get("reason", "승인됨")
            else:
                reason = data.get("reason", "승인 대기 중이거나 사용기간이 만료되었습니다.")
                return False, reason
        else:
            return False, f"서버 오류: {response.status_code}"
    except Exception as e:
        print(f"🔍 PC STATUS CHECK ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, f"승인 확인 실패: {e}"

def register_pc_to_server():
    """PC를 서버에 등록 (main.py에서는 사용하지 않음, register_pc.py에서만 사용)"""
    # main.py에서는 PC 등록을 하지 않고, 승인 상태만 확인
    pass

def update_pc_last_seen():
    """PC 마지막 접속 시간 업데이트"""
    if not PC_REGISTRATION_ENABLED:
        return
    
    try:
        pc_info = get_pc_info()
        pc_unique_id = pc_info.get("unique_id")
        
        headers = get_auth_headers()
        response = requests.post(
            f"{DEFAULT_SERVER_URL}/api/update_pc_last_seen",
            json={"pc_unique_id": pc_unique_id},
            headers=headers,
            timeout=5
        )
    except Exception:
        pass  # 조용히 실패 (주기적 업데이트이므로)

def run(regions=None):
    """
    샷 수집 루프 실행
    
    Args:
        regions: 좌표 데이터 딕셔너리 (GUI에서 전달). None이면 기본 좌표 파일 사용
    """
    global REGIONS
    
    # GUI 모드 확인 (GUI 스레드 환경 또는 PyInstaller 빌드)
    IS_GUI_MODE = sys.stdin is None or getattr(sys, "frozen", False)
    # GUI에서 좌표를 전달받았으면 사용, 아니면 기본 좌표 파일 사용
    if regions is not None:
        REGIONS = regions
        print(f"✅ GUI에서 전달받은 좌표 사용")
    else:
        # temp_regions.json이 있으면 우선적으로 로드 (GUI에서 다운로드한 좌표 파일)
        temp_regions_file = os.path.join(os.path.dirname(__file__), "temp_regions.json")
        if os.path.exists(temp_regions_file):
            try:
                REGIONS = load_json(temp_regions_file)["regions"]
                print(f"✅ GUI에서 다운로드한 좌표 파일 로드: temp_regions.json")
            except Exception as e:
                print(f"⚠️ temp_regions.json 로드 실패, 기본 좌표 파일 사용: {e}")
    
    # PC 승인 상태 확인 (프로그램 시작 시 필수)
    print("=" * 60)
    print("⛳ 골프 샷 트래커 시작")
    print("=" * 60)
    print("PC 승인 상태 확인 중...")
    
    approved, message = check_pc_approval()
    if not approved:
        print("=" * 60)
        print("❌ 프로그램 실행 불가")
        print(f"   사유: {message}")
        print()
        print("💡 해결 방법:")
        print("   1. PC 등록 프로그램(register_pc.exe)을 실행하여 등록")
        print("   2. 슈퍼 관리자에게 승인 요청")
        print("   3. 승인 후 다시 실행")
        print("=" * 60)
        # GUI 모드가 아닐 때만 input() 사용 (콘솔 환경)
        if not IS_GUI_MODE:
            try:
                input("엔터 키를 눌러 종료...")
            except (EOFError, OSError):
                pass
        return
    
    print(f"✅ PC 승인 확인: {message}")
    print()
    
    last_pc_update_time = time.time()
    PC_UPDATE_INTERVAL = 5 * 60  # 5분마다 마지막 접속 시간 업데이트
    
    # 상태: WAITING (대기, 런 텍스트 있음) → COLLECTING (샷 진행 중, 런 텍스트 없음) → WAITING
    state = "WAITING"
    stable_count = 0
    last_fire = 0.0
    text_disappear_time = None  # 텍스트가 사라진 시간 기록

    prev_bs = None
    prev_cs = None
    prev_run_detected = None
    
    # 자동 세션 종료를 위한 시간 추적
    last_shot_time = time.time()  # 마지막 샷 시간
    last_screen_detected_time = time.time()  # 마지막으로 연습 화면이 감지된 시간

    print("🟢 텍스트 존재 여부 기반 샷 감지 시작")
    print("💡 상태: WAITING (텍스트 대기 중)")
    print(f"⏰ 자동 세션 종료: {SESSION_AUTO_LOGOUT_NO_SHOT//60}분 동안 샷 없음 또는 {SESSION_AUTO_LOGOUT_NO_SCREEN//60}분 동안 연습 화면 아님")
    if TRAY_AVAILABLE:
        print("💡 최소화하면 시스템 트레이로 이동합니다.")

    while True:
        try:
            # 종료 플래그 확인
            if should_exit:
                print("프로그램 종료 중...")
                break
            # =========================
            # WAITING 상태: 텍스트 존재 여부 모니터링 (있으면 대기, 없으면 샷 시작)
            # =========================
            if state == "WAITING":
                has_text = detect_text_presence()
                now = time.time()
                
                # 연습 화면 감지 여부 업데이트
                if has_text is not None:
                    if has_text:
                        # 연습 화면이 감지됨
                        last_screen_detected_time = now
                
                # 자동 세션 종료 체크 1: 연습 화면이 아닌 경우 (5분)
                if has_text is not None and not has_text:
                    time_since_screen = now - last_screen_detected_time
                    if time_since_screen >= SESSION_AUTO_LOGOUT_NO_SCREEN:
                        active_user = get_active_user(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                        if active_user:
                            print(f"⏰ {SESSION_AUTO_LOGOUT_NO_SCREEN//60}분 동안 연습 화면이 감지되지 않음 → 자동 세션 종료")
                            clear_active_session(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                            last_screen_detected_time = now  # 재체크 방지
                
                # 자동 세션 종료 체크 2: 20분 동안 샷이 없는 경우
                time_since_last_shot = now - last_shot_time
                if time_since_last_shot >= SESSION_AUTO_LOGOUT_NO_SHOT:
                    active_user = get_active_user(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                    if active_user:
                        print(f"⏰ {SESSION_AUTO_LOGOUT_NO_SHOT//60}분 동안 샷이 없음 → 자동 세션 종료")
                        clear_active_session(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                        last_shot_time = now  # 재체크 방지
                
                if has_text is None:
                    # 텍스트 영역이 없으면 기존 방식으로 동작
                    print("⚠️ 텍스트 영역이 설정되지 않았습니다. 기존 방식으로 전환합니다.")
                    state = "COLLECTING"
                    prev_bs = None
                    prev_cs = None
                    continue
                
                if prev_run_detected is None:
                    prev_run_detected = has_text
                    time.sleep(WAITING_POLL_INTERVAL)
                    continue

                # 텍스트가 사라지면 (샷 시작) - 시간 기록
                if prev_run_detected and not has_text:
                    print("🎯 텍스트 사라짐 → 샷 시작 감지")
                    print("💡 상태: COLLECTING (샷 데이터 수집 시작)")
                    state = "COLLECTING"
                    text_disappear_time = time.time()  # 텍스트가 사라진 시간 기록
                    prev_run_detected = False  # COLLECTING 상태에서는 텍스트가 없는 상태
                    prev_bs = None
                    prev_cs = None
                    stable_count = 0
                else:
                    prev_run_detected = has_text
                    time.sleep(WAITING_POLL_INTERVAL)

            # =========================
            # COLLECTING 상태: 텍스트 재감지 대기 (데이터 수집 안함)
            # =========================
            elif state == "COLLECTING":
                # 텍스트 상태만 확인 (데이터는 수집하지 않음)
                has_text = detect_text_presence()
                now = time.time()
                
                # 텍스트가 다시 나타났는지 확인
                if not prev_run_detected and has_text:
                    # 텍스트가 다시 나타남
                    if text_disappear_time is not None:
                        elapsed_time = now - text_disappear_time
                    
                    if elapsed_time >= TEXT_REAPPEAR_MIN_TIME:
                        # 1초 이상 경과 → 정상 샷
                        print(f"✅ 텍스트 재감지 (경과 시간: {elapsed_time:.2f}초) → 샷 완료")
                        print("⏳ 런 텍스트 나타난 후 1초 대기 중... (화면 업데이트 대기)")
                        
                        # 런 텍스트가 나타난 후 1초 대기 (화면이 완전히 업데이트될 때까지)
                        time.sleep(1.0)
                        
                        print("📊 데이터 수집 시작")
                        
                        # 현재 활성 사용자 조회
                        active_user = get_active_user(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                        if not active_user:
                            # 로그인하지 않은 경우 게스트로 저장
                            active_user = "GUEST"
                            print("👤 활성 사용자가 없습니다. 게스트로 기록합니다.")

                        # 1초 대기 후 데이터 수집 (화면이 완전히 업데이트된 후)
                        metrics = read_metrics()
                        
                        # 의미 없는 샷 스킵 (None 방어)
                        ball_speed = safe_number(metrics.get("ball_speed") if metrics else None)
                        if ball_speed is None or ball_speed < 5:
                            log("⚠️ 의미 없는 샷 스킵 (ball_speed < 5)")
                            state = "WAITING"
                            prev_run_detected = has_text
                            text_disappear_time = None
                            prev_bs = None
                            prev_cs = None
                            time.sleep(POLL_INTERVAL)
                            continue
                        
                        # 샷 감지 시 디버그 이미지 저장 (한 번만)
                        try:
                            bs_img = capture_region_ratio(REGIONS["ball_speed"])
                            cs_img = capture_region_ratio(REGIONS["club_speed"])
                            
                            # 볼스피드 이미지 전처리 및 저장
                            h, w = bs_img.shape[:2]
                            if w < 150 or h < 50:
                                scale = max(5.0, 150.0 / w, 50.0 / h)
                                bs_img = cv2.resize(bs_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                            bs_gray = cv2.cvtColor(bs_img, cv2.COLOR_BGR2GRAY)
                            bs_gray = cv2.normalize(bs_gray, None, 0, 255, cv2.NORM_MINMAX)
                            bs_gray = cv2.GaussianBlur(bs_gray, (3, 3), 0)
                            bs_thresh = cv2.threshold(bs_gray, 145, 255, cv2.THRESH_BINARY)[1]
                            cv2.imwrite("debug_ball_speed.png", bs_thresh)
                            
                            # 클럽스피드 이미지 전처리 및 저장
                            h, w = cs_img.shape[:2]
                            if w < 150 or h < 50:
                                scale = max(5.0, 150.0 / w, 50.0 / h)
                                cs_img = cv2.resize(cs_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                            cs_gray = cv2.cvtColor(cs_img, cv2.COLOR_BGR2GRAY)
                            cs_gray = cv2.normalize(cs_gray, None, 0, 255, cv2.NORM_MINMAX)
                            cs_gray = cv2.GaussianBlur(cs_gray, (3, 3), 0)
                            cs_thresh = cv2.threshold(cs_gray, 145, 255, cv2.THRESH_BINARY)[1]
                            cv2.imwrite("debug_club_speed.png", cs_thresh)
                            
                            print("💾 디버그 이미지 저장: debug_ball_speed.png, debug_club_speed.png")
                        except Exception as e:
                            print(f"⚠️ 디버그 이미지 저장 실패: {e}")

                        # PC 고유번호 추출
                        try:
                            pc_info = get_pc_info()
                            pc_unique_id = pc_info.get("unique_id")
                        except Exception as e:
                            print(f"⚠️ PC 고유번호 추출 실패: {e}")
                            pc_unique_id = None
                        
                        payload = {
                            "store_id": DEFAULT_STORE_ID,
                            "bay_id": DEFAULT_BAY_ID,
                            "user_id": active_user,
                            "club_id": DEFAULT_CLUB_ID,
                            "pc_unique_id": pc_unique_id,  # 추가

                            "total_distance":   metrics["total_distance"],
                            "carry":            metrics["carry"],
                            "ball_speed":       metrics["ball_speed"],
                            "club_speed":       metrics["club_speed"],
                            "launch_angle":     metrics["launch_angle"],
                            "smash_factor":     metrics["smash_factor"],

                            "face_angle":       metrics["face_angle"],
                            "club_path":        metrics["club_path"],
                            "lateral_offset":   metrics["lateral_offset"],
                            "direction_angle":  metrics["direction_angle"],
                            "side_spin":        metrics["side_spin"],
                            "back_spin":        metrics["back_spin"],

                            "feedback": None,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        # 중복 샷 차단
                        if is_same_shot(payload):
                            log("⚠️ 중복 샷 감지 → 스킵")
                            state = "WAITING"
                            prev_run_detected = has_text
                            text_disappear_time = None
                            prev_bs = None
                            prev_cs = None
                            time.sleep(POLL_INTERVAL)
                            continue

                        log("📦 전송:", payload)
                        send_to_server(payload)
                        
                        # 마지막 샷 시간 업데이트
                        last_shot_time = time.time()
                        last_screen_detected_time = time.time()
                        
                        # 샷 평가 및 음성 안내 (GPT 피드백 우선)
                        if DEFAULT_CLUB_ID.lower() == "driver":
                            feedback = None
                            
                            # GPT 피드백 사용
                            if USE_GPT_FEEDBACK and gpt_client:
                                feedback = get_gpt_feedback(metrics, DEFAULT_CLUB_ID)
                            
                            # GPT 실패 시 기존 방식 사용
                            if not feedback:
                                evaluations = evaluate_shot(metrics, DEFAULT_CLUB_ID)
                                feedback = generate_voice_feedback(evaluations)
                            
                            if feedback:
                                speak(feedback)
                        
                        last_fire = now
                        print("💡 상태: WAITING (다음 샷 대기 중)")
                        state = "WAITING"
                        stable_count = 0
                        text_disappear_time = None
                        prev_run_detected = has_text
                        prev_bs = None
                        prev_cs = None
                        time.sleep(POLL_INTERVAL)
                        continue
                    else:
                        # 1초 미만 → 오류로 판단, 저장하지 않음
                        print(f"⚠️ 텍스트 재감지 (경과 시간: {elapsed_time:.2f}초) → 오류로 판단, 저장 안함")
                        # 상태 초기화하고 다시 WAITING으로
                        state = "WAITING"
                        prev_run_detected = has_text
                        text_disappear_time = None
                        prev_bs = None
                        prev_cs = None
                        time.sleep(POLL_INTERVAL)
                        continue
            else:
                prev_run_detected = has_text
            
            # PC 마지막 접속 시간 주기적 업데이트
            if PC_REGISTRATION_ENABLED and (time.time() - last_pc_update_time) >= PC_UPDATE_INTERVAL:
                update_pc_last_seen()
                last_pc_update_time = time.time()
            
            # 텍스트 재감지 대기 중
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            # 예외 발생해도 프로그램 종료하지 않고 계속 실행
            import traceback
            log(f"샷 수집 루프 오류: {e}")
            if DEBUG:
                traceback.print_exc()
            time.sleep(0.2)  # 잠깐 쉬고 계속
            continue

# =========================
# 시스템 트레이 관련 함수
# =========================
tray_icon = None
tray_thread = None
main_thread = None
should_exit = False

def create_tray_icon():
    """시스템 트레이 아이콘 생성"""
    # 간단한 아이콘 이미지 생성 (골프공 모양)
    image = Image.new('RGB', (64, 64), color='green')
    draw = ImageDraw.Draw(image)
    # 골프공 모양 그리기
    draw.ellipse([10, 10, 54, 54], fill='white', outline='black', width=2)
    draw.ellipse([20, 20, 44, 44], fill='lightgray')
    
    menu = pystray.Menu(
        pystray.MenuItem("상태 보기", show_status, default=True),
        pystray.MenuItem("종료", quit_app)
    )
    
    icon = pystray.Icon("GolfShotTracker", image, "골프 샷 트래커", menu)
    return icon

def show_status(icon, item):
    """상태 보기 (콘솔 창 표시)"""
    # 콘솔 창이 숨겨져 있으면 다시 표시
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # 콘솔 창 표시
        kernel32.AllocConsole()
        print("\n골프 샷 트래커가 실행 중입니다.")
        print("최소화하면 다시 트레이로 이동합니다.")
    except:
        pass

def quit_app(icon, item):
    """프로그램 종료"""
    global should_exit, tray_icon
    should_exit = True
    print("\n프로그램을 종료합니다...")
    if tray_icon:
        tray_icon.stop()
    os._exit(0)


def run_with_tray():
    """트레이와 함께 메인 프로그램 실행"""
    global main_thread, tray_icon
    
    if not TRAY_AVAILABLE:
        # 트레이를 사용할 수 없으면 일반 실행
        run()
        return
    
    # 메인 프로그램을 별도 스레드에서 실행
    main_thread = threading.Thread(target=run, daemon=True)
    main_thread.start()
    
    # 트레이 아이콘 생성 및 실행 (메인 스레드에서 - pystray 요구사항)
    tray_icon = create_tray_icon()
    
    # 콘솔 창 최소화 (트레이로 이동)
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # 콘솔 창 핸들 가져오기
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            # 최소화
            user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    except:
        pass
    
    # 트레이 아이콘 실행 (메인 스레드에서 블로킹)
    tray_icon.run()

if __name__ == "__main__":
    # 트레이 모드로 실행 (명령줄 인자로 --no-tray를 주면 일반 모드)
    if "--no-tray" in sys.argv or not TRAY_AVAILABLE:
        run()
    else:
        run_with_tray()