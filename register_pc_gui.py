#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PC 등록 프로그램 (GUI 버전)
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import json
import requests
import sys

# pc_identifier 모듈 import
try:
    from pc_identifier import get_pc_info
except ImportError:
    messagebox.showerror("오류", "pc_identifier.py 파일을 찾을 수 없습니다.")
    sys.exit(1)

# 설정
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "pc_token.json")
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://golf-api-production-e675.up.railway.app")

class PCRegistrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("매장 PC 등록 프로그램")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # PC 정보 저장
        self.pc_info = None
        self.server_url = DEFAULT_SERVER_URL
        
        # UI 생성
        self.create_ui()
        
        # PC 정보 수집
        self.collect_pc_info()
        
        # 저장된 토큰 확인
        self.check_existing_token()
    
    def create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(
            main_frame, 
            text="매장 PC 등록 프로그램",
            font=("맑은 고딕", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # PC 정보 영역 (읽기 전용)
        info_frame = ttk.LabelFrame(main_frame, text="PC 정보 (자동 수집)", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.pc_info_text = scrolledtext.ScrolledText(
            info_frame,
            height=6,
            state=tk.DISABLED,
            font=("Consolas", 9)
        )
        self.pc_info_text.pack(fill=tk.X)
        
        # 입력 영역
        input_frame = ttk.LabelFrame(main_frame, text="등록 정보 입력", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # PC 등록 코드
        ttk.Label(input_frame, text="PC 등록 코드:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.code_entry = ttk.Entry(input_frame, width=30, font=("맑은 고딕", 10))
        self.code_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 매장명
        ttk.Label(input_frame, text="매장명:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.store_entry = ttk.Entry(input_frame, width=30, font=("맑은 고딕", 10))
        self.store_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 타석/룸명
        ttk.Label(input_frame, text="타석 / 룸명:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.bay_entry = ttk.Entry(input_frame, width=30, font=("맑은 고딕", 10))
        self.bay_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 버튼 영역
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.register_button = ttk.Button(
            button_frame,
            text="등록 요청",
            command=self.register_pc,
            width=20
        )
        self.register_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="취소",
            command=self.root.quit,
            width=20
        )
        self.cancel_button.pack(side=tk.LEFT)
        
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
    
    def update_status(self, message, is_error=False):
        """상태 메시지 업데이트"""
        self.status_text.config(state=tk.NORMAL)
        if is_error:
            self.status_text.insert(tk.END, f"[ERROR] {message}\n", "error")
        else:
            self.status_text.insert(tk.END, f"[OK] {message}\n", "normal")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
    
    def collect_pc_info(self):
        """PC 정보 수집"""
        try:
            self.update_status("PC 정보 수집 중...")
            self.pc_info = get_pc_info()
            
            # PC 정보 표시 (읽기 전용)
            info_text = f"""PC 고유번호:  {self.pc_info.get('unique_id', 'N/A')}
MAC 주소:     {self.pc_info.get('mac_address', 'N/A')}
PC UUID:      {self.pc_info.get('system_uuid') or self.pc_info.get('machine_guid', 'N/A')}
호스트명:     {self.pc_info.get('hostname', 'N/A')}
운영체제:     {self.pc_info.get('platform', 'N/A')}"""
            
            self.pc_info_text.config(state=tk.NORMAL)
            self.pc_info_text.delete(1.0, tk.END)
            self.pc_info_text.insert(1.0, info_text)
            self.pc_info_text.config(state=tk.DISABLED)
            
            self.update_status("PC 정보 수집 완료")
        except Exception as e:
            self.update_status(f"PC 정보 수집 실패: {e}", is_error=True)
            messagebox.showerror("오류", f"PC 정보 수집에 실패했습니다.\n{e}")
    
    def check_existing_token(self):
        """저장된 토큰 확인"""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    token = data.get("pc_token")
                    if token:
                        # 이미 등록된 PC
                        self.update_status("이미 등록된 PC입니다.")
                        self.update_status(f"토큰: {token[:20]}...")
                        
                        # 입력 필드 비활성화
                        self.code_entry.config(state=tk.DISABLED)
                        self.store_entry.config(state=tk.DISABLED)
                        self.bay_entry.config(state=tk.DISABLED)
                        self.register_button.config(state=tk.DISABLED)
                        
                        # 재등록 옵션
                        response = messagebox.askyesno(
                            "이미 등록됨",
                            "이 PC는 이미 등록되어 있습니다.\n재등록하시겠습니까?",
                            icon=messagebox.QUESTION
                        )
                        
                        if response:
                            # 재등록 모드
                            self.code_entry.config(state=tk.NORMAL)
                            self.store_entry.config(state=tk.NORMAL)
                            self.bay_entry.config(state=tk.NORMAL)
                            self.register_button.config(state=tk.NORMAL)
                            self.update_status("재등록 모드입니다.")
                        else:
                            self.root.quit()
                        return
            except Exception:
                pass
    
    def load_pc_token(self):
        """PC 토큰 로드"""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("pc_token"), data.get("server_url")
            except Exception:
                pass
        return None, None
    
    def save_pc_token(self, pc_token, server_url):
        """PC 토큰 저장"""
        try:
            data = {
                "pc_token": pc_token,
                "server_url": server_url
            }
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.update_status(f"토큰 저장 실패: {e}", is_error=True)
            return False
    
    def register_pc(self):
        """PC 등록 요청"""
        # 입력값 확인
        registration_code = self.code_entry.get().strip().upper()
        store_name = self.store_entry.get().strip()
        bay_name = self.bay_entry.get().strip()
        
        if not registration_code:
            messagebox.showerror("오류", "PC 등록 코드를 입력하세요.")
            return
        
        if not store_name:
            messagebox.showerror("오류", "매장명을 입력하세요.")
            return
        
        if not bay_name:
            messagebox.showerror("오류", "타석/룸명을 입력하세요.")
            return
        
        if not self.pc_info:
            messagebox.showerror("오류", "PC 정보를 수집할 수 없습니다.")
            return
        
        # 필수 정보 확인
        mac_address = self.pc_info.get("mac_address")
        pc_uuid = self.pc_info.get("system_uuid") or self.pc_info.get("machine_guid")
        
        if not mac_address:
            messagebox.showerror("오류", "MAC Address를 수집할 수 없습니다.")
            return
        
        if not pc_uuid:
            messagebox.showerror("오류", "PC UUID를 수집할 수 없습니다.")
            return
        
        # PC 이름 자동 생성
        pc_name = f"{store_name}-{bay_name}-PC"
        
        # 등록 요청
        self.update_status("서버에 등록 요청 중...")
        self.register_button.config(state=tk.DISABLED)
        
        try:
            payload = {
                "registration_key": registration_code,
                "store_name": store_name,
                "bay_name": bay_name,
                "pc_name": pc_name,
                "pc_info": self.pc_info
            }
            
            response = requests.post(
                f"{self.server_url}/api/register_pc",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    pc_token = data.get("pc_token")
                    
                    if pc_token:
                        # 토큰 저장
                        if self.save_pc_token(pc_token, self.server_url):
                            self.update_status("PC 등록이 완료되었습니다.")
                            self.update_status(f"이 PC는 {bay_name}으로 등록되었습니다.")
                            self.update_status("토큰이 자동으로 저장되었습니다.")
                            
                            # 입력 필드 비활성화
                            self.code_entry.config(state=tk.DISABLED)
                            self.store_entry.config(state=tk.DISABLED)
                            self.bay_entry.config(state=tk.DISABLED)
                            self.register_button.config(state=tk.DISABLED)
                            
                            messagebox.showinfo(
                                "등록 완료",
                                f"PC 등록이 완료되었습니다.\n\n"
                                f"매장: {store_name}\n"
                                f"타석: {bay_name}\n\n"
                                f"토큰이 자동으로 저장되었습니다."
                            )
                        else:
                            self.update_status("등록은 완료되었지만 토큰 저장에 실패했습니다.", is_error=True)
                    else:
                        self.update_status("등록 완료 (토큰 없음)")
                else:
                    error_msg = data.get("error", "알 수 없는 오류")
                    self.update_status(f"등록 실패: {error_msg}", is_error=True)
                    messagebox.showerror("등록 실패", error_msg)
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text)
                except:
                    error_msg = f"서버 오류: {response.status_code}"
                
                self.update_status(f"등록 실패: {error_msg}", is_error=True)
                messagebox.showerror("등록 실패", error_msg)
        
        except requests.exceptions.ConnectionError:
            error_msg = f"서버 연결 실패: {self.server_url}"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("연결 실패", "서버에 연결할 수 없습니다.\n서버 URL을 확인하세요.")
        except requests.exceptions.Timeout:
            error_msg = "서버 응답 시간 초과"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("시간 초과", "서버 응답 시간이 초과되었습니다.")
        except Exception as e:
            error_msg = f"등록 요청 실패: {e}"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("오류", error_msg)
        finally:
            self.register_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    # 상태 텍스트 태그 설정
    app = PCRegistrationGUI(root)
    
    # 상태 텍스트 태그 설정 (나중에)
    app.status_text.tag_config("error", foreground="red")
    app.status_text.tag_config("normal", foreground="green")
    
    root.mainloop()

if __name__ == "__main__":
    main()
