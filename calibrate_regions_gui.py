#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
좌표 설정 프로그램 (GUI 버전)
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cv2
import pyautogui
import numpy as np
import json
import os
import sys
import threading

# 모든 항목 목록
ALL_ITEMS = [
    ("total_distance", "총거리"),
    ("carry", "캐리"),
    ("ball_speed", "볼스피드"),
    ("club_speed", "클럽스피드"),
    ("launch_angle", "발사각"),
    ("back_spin", "백스핀"),
    ("club_path", "클럽패스"),
    ("lateral_offset", "좌우이격"),
    ("direction_angle", "방향각"),
    ("side_spin", "사이드스핀"),
    ("face_angle", "페이스각"),
    ("run_text", "런 텍스트"),
]

def get_regions_file(store_id=None):
    """매장별 좌표 파일 경로 반환"""
    if store_id:
        return f"regions/{store_id}.json"
    return "regions/test.json"

def capture_screen():
    """전체 화면 캡처"""
    img = pyautogui.screenshot()
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def resize_for_display(img, max_width=1920, max_height=1080):
    """화면이 너무 크면 리사이즈 (표시용)"""
    h, w = img.shape[:2]
    
    if w <= max_width and h <= max_height:
        return img, 1.0
    
    scale_w = max_width / w
    scale_h = max_height / h
    scale = min(scale_w, scale_h)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale

def select_region_interactive(screen, item_name):
    """대화형 영역 선택"""
    screen_h, screen_w = screen.shape[:2]
    
    display_img, display_scale = resize_for_display(screen, max_width=1920, max_height=1080)
    
    window_name = f"좌표 설정 - {item_name} (ESC: 취소, Space: 건너뛰기)"
    roi = cv2.selectROI(
        window_name,
        display_img,
        showCrosshair=True,
        fromCenter=False
    )
    cv2.destroyAllWindows()
    
    x, y, w, h = roi
    
    if w == 0 or h == 0:
        return None
    
    # 리사이즈된 좌표를 원본 화면 좌표로 변환
    x_orig = int(x / display_scale)
    y_orig = int(y / display_scale)
    w_orig = int(w / display_scale)
    h_orig = int(h / display_scale)
    
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

class RegionCalibratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("좌표 설정 프로그램")
        self.root.geometry("700x800")
        self.root.resizable(True, True)
        
        self.store_id = None
        self.regions = {}
        self.screen = None
        self.screen_scale = 1.0
        self.selected_items = []
        
        # UI 생성
        self.create_ui()
        
        # 기존 좌표 파일 로드
        self.load_regions()
    
    def create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(
            main_frame, 
            text="좌표 설정 프로그램",
            font=("맑은 고딕", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 매장 ID 입력 영역
        store_frame = ttk.LabelFrame(main_frame, text="매장 설정", padding="10")
        store_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(store_frame, text="매장 ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.store_id_entry = ttk.Entry(store_frame, width=30, font=("맑은 고딕", 10))
        self.store_id_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.store_id_entry.insert(0, "test")
        
        ttk.Button(
            store_frame,
            text="좌표 파일 로드",
            command=self.load_regions
        ).grid(row=0, column=2, padx=(10, 0))
        
        # 화면 캡처 영역
        capture_frame = ttk.LabelFrame(main_frame, text="화면 캡처", padding="10")
        capture_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.capture_button = ttk.Button(
            capture_frame,
            text="화면 캡처",
            command=self.capture_screen_thread,
            width=20
        )
        self.capture_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.screen_info_label = ttk.Label(
            capture_frame,
            text="화면을 캡처하세요",
            font=("맑은 고딕", 9),
            foreground="gray"
        )
        self.screen_info_label.pack(side=tk.LEFT)
        
        # 항목 선택 영역
        items_frame = ttk.LabelFrame(main_frame, text="설정할 항목 선택", padding="10")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 체크박스 프레임 (스크롤 가능)
        canvas = tk.Canvas(items_frame, height=200)
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.item_vars = {}
        for item_key, item_name in ALL_ITEMS:
            var = tk.BooleanVar(value=True)
            self.item_vars[item_key] = var
            
            checkbox = ttk.Checkbutton(
                scrollable_frame,
                text=f"{item_name} ({item_key})",
                variable=var
            )
            checkbox.pack(anchor=tk.W, pady=2)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 좌표 설정 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.start_button = ttk.Button(
            button_frame,
            text="좌표 설정 시작",
            command=self.start_calibration,
            width=20,
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(
            button_frame,
            text="저장",
            command=self.save_regions,
            width=20,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT)
        
        # 상태 메시지 영역
        status_frame = ttk.LabelFrame(main_frame, text="상태", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=8,
            state=tk.DISABLED,
            font=("맑은 고딕", 9),
            wrap=tk.WORD
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # 상태 텍스트 태그 설정
        self.status_text.tag_config("error", foreground="red")
        self.status_text.tag_config("normal", foreground="green")
        self.status_text.tag_config("info", foreground="blue")
    
    def update_status(self, message, tag="normal"):
        """상태 메시지 업데이트"""
        self.status_text.config(state=tk.NORMAL)
        if tag == "error":
            self.status_text.insert(tk.END, f"[ERROR] {message}\n", tag)
        elif tag == "info":
            self.status_text.insert(tk.END, f"[INFO] {message}\n", tag)
        else:
            self.status_text.insert(tk.END, f"[OK] {message}\n", tag)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
    
    def load_regions(self):
        """기존 좌표 파일 로드"""
        store_id = self.store_id_entry.get().strip()
        if not store_id:
            store_id = "test"
        
        self.store_id = store_id
        regions_file = get_regions_file(store_id)
        
        self.regions = {}
        if os.path.exists(regions_file):
            try:
                with open(regions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.regions = data.get("regions", {})
                self.update_status(f"기존 좌표 파일 로드 완료: {regions_file}", "info")
                self.update_status(f"기존 항목: {list(self.regions.keys())}", "info")
            except Exception as e:
                self.update_status(f"기존 파일 읽기 실패: {e}", "error")
        else:
            self.update_status(f"좌표 파일이 없습니다. 새로 생성합니다: {regions_file}", "info")
    
    def capture_screen_thread(self):
        """화면 캡처 (별도 스레드)"""
        def capture():
            self.capture_button.config(state=tk.DISABLED)
            self.update_status("화면 캡처 중...", "info")
            
            try:
                # 2초 대기 (사용자가 골프 화면으로 전환할 시간)
                self.root.after(2000, self.do_capture)
            except Exception as e:
                self.update_status(f"화면 캡처 실패: {e}", "error")
                self.capture_button.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "화면 캡처",
            "2초 후 화면을 캡처합니다.\n골프 화면이 보이도록 준비하세요."
        )
        
        threading.Thread(target=capture, daemon=True).start()
    
    def do_capture(self):
        """실제 화면 캡처"""
        try:
            self.screen = capture_screen()
            screen_h, screen_w = self.screen.shape[:2]
            
            self.screen_info_label.config(
                text=f"화면 크기: {screen_w} x {screen_h}",
                foreground="green"
            )
            
            self.update_status(f"화면 캡처 완료: {screen_w} x {screen_h}")
            self.start_button.config(state=tk.NORMAL)
            self.capture_button.config(state=tk.NORMAL)
        except Exception as e:
            self.update_status(f"화면 캡처 실패: {e}", "error")
            self.capture_button.config(state=tk.NORMAL)
    
    def start_calibration(self):
        """좌표 설정 시작"""
        if self.screen is None:
            messagebox.showerror("오류", "먼저 화면을 캡처하세요.")
            return
        
        # 선택된 항목 확인
        selected = [item_key for item_key, var in self.item_vars.items() if var.get()]
        if not selected:
            messagebox.showerror("오류", "설정할 항목을 하나 이상 선택하세요.")
            return
        
        self.selected_items = selected
        
        # 좌표 설정 시작
        self.update_status("좌표 설정을 시작합니다...", "info")
        self.update_status("각 항목의 숫자 + 부호 + 단위를 모두 포함하도록 영역을 드래그하세요.", "info")
        
        # 별도 스레드에서 좌표 설정 (GUI 블로킹 방지)
        threading.Thread(target=self.calibrate_regions, daemon=True).start()
    
    def calibrate_regions(self):
        """좌표 설정 메인 로직"""
        for idx, item_key in enumerate(self.selected_items, 1):
            item_name = dict(ALL_ITEMS).get(item_key, item_key)
            
            self.update_status(f"[{idx}/{len(self.selected_items)}] {item_name} ({item_key}) 설정 중...", "info")
            
            # 이미 설정된 좌표가 있으면 확인
            if item_key in self.regions:
                self.update_status(f"기존 좌표: {self.regions[item_key]}", "info")
                # GUI에서 확인 (간단하게 덮어쓰기)
                response = messagebox.askyesno(
                    "기존 좌표 있음",
                    f"{item_name}의 기존 좌표가 있습니다.\n덮어쓰시겠습니까?",
                    icon=messagebox.QUESTION
                )
                if not response:
                    self.update_status(f"{item_name} 건너뛰기")
                    continue
            
            # 영역 선택
            region = select_region_interactive(self.screen, item_name)
            
            if region is None:
                self.update_status(f"{item_name} 건너뛰기")
                continue
            
            self.regions[item_key] = region
            self.update_status(f"{item_name} 저장: {region}")
        
        self.update_status("좌표 설정 완료!", "info")
        self.save_button.config(state=tk.NORMAL)
        messagebox.showinfo("완료", "좌표 설정이 완료되었습니다.\n저장 버튼을 클릭하여 파일에 저장하세요.")
    
    def save_regions(self):
        """좌표 파일 저장"""
        if not self.store_id:
            self.store_id = self.store_id_entry.get().strip() or "test"
        
        regions_file = get_regions_file(self.store_id)
        
        try:
            os.makedirs("regions", exist_ok=True)
            with open(regions_file, "w", encoding="utf-8") as f:
                json.dump({"regions": self.regions}, f, indent=2, ensure_ascii=False)
            
            self.update_status(f"좌표 파일 저장 완료: {regions_file}")
            self.update_status(f"설정된 항목: {list(self.regions.keys())}")
            
            messagebox.showinfo(
                "저장 완료",
                f"좌표 파일이 저장되었습니다.\n\n파일 위치: {regions_file}\n설정된 항목: {len(self.regions)}개"
            )
        except Exception as e:
            self.update_status(f"저장 실패: {e}", "error")
            messagebox.showerror("저장 실패", f"좌표 파일 저장에 실패했습니다.\n{e}")

def main():
    root = tk.Tk()
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    app = RegionCalibratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
