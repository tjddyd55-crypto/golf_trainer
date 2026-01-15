# ===== main.py (FINAL) =====
import sys
import traceback
from datetime import datetime
from pathlib import Path
import os

# =========================
# 강제 파일 로그 (가장 중요 - GUI/트레이/어떤 코드보다 위)
# =========================
DEBUG_LOG = os.path.join(os.path.dirname(sys.executable), "early_debug.log")

def early_log(msg):
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

early_log("=== main.py start ===")

LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

def log_error(exc: Exception):
    log_file = LOG_DIR / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== UNHANDLED EXCEPTION ===\n")
        f.write(traceback.format_exc())

def global_exception_hook(exctype, value, tb):
    log_error(value)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_hook

import json
import time
import os
import re
import threading
import subprocess
import queue

import requests
import pyautogui
import numpy as np
import cv2
import pytesseract
from openai import OpenAI

# pytesseract subprocess 창 숨기기 (Windows cmd 깜빡임 방지)
if os.name == 'nt':  # Windows
    import subprocess
    # subprocess 모듈을 monkey patch하여 기본적으로 창을 숨기도록 설정
    _original_popen = subprocess.Popen
    def _popen_hidden(*args, **kwargs):
        # Windows에서 subprocess 창 숨기기
        if 'startupinfo' not in kwargs:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
        return _original_popen(*args, **kwargs)
    subprocess.Popen = _popen_hidden

# GUI 관련 import
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# =========================
# 로그 리다이렉트 (가장 중요 - 맨 위, import 바로 다음)
# =========================
early_log("before log redirect")
LOG_DIR = os.path.dirname(sys.executable)
sys.stdout = open(os.path.join(LOG_DIR, "runtime.log"), "a", encoding="utf-8")
sys.stderr = open(os.path.join(LOG_DIR, "error.log"), "a", encoding="utf-8")
early_log("after log redirect")

# 시스템 트레이 관련
early_log("before tray init")
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
    early_log("tray init success")
except Exception as e:
    early_log(f"tray init failed: {e}")
    with open("tray_import_error.log", "a", encoding="utf-8") as f:
        f.write(str(e))
    raise

# =========================
# 설정
# =========================
# 서버 URL은 환경 변수로 설정 가능 (Railway 배포 시 사용)
# 환경 변수가 없으면 Railway 프로덕션 서버 기본값 사용
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://golf-api-production-e675.up.railway.app")
SERVER_URL = f"{DEFAULT_SERVER_URL}/api/save_shot"

# PC 토큰 파일 경로 (register_pc.py와 동일한 위치)
PC_TOKEN_FILE = os.path.join(os.path.dirname(__file__), "pc_token.json")

# =========================
# GUI 관련 상수 및 함수
# =========================
# 브랜드 목록
BRANDS = [
    ("GOLFZON", "골프존"),
    ("SGGOLF", "SG골프"),
    ("KAKAO", "카카오골프"),
    ("BRAVO", "브라보"),
    ("ETC", "기타"),
]

# 설정 파일 경로 (헬퍼 함수 사용)
def get_config_file():
    """config.json 파일 경로 반환"""
    return os.path.join(get_base_path(), "config.json")

def load_config():
    """config.json 파일 로드"""
    config_file = get_config_file()
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config_data):
    """config.json 파일 저장"""
    try:
        config_file = get_config_file()
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        log(f"✅ config.json 저장 완료: {config_file}")
    except Exception as e:
        log(f"⚠️ config.json 저장 실패: {e}")

def get_api_base_url():
    """API 베이스 URL 가져오기"""
    config = load_config()
    api_url = os.environ.get("API_BASE_URL") or config.get("API_BASE_URL")
    if api_url:
        return api_url.rstrip('/')
    return "https://golf-api-production-e675.up.railway.app"

def auto_start_collection():
    """자동 시작: config.json에서 설정된 좌표값으로 자동 시작"""
    try:
        config = load_config()
        auto_brand = config.get("auto_brand")
        auto_filename = config.get("auto_filename")
        
        if not auto_brand or not auto_filename:
            log("[AUTO_START] ⚠️ 자동 시작 설정이 없습니다. config.json에 auto_brand와 auto_filename을 설정하세요.")
            return
        
        log(f"[AUTO_START] 설정된 좌표값으로 자동 시작: brand={auto_brand}, filename={auto_filename}")
        
        # GUI에 선택값 설정
        global gui_app
        if gui_app:
            gui_app.selected_brand = auto_brand
            gui_app.selected_filename = auto_filename
            # 자동으로 시작
            threading.Thread(target=gui_app.start_collection, daemon=True).start()
        else:
            log("[AUTO_START] ⚠️ GUI가 초기화되지 않았습니다.")
    except Exception as e:
        log(f"[AUTO_START] ⚠️ 자동 시작 실패: {e}")

# =========================
# 전역 상태
# =========================
shot_count = 0
global_last_shot_time = None

# GUI 참조
status_label = None   # GUI에서 만든 Label
root = None           # Tk 루트

# Tray 참조
tray_icon = None
tray_notify_enabled = False  # 트레이 알림 on/off 옵션 (기본값: 끄기)

# ===============================
# RUN 중복 실행 방지 (하드 가드)
# ===============================
run_entered = False
run_enter_lock = threading.Lock()

# Run 상태
run_started = False  # run() 스레드 시작 여부

