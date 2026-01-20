#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
좌표 설정 프로그램 (캡처 기반)
게임 화면을 캡처하여 픽셀 1:1로 좌표를 설정하는 프로그램
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
import sys
import base64
from datetime import datetime
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 좌표 설정 항목 (순서 고정 - regions/test.json과 동일)
REGION_ITEMS = [
    ("ball_speed", "Ball Speed"),
    ("club_speed", "Club Speed"),
    ("launch_angle", "Launch Angle"),
    ("back_spin", "Back Spin"),
    ("club_path", "Club Path"),
    ("lateral_offset", "Lateral Offset"),
    ("direction_angle", "Direction Angle"),
    ("side_spin", "Side Spin"),
    ("face_angle", "Face Angle"),
    ("run_text", "Run Text"),
    ("total_distance", "Total Distance"),
    ("carry", "Carry"),
]

# 브랜드 목록
BRANDS = [
    ("GOLFZON", "골프존"),
    ("SGGOLF", "SG골프"),
    ("KAKAO", "카카오골프"),
    ("BRAVO", "브라보"),
    ("ETC", "기타"),
]

# 좌표 키 목록 (순서 고정 - regions/test.json과 동일)
REGION_KEYS = [
    "ball_speed",
    "club_speed",
    "launch_angle",
    "back_spin",
    "club_path",
    "lateral_offset",
    "direction_angle",
    "side_spin",
    "face_angle",
    "run_text",
    "total_distance",
    "carry"
]

def rect_px_to_ratio(x, y, w, h, screen_width, screen_height):
    """px 좌표를 비율로 변환"""
    return {
        "x": round(x / screen_width, 6),
        "y": round(y / screen_height, 6),
        "w": round(w / screen_width, 6),
        "h": round(h / screen_height, 6),
    }

# 설정 파일 경로 (exe와 같은 디렉토리)
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """config.json 파일 로드"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 오류: {e}")
            return {}
    return {}

def get_api_base_url():
    """API 베이스 URL 가져오기 (환경 변수 → config.json → 기본값)"""
    # 1. 환경 변수 우선
    api_url = os.environ.get("API_BASE_URL")
    if api_url:
        return api_url
    
    # 2. config.json에서 읽기
    config = load_config()
    api_url = config.get("API_BASE_URL")
    if api_url:
        return api_url
    
    # 3. 기본값
    return "https://golf-api-production-e675.up.railway.app"

def get_auth_credentials():
    """인증 정보 가져오기 (환경 변수 → config.json → None)"""
    # 1. 환경 변수 우선
    username = os.environ.get("SUPER_ADMIN_USERNAME")
    password = os.environ.get("SUPER_ADMIN_PASSWORD")
    if username and password:
        return username, password
    
    # 2. config.json에서 읽기
    config = load_config()
    username = config.get("SUPER_ADMIN_USERNAME")
    password = config.get("SUPER_ADMIN_PASSWORD")
    if username and password:
        return username, password
    
    # 3. None 반환 (사용자 입력 필요)
    return None, None

def get_regions_file(store_id=None):
    """매장별 좌표 파일 경로 반환"""
    if store_id:
        return f"regions/{store_id}.json"
    return "regions/test.json"

def load_regions(file_path):
    """좌표 파일 로드"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("regions", {})
        except Exception as e:
            print(f"좌표 파일 로드 오류: {e}")
            return {}
    return {}

