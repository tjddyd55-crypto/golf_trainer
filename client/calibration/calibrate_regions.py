# ===== calibrate_regions.py (통합 좌표 설정 스크립트) =====
import cv2
import pyautogui
import numpy as np
import json
import os
import sys

# ------------------------------------------------
# 모든 좌표를 설정하는 통합 스크립트
# 전체화면에서도 쉽게 좌표를 설정할 수 있도록 개선
# ------------------------------------------------

# 모든 항목 목록 (순서대로 설정)
ALL_ITEMS = [
    "total_distance",    # 총거리
    "carry",             # 캐리
    "ball_speed",        # 볼스피드
    "club_speed",        # 클럽스피드
    "launch_angle",      # 발사각
    "back_spin",         # 백스핀
    "club_path",         # 클럽패스
    "lateral_offset",    # 좌우이격
    "direction_angle",   # 방향각
    "side_spin",         # 사이드스핀
    "face_angle",        # 페이스각
    "run_text",          # 런 텍스트 (샷 시작/종료 감지용)
]

# 매장별 좌표 파일 경로
def get_regions_file(store_id=None):
    """매장별 좌표 파일 경로 반환"""
    if store_id:
        return f"regions/{store_id}.json"
    return "regions/test.json"

# ------------------------------------------------
def capture_screen():
    """전체 화면 캡처"""
    img = pyautogui.screenshot()
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def resize_for_display(img, max_width=1920, max_height=1080):
    """화면이 너무 크면 리사이즈 (표시용)"""
    h, w = img.shape[:2]
    
    # 화면이 max 크기보다 작으면 그대로 반환
    if w <= max_width and h <= max_height:
        return img, 1.0
    
    # 비율 유지하면서 리사이즈
    scale_w = max_width / w
    scale_h = max_height / h
    scale = min(scale_w, scale_h)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale

def select_region_interactive(screen, item_name):
    """대화형 영역 선택 (전체화면 지원, 캡처된 화면에서 좌표 설정)"""
    screen_h, screen_w = screen.shape[:2]
    
    # 화면이 너무 크면 리사이즈해서 표시 (표시는 작게, 좌표는 정확하게)
    display_img, display_scale = resize_for_display(screen, max_width=1920, max_height=1080)
    display_h, display_w = display_img.shape[:2]
    
    print(f"\n🖱️ [{item_name}] 영역 선택")
    print(f"   화면 크기: {screen_w}x{screen_h}")
    if display_scale < 1.0:
        print(f"   표시 크기: {display_w}x{display_h} (축소율: {display_scale:.2f})")
        print(f"   💡 화면이 커서 축소 표시되지만, 좌표는 정확하게 계산됩니다.")
    print("   방법: 마우스로 드래그하여 영역 선택 후 Enter")
    print("   ESC: 취소, Space: 건너뛰기")
    print("   ⚠️ 캡처된 화면 위에서 좌표를 설정하세요 (전체화면 골프 화면을 가리지 않음)\n")
    
    # 리사이즈된 화면에서 ROI 선택
    # 창 이름에 항목명 표시
    window_name = f"좌표 설정 - {item_name} (ESC: 취소)"
    roi = cv2.selectROI(
        window_name,
        display_img,
        showCrosshair=True,
        fromCenter=False
    )
    cv2.destroyAllWindows()
    
    x, y, w, h = roi
    
    # 취소 또는 건너뛰기
    if w == 0 or h == 0:
        return None
    
    # 리사이즈된 좌표를 원본 화면 좌표로 변환
    x_orig = int(x / display_scale)
    y_orig = int(y / display_scale)
    w_orig = int(w / display_scale)
    h_orig = int(h / display_scale)
    
    # 원본 화면 크기를 넘지 않도록 보정
    x_orig = min(x_orig, screen_w - 1)
    y_orig = min(y_orig, screen_h - 1)
    w_orig = min(w_orig, screen_w - x_orig)
    h_orig = min(h_orig, screen_h - y_orig)
    
    return {
        "x": round(x_orig / screen_w, 4),
        "y": round(y_orig / screen_h, 4),
        "w": round(w_orig / screen_w, 4),
        "h": round(h_orig / screen_h, 4)
    }

