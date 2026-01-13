#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
shot_collector GUI - 좌표 선택 및 시작/종료 제어
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import threading
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

class ShotCollectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("샷 수집 프로그램 설정")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # API URL
        self.api_base_url = get_api_base_url()
        
        # 선택된 값
        self.selected_brand = None
        self.selected_filename = None
        self.coordinate_files = []
        
        # OCR 루프 스레드
        self.collection_thread = None
        self.is_running = False
        self.tray_icon = None
        self.downloaded_regions = None  # 다운로드한 좌표 데이터 (세션 동안 고정)
        
        # GUI 구성
        self.setup_ui()
        
        # 창 닫기 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self.root,
            text="샷 수집 프로그램",
            font=("맑은 고딕", 16, "bold"),
            pady=20
        )
        title_label.pack()
        
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
        file_frame = tk.Frame(self.root, pady=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(
            file_frame,
            text="좌표 파일 선택:",
            font=("맑은 고딕", 10)
        ).pack(anchor=tk.W)
        
        # 리스트박스와 스크롤바
        listbox_frame = tk.Frame(file_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            font=("맑은 고딕", 9),
            height=8
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)
        
        # 버튼 프레임
        button_frame = tk.Frame(self.root, pady=20)
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
        
        # 상태 표시
        self.status_label = tk.Label(
            self.root,
            text="브랜드를 선택하세요",
            font=("맑은 고딕", 9),
            fg="gray",
            pady=10
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
        
        # 디버그: 선택된 브랜드 정보 출력
        print(f"[DEBUG] 선택된 브랜드: {brand_name} -> 코드: {brand_code}")
        
        self.selected_brand = brand_code
        self.status_label.config(text="좌표 파일 목록 가져오는 중...", fg="blue")
        self.file_listbox.delete(0, tk.END)
        
        # 서버에서 좌표 파일 목록 가져오기
        threading.Thread(target=self.load_coordinate_files, args=(brand_code,), daemon=True).start()
    
    def load_coordinate_files(self, brand_code):
        """서버에서 좌표 파일 목록 가져오기"""
        try:
            url = f"{self.api_base_url}/api/coordinates/{brand_code}"
            print(f"[DEBUG] API 호출: {url}")
            response = requests.get(url, timeout=10)
            print(f"[DEBUG] 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[DEBUG] 응답 데이터 타입: {type(data)}")
                print(f"[DEBUG] 응답 데이터: {data}")
                
                if data.get("success"):
                    files = data.get("files", [])
                    print(f"[DEBUG] 파일 개수: {len(files)}, 타입: {type(files)}")
                    if files:
                        print(f"[DEBUG] 파일 목록: {[f.get('filename') for f in files]}")
                    
                    self.coordinate_files = files
                    
                    # UI 업데이트 (메인 스레드)
                    self.root.after(0, self.update_file_listbox, files)
                    return
                else:
                    error_msg = data.get("error", "알 수 없는 오류")
                    print(f"[DEBUG] API 오류: {error_msg}")
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"오류: {error_msg}",
                        fg="red"
                    ))
                    return
            else:
                # HTTP 오류
                error_text = response.text[:100] if response.text else "알 수 없는 오류"
                print(f"[DEBUG] HTTP 오류: {response.status_code}, {error_text}")
                self.root.after(0, lambda: self.status_label.config(
                    text=f"서버 오류 ({response.status_code}): {error_text}",
                    fg="red"
                ))
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"[DEBUG] 요청 오류: {error_msg}")
            self.root.after(0, lambda: self.status_label.config(
                text=f"연결 오류: {error_msg}",
                fg="red"
            ))
        except Exception as e:
            import traceback
            print(f"[DEBUG] 예외 발생:")
            traceback.print_exc()
            self.root.after(0, lambda: self.status_label.config(
                text=f"오류: {str(e)}",
                fg="red"
            ))
    
    def update_file_listbox(self, files):
        """파일 목록 업데이트"""
        self.file_listbox.delete(0, tk.END)
        for file_info in files:
            filename = file_info.get("filename", "")
            resolution = file_info.get("resolution", "")
            version = file_info.get("version", 0)
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
            
            # 좌표를 메모리에 저장 (세션 동안 고정)
            self.downloaded_regions = regions
            
            # OCR 루프 시작 (별도 스레드)
            self.is_running = True
            self.collection_thread = threading.Thread(target=self.run_collection_loop, daemon=True)
            self.collection_thread.start()
            
            # UI 업데이트
            self.root.after(0, self.on_collection_started)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"시작 실패: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="시작 실패", fg="red"))
    
    def run_collection_loop(self):
        """샷 수집 루프 실행 (main.py의 run 함수를 직접 호출)"""
        try:
            # main.py를 import하여 run 함수 실행
            import main
            
            # 좌표 데이터 전달하여 실행
            main.run(regions=self.downloaded_regions)
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.root.after(0, lambda: messagebox.showerror("오류", f"샷 수집 루프 오류: {str(e)}\n\n{error_msg}"))
            self.is_running = False
            self.root.after(0, self.on_collection_stopped)
    
    def on_collection_started(self):
        """수집 시작 후 UI 업데이트"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.brand_combo.config(state=tk.DISABLED)
        self.file_listbox.config(state=tk.DISABLED)
        self.status_label.config(text="● 실행 중 - 트레이로 이동합니다", fg="green")
        
        # 트레이로 이동 (GUI 숨김)
        self.root.after(2000, self.hide_to_tray)
    
    def hide_to_tray(self):
        """트레이로 이동 (GUI 숨김)"""
        if TRAY_AVAILABLE:
            # GUI 창 숨기기
            self.root.withdraw()
            
            # 트레이 아이콘 생성 및 실행
            self.create_tray_icon()
        else:
            # 트레이를 사용할 수 없으면 최소화
            self.root.iconify()
    
    def create_tray_icon(self):
        """시스템 트레이 아이콘 생성"""
        if not TRAY_AVAILABLE:
            return
        
        # 간단한 아이콘 이미지 생성 (골프공 모양)
        image = Image.new('RGB', (64, 64), color='green')
        draw = ImageDraw.Draw(image)
        # 골프공 모양 그리기
        draw.ellipse([10, 10, 54, 54], fill='white', outline='black', width=2)
        draw.ellipse([20, 20, 44, 44], fill='lightgray')
        
        menu = pystray.Menu(
            pystray.MenuItem("창 보기", self.show_window, default=True),
            pystray.MenuItem("종료", self.quit_from_tray)
        )
        
        self.tray_icon = pystray.Icon("ShotCollector", image, "샷 수집 프로그램", menu)
        
        # 트레이 아이콘을 별도 스레드에서 실행
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_window(self, icon=None, item=None):
        """트레이에서 창 보기"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        # 트레이 아이콘 제거
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
    
    def quit_from_tray(self, icon=None, item=None):
        """트레이에서 종료"""
        self.stop_collection()
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
    
    def on_stop_clicked(self):
        """종료 버튼 클릭"""
        if messagebox.askyesno("확인", "샷 수집을 종료하시겠습니까?"):
            self.stop_collection()
    
    def stop_collection(self):
        """샷 수집 종료"""
        self.is_running = False
        
        # main.py의 should_exit 플래그 설정 (main.py에 있으면)
        try:
            import main
            if hasattr(main, 'should_exit'):
                main.should_exit = True
        except Exception:
            pass
        
        # 트레이 아이콘 제거
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        # GUI 복원
        self.root.deiconify()  # 창 다시 표시
        
        self.on_collection_stopped()
    
    def on_collection_stopped(self):
        """수집 종료 후 UI 업데이트"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.brand_combo.config(state="readonly")
        self.file_listbox.config(state=tk.NORMAL)
        self.status_label.config(text="종료됨", fg="gray")
    
    def on_closing(self):
        """창 닫기"""
        if self.is_running:
            if messagebox.askyesno("확인", "샷 수집이 실행 중입니다. 종료하시겠습니까?"):
                self.stop_collection()
                self.root.destroy()
        else:
            # 트레이 아이콘 제거
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = ShotCollectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
