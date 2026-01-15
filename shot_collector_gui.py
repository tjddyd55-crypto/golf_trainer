#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
shot_collector GUI - 좌표 선택 및 시작/종료 제어 (Supervisor 구조)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import threading
import queue
import time
import traceback
import requests

# 트레이 관련 import
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# 브랜드 목록
BRANDS = [
    ("GOLFZON", "골프존"),
    ("SGGOLF", "SG골프"),
    ("KAKAO", "카카오골프"),
    ("BRAVO", "브라보"),
    ("ETC", "기타"),
]

# 설정 파일 경로
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# 로그 파일 경로
RUNTIME_LOG = "runtime.log"
ERROR_LOG = "error.log"

# 로그 파일 리다이렉트
def setup_log_redirect():
    """stdout/stderr를 파일로 리다이렉트"""
    runtime_log_file = open(RUNTIME_LOG, 'a', encoding='utf-8')
    error_log_file = open(ERROR_LOG, 'a', encoding='utf-8')
    
    class LogWriter:
        def __init__(self, file_obj, is_error=False):
            self.file = file_obj
            self.is_error = is_error
        
        def write(self, text):
            if text:
                self.file.write(text)
                self.file.flush()
                if self.is_error and ERROR_LOG:
                    error_log_file.write(text)
                    error_log_file.flush()
        
        def flush(self):
            self.file.flush()
            if self.is_error:
                error_log_file.flush()
        
        def isatty(self):
            return False
    
    sys.stdout = LogWriter(runtime_log_file, False)
    sys.stderr = LogWriter(error_log_file, True)