# =========================
# 로그 브리지 클래스 (GUI 표시용)
# =========================
class UILogBridge:
    """GUI Text 위젯에 스레드 안전하게 로그를 전달하는 클래스"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.log_queue = queue.Queue()
        self.max_log_lines = 500
    
    def append(self, message):
        """로그 메시지 추가 (스레드 안전)"""
        self.log_queue.put(message)
    
    def process_queue(self):
        """큐에 쌓인 로그를 GUI에 표시 (메인 스레드에서 호출)"""
        if not GUI_AVAILABLE:
            return
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, message + "\n")
                
                # 라인 수 제한
                lines = int(self.text_widget.index("end-1c").split(".")[0])
                if lines > self.max_log_lines:
                    self.text_widget.delete("1.0", "2.0")
                
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
        except queue.Empty:
            pass

# =========================
# GUI 클래스 (ShotCollectorGUI)
# =========================
class ShotCollectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("샷 수집 프로그램 설정")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # API URL
        self.api_base_url = get_api_base_url()
        
        # 선택된 값
        self.selected_brand = None
        self.selected_filename = None
        self.coordinate_files = []
        
        # 실행 상태
        self.is_running = False
        self.downloaded_regions = None
        
        # GUI 구성
        self.setup_ui()
        
        # 로그 브리지 설정
        self.log_bridge = UILogBridge(self.log_text)
        self.root.after(100, self._process_logs)
        
        # 창 닫기 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _process_logs(self):
        """로그 큐 처리 (메인 스레드)"""
        self.log_bridge.process_queue()
        self.root.after(100, self._process_logs)
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self.root,
            text="샷 수집 프로그램",
            font=("맑은 고딕", 16, "bold"),
            pady=10
        )
        title_label.pack()
        
        # 상태 표시 (상단 고정)
        self.status_var = tk.StringVar(value="🔴 대기중")
        self.running_status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("맑은 고딕", 12, "bold"),
            fg="red",
            pady=5
        )
        self.running_status_label.pack(fill=tk.X, padx=10, pady=5)
        
        # 샷 통계 표시
        stats_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, borderwidth=1)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.shot_count_label = tk.Label(
            stats_frame,
            text="샷 수: 0",
            font=("맑은 고딕", 10, "bold"),
            bg="#f0f0f0",
            fg="#333333"
        )
        self.shot_count_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.last_shot_time_label = tk.Label(
            stats_frame,
            text="마지막 샷: 없음",
            font=("맑은 고딕", 10),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.last_shot_time_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 브랜드 선택
        brand_frame = tk.Frame(self.root, pady=10)
        brand_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(
            brand_frame,
            text="브랜드 선택:",
            font=("맑은 고딕", 10)
        ).pack(anchor=tk.W)
        
        self.brand_var = tk.StringVar()
        self.brand_combo = ttk.Combobox(
            brand_frame,
            textvariable=self.brand_var,
            state="readonly",
            font=("맑은 고딕", 10),
            width=30
        )
        self.brand_combo['values'] = [name for _, name in BRANDS]
        self.brand_combo.bind("<<ComboboxSelected>>", self.on_brand_selected)
        self.brand_combo.pack(fill=tk.X, pady=5)
        
        # 좌표 파일 선택
        file_frame = tk.Frame(self.root, pady=5)
        file_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(
            file_frame,
            text="좌표 파일 선택:",
            font=("맑은 고딕", 10)
        ).pack(anchor=tk.W)
        
        # 리스트박스와 스크롤바
        listbox_frame = tk.Frame(file_frame)
        listbox_frame.pack(fill=tk.X, pady=5)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            font=("맑은 고딕", 9),
            height=5
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)
        
        # 버튼 프레임
        button_frame = tk.Frame(self.root, pady=10)
        button_frame.pack(fill=tk.X, padx=20)
        
        self.start_button = tk.Button(
            button_frame,
            text="시작",
            font=("맑은 고딕", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=10,
            height=2,
            command=self.on_start_clicked,
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.stop_button = tk.Button(
            button_frame,
            text="종료",
            font=("맑은 고딕", 12, "bold"),
            bg="#f44336",
            fg="white",
            width=10,
            height=2,
            command=self.on_stop_clicked,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 좌표 영역 보기 버튼
        view_coords_button = tk.Button(
            button_frame,
            text="좌표 영역 보기",
            font=("맑은 고딕", 10),
            bg="#2196F3",
            fg="white",
            command=self.show_coordinate_regions
        )
        view_coords_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 실행 로그 패널
        log_frame = tk.Frame(self.root, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(
            log_frame,
            text="실행 로그:",
            font=("맑은 고딕", 10)
        ).pack(anchor=tk.W)
        
        log_scrollbar = tk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            yscrollcommand=log_scrollbar.set,
            font=("Consolas", 9),
            bg="#111111",
            fg="#00ff88",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # 상태 표시 (하단)
        self.status_label = tk.Label(
            self.root,
            text="브랜드를 선택하세요",
            font=("맑은 고딕", 9),
            fg="gray",
            pady=5
        )
        self.status_label.pack()
    
    def on_brand_selected(self, event=None):
        """브랜드 선택 시 좌표 파일 목록 가져오기"""
        brand_name = self.brand_var.get()
        if not brand_name:
            return
        
        # 브랜드 코드 찾기
        brand_code = None
        for code, name in BRANDS:
            if name == brand_name:
                brand_code = code
                break
        
        if not brand_code:
            self.status_label.config(text=f"브랜드 코드를 찾을 수 없습니다: {brand_name}", fg="red")
            return
        
        self.selected_brand = brand_code
        self.status_label.config(text="좌표 파일 목록 가져오는 중...", fg="blue")
        self.file_listbox.delete(0, tk.END)
        
        # 서버에서 좌표 파일 목록 가져오기
        threading.Thread(target=self.load_coordinate_files, args=(brand_code,), daemon=True).start()
    
    def load_coordinate_files(self, brand_code):
        """서버에서 좌표 파일 목록 가져오기"""
        try:
            url = f"{self.api_base_url}/api/coordinates/{brand_code}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    files = data.get("files", [])
                    self.coordinate_files = files
                    
                    # UI 업데이트 (메인 스레드)
                    self.root.after(0, self.update_file_listbox, files)
                    return
                else:
                    error_msg = data.get("error", "알 수 없는 오류")
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"오류: {error_msg}",
                        fg="red"
                    ))
                    return
            else:
                error_text = response.text[:100] if response.text else "알 수 없는 오류"
                self.root.after(0, lambda: self.status_label.config(
                    text=f"서버 오류 ({response.status_code}): {error_text}",
                    fg="red"
                ))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(
                text=f"연결 오류: {str(e)}",
                fg="red"
            ))
    
    def update_file_listbox(self, files):
        """파일 목록 업데이트"""
        self.file_listbox.delete(0, tk.END)
        for file_info in files:
            filename = file_info.get("filename", "")
            resolution = file_info.get("resolution", "")
            display_text = f"{filename}"
            if resolution:
                display_text += f" ({resolution})"
            self.file_listbox.insert(tk.END, display_text)
        
        if files:
            self.status_label.config(text="좌표 파일을 선택하세요", fg="gray")
        else:
            self.status_label.config(text="좌표 파일이 없습니다", fg="orange")
    
    def on_file_selected(self, event=None):
        """좌표 파일 선택"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.coordinate_files):
                file_info = self.coordinate_files[index]
                self.selected_filename = file_info.get("filename")
                self.start_button.config(state=tk.NORMAL)
                self.status_label.config(
                    text=f"선택: {self.selected_filename}",
                    fg="green"
                )
    
    def on_start_clicked(self):
        """시작 버튼 클릭"""
        if not self.selected_brand or not self.selected_filename:
            # GUI가 보이는 상태일 때만 경고 표시
            if root and root.winfo_viewable():
                messagebox.showwarning("경고", "브랜드와 좌표 파일을 선택하세요")
            else:
                log("⚠️ 브랜드와 좌표 파일을 선택하세요")
            return
        
        # 좌표 파일 다운로드
        self.status_label.config(text="좌표 파일 다운로드 중...", fg="blue")
        threading.Thread(target=self.start_collection, daemon=True).start()
    
    def start_collection(self):
        """샷 수집 시작"""
        try:
            # 좌표 파일 다운로드
            url = f"{self.api_base_url}/api/coordinates/{self.selected_brand}/{self.selected_filename}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                data = response.json()
                error = data.get("error", "다운로드 실패")
                # GUI가 보이는 상태일 때만 오류 팝업 표시
                if root and root.winfo_viewable():
                    self.root.after(0, lambda: messagebox.showerror("오류", f"좌표 파일 다운로드 실패: {error}"))
                else:
                    log(f"⚠️ 좌표 파일 다운로드 실패: {error}")
                self.root.after(0, lambda: self.status_label.config(text="다운로드 실패", fg="red"))
                return
            
            data = response.json()
            if not data.get("success"):
                error = data.get("error", "다운로드 실패")
                # GUI가 보이는 상태일 때만 오류 팝업 표시
                if root and root.winfo_viewable():
                    self.root.after(0, lambda: messagebox.showerror("오류", f"좌표 파일 다운로드 실패: {error}"))
                else:
                    log(f"⚠️ 좌표 파일 다운로드 실패: {error}")
                self.root.after(0, lambda: self.status_label.config(text="다운로드 실패", fg="red"))
                return
            
            coordinate_data = data.get("data")
            regions = coordinate_data.get("regions", {})
            
            # 좌표를 메모리에 저장
            self.downloaded_regions = regions
            
            # config.json에 자동 시작 설정 저장 (재부팅 시 자동 시작용)
            try:
                config = load_config()
                config["auto_brand"] = self.selected_brand
                config["auto_filename"] = self.selected_filename
                save_config(config)
                log(f"💾 자동 시작 설정 저장: brand={self.selected_brand}, filename={self.selected_filename}")
            except Exception as e:
                log(f"⚠️ 자동 시작 설정 저장 실패: {e}")
            
            # run() 함수 시작 (별도 스레드)
            global main_thread, should_exit, run_started
            should_exit = False
            run_started = False  # run_started 플래그 리셋
            main_thread = threading.Thread(
                target=run,
                args=(regions,),
                daemon=False
            )
            main_thread.start()
            
            # UI 업데이트
            self.root.after(0, self.on_collection_started)
            
        except Exception as e:
            # 백그라운드 실행 시 팝업 방지: 로그만 기록
            log(f"⚠️ 시작 실패: {str(e)}")
            if root and root.winfo_viewable():  # GUI가 보이는 상태일 때만 메시지 표시
                self.root.after(0, lambda: messagebox.showerror("오류", f"시작 실패: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="시작 실패", fg="red"))
    
    def on_collection_started(self):
        """수집 시작 후 UI 업데이트"""
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.brand_combo.config(state=tk.DISABLED)
        self.file_listbox.config(state=tk.DISABLED)
        
        # 상단 상태 표시 변경
        self.status_var.set("🟢 작동중")
        self.running_status_label.config(fg="green")
        
        self.status_label.config(text="● 실행 중", fg="green")
    
    def on_stop_clicked(self):
        """종료 버튼 클릭"""
        if messagebox.askyesno("확인", "샷 수집을 종료하시겠습니까?"):
            self.stop_collection()
    
    def stop_collection(self):
        """샷 수집 종료"""
        global should_exit
        should_exit = True
        
        # GUI 복원
        self.root.deiconify()
        
        self.on_collection_stopped()
    
    def on_collection_stopped(self):
        """수집 종료 후 UI 업데이트"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.brand_combo.config(state="readonly")
        self.file_listbox.config(state=tk.NORMAL)
        
        # 상단 상태 표시 변경
        self.status_var.set("🔴 대기중")
        self.running_status_label.config(fg="red")
        
        self.status_label.config(text="종료됨", fg="gray")
    
    def update_shot_stats(self, count, last_time):
        """샷 통계 업데이트 (메인 스레드에서 호출)"""
        try:
            self.shot_count_label.config(text=f"샷 수: {count}")
            if last_time:
                from datetime import datetime
                time_str = datetime.fromtimestamp(last_time).strftime("%H:%M:%S")
                self.last_shot_time_label.config(text=f"마지막 샷: {time_str}")
            else:
                self.last_shot_time_label.config(text="마지막 샷: 없음")
        except Exception as e:
            early_log(f"샷 통계 업데이트 실패: {e}")
    
    def on_closing(self):
        """창 닫기 (X 버튼 클릭 시 항상 트레이로 숨김)"""
        # X 버튼 클릭 시 항상 트레이로 숨김 (종료하지 않음)
        self.hide_to_tray()
    
    def hide_to_tray(self):
        """트레이로 이동 (GUI 숨김)"""
        self.root.withdraw()
    
    def show_coordinate_regions(self):
        """좌표 영역을 빨간 박스로 표시하는 이미지 생성 및 표시"""
        try:
            from PIL import ImageTk
            
            # 선택한 좌표 파일 확인
            if not self.selected_brand or not self.selected_filename:
                # GUI가 보이는 상태일 때만 경고 표시
                if root and root.winfo_viewable():
                    messagebox.showwarning("경고", "브랜드와 좌표 파일을 선택하세요.")
                else:
                    log("⚠️ 브랜드와 좌표 파일을 선택하세요.")
                return
            
            log(f"좌표 파일 로드 중: {self.selected_filename}")
            
            # 선택한 좌표 파일 다운로드
            try:
                url = f"{self.api_base_url}/api/coordinates/{self.selected_brand}/{self.selected_filename}"
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    # GUI가 보이는 상태일 때만 오류 팝업 표시
                    if root and root.winfo_viewable():
                        messagebox.showerror("오류", f"좌표 파일 다운로드 실패: {response.status_code}")
                    else:
                        log(f"⚠️ 좌표 파일 다운로드 실패: {response.status_code}")
                    return
                
                data = response.json()
                if not data.get("success"):
                    error = data.get("error", "다운로드 실패")
                    # GUI가 보이는 상태일 때만 오류 팝업 표시
                    if root and root.winfo_viewable():
                        messagebox.showerror("오류", f"좌표 파일 다운로드 실패: {error}")
                    else:
                        log(f"⚠️ 좌표 파일 다운로드 실패: {error}")
                    return
                
                coordinate_data = data.get("data", {})
                regions = coordinate_data.get("regions", {})
                resolution = coordinate_data.get("resolution", "")
                
                if not regions:
                    # GUI가 보이는 상태일 때만 경고 표시
                    if root and root.winfo_viewable():
                        messagebox.showwarning("경고", "좌표 데이터가 없습니다.")
                    else:
                        log("⚠️ 좌표 데이터가 없습니다.")
                    return
                
                log(f"좌표 파일 로드 완료: {len(regions)}개 영역")
                
            except Exception as e:
                log(f"좌표 파일 다운로드 실패: {e}")
                # GUI가 보이는 상태일 때만 오류 팝업 표시
                if root and root.winfo_viewable():
                    messagebox.showerror("오류", f"좌표 파일 다운로드 실패: {e}")
                return
            
            log("화면 캡처 중...")
            
            # 화면 캡처
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            screen_h, screen_w = screen_cv.shape[:2]
            
            log(f"화면 캡처 완료: {screen_w}x{screen_h}")
            
            # 해상도 불일치 경고
            if resolution:
                try:
                    coord_w, coord_h = map(int, resolution.split('x'))
                    if coord_w != screen_w or coord_h != screen_h:
                        log(f"⚠️ 해상도 불일치: 좌표 파일={resolution}, 실제 화면={screen_w}x{screen_h}")
                except:
                    pass
            
            # 좌표 영역을 빨간 박스로 그리기
            for key, region in regions.items():
                x_ratio = region.get("x", 0)
                y_ratio = region.get("y", 0)
                w_ratio = region.get("w", 0)
                h_ratio = region.get("h", 0)
                
                # 비율을 픽셀 좌표로 변환
                x = int(x_ratio * screen_w)
                y = int(y_ratio * screen_h)
                w = int(w_ratio * screen_w)
                h = int(h_ratio * screen_h)
                
                # 좌표 유효성 검사
                if w <= 0 or h <= 0:
                    continue
                
                # 빨간 박스 그리기
                cv2.rectangle(screen_cv, (x, y), (x + w, y + h), (0, 0, 255), 3)
                
                # 영역 이름 표시 (박스 위에)
                text_y = max(y - 5, 15)  # 화면 위로 벗어나지 않도록
                cv2.putText(
                    screen_cv,
                    key,
                    (x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )
            
            # 새 창 생성
            coord_window = tk.Toplevel(self.root)
            coord_window.title(f"좌표 영역 표시 - {self.selected_filename}")
            coord_window.geometry("1200x800")
            
            # 이미지 리사이즈 (표시용)
            display_width = 1200
            display_height = 800
            scale = min(display_width / screen_w, display_height / screen_h, 1.0)
            new_width = int(screen_w * scale)
            new_height = int(screen_h * scale)
            
            resized = cv2.resize(screen_cv, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # OpenCV 이미지를 PIL 이미지로 변환
            resized_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(resized_rgb)
            photo = ImageTk.PhotoImage(image=pil_image)
            
            # 이미지 표시
            image_label = tk.Label(coord_window, image=photo)
            image_label.image = photo  # 참조 유지
            image_label.pack(fill=tk.BOTH, expand=True)
            
            # 설명 라벨
            info_text = f"빨간 박스로 표시된 영역: {self.selected_filename}"
            if resolution:
                info_text += f" (해상도: {resolution})"
            if resolution and (screen_w != int(resolution.split('x')[0]) or screen_h != int(resolution.split('x')[1])):
                info_text += f" ⚠️ 실제 화면: {screen_w}x{screen_h}"
            
            info_label = tk.Label(
                coord_window,
                text=info_text,
                font=("맑은 고딕", 10),
                fg="red"
            )
            info_label.pack(pady=5)
            
            log("좌표 영역 표시 완료")
            
        except Exception as e:
            log(f"좌표 영역 표시 실패: {e}")
            import traceback
            log(traceback.format_exc())
            # GUI가 보이는 상태일 때만 오류 팝업 표시
            if root and root.winfo_viewable():
                messagebox.showerror("오류", f"좌표 영역 표시 실패: {e}")
    
    def show_window(self):
        """GUI 창 표시"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

# run_with_retry_wrapper 함수 제거됨 - run()은 한 번만 실행되고 중복 실행 방지됨

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
    """로그 출력 (GUI 로그 브리지로 전달, 파일 저장, cmd 깜빡임 방지)"""
    message = " ".join(str(arg) for arg in args)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    
    # 1. 파일에 직접 저장 (항상 실행, sys.stdout 리다이렉트와 별도)
    try:
        runtime_log_path = os.path.join(LOG_DIR, "runtime.log")
        with open(runtime_log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass  # 파일 쓰기 실패해도 계속 진행
    
    # 2. GUI 로그 브리지로 전달 (gui_app가 초기화된 경우에만)
    try:
        if GUI_AVAILABLE:
            # gui_app가 전역 변수로 정의되어 있는지 확인
            if 'gui_app' in globals() and gui_app and hasattr(gui_app, 'log_bridge'):
                try:
                    gui_app.log_bridge.append(message)
                except Exception:
                    pass
    except NameError:
        # gui_app가 아직 정의되지 않은 경우 무시
        pass
    
    # 3. DEBUG 모드에서만 콘솔 출력 (cmd 깜빡임 방지)
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
# resource_path는 나중에 정의되므로 상대 경로만 저장
REGIONS_FILE_RELATIVE = os.path.join("regions", f"{DEFAULT_STORE_ID}.json")
REGIONS_FILE_FALLBACK = os.path.join("regions", "test.json")

# 샷 기준표 파일 경로
CRITERIA_FILE_RELATIVE = os.path.join("config", "criteria.json")
# 피드백 메시지 파일 경로
FEEDBACK_MESSAGES_FILE_RELATIVE = os.path.join("config", "feedback_messages.json")

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
# 경로 헬퍼 함수 (PyInstaller onefile 대응)
# =========================
def get_runtime_base_dir():
    """
    exe 실행 시: exe가 있는 폴더
    python 실행 시: main.py가 있는 폴더
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_base_path():
    """실행 파일 기준 경로 반환 (onefile 환경 고려) - get_runtime_base_dir() 별칭"""
    return get_runtime_base_dir()

def get_resource_path(relative_path):
    """리소스 파일 경로 반환 (onefile 환경 고려)
    
    우선순위:
    1. sys._MEIPASS (onefile 임시 폴더) - 읽기 전용
    2. 실행 파일 기준 경로 - 읽기/쓰기 가능
    """
    try:
        # PyInstaller onefile 모드: sys._MEIPASS에 임시 폴더 경로
        bundled_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundled_path):
            return bundled_path
    except AttributeError:
        pass
    
    # 실행 파일 기준 경로 (쓰기 가능)
    return os.path.join(get_base_path(), relative_path)

def ensure_dir(dir_path):
    """디렉토리가 없으면 생성"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        early_log(f"Created directory: {dir_path}")

def ensure_config_dirs():
    """config/와 regions/ 폴더가 없으면 생성"""
    base = get_base_path()
    config_dir = os.path.join(base, "config")
    regions_dir = os.path.join(base, "regions")
    
    ensure_dir(config_dir)
    ensure_dir(regions_dir)
    
    # 기본 파일이 없으면 생성
    _create_default_config_if_needed()
    _create_default_regions_if_needed()

def _create_default_config_if_needed():
    """기본 config 파일 생성 (없는 경우)"""
    base = get_base_path()
    config_file = os.path.join(base, "config", "criteria.json")
    
    if not os.path.exists(config_file):
        try:
            # bundled 파일에서 복사 시도
            bundled_path = get_resource_path("config/criteria.json")
            if os.path.exists(bundled_path):
                import shutil
                ensure_dir(os.path.dirname(config_file))
                shutil.copy2(bundled_path, config_file)
                early_log(f"Copied default criteria.json to {config_file}")
        except Exception as e:
            early_log(f"Failed to create default criteria.json: {e}")

def _create_default_regions_if_needed():
    """기본 regions 파일 생성 (없는 경우)"""
    base = get_base_path()
    regions_file = os.path.join(base, "regions", "test.json")
    
    if not os.path.exists(regions_file):
        try:
            # bundled 파일에서 복사 시도
            bundled_path = get_resource_path("regions/test.json")
            if os.path.exists(bundled_path):
                import shutil
                ensure_dir(os.path.dirname(regions_file))
                shutil.copy2(bundled_path, regions_file)
                early_log(f"Copied default test.json to {regions_file}")
        except Exception as e:
            early_log(f"Failed to create default test.json: {e}")

def load_json(filename):
    """JSON 파일 로드 (regions 파일 전용)
    
    우선순위:
    1. regions/{filename} (primary)
    2. regions/test.json (fallback)
    """
    BASE_DIR = get_runtime_base_dir()
    REGIONS_DIR = os.path.join(BASE_DIR, "regions")
    
    primary = os.path.join(REGIONS_DIR, filename)
    fallback = os.path.join(REGIONS_DIR, "test.json")
    
    if os.path.exists(primary):
        return json.load(open(primary, "r", encoding="utf-8"))
    
    if os.path.exists(fallback):
        return json.load(open(fallback, "r", encoding="utf-8"))
    
    raise FileNotFoundError(
        f"regions 파일을 찾을 수 없습니다: {primary}, {fallback}"
    )

def load_config_json(filename):
    """JSON 파일 로드 (config 파일 전용)
    
    config/{filename} 파일을 로드합니다.
    """
    BASE_DIR = get_runtime_base_dir()
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    
    config_path = os.path.join(CONFIG_DIR, filename)
    
    if os.path.exists(config_path):
        return json.load(open(config_path, "r", encoding="utf-8"))
    
    raise FileNotFoundError(
        f"config 파일을 찾을 수 없습니다: {config_path}"
    )

def load_feedback_messages():
    """피드백 메시지 파일 안전 로드"""
    BASE_DIR = get_runtime_base_dir()
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    path = os.path.join(CONFIG_DIR, "feedback_messages.json")

    if not os.path.exists(path):
        log(f"feedback messages file not found: config 파일을 찾을 수 없습니다: {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"feedback messages load error: {e}")
        return {}

# config/와 regions/ 폴더 자동 생성 (onefile 배포 대응)
early_log("ensuring config/regions directories")
ensure_config_dirs()

# 매장별 좌표 파일 로드
early_log("before load_json")
try:
    # load_json() 함수가 자동으로 fallback 처리
    regions_filename = f"{DEFAULT_STORE_ID}.json"
    early_log(f"loading regions file: {regions_filename}")
    REGIONS = load_json(regions_filename)["regions"]
    log(f"✅ 좌표 파일 로드 완료: {regions_filename}")
    early_log("regions file loaded successfully")
except FileNotFoundError as e:
    early_log(f"regions file load failed: {e}")
    log(f"❌ 오류: {e}")
    log(f"💡 regions/{DEFAULT_STORE_ID}.json 파일을 생성하거나 regions/test.json 파일을 확인하세요.")
    raise

# 샷 기준표 파일 로드
early_log("before load criteria")
try:
    CRITERIA = load_config_json("criteria.json")
    log(f"✅ 샷 기준표 로드 완료: criteria.json")
    early_log("criteria file loaded")
except FileNotFoundError as e:
    log(f"⚠️ 샷 기준표 파일을 찾을 수 없습니다: {e}")
    early_log(f"criteria file not found: {e}")
    CRITERIA = {}

# 피드백 메시지 파일 로드
early_log("before load feedback messages")
FEEDBACK_MESSAGES = load_feedback_messages()
if FEEDBACK_MESSAGES:
    log(f"✅ 피드백 메시지 로드 완료: feedback_messages.json")
    early_log("feedback messages loaded")
else:
    log(f"⚠️ 피드백 메시지 파일이 없거나 비어있습니다.")
    early_log("feedback messages file not found or empty")

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

    # OCR 파싱 (모든 값 동일하게 처리)
    ball_speed = parse_value(bs_txt, mode="plain")
    club_speed = parse_value(cs_txt, mode="plain")
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
        log("✅ GPT API 초기화 완료")
    except Exception as e:
        log(f"⚠️ GPT API 초기화 실패: {e}")
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
        log(f"⚠️ GPT 피드백 생성 실패: {e}")
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
    """서버로 샷 데이터 전송 (상세 로그 포함)"""
    try:
        headers = get_auth_headers()
        log(f"🌐 서버 전송 시도: {SERVER_URL}")
        r = requests.post(SERVER_URL, json=payload, headers=headers, timeout=2)
        if r.status_code == 200:
            log(f"✅ 서버 전송 성공: {r.status_code}, 응답={r.text[:200]}")
        else:
            log(f"⚠️ 서버 전송 부분 실패: 상태코드={r.status_code}, 응답={r.text[:200]}")
    except requests.exceptions.Timeout:
        log(f"❌ 서버 전송 실패: 타임아웃 (서버 응답 없음, URL={SERVER_URL})")
    except requests.exceptions.ConnectionError:
        log(f"❌ 서버 전송 실패: 연결 오류 (서버에 연결할 수 없음, URL={SERVER_URL})")
    except Exception as e:
        log(f"❌ 서버 전송 실패: {type(e).__name__}: {str(e)} (URL={SERVER_URL})")

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
                log(f"👤 현재 활성 사용자: {user_id}")
                return user_id
        return None
    except Exception as e:
        log(f"⚠️ 활성 사용자 조회 실패: {e}")
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
            log(f"✅ 자동 세션 종료: {store_id}/{bay_id}")
            return True
        return False
    except Exception as e:
        log(f"⚠️ 세션 종료 실패: {e}")
        return False

# =========================
# 중복 샷 차단
# =========================
last_shot_signature = None
last_shot_time = None
MIN_SHOT_INTERVAL = 2.0  # 최소 샷 간격 (초) - 테스트 환경에서 같은 캡처본 사용 시에도 기록되도록

def is_same_shot(shot_data):
    """중복 샷 차단 (ball_speed, club_speed, launch_angle 비교 + 시간 간격 체크)"""
    global last_shot_signature, last_shot_time
    import time
    
    now = time.time()
    
    # 최소 시간 간격 체크 (테스트 환경 대응)
    if last_shot_time is not None:
        time_diff = now - last_shot_time
        if time_diff < MIN_SHOT_INTERVAL:
            # 너무 짧은 간격이면 중복으로 판단
            return True
    
    sig = (
        shot_data.get("ball_speed"),
        shot_data.get("club_speed"),
        shot_data.get("launch_angle"),
    )
    
    # 같은 수치이고 시간 간격도 짧으면 중복
    if sig == last_shot_signature and last_shot_time is not None:
        time_diff = now - last_shot_time
        if time_diff < MIN_SHOT_INTERVAL:
            return True
    
    # 새로운 샷으로 기록
    last_shot_signature = sig
    last_shot_time = now
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
        log(f"🔍 PC STATUS CHECK URL: {api_url}")
        
        headers = get_auth_headers()
        response = requests.post(
            api_url,
            json={"pc_unique_id": pc_unique_id},
            headers=headers,
            timeout=10
        )
        
        # STEP 2: 실제 응답 로그 출력 (진단용)
        log(f"🔍 PC STATUS RESPONSE STATUS: {response.status_code}")
        try:
            response_data = response.json()
            log(f"🔍 PC STATUS RESPONSE DATA: {response_data}")
        except:
            log(f"🔍 PC STATUS RESPONSE TEXT: {response.text[:500]}")
        
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
        log(f"🔍 PC STATUS CHECK ERROR: {e}")
        import traceback
        log(traceback.format_exc())
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
    global run_entered
    
    with run_enter_lock:
        if run_entered:
            log("[RUN] second run() call blocked")
            return
        run_entered = True
    
    log("[RUN] run() entered (first and only)")
    # early_log("run() function called")  # 최종 정리: 중복 로그 제거
    
    try:
        global REGIONS
        
        # GUI 모드 확인 (GUI 스레드 환경 또는 PyInstaller 빌드)
        IS_GUI_MODE = sys.stdin is None or getattr(sys, "frozen", False)
        
        # regions 처리: GUI에서 전달받았으면 사용, 아니면 전역 REGIONS 사용
        # (onefile 환경에서도 이미 load_json()에서 fallback(test.json)까지 로드됨)
        if regions is not None:
            REGIONS = regions
            log(f"✅ GUI에서 전달받은 좌표 사용")
        else:
            # regions=None이면 전역 REGIONS 사용 (이미 로드됨)
            # temp_regions.json이 있으면 우선적으로 로드 시도
            try:
                if getattr(sys, "frozen", False):
                    base_dir = os.path.dirname(sys.executable)
                else:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                temp_regions_file = os.path.join(base_dir, "temp_regions.json")
                if os.path.exists(temp_regions_file):
                    try:
                        with open(temp_regions_file, "r", encoding="utf-8") as f:
                            REGIONS = json.load(f)["regions"]
                        log(f"✅ GUI에서 다운로드한 좌표 파일 로드: temp_regions.json")
                    except Exception as e:
                        log(f"⚠️ temp_regions.json 로드 실패, 전역 REGIONS 사용: {e}")
                else:
                    # temp_regions.json이 없으면 전역 REGIONS 사용 (이미 로드됨)
                    log(f"✅ 전역 REGIONS 사용 (이미 로드됨)")
            except Exception as e:
                log(f"⚠️ 좌표 파일 확인 실패, 전역 REGIONS 사용: {e}")
        
        # PC 승인 상태 확인 (프로그램 시작 시 필수)
        log("=" * 60)
        log("⛳ 골프 샷 트래커 시작")
        log("=" * 60)
        log("PC 승인 상태 확인 중...")
        
        # PC 승인 상태 확인 (초기 확인만, 실패해도 루프는 계속 실행)
        approved, message = check_pc_approval()
        pc_approved = approved
        last_pc_check_time = time.time()
        PC_CHECK_INTERVAL = 60  # 1분마다 PC 승인 상태 재확인
        
        if not approved:
            log("=" * 60)
            log("⚠️ PC 승인 미완료")
            log(f"   사유: {message}")
            log("")
            log("💡 해결 방법:")
            log("   1. PC 등록 프로그램(register_pc.exe)을 실행하여 등록")
            log("   2. 슈퍼 관리자에게 승인 요청")
            log("   3. 승인 후 샷 수집이 시작됩니다")
            log("=" * 60)
            log("⚠️ PC 승인 전까지 샷 수집이 비활성화됩니다.")
            log("🔄 PC 승인 상태를 주기적으로 확인합니다...")
        else:
            log(f"✅ PC 승인 확인: {message}")
        
        log("")
        
        last_pc_update_time = time.time()
        PC_UPDATE_INTERVAL = 5 * 60  # 5분마다 마지막 접속 시간 업데이트
        
        # 상태: WAITING (대기, 런 텍스트 있음) → COLLECTING (샷 진행 중, 런 텍스트 없음) → WAITING
        state = "WAITING"
        stable_count = 0
        last_fire = 0.0
        text_disappear_time = None  # 텍스트가 사라진 시간 기록
        
        # 빠른 샷 확정을 위한 상태 변수
        shot_in_progress = False  # 샷 진행 중 여부 (텍스트 사라짐 → True)
        pending_read_at = None    # OCR 읽기 예약 시간 (텍스트 재등장 시 now + 1.2 설정)

        prev_bs = None
        prev_cs = None
        prev_run_detected = None
        
        # 자동 세션 종료를 위한 시간 추적
        last_shot_time = time.time()  # 마지막 샷 시간
        last_screen_detected_time = time.time()  # 마지막으로 연습 화면이 감지된 시간

        log("🟢 텍스트 존재 여부 기반 샷 감지 시작")
        log("💡 상태: WAITING (텍스트 대기 중)")
        log(f"⏰ 자동 세션 종료: {SESSION_AUTO_LOGOUT_NO_SHOT//60}분 동안 샷 없음 또는 {SESSION_AUTO_LOGOUT_NO_SCREEN//60}분 동안 연습 화면 아님")
        if TRAY_AVAILABLE:
            log("💡 최소화하면 시스템 트레이로 이동합니다.")

        # =========================
        # 기존 while True 루프
        # OCR / 샷 감지 로직
        # =========================
        while True:
            try:
                # 종료 플래그 확인
                if should_exit:
                    log("프로그램 종료 중...")
                    break
                
                # PC 승인 상태 주기적 확인 (1분마다)
                now = time.time()
                if now - last_pc_check_time >= PC_CHECK_INTERVAL:
                    approved, message = check_pc_approval()
                    if approved and not pc_approved:
                        # 승인 상태로 변경됨
                        log(f"✅ PC 승인 확인: {message}")
                        pc_approved = True
                    elif not approved and pc_approved:
                        # 승인 상태가 해제됨
                        log(f"⚠️ PC 승인 상태 변경: {message}")
                        pc_approved = False
                    last_pc_check_time = now
                
                # PC 승인 전에는 샷 수집 비활성화
                if not pc_approved:
                    time.sleep(POLL_INTERVAL)
                    continue
                
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
                                log(f"⏰ {SESSION_AUTO_LOGOUT_NO_SCREEN//60}분 동안 연습 화면이 감지되지 않음 → 자동 세션 종료")
                                clear_active_session(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                                last_screen_detected_time = now  # 재체크 방지
                    
                    # 자동 세션 종료 체크 2: 20분 동안 샷이 없는 경우
                    time_since_last_shot = now - last_shot_time
                    if time_since_last_shot >= SESSION_AUTO_LOGOUT_NO_SHOT:
                        active_user = get_active_user(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                        if active_user:
                            log(f"⏰ {SESSION_AUTO_LOGOUT_NO_SHOT//60}분 동안 샷이 없음 → 자동 세션 종료")
                            clear_active_session(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                            last_shot_time = now  # 재체크 방지
                    
                    if has_text is None:
                        # 텍스트 영역이 없으면 기존 방식으로 동작
                        log("⚠️ 텍스트 영역이 설정되지 않았습니다. 기존 방식으로 전환합니다.")
                        state = "COLLECTING"
                        prev_bs = None
                        prev_cs = None
                        continue
                    
                    if prev_run_detected is None:
                        prev_run_detected = has_text
                        time.sleep(WAITING_POLL_INTERVAL)
                        continue

                    # 텍스트가 사라지면 (샷 시작) - 시간 기록
                    # prev_run_detected가 True이고 현재 has_text가 False일 때만 샷 시작으로 판단
                    if prev_run_detected is True and has_text is False:
                        log("🎯 텍스트 사라짐 → 샷 시작 감지")
                        log("💡 상태: COLLECTING (샷 진행 중)")
                        state = "COLLECTING"
                        shot_in_progress = True  # 샷 진행 중 플래그 설정
                        text_disappear_time = time.time()  # 텍스트가 사라진 시간 기록
                        pending_read_at = None  # 이전 예약 시간 초기화
                        prev_run_detected = False  # COLLECTING 상태에서는 텍스트가 없는 상태
                        prev_bs = None
                        prev_cs = None
                        stable_count = 0
                    else:
                        # 상태 업데이트 (None이 아닐 때만)
                        if prev_run_detected is not None:
                            prev_run_detected = has_text
                        time.sleep(WAITING_POLL_INTERVAL)

                # =========================
                # COLLECTING 상태: 텍스트 재감지 대기 (데이터 수집 안함)
                # =========================
                elif state == "COLLECTING":
                    # 텍스트 상태만 확인 (데이터는 수집하지 않음)
                    has_text = detect_text_presence()
                    now = time.time()
                    
                    # 텍스트가 다시 나타났는지 확인 (샷 종료 이벤트)
                    # prev_run_detected가 False이고 현재 has_text가 True일 때만 샷 종료로 판단
                    if prev_run_detected is False and has_text is True:
                        # Run Text 재등장 → 즉시 OCR 읽기 예약
                        log("✅ 텍스트 재등장 → 샷 종료 감지")
                        pending_read_at = now + 1.0  # 1.0초 후 OCR 읽기 예약
                        shot_in_progress = False  # 샷 진행 종료
                        state = "WAITING"  # WAITING 상태로 전환하여 pending_read_at 체크
                        prev_run_detected = has_text
                        log(f"⏳ 1.0초 후 OCR 읽기 예약됨 (pending_read_at={pending_read_at:.2f})")
                        time.sleep(POLL_INTERVAL)
                        continue
                    else:
                        # 상태 업데이트
                        if prev_run_detected is not None:
                            prev_run_detected = has_text
                        time.sleep(POLL_INTERVAL)
                        continue
                
                # =========================
                # WAITING 상태: pending_read_at 체크 및 샷 확정
                # =========================
                if state == "WAITING" and pending_read_at is not None:
                    now = time.time()
                    if now >= pending_read_at:
                        # 예약 시간 도달 → OCR 읽기 및 샷 확정
                        log("📊 OCR 읽기 시작 (예약 시간 도달)")
                        pending_read_at = None  # 예약 시간 초기화
                        
                        # OCR 읽기 (예약 시간 도달 후 단 1회) - 활성 사용자 조회보다 먼저
                        metrics = read_metrics()
                        
                        # 현재 활성 사용자 조회 (OCR 읽기 후 즉시)
                        active_user = get_active_user(DEFAULT_STORE_ID, DEFAULT_BAY_ID)
                        if not active_user:
                            # 로그인하지 않은 경우 게스트로 저장
                            active_user = "GUEST"
                            log("👤 활성 사용자가 없습니다. 게스트로 기록합니다.")
                        
                        # 의미 없는 샷 스킵 (None 방어)
                        ball_speed = safe_number(metrics.get("ball_speed") if metrics else None)
                        if ball_speed is None or ball_speed < 5:
                            log(f"⚠️ 의미 없는 샷 스킵: ball_speed={ball_speed} (ball_speed < 5 또는 None)")
                            if metrics:
                                log(f"📊 전체 OCR 값: {metrics}")
                            state = "WAITING"
                            prev_run_detected = has_text
                            text_disappear_time = None
                            prev_bs = None
                            prev_cs = None
                            time.sleep(POLL_INTERVAL)
                            continue
                        

                        # PC 고유번호 추출
                        try:
                            pc_info = get_pc_info()
                            pc_unique_id = pc_info.get("unique_id")
                        except Exception as e:
                            log(f"⚠️ PC 고유번호 추출 실패: {e}")
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

                        # ===== 샷 확정 시점 =====
                        # 중요: send_to_server() 앞에 둬야 함
                        # → 서버 실패해도 "샷은 찍혔다"는 UX 보장
                        
                        # 1️⃣ 샷 통계 업데이트
                        global shot_count, global_last_shot_time
                        with shot_stats_lock:
                            shot_count += 1
                            global_last_shot_time = datetime.now().strftime("%H:%M:%S")
                        
                        # (A) 샷 확정 시 로그 (운영용 - 문제 진단 핵심)
                        # GUI/트레이와 별도로 로그에 명확한 흔적 남기기
                        # → 나중에 현장 문제 생기면 이 한 줄이 생명줄임
                        log(f"[SHOT CONFIRMED] count={shot_count}, time={global_last_shot_time}, user={active_user}")
                        log(f"📊 OCR 값: ball_speed={metrics.get('ball_speed')}, club_speed={metrics.get('club_speed')}, launch_angle={metrics.get('launch_angle')}")
                        log("📦 전송:", payload)
                        
                        # 2️⃣ GUI / Tray 즉시 반영
                        # root.after() 사용 → run()이 백그라운드 스레드여도 GUI 안전
                        update_gui_stats()  # 내부에서 root.after() 사용
                        update_tray_stats()
                        
                        # (B) 샷 감지 음성 알림 (FEEDBACK_MESSAGES 사용)
                        msg = FEEDBACK_MESSAGES.get("shot_detected")
                        if msg:
                            speak(msg)
                        
                        # (C) 트레이 notify (선택이지만 강력 추천)
                        # 샷이 실제로 들어올 때 한 번만이라도 팝업
                        update_tray_notify()
                        
                        # 3️⃣ 서버 전송 (기존 로직 유지)
                        send_to_server(payload)
                        
                        # 마지막 샷 시간 업데이트 (기존 변수)
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
                        log("💡 상태: WAITING (다음 샷 대기 중)")
                        state = "WAITING"
                        stable_count = 0
                        text_disappear_time = None
                        prev_run_detected = has_text
                        prev_bs = None
                        prev_cs = None
                        time.sleep(POLL_INTERVAL)
                        continue
                
                # PC 마지막 접속 시간 주기적 업데이트
                if PC_REGISTRATION_ENABLED and (time.time() - last_pc_update_time) >= PC_UPDATE_INTERVAL:
                    update_pc_last_seen()
                    last_pc_update_time = time.time()
                
                # 텍스트 재감지 대기 중
                time.sleep(POLL_INTERVAL)
            except Exception as e:
                # OCR 오류 등은 루프 내부에서 처리 (run()은 계속 살아있음)
                log(f"[RUN] loop error: {e}")
                time.sleep(0.5)
                continue
    except Exception as e:
        log(f"[RUN] fatal error: {e}")
    finally:
        log("[RUN] run() terminated")

# =========================
# GUI 관련 전역 변수
# =========================
gui_app = None
shot_stats_lock = threading.Lock()  # 통계 업데이트용 락
tray_thread = None
main_thread = None
should_exit = False

def load_icon():
    """icon.ico 파일 로드 (실패 시 기본 이미지 반환)"""
    early_log("loading icon.ico")
    try:
        icon_path = get_resource_path("icon.ico")
        img = Image.open(icon_path)
        early_log(f"icon.ico loaded from {icon_path}")
        return img
    except Exception as e:
        early_log(f"failed to load icon.ico: {e}, returning default image")
        return Image.new("RGB", (64, 64), color="black")

def show_gui():
    """GUI 표시"""
    if root:
        root.deiconify()
        root.lift()
        root.focus_force()

def hide_gui():
    """GUI 숨기기"""
    if root:
        root.withdraw()

def tray_open_gui(icon=None, item=None):
    """트레이 → GUI 열기"""
    if root:
        root.after(0, show_gui)

def tray_hide_gui(icon=None, item=None):
    """트레이 → GUI 숨기기"""
    if root:
        root.after(0, hide_gui)

def update_gui_stats():
    """GUI 통계 업데이트 (run 스레드 → GUI)"""
    global gui_app, root, shot_count
    if gui_app and root:
        def _update():
            try:
                with shot_stats_lock:
                    count = shot_count
                if gui_app and hasattr(gui_app, 'shot_count_label'):
                    gui_app.shot_count_label.config(text=str(count))
            except Exception as e:
                early_log(f"GUI 통계 업데이트 실패: {e}")
        root.after(0, _update)

def update_tray_stats():
    """트레이 툴팁 업데이트"""
    global tray_icon, shot_count
    if tray_icon:
        try:
            with shot_stats_lock:
                count = shot_count
            tray_icon.title = f"골프 샷 트래커 | 샷 {count}개"
        except Exception as e:
            early_log(f"트레이 툴팁 업데이트 실패: {e}")

def update_tray_notify():
    """트레이 알림 (샷 감지 시 팝업)"""
    global tray_icon, shot_count, global_last_shot_time, tray_notify_enabled
    if tray_icon and tray_notify_enabled:
        try:
            with shot_stats_lock:
                count = shot_count
                last_time = global_last_shot_time
            tray_icon.notify(
                "샷 감지됨",
                f"총 {count}샷 / {last_time}"
            )
        except Exception as e:
            early_log(f"트레이 알림 실패: {e}")

def create_tray_icon():
    """시스템 트레이 아이콘 생성"""
    # icon.ico 파일 로드 시도, 실패 시 기본 이미지 생성
    image = load_icon()
    if image.size == (64, 64) and image.mode == "RGB":
        # 기본 이미지인 경우 골프공 모양 그리기
        draw = ImageDraw.Draw(image)
        # 골프공 모양 그리기
        draw.ellipse([10, 10, 54, 54], fill='white', outline='black', width=2)
        draw.ellipse([20, 20, 44, 44], fill='lightgray')
    
    # 샷 통계를 포함한 툴팁 생성
    with shot_stats_lock:
        count = shot_count
        last_time = global_last_shot_time
    
    if last_time:
        from datetime import datetime
        time_str = datetime.fromtimestamp(last_time).strftime("%H:%M:%S")
        tooltip = f"골프 샷 트래커\n샷 수: {count}\n마지막 샷: {time_str}"
    else:
        tooltip = f"골프 샷 트래커\n샷 수: {count}\n마지막 샷: 없음"
    
    # GUI 메뉴 항목 (GUI 사용 가능한 경우에만)
    menu_items = []
    if GUI_AVAILABLE:
        menu_items.append(pystray.MenuItem("GUI 열기", tray_open_gui, default=True))
        menu_items.append(pystray.MenuItem("GUI 숨기기", tray_hide_gui))
    menu_items.append(pystray.MenuItem("상태 보기", show_status))
    menu_items.append(pystray.MenuItem("종료", quit_app))
    
    menu = pystray.Menu(*menu_items)
    
    icon = pystray.Icon("GolfShotTracker", image, tooltip, menu)
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


# run_with_tray() 함수 제거됨 - start_run_thread()로 대체
    
    # 트레이 아이콘 생성 및 실행 (메인 스레드에서 - pystray 요구사항)
    early_log("creating tray icon")
    tray_icon = create_tray_icon()
    early_log("tray icon created")
    
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
    
    # 트레이 아이콘을 별도 스레드에서 실행 (pystray는 별도 스레드에서 실행 가능)
    early_log("starting tray icon in thread")
    tray_thread = threading.Thread(target=tray_icon.run, daemon=False)
    tray_thread.start()
    early_log("tray icon thread started")
    
    # 메인 스레드를 유지하기 위한 blocking loop
    early_log("entering main thread blocking loop")
    try:
        while True:
            # 메인 스레드가 종료되지 않도록 무한 루프
            # run() 스레드와 tray 스레드가 살아있는지 확인
            if main_thread and not main_thread.is_alive():
                early_log("main_thread is not alive, restarting...")
                # run_started 플래그 리셋 후 재시작
                global run_started
                run_started = False
                start_run_thread()
                early_log("main_thread restarted")
            
            if not tray_thread.is_alive():
                early_log("tray_thread is not alive, restarting...")
                tray_icon = create_tray_icon()
                tray_thread = threading.Thread(target=tray_icon.run, daemon=False)
                tray_thread.start()
                early_log("tray_thread restarted")
            
            time.sleep(1)  # 1초마다 체크
    except KeyboardInterrupt:
        early_log("keyboard interrupt received")
        should_exit = True
        if tray_icon:
            tray_icon.stop()
    except Exception as e:
        early_log(f"main thread loop exception: {e}")
        import traceback
        early_log(f"main thread loop traceback: {traceback.format_exc()}")
        raise

def init_gui():
    """GUI 초기화 (조건 없이 호출)"""
    global root, gui_app, status_label
    if GUI_AVAILABLE:
        early_log("creating GUI in main thread")
        root = tk.Tk()
        root.title("샷 수집 프로그램 설정")
        root.geometry("800x600")
        gui_app = ShotCollectorGUI(root)
        status_label = gui_app.status_label  # 전역 참조 설정
        root.withdraw()  # 시작 시 숨김
        early_log("GUI created and withdrawn")
    else:
        early_log("GUI not available (tkinter not installed)")

def init_tray():
    """트레이 초기화 (tray_icon = icon 반드시 연결)"""
    global tray_icon, tray_thread
    if not TRAY_AVAILABLE:
        early_log("Tray not available")
        return
    
    early_log("creating tray icon")
    
    # icon.ico 파일 로드 시도, 실패 시 기본 이미지 생성
    image = load_icon()
    if image.size == (64, 64) and image.mode == "RGB":
        # 기본 이미지인 경우 골프공 모양 그리기
        draw = ImageDraw.Draw(image)
        # 골프공 모양 그리기
        draw.ellipse([10, 10, 54, 54], fill='white', outline='black', width=2)
        draw.ellipse([20, 20, 44, 44], fill='lightgray')
    
    # 샷 통계를 포함한 툴팁 생성
    with shot_stats_lock:
        count = shot_count
        last_time = global_last_shot_time
    
    if last_time:
        tooltip = f"골프 샷 트래커\n샷 수: {count}\n마지막 샷: {last_time}"
    else:
        tooltip = f"골프 샷 트래커\n샷 수: {count}\n마지막 샷: 없음"
    
    # GUI 메뉴 항목 (GUI 사용 가능한 경우에만)
    menu_items = []
    if GUI_AVAILABLE:
        menu_items.append(pystray.MenuItem("GUI 열기", tray_open_gui, default=True))
        menu_items.append(pystray.MenuItem("GUI 숨기기", tray_hide_gui))
    menu_items.append(pystray.MenuItem("상태 보기", show_status))
    menu_items.append(pystray.MenuItem("종료", quit_app))
    
    menu = pystray.Menu(*menu_items)
    
    # tray_icon = icon 반드시 연결
    tray_icon = pystray.Icon("GolfShotTracker", image, tooltip, menu)
    early_log("tray icon created")
    
    # 트레이 아이콘을 별도 스레드에서 실행
    tray_thread = threading.Thread(target=tray_icon.run, daemon=False)
    tray_thread.start()
    early_log("tray icon thread started")

def start_run_thread():
    """run() 함수를 스레드로 시작 (단일 실행 구조)"""
    global main_thread
    
    if main_thread and main_thread.is_alive():
        log("[RUN] start_run_thread called but already running")
        return
    
    log("[RUN] starting run thread")
    main_thread = threading.Thread(target=run, daemon=True)
    main_thread.start()

def main():
    log("[MAIN] start")
    
    global run_entered
    run_entered = False   # ← 반드시 초기화
    
    # 자동 시작 모드 확인
    # 1. 명령줄 인자 --autostart
    # 2. 환경 변수 AUTO_START=true
    # 3. config.json에 auto_brand와 auto_filename이 있으면 자동 시작 (더블클릭 시에도)
    auto_start = "--autostart" in sys.argv or os.environ.get("AUTO_START", "").lower() == "true"
    
    # config.json 확인 (더블클릭 시에도 자동 시작 가능하도록)
    if not auto_start:
        config = load_config()
        if config.get("auto_brand") and config.get("auto_filename"):
            auto_start = True
            log("[AUTO_START] config.json에서 자동 시작 설정 발견")
    
    init_gui()
    init_tray()
    
    # 자동 시작 모드: 지정된 좌표값으로 자동 시작
    if auto_start:
        log("[AUTO_START] 자동 시작 모드 활성화")
        auto_start_collection()
    else:
        # 수동 모드: 시작 버튼을 누르지 않았으면 run() 실행하지 않음
        # start_run_thread()는 GUI의 "시작" 버튼에서만 호출됨
        log("[MANUAL] 수동 모드 - 시작 버튼 대기")
    
    log("[MAIN] entering tkinter mainloop")
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(e)
        raise