def save_regions(file_path, regions):
    """좌표 파일 저장"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    data = {"regions": regions}
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def capture_screen():
    """게임 화면 캡처 (작업표시줄 제외)"""
    if not PYAUTOGUI_AVAILABLE:
        raise ImportError("pyautogui가 설치되지 않았습니다. pip install pyautogui")
    
    # 전체 화면 캡처
    screenshot = pyautogui.screenshot()
    return screenshot

class RegionCalibratorOverlay:
    def __init__(self, root, brand, resolution):
        self.root = root
        self.brand = brand
        self.resolution = resolution
        self.regions = {}
        
        # 현재 설정 중인 항목 인덱스
        self.current_index = 0
        
        # 드래그 상태
        self.dragging = False
        self.drag_start = None
        self.drag_end = None
        self.current_rect = None
        self.current_rect_px = None  # 현재 드래그 영역의 px 좌표 (x, y, w, h)
        self.coordinate_labels = []  # 좌표 순서 목록 레이블
        
        # 캡처 이미지
        try:
            self.capture_image = capture_screen()
        except Exception as e:
            messagebox.showerror("오류", f"화면 캡처 실패: {e}")
            root.destroy()
            return
        
        # 캡처 이미지 크기
        self.image_width = self.capture_image.width
        self.image_height = self.capture_image.height
        
        # resolution을 캡처 이미지 크기로 업데이트
        self.resolution = f"{self.image_width}x{self.image_height}"
        
        # ✅ 보더리스 + 전체화면 + 리사이즈 없음 설정
        # Tkinter에서 overrideredirect와 -fullscreen은 함께 사용할 수 없음
        # -fullscreen 사용 (overrideredirect 제거)
        
        # 1️⃣ 전체화면
        self.root.attributes("-fullscreen", True)
        
        # 2️⃣ 항상 최상단 (작업표시줄 위)
        self.root.attributes("-topmost", True)
        
        # 포커스 강제
        self.root.lift()
        self.root.focus_force()
        self.root.bind('<KeyPress>', self.on_key_press)
        
        # 4️⃣ Canvas 생성 (리사이즈 금지)
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 5️⃣ 캡처 이미지 로드 및 표시 (절대 resize ❌)
        self.photo = ImageTk.PhotoImage(self.capture_image)
        self.canvas.create_image(
            0, 0,
            image=self.photo,
            anchor="nw"
        )
        
        # ✅ 마우스 이벤트를 canvas에 바인딩
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # UI 패널 (오른쪽 상단)
        self.create_ui_panel()
        
        # 첫 항목으로 이동
        self.update_current_item()
        
    def create_ui_panel(self):
        """오른쪽 상단 UI 패널 생성"""
        # 반투명 배경 프레임
        self.ui_frame = tk.Frame(
            self.root,
            bg='#2C2C2C',
            relief=tk.FLAT
        )
        
        # UI 패널을 오른쪽 상단에 배치 (크기 확대)
        panel_width = 400
        panel_height = 450
        panel_x = self.image_width - panel_width - 20
        panel_y = 20
        
        self.ui_frame.place(x=panel_x, y=panel_y, width=panel_width, height=panel_height)
        
        # 제목
        title_label = tk.Label(
            self.ui_frame,
            text=f"좌표 설정 ({self.current_index + 1} / {len(REGION_ITEMS)})",
            font=("맑은 고딕", 14, "bold"),
            bg='#2C2C2C',
            fg='white',
            anchor='w'
        )
        title_label.pack(pady=(10, 5), padx=15, fill=tk.X)
        
        # 현재 항목
        self.item_label = tk.Label(
            self.ui_frame,
            text="",
            font=("맑은 고딕", 12, "bold"),
            bg='#2C2C2C',
            fg='#FFD700',
            anchor='w'
        )
        self.item_label.pack(pady=(0, 10), padx=15, fill=tk.X)
        
        # 안내 문구
        self.instruction_label = tk.Label(
            self.ui_frame,
            text="① 마우스로 숫자 영역 드래그\n② Enter 키를 누르세요",
            font=("맑은 고딕", 10),
            bg='#2C2C2C',
            fg='#CCCCCC',
            anchor='w',
            justify=tk.LEFT
        )
        self.instruction_label.pack(pady=(0, 10), padx=15, fill=tk.X)
        
        # 좌표 순서 목록 프레임
        list_frame = tk.Frame(self.ui_frame, bg='#1C1C1C', relief=tk.SUNKEN, bd=2)
        list_frame.pack(pady=(0, 10), padx=15, fill=tk.BOTH, expand=True)
        
        list_title = tk.Label(
            list_frame,
            text="좌표 설정 순서",
            font=("맑은 고딕", 10, "bold"),
            bg='#1C1C1C',
            fg='#FFFFFF',
            anchor='w'
        )
        list_title.pack(pady=(8, 5), padx=10, fill=tk.X)
        
        # 스크롤 가능한 리스트 (레이블 목록)
        self.coordinate_list_frame = tk.Frame(list_frame, bg='#1C1C1C')
        self.coordinate_list_frame.pack(pady=(0, 8), padx=10, fill=tk.BOTH, expand=True)
        
        self.coordinate_labels = []
        for i in range(len(REGION_ITEMS)):
            label = tk.Label(
                self.coordinate_list_frame,
                text="",
                font=("맑은 고딕", 9),
                bg='#1C1C1C',
                fg='#AAAAAA',
                anchor='w'
            )
            label.pack(pady=2, padx=5, fill=tk.X)
            self.coordinate_labels.append(label)
        
        # 이전 버튼
        button_frame = tk.Frame(self.ui_frame, bg='#2C2C2C')
        button_frame.pack(pady=(0, 10), padx=15, fill=tk.X)
        
        self.prev_button = tk.Button(
            button_frame,
            text="◀ 이전",
            font=("맑은 고딕", 10),
            command=self.go_previous,
            bg='#4A4A4A',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            state=tk.DISABLED
        )
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 완료/취소 버튼
        cancel_button = tk.Button(
            button_frame,
            text="취소 (ESC)",
            font=("맑은 고딕", 10),
            command=self.cancel,
            bg='#6A6A6A',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        cancel_button.pack(side=tk.RIGHT)
        
    def update_current_item(self):
        """현재 항목 업데이트"""
        if self.current_index < len(REGION_ITEMS):
            item_key, item_name = REGION_ITEMS[self.current_index]
            self.item_label.config(text=f"현재 항목: {item_name}")
            
            # 제목 업데이트
            title_label = self.ui_frame.winfo_children()[0]
            title_label.config(text=f"좌표 설정 ({self.current_index + 1} / {len(REGION_ITEMS)})")
            
            # 이전 버튼 활성화/비활성화
            if self.current_index > 0:
                self.prev_button.config(state=tk.NORMAL)
            else:
                self.prev_button.config(state=tk.DISABLED)
            
            # 기존 드래그 영역 초기화
            self.drag_start = None
            self.drag_end = None
            self.current_rect_px = None
            if self.current_rect:
                self.canvas.delete(self.current_rect)
                self.current_rect = None
            
            # 기존 좌표가 있으면 미리 표시 (노란색)
            # 캡처 이미지 크기 기준으로 표시 (픽셀 1:1)
            if item_key in self.regions:
                region = self.regions[item_key]
                x = int(region['x'] * self.image_width)
                y = int(region['y'] * self.image_height)
                w = int(region['w'] * self.image_width)
                h = int(region['h'] * self.image_height)
                self.draw_rectangle(x, y, w, h, color='yellow', width=3)
            
            # 좌표 순서 목록 표시 업데이트
            self.update_coordinate_list()
    
    def on_mouse_down(self, event):
        """마우스 다운"""
        # 캔버스 좌표로 변환
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # UI 패널 영역 체크 (오른쪽 상단)
        panel_x = self.image_width - 420
        panel_y = 20
        if panel_x <= canvas_x <= self.image_width and panel_y <= canvas_y <= panel_y + 450:
            return  # UI 패널 클릭은 무시
        
        self.dragging = True
        self.drag_start = (canvas_x, canvas_y)
        
        # 기존 사각형 삭제
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
    
    def on_mouse_drag(self, event):
        """마우스 드래그"""
        if not self.dragging or not self.drag_start:
            return
        
        # 캔버스 좌표로 변환
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # UI 패널 영역 체크
        panel_x = self.image_width - 370
        panel_y = 20
        if panel_x <= canvas_x <= self.image_width and panel_y <= canvas_y <= panel_y + 200:
            return
        
        self.drag_end = (canvas_x, canvas_y)
        self.draw_current_rect()
    
    def on_mouse_up(self, event):
        """마우스 업"""
        if not self.dragging:
            return
        
        # 캔버스 좌표로 변환
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # UI 패널 영역 체크
        panel_x = self.image_width - 370
        panel_y = 20
        if panel_x <= canvas_x <= self.image_width and panel_y <= canvas_y <= panel_y + 200:
            self.dragging = False
            return
        
        self.dragging = False
        if self.drag_start and self.drag_end:
            self.draw_current_rect()
    
    def draw_current_rect(self):
        """현재 드래그 영역 표시"""
        if not self.drag_start or not self.drag_end:
            return
        
        x1, y1 = self.drag_start
        x2, y2 = self.drag_end
        
        # 좌표 정규화 (왼쪽 상단, 오른쪽 하단)
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        
        # px 좌표 저장
        self.current_rect_px = (x, y, w, h)
        
        # 기존 사각형 삭제
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        # 새 사각형 그리기 (빨간색, 두꺼운 선으로 명확하게)
        self.draw_rectangle(x, y, w, h, color='red', width=3)
    
    def draw_rectangle(self, x, y, w, h, color='red', width=3):
        """사각형 그리기 (드래그 영역 표시)"""
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        # 사각형 테두리 그리기
        self.current_rect = self.canvas.create_rectangle(
            x, y, x + w, y + h,
            outline=color,
            width=width,
            fill='',
            tags='drag_rect'
        )
        
        # 좌표 정보 텍스트 표시 (옵션)
        if w > 50 and h > 20:  # 너무 작은 영역은 텍스트 표시 안함
            coord_text = f"{w}×{h}"
            self.canvas.create_text(
                x + w/2, y + h/2,
                text=coord_text,
                fill=color,
                font=("맑은 고딕", 10, "bold"),
                tags='drag_rect'
            )
    
    def update_coordinate_list(self):
        """좌표 순서 목록 업데이트"""
        for i, label in enumerate(self.coordinate_labels):
            if i < len(REGION_ITEMS):
                item_key, item_name = REGION_ITEMS[i]
                if i == self.current_index:
                    # 현재 항목은 강조 표시
                    label.config(
                        text=f"▶ {i+1}. {item_name}",
                        fg='#FFD700',
                        font=("맑은 고딕", 9, "bold"),
                        bg='#3C3C3C'
                    )
                elif item_key in self.regions:
                    # 설정 완료된 항목
                    label.config(
                        text=f"✓ {i+1}. {item_name}",
                        fg='#90EE90',
                        font=("맑은 고딕", 9),
                        bg='#1C1C1C'
                    )
                else:
                    # 미설정 항목
                    label.config(
                        text=f"  {i+1}. {item_name}",
                        fg='#AAAAAA',
                        font=("맑은 고딕", 9),
                        bg='#1C1C1C'
                    )
            else:
                label.config(text="", bg='#1C1C1C')
    
    def on_key_press(self, event):
        """키 입력 처리"""
        if event.keysym == 'Return' or event.keysym == 'KP_Enter':
            self.confirm_current_region()
        elif event.keysym == 'Escape':
            self.cancel()
        elif event.keysym == 'BackSpace' and event.state & 0x4:  # Ctrl+BackSpace
            self.go_previous()
    
    def confirm_current_region(self):
        """현재 영역 확정"""
        if not self.current_rect_px:
            messagebox.showwarning(
                "경고",
                "영역을 먼저 드래그하여 선택하세요.",
                parent=self.root
            )
            return
        
        x, y, w, h = self.current_rect_px
        
        if w < 5 or h < 5:
            messagebox.showwarning(
                "경고",
                "영역이 너무 작습니다. 더 큰 영역을 선택하세요.",
                parent=self.root
            )
            return
        
        # px → 비율 변환 (6자리)
        # 캡처 이미지 크기 기준으로 변환 (픽셀 1:1)
        item_key = REGION_KEYS[self.current_index]
        ratio = rect_px_to_ratio(x, y, w, h, self.image_width, self.image_height)
        self.regions[item_key] = ratio
        
        # 다음 항목으로 이동
        self.current_index += 1
        self.current_rect_px = None
        
        # 좌표 순서 목록 업데이트 (완료된 항목 표시)
        self.update_coordinate_list()
        
        if self.current_index >= len(REGION_KEYS):
            # 모든 항목 설정 완료
            self.finish_calibration()
        else:
            self.update_current_item()
    
    def go_previous(self):
        """이전 항목으로 이동"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_current_item()
    
    def save_coordinates_json(self):
        """좌표 JSON 파일 저장"""
        data = {
            "brand": self.brand,
            "resolution": self.resolution,
            "version": 1,
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "regions": self.regions
        }
        
        filename = f"{self.brand}_{self.resolution}_v1.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename, data
    
    def finish_calibration(self):
        """좌표 캘리브레이션 완료 처리"""
        # JSON 파일 저장
        filename, payload = self.save_coordinates_json()
        
        # 오버레이 창 닫기
        self.root.quit()
        self.root.destroy()
        
        # 서버 업로드 옵션 제공
        upload = messagebox.askyesno(
            "완료",
            f"좌표 설정이 완료되었습니다.\n\n로컬 파일: {filename}\n\n서버에 업로드하시겠습니까?"
        )
        
        if upload:
            self.upload_to_server(payload)
        else:
            messagebox.showinfo(
                "완료",
                f"좌표 설정이 완료되었습니다.\n\n로컬 파일: {filename}\n(서버에 업로드하지 않음)"
            )
    
    def upload_to_server(self, payload):
        """서버에 좌표 업로드"""
        if not REQUESTS_AVAILABLE:
            messagebox.showerror(
                "오류",
                "requests 라이브러리가 설치되지 않았습니다.\n\n설치: pip install requests"
            )
            return
        
        # API URL 가져오기 (환경 변수 → config.json → 기본값)
        api_base_url = get_api_base_url()
        upload_url = f"{api_base_url}/api/coordinates/upload"
        
        # 인증 정보 가져오기 (환경 변수 → config.json → 사용자 입력)
        username, password = get_auth_credentials()
        
        # 인증 정보가 없으면 사용자 입력 요청
        if not username or not password:
            username = simpledialog.askstring(
                "인증 정보",
                "슈퍼 관리자 사용자명:"
            )
            if not username:
                return
            
            password = simpledialog.askstring(
                "인증 정보",
                "슈퍼 관리자 비밀번호:",
                show='*'
            )
            if not password:
                return
        
        # HTTP Basic Auth 헤더 생성
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        # 요청 데이터 준비 (서버 API 형식: brand, resolution, regions만 전송)
        data = {
            "brand": payload["brand"],
            "resolution": payload["resolution"],
            "regions": payload["regions"]
        }
        
        try:
            # 서버에 업로드
            response = requests.post(upload_url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    filename = result.get("filename", "알 수 없음")
                    version = result.get("version", "?")
                    messagebox.showinfo(
                        "업로드 성공",
                        f"좌표 파일이 서버에 업로드되었습니다.\n\n파일명: {filename}\n버전: {version}"
                    )
                else:
                    error = result.get("error", "알 수 없는 오류")
                    messagebox.showerror(
                        "업로드 실패",
                        f"서버 업로드에 실패했습니다.\n\n오류: {error}"
                    )
            elif response.status_code == 401:
                messagebox.showerror(
                    "인증 실패",
                    "인증 정보가 올바르지 않습니다.\n\n사용자명과 비밀번호를 확인하세요."
                )
            elif response.status_code == 404:
                messagebox.showerror(
                    "API 경로 오류",
                    f"API 엔드포인트를 찾을 수 없습니다.\n\nURL: {upload_url}\n\n서버가 실행 중인지, API 경로가 올바른지 확인하세요."
                )
            else:
                try:
                    error_data = response.json()
                    error = error_data.get("error", "알 수 없는 오류")
                except:
                    error = f"HTTP {response.status_code}"
                
                messagebox.showerror(
                    "업로드 실패",
                    f"서버 업로드에 실패했습니다.\n\nHTTP 상태 코드: {response.status_code}\n오류: {error}\n\nURL: {upload_url}"
                )
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "연결 실패",
                f"서버에 연결할 수 없습니다.\n\nURL: {upload_url}\n\n서버가 실행 중인지 확인하세요."
            )
        except requests.exceptions.Timeout:
            messagebox.showerror(
                "시간 초과",
                "서버 응답 시간이 초과되었습니다."
            )
        except Exception as e:
            messagebox.showerror(
                "오류",
                f"업로드 중 오류가 발생했습니다.\n\n{str(e)}"
            )
    
    def cancel(self):
        """취소"""
        if messagebox.askyesno(
            "취소",
            "좌표 설정을 취소하시겠습니까?",
            parent=self.root
        ):
            self.root.quit()