def load_config():
    """config.json 파일 로드"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def get_api_base_url():
    """API 베이스 URL 가져오기"""
    config = load_config()
    api_url = os.environ.get("API_BASE_URL") or config.get("API_BASE_URL")
    if api_url:
        return api_url.rstrip('/')
    return "https://golf-api-production-e675.up.railway.app"

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
# 시작프로그램 등록
# =========================
def register_startup():
    """시작프로그램 등록 (1회만 실행, 바로가기 방식)"""
    startup_flag_file = os.path.join(os.path.dirname(__file__), ".startup_registered")
    if os.path.exists(startup_flag_file):
        return
    
    try:
        startup_folder = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        if not os.path.exists(startup_folder):
            return
        
        script_path = __file__ if not getattr(sys, 'frozen', False) else sys.executable
        shortcut_path = os.path.join(startup_folder, "GolfShotCollector.lnk")
        
        if not os.path.exists(shortcut_path):
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = script_path
                shortcut.WorkingDirectory = os.path.dirname(script_path)
                shortcut.save()
            except ImportError:
                pass  # win32com 없으면 스킵
        
        # 등록 플래그 파일 생성
        with open(startup_flag_file, 'w') as f:
            f.write("registered")
    except Exception:
        pass  # 실패해도 계속 진행

# =========================
# Supervisor 구조
# =========================
class Supervisor:
    def __init__(self, gui_app):
        self.gui_app = gui_app
        self.should_exit = False
        self.collection_thread = None
    
    def run_collection_loop(self, regions):
        """샷 수집 루프 (기능 루프만 담당)"""
        try:
            import main
            main.run(regions=regions)
        except Exception as e:
            # 치명적 예외는 raise하여 supervisor가 처리
            raise
    
    def supervisor_loop(self, regions):
        """Supervisor 루프 (while True 구조)"""
        while True:
            try:
                self.run_collection_loop(regions)
            except Exception as e:
                # 예외 발생 시 2초 sleep 후 재시작
                error_msg = traceback.format_exc()
                try:
                    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
                        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Supervisor 오류:\n{error_msg}\n")
                except Exception:
                    pass
                time.sleep(2.0)
                continue

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
        
        # Supervisor 및 스레드
        self.supervisor = None
        self.supervisor_thread = None
        self.is_running = False
        self.tray_icon = None
        self.downloaded_regions = None
        
        # GUI 구성
        self.setup_ui()
        
        # 로그 브리지 설정 (GUI 표시용, 파일 로그는 setup_log_redirect에서 처리)
        self.log_bridge = UILogBridge(self.log_text)
        self.root.after(100, self._process_logs)
        
        # 창 닫기 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 시작프로그램 등록 (1회만)
        register_startup()
        
        # 프로그램 시작 시 트레이 상주
        if TRAY_AVAILABLE:
            self.create_tray_icon_startup()
            # 시작 시 GUI 숨김 (트레이로만 표시)
            self.root.withdraw()
    
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
            messagebox.showwarning("경고", "브랜드와 좌표 파일을 선택하세요")
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
                self.root.after(0, lambda: messagebox.showerror("오류", f"좌표 파일 다운로드 실패: {error}"))
                self.root.after(0, lambda: self.status_label.config(text="다운로드 실패", fg="red"))
                return
            
            data = response.json()
            if not data.get("success"):
                error = data.get("error", "다운로드 실패")
                self.root.after(0, lambda: messagebox.showerror("오류", f"좌표 파일 다운로드 실패: {error}"))
                self.root.after(0, lambda: self.status_label.config(text="다운로드 실패", fg="red"))
                return
            
            coordinate_data = data.get("data")
            regions = coordinate_data.get("regions", {})
            
            # 좌표를 메모리에 저장
            self.downloaded_regions = regions
            
            # Supervisor 시작
            self.is_running = True
            self.supervisor = Supervisor(self)
            self.supervisor_thread = threading.Thread(
                target=self.supervisor.supervisor_loop,
                args=(regions,),
                daemon=True
            )
            self.supervisor_thread.start()
            
            # UI 업데이트
            self.root.after(0, self.on_collection_started)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"시작 실패: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="시작 실패", fg="red"))
    
    def on_collection_started(self):
        """수집 시작 후 UI 업데이트"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.brand_combo.config(state=tk.DISABLED)
        self.file_listbox.config(state=tk.DISABLED)
        
        # 상단 상태 표시 변경
        self.status_var.set("🟢 작동중")
        self.running_status_label.config(fg="green")
        
        self.status_label.config(text="● 실행 중", fg="green")
        
        # 트레이로 이동 (GUI 숨김)
        self.root.after(2000, self.hide_to_tray)
    
    def hide_to_tray(self):
        """트레이로 이동 (GUI 숨김)"""
        if TRAY_AVAILABLE:
            self.root.withdraw()
    
    def create_tray_icon_startup(self):
        """프로그램 시작 시 트레이 아이콘 생성"""
        if not TRAY_AVAILABLE:
            return
        
        image = Image.new('RGB', (64, 64), color='green')
        draw = ImageDraw.Draw(image)
        draw.ellipse([10, 10, 54, 54], fill='white', outline='black', width=2)
        draw.ellipse([20, 20, 44, 44], fill='lightgray')
        
        menu = pystray.Menu(
            pystray.MenuItem("열기", self.show_window, default=True),
            pystray.MenuItem("종료", self.quit_from_tray)
        )
        
        self.tray_icon = pystray.Icon("ShotCollector", image, "샷 수집 프로그램", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def create_tray_icon(self):
        """트레이 아이콘 생성 (기존 트레이 아이콘이 없을 때)"""
        if not TRAY_AVAILABLE or self.tray_icon:
            return
        
        image = Image.new('RGB', (64, 64), color='green')
        draw = ImageDraw.Draw(image)
        draw.ellipse([10, 10, 54, 54], fill='white', outline='black', width=2)
        draw.ellipse([20, 20, 44, 44], fill='lightgray')
        
        menu = pystray.Menu(
            pystray.MenuItem("열기", self.show_window, default=True),
            pystray.MenuItem("종료", self.quit_from_tray)
        )
        
        self.tray_icon = pystray.Icon("ShotCollector", image, "샷 수집 프로그램", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_window(self, icon=None, item=None):
        """트레이에서 창 보기"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def quit_from_tray(self, icon=None, item=None):
        """트레이에서 종료 (sys.exit 허용)"""
        self.stop_collection()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        sys.exit(0)
    
    def on_stop_clicked(self):
        """종료 버튼 클릭"""
        if messagebox.askyesno("확인", "샷 수집을 종료하시겠습니까?"):
            self.stop_collection()
    
    def stop_collection(self):
        """샷 수집 종료"""
        self.is_running = False
        
        # Supervisor 종료
        if self.supervisor:
            self.supervisor.should_exit = True
            try:
                import main
                if hasattr(main, 'should_exit'):
                    main.should_exit = True
            except Exception:
                pass
        
        # GUI 복원
        self.root.deiconify()
        
        self.on_collection_stopped()
    
    def on_collection_stopped(self):
        """수집 종료 후 UI 업데이트"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.brand_combo.config(state="readonly")
        self.file_listbox.config(state=tk.NORMAL)
        
        # 상단 상태 표시 변경
        self.status_var.set("🔴 대기중")
        self.running_status_label.config(fg="red")
        
        self.status_label.config(text="종료됨", fg="gray")
    
    def on_closing(self):
        """창 닫기 (X 버튼 클릭 시 항상 트레이로 숨김)"""
        # X 버튼 클릭 시 항상 트레이로 숨김 (종료하지 않음)
        self.hide_to_tray()

def main():
    # 로그 파일 리다이렉트 설정
    setup_log_redirect()
    
    root = tk.Tk()
    app = ShotCollectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
