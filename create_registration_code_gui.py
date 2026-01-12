#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
등록 코드 생성 프로그램 (GUI 버전)
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import requests
import sys

# 설정
DEFAULT_SUPER_ADMIN_URL = os.environ.get("SUPER_ADMIN_URL", "https://golf-super-admin-production.up.railway.app")

class RegistrationCodeGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("등록 코드 생성 프로그램")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.super_admin_url = DEFAULT_SUPER_ADMIN_URL
        self.session = None
        
        # UI 생성
        self.create_ui()
    
    def create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(
            main_frame, 
            text="등록 코드 생성 프로그램",
            font=("맑은 고딕", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 로그인 영역
        login_frame = ttk.LabelFrame(main_frame, text="슈퍼 관리자 로그인", padding="10")
        login_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 사용자명
        ttk.Label(login_frame, text="사용자명:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(login_frame, width=30, font=("맑은 고딕", 10))
        self.username_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.username_entry.insert(0, "admin")  # 기본값
        
        # 비밀번호
        ttk.Label(login_frame, text="비밀번호:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(login_frame, width=30, font=("맑은 고딕", 10), show="*")
        self.password_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 로그인 버튼
        login_button = ttk.Button(
            login_frame,
            text="로그인",
            command=self.login,
            width=20
        )
        login_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # 등록 코드 생성 영역
        code_frame = ttk.LabelFrame(main_frame, text="등록 코드 생성", padding="10")
        code_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 메모/노트
        ttk.Label(code_frame, text="메모 (선택):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.notes_entry = ttk.Entry(code_frame, width=30, font=("맑은 고딕", 10))
        self.notes_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.notes_entry.insert(0, "PC 등록 프로그램을 통해 생성된 코드")
        
        # 생성 버튼
        self.generate_button = ttk.Button(
            code_frame,
            text="등록 코드 생성",
            command=self.generate_code,
            width=20,
            state=tk.DISABLED
        )
        self.generate_button.grid(row=1, column=0, columnspan=2, pady=10)
        
        # 결과 영역
        result_frame = ttk.LabelFrame(main_frame, text="생성된 등록 코드", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 등록 코드 표시
        self.code_label = ttk.Label(
            result_frame,
            text="등록 코드가 생성되면 여기에 표시됩니다.",
            font=("맑은 고딕", 12),
            foreground="gray"
        )
        self.code_label.pack(pady=10)
        
        # 복사 버튼
        self.copy_button = ttk.Button(
            result_frame,
            text="코드 복사",
            command=self.copy_code,
            width=20,
            state=tk.DISABLED
        )
        self.copy_button.pack(pady=5)
        
        # 상태 메시지 영역
        status_frame = ttk.LabelFrame(main_frame, text="상태", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=6,
            state=tk.DISABLED,
            font=("맑은 고딕", 9),
            wrap=tk.WORD
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # 상태 텍스트 태그 설정
        self.status_text.tag_config("error", foreground="red")
        self.status_text.tag_config("normal", foreground="green")
        
        # 저장된 코드
        self.generated_code = None
    
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
    
    def login(self):
        """슈퍼 관리자 로그인"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("오류", "사용자명과 비밀번호를 입력하세요.")
            return
        
        self.update_status("로그인 중...")
        
        try:
            # 세션 생성
            self.session = requests.Session()
            login_url = f"{self.super_admin_url}/login"
            
            # 로그인 요청
            login_response = self.session.post(
                login_url,
                data={"username": username, "password": password},
                timeout=10,
                allow_redirects=False
            )
            
            # Flask 로그인 성공 시 302 리다이렉트 반환
            if login_response.status_code == 302:
                location = login_response.headers.get('Location', '')
                if 'super_admin_dashboard' in location or 'dashboard' in location:
                    self.update_status("로그인 성공")
                    self.generate_button.config(state=tk.NORMAL)
                    messagebox.showinfo("로그인 성공", "로그인에 성공했습니다.\n이제 등록 코드를 생성할 수 있습니다.")
                else:
                    self.update_status("로그인 실패: 잘못된 리다이렉트", is_error=True)
                    messagebox.showerror("로그인 실패", "로그인에 실패했습니다.\n사용자명 또는 비밀번호를 확인하세요.")
            elif login_response.status_code == 200:
                if "인증 실패" in login_response.text or "error" in login_response.text.lower():
                    self.update_status("로그인 실패: 인증 실패", is_error=True)
                    messagebox.showerror("로그인 실패", "로그인에 실패했습니다.\n사용자명 또는 비밀번호를 확인하세요.")
                else:
                    self.update_status("로그인 성공")
                    self.generate_button.config(state=tk.NORMAL)
                    messagebox.showinfo("로그인 성공", "로그인에 성공했습니다.")
            else:
                self.update_status(f"로그인 실패: 상태 코드 {login_response.status_code}", is_error=True)
                messagebox.showerror("로그인 실패", f"로그인에 실패했습니다.\n상태 코드: {login_response.status_code}")
        
        except requests.exceptions.ConnectionError:
            error_msg = f"서버 연결 실패: {self.super_admin_url}"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("연결 실패", "서버에 연결할 수 없습니다.\n서버 URL을 확인하세요.")
        except requests.exceptions.Timeout:
            error_msg = "서버 응답 시간 초과"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("시간 초과", "서버 응답 시간이 초과되었습니다.")
        except Exception as e:
            error_msg = f"로그인 실패: {e}"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("오류", error_msg)
    
    def generate_code(self):
        """등록 코드 생성"""
        if not self.session:
            messagebox.showerror("오류", "먼저 로그인하세요.")
            return
        
        notes = self.notes_entry.get().strip()
        
        self.update_status("등록 코드 생성 중...")
        self.generate_button.config(state=tk.DISABLED)
        
        try:
            create_url = f"{self.super_admin_url}/api/create_registration_code"
            
            create_response = self.session.post(
                create_url,
                json={"notes": notes},
                timeout=10
            )
            
            if create_response.status_code == 200:
                data = create_response.json()
                if data.get("success"):
                    registration_code = data.get("registration_code") or data.get("registration_key")
                    self.generated_code = registration_code
                    
                    # 등록 코드 표시
                    self.code_label.config(
                        text=f"등록 코드: {registration_code}",
                        font=("맑은 고딕", 14, "bold"),
                        foreground="green"
                    )
                    
                    self.copy_button.config(state=tk.NORMAL)
                    
                    self.update_status("등록 코드 생성 완료")
                    self.update_status(f"생성된 코드: {registration_code}")
                    self.update_status("기존 ACTIVE 코드는 자동으로 REVOKED 처리되었습니다.")
                    
                    messagebox.showinfo(
                        "생성 완료",
                        f"등록 코드가 생성되었습니다.\n\n"
                        f"등록 코드: {registration_code}\n\n"
                        f"이 코드를 PC 등록 프로그램에서 사용하세요."
                    )
                else:
                    error_msg = data.get("message", "알 수 없는 오류")
                    self.update_status(f"등록 코드 생성 실패: {error_msg}", is_error=True)
                    messagebox.showerror("생성 실패", error_msg)
            else:
                try:
                    error_data = create_response.json()
                    error_msg = error_data.get("message", create_response.text)
                except:
                    error_msg = f"서버 오류: {create_response.status_code}"
                
                self.update_status(f"등록 코드 생성 실패: {error_msg}", is_error=True)
                messagebox.showerror("생성 실패", error_msg)
        
        except requests.exceptions.ConnectionError:
            error_msg = f"서버 연결 실패: {self.super_admin_url}"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("연결 실패", "서버에 연결할 수 없습니다.")
        except requests.exceptions.Timeout:
            error_msg = "서버 응답 시간 초과"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("시간 초과", "서버 응답 시간이 초과되었습니다.")
        except Exception as e:
            error_msg = f"등록 코드 생성 실패: {e}"
            self.update_status(error_msg, is_error=True)
            messagebox.showerror("오류", error_msg)
        finally:
            self.generate_button.config(state=tk.NORMAL)
    
    def copy_code(self):
        """생성된 등록 코드를 클립보드에 복사"""
        if self.generated_code:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.generated_code)
            self.update_status("등록 코드가 클립보드에 복사되었습니다.")
            messagebox.showinfo("복사 완료", f"등록 코드가 클립보드에 복사되었습니다.\n\n{self.generated_code}")

def main():
    root = tk.Tk()
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    app = RegistrationCodeGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