def select_brand(root):
    """브랜드 선택 다이얼로그"""
    selected_brand = {"value": None}

    dialog = tk.Toplevel(root)
    dialog.title("브랜드 선택")
    dialog.geometry("400x350")
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()  # 모달

    x = (dialog.winfo_screenwidth() // 2) - 200
    y = (dialog.winfo_screenheight() // 2) - 175
    dialog.geometry(f"+{x}+{y}")

    def on_select(brand_code):
        selected_brand["value"] = brand_code
        dialog.destroy()

    tk.Label(
        dialog,
        text="스크린골프 브랜드 선택",
        font=("맑은 고딕", 16, "bold"),
        pady=20
    ).pack()

    frame = tk.Frame(dialog)
    frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)

    for brand_code, brand_name in BRANDS:
        tk.Button(
            frame,
            text=brand_name,
            font=("맑은 고딕", 12),
            command=lambda b=brand_code: on_select(b),
            bg="#4A90E2",
            fg="white",
            height=2
        ).pack(fill=tk.X, pady=6)

    tk.Button(
        frame,
        text="취소",
        command=dialog.destroy,
        bg="#999999",
        fg="white"
    ).pack(fill=tk.X, pady=(20, 0))

    root.wait_window(dialog)
    return selected_brand["value"]

def main():
    """메인 함수"""
    try:
        root = tk.Tk()

        # 1️⃣ 브랜드 선택 (일반 창 상태)
        brand = select_brand(root)
        if brand is None:
            root.destroy()
            return

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        resolution = f"{screen_width}x{screen_height}"

        # ❌ root.withdraw() 사용하지 않음
        # 2️⃣ 오버레이는 Overlay 클래스가 책임짐
        app = RegionCalibratorOverlay(root, brand, resolution)

        root.mainloop()

    except Exception as e:
        with open("calibrate_error.log", "a", encoding="utf-8") as f:
            import traceback
            f.write(traceback.format_exc())

        from tkinter import messagebox
        messagebox.showerror("오류", str(e))

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