# ------------------------------------------------
def select_regions(store_id=None, items=None):
    """좌표 설정 메인 함수"""
    # 매장별 좌표 파일 경로
    regions_file = get_regions_file(store_id)
    
    # 기존 좌표 파일 읽기
    regions = {}
    if os.path.exists(regions_file):
        try:
            with open(regions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                regions = data.get("regions", {})
            print(f"✅ 기존 좌표 파일을 불러왔습니다: {regions_file}")
            print(f"   기존 항목: {list(regions.keys())}\n")
        except Exception as e:
            print(f"⚠️ 기존 파일 읽기 실패: {e}\n")
    
    # 설정할 항목 선택
    if items is None:
        items = ALL_ITEMS
    
    # 화면 캡처
    print("\n" + "="*60)
    print("📸 화면 캡처 중...")
    print("="*60)
    print("💡 골프 화면이 전체화면으로 실행 중이라면,")
    print("   이 스크립트가 화면을 캡처해서 별도 창에 표시합니다.")
    print("   캡처된 화면 위에서 좌표를 설정하면 됩니다.")
    print("="*60 + "\n")
    
    input("골프 화면이 준비되면 Enter를 눌러주세요...")
    
    screen = capture_screen()
    screen_h, screen_w = screen.shape[:2]
    print(f"✅ 화면 캡처 완료: {screen_w} x {screen_h}")
    
    print("\n" + "="*60)
    print("🟢 좌표 설정 시작")
    print("="*60)
    print("⚠️ 각 항목의 숫자 + 부호(R/L 또는 -) + 단위(°, rpm, m/s 등)를")
    print("   모두 포함하도록 영역을 드래그하세요.")
    print("⚠️ ESC: 취소, Space: 현재 항목 건너뛰기")
    print("💡 캡처된 화면 창이 열리면, 그 위에서 좌표를 설정하세요.")
    print("="*60 + "\n")
    
    # 각 항목 설정
    for idx, item in enumerate(items, 1):
        print(f"\n[{idx}/{len(items)}] {item}")
        
        # 이미 설정된 좌표가 있으면 확인
        if item in regions:
            print(f"   기존 좌표: {regions[item]}")
            response = input("   덮어쓰시겠습니까? (y/n/s=건너뛰기): ").lower()
            if response == 'n':
                print(f"   ✅ {item} 건너뛰기\n")
                continue
            elif response == 's':
                print(f"   ⏭️ {item} 건너뛰기\n")
                continue
        
        # 영역 선택
        region = select_region_interactive(screen, item)
        
        if region is None:
            print(f"   ⏭️ {item} 건너뛰기\n")
            continue
        
        regions[item] = region
        print(f"   ✅ {item} 저장: {region}\n")
    
    # 저장
    os.makedirs("regions", exist_ok=True)
    with open(regions_file, "w", encoding="utf-8") as f:
        json.dump({"regions": regions}, f, indent=2, ensure_ascii=False)
    
    print("="*60)
    print("🎉 좌표 설정 완료!")
    print(f"📁 저장 위치: {regions_file}")
    print(f"✅ 설정된 항목: {list(regions.keys())}")
    print("="*60)

# ------------------------------------------------
if __name__ == "__main__":
    # 명령줄 인자로 매장 ID와 항목 선택 가능
    store_id = None
    items = None
    
    if len(sys.argv) > 1:
        store_id = sys.argv[1]
        print(f"📌 매장 ID: {store_id}")
    
    if len(sys.argv) > 2:
        # 특정 항목만 설정
        items = sys.argv[2].split(",")
        print(f"📌 설정할 항목: {items}")
    
    select_regions(store_id, items)
