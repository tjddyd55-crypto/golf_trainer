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
import re

# pc_identifier 모듈 import
try:
    # 프로젝트 루트를 sys.path에 추가 (실행 경로 문제 해결)
    import sys
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.abspath(os.path.join(_script_dir, '..', '..', '..'))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    from client.core.pc_identifier import get_pc_info
except ImportError:
    try:
        from ...core.pc_identifier import get_pc_info
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
        self.root.geometry("600x750")
        self.root.resizable(False, False)
        
        # PC 정보 저장
        self.pc_info = None
        self.server_url = DEFAULT_SERVER_URL
        
        # 선택된 매장 정보 저장
        self.selected_store_id = None
        self.selected_store_name = None
        
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
        self.code_entry.bind("<KeyRelease>", self.on_code_entry_change)
        
        # 매장아이디 (매장코드)
        ttk.Label(input_frame, text="매장아이디:").grid(row=1, column=0, sticky=tk.W, pady=5)
        store_frame = ttk.Frame(input_frame)
        store_frame.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.store_id_entry = ttk.Entry(store_frame, width=20, font=("맑은 고딕", 10))
        self.store_id_entry.pack(side=tk.LEFT)
        self.store_id_entry.bind("<KeyRelease>", self.on_store_id_entry_change)
        self.lookup_button = ttk.Button(store_frame, text="조회", command=self.lookup_store, width=8)
        self.lookup_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 매장 정보 표시 영역
        self.store_info_label = ttk.Label(input_frame, text="", foreground="blue", font=("맑은 고딕", 9))
        self.store_info_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        # 확인 버튼
        self.confirm_button = ttk.Button(input_frame, text="확인", command=self.confirm_store, width=20, state=tk.DISABLED)
        self.confirm_button.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 타석 번호 선택
        ttk.Label(input_frame, text="타석 번호:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.bay_number_var = tk.StringVar()
        self.bay_number_combo = ttk.Combobox(input_frame, textvariable=self.bay_number_var, width=27, font=("맑은 고딕", 10), state=tk.DISABLED)
        self.bay_number_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.bay_number_combo.bind("<<ComboboxSelected>>", self.on_bay_number_change)
        
        # 타석 이름 (선택사항)
        ttk.Label(input_frame, text="타석 이름 (선택):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.bay_name_entry = ttk.Entry(input_frame, width=30, font=("맑은 고딕", 10), state=tk.DISABLED)
        self.bay_name_entry.grid(row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.bay_name_entry.bind("<KeyRelease>", self.on_bay_name_change)
        
        # 버튼 영역
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.register_button = ttk.Button(
            button_frame,
            text="등록 요청",
            command=self.register_pc,
            width=20,
            state=tk.DISABLED
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
    
    def filter_alphanumeric_upper(self, value):
        """영문/숫자만 허용하고 대문자로 변환, 공백 제거"""
        filtered = re.sub(r'[^A-Za-z0-9]', '', value)
        return filtered.upper()
    
    def filter_registration_code(self, value):
        """등록코드 입력 필터링 (영문/숫자/하이픈 허용, 대문자 변환, 공백 제거)"""
        # 하이픈을 제외한 특수문자와 공백 제거, 대문자 변환
        filtered = re.sub(r'[^A-Za-z0-9-]', '', value)
        return filtered.upper()
    
    def on_code_entry_change(self, event=None):
        """PC 등록 코드 입력 필터링"""
        current = self.code_entry.get()
        filtered = self.filter_registration_code(current)
        if current != filtered:
            cursor_pos = self.code_entry.index(tk.INSERT)
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, filtered)
            # 커서 위치 조정
            new_pos = min(cursor_pos - (len(current) - len(filtered)), len(filtered))
            self.code_entry.icursor(new_pos)
    
    def on_store_id_entry_change(self, event=None):
        """매장아이디 입력 필터링"""
        current = self.store_id_entry.get()
        filtered = self.filter_alphanumeric_upper(current)
        if current != filtered:
            cursor_pos = self.store_id_entry.index(tk.INSERT)
            self.store_id_entry.delete(0, tk.END)
            self.store_id_entry.insert(0, filtered)
            # 커서 위치 조정
            new_pos = min(cursor_pos - (len(current) - len(filtered)), len(filtered))
            self.store_id_entry.icursor(new_pos)
    
    def on_bay_number_change(self, event=None):
        """타석 번호 선택 시 등록 요청 버튼 활성화"""
        self.on_bay_name_change()
    
    def on_bay_name_change(self, event=None):
        """타석 이름 입력 시 등록 요청 버튼 활성화"""
        bay_number = self.bay_number_var.get()
        registration_code = self.code_entry.get().strip()
        if bay_number and self.selected_store_id and registration_code:
            self.register_button.config(state=tk.NORMAL)
        else:
            self.register_button.config(state=tk.DISABLED)
    
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
                        self.store_id_entry.config(state=tk.DISABLED)
                        self.lookup_button.config(state=tk.DISABLED)
                        self.confirm_button.config(state=tk.DISABLED)
                        self.bay_number_combo.config(state=tk.DISABLED)
                        self.bay_name_entry.config(state=tk.DISABLED)
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
                            self.store_id_entry.config(state=tk.NORMAL)
                            self.lookup_button.config(state=tk.NORMAL)
                            self.bay_number_combo.config(state=tk.DISABLED)
                            self.bay_name_entry.config(state=tk.DISABLED)
                            self.store_info_label.config(text="")
                            self.selected_store_id = None
                            self.selected_store_name = None
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
    
    def lookup_store(self):
        """매장 조회"""
        store_id = self.store_id_entry.get().strip().upper()
        if not store_id:
            messagebox.showerror("오류", "매장아이디를 입력하세요.")
            return
        
        self.update_status(f"매장 조회 중: {store_id}")
        self.lookup_button.config(state=tk.DISABLED)
        
        try:
            # 매장 조회 API 호출
            response = requests.get(
                f"{self.server_url}/api/get_store",
                params={"store_id": store_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    store_name = data.get("store_name", "")
                    business_number = data.get("business_number", "")
                    
                    if store_name:
                        # 매장명과 사업자등록번호 표시
                        info_text = f"매장명: {store_name}"
                        if business_number:
                            info_text += f" | 사업자등록번호: {business_number}"
                        
                        self.store_info_label.config(text=info_text, foreground="blue")
                        self.selected_store_id = store_id
                        self.selected_store_name = store_name
                        self.confirm_button.config(state=tk.NORMAL)
                        self.update_status(f"매장 조회 성공: {store_name}")
                    else:
                        self.store_info_label.config(text="매장을 찾을 수 없습니다.", foreground="red")
                        self.update_status("매장을 찾을 수 없습니다.", is_error=True)
                else:
                    error_msg = data.get("error", "알 수 없는 오류")
                    self.store_info_label.config(text=error_msg, foreground="red")
                    self.update_status(f"매장 조회 실패: {error_msg}", is_error=True)
            elif response.status_code == 404:
                self.store_info_label.config(text="매장을 찾을 수 없습니다.", foreground="red")
                self.update_status("매장을 찾을 수 없습니다.", is_error=True)
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text[:100])
                except:
                    error_msg = f"서버 오류: {response.status_code}"
                self.store_info_label.config(text="매장 조회 실패", foreground="red")
                self.update_status(f"매장 조회 실패 ({response.status_code}): {error_msg}", is_error=True)
        except requests.exceptions.ConnectionError:
            self.store_info_label.config(text="서버 연결 실패", foreground="red")
            self.update_status("서버 연결 실패", is_error=True)
            messagebox.showerror("연결 실패", "서버에 연결할 수 없습니다.")
        except Exception as e:
            self.store_info_label.config(text=f"조회 오류: {e}", foreground="red")
            self.update_status(f"매장 조회 오류: {e}", is_error=True)
        finally:
            self.lookup_button.config(state=tk.NORMAL)
    
    def confirm_store(self):
        """매장 확인 후 타석 목록 조회 및 드롭다운 생성"""
        if not self.selected_store_id:
            messagebox.showerror("오류", "매장을 먼저 조회하세요.")
            return
        
        self.update_status(f"타석 목록 조회 중: {self.selected_store_id}")
        self.confirm_button.config(state=tk.DISABLED)
        
        try:
            # GET /api/stores/<store_id>/bays 호출
            response = requests.get(
                f"{self.server_url}/api/stores/{self.selected_store_id}/bays",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                bays_count = data.get("bays_count", 0)
                bays = data.get("bays", [])
                
                # 드롭다운 옵션 생성
                options = []
                for bay in bays:
                    bay_number = bay.get("bay_number")
                    bay_name = bay.get("bay_name")
                    assigned = bay.get("assigned", False)
                    
                    # 옵션 텍스트 생성
                    if bay_name:
                        option_text = f"{bay_number}번 - {bay_name}"
                    else:
                        option_text = f"{bay_number}번 타석(룸)"
                    
                    if assigned:
                        option_text += " (할당됨)"
                    
                    options.append(option_text)
                
                # 드롭다운 설정
                self.bay_number_combo['values'] = options
                self.bay_number_combo.config(state=tk.NORMAL)
                self.bay_name_entry.config(state=tk.NORMAL)
                
                self.update_status(f"매장 확인 완료: {self.selected_store_name} (타석 {bays_count}개)")
                self.on_bay_name_change()
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text[:100])
                except:
                    error_msg = f"서버 오류: {response.status_code}"
                self.update_status(f"타석 목록 조회 실패: {error_msg}", is_error=True)
                messagebox.showerror("조회 실패", error_msg)
        except requests.exceptions.ConnectionError:
            self.update_status("서버 연결 실패", is_error=True)
            messagebox.showerror("연결 실패", "서버에 연결할 수 없습니다.")
        except Exception as e:
            self.update_status(f"타석 목록 조회 오류: {e}", is_error=True)
            messagebox.showerror("오류", f"타석 목록 조회 중 오류가 발생했습니다.\n{e}")
        finally:
            self.confirm_button.config(state=tk.NORMAL)
    
    def register_pc(self):
        """PC 등록 요청 (새로운 API 사용)"""
        # 입력값 확인
        registration_code = self.code_entry.get().strip().upper()
        bay_number_text = self.bay_number_var.get()
        bay_name = self.bay_name_entry.get().strip()
        
        if not registration_code:
            messagebox.showerror("오류", "PC 등록 코드를 입력하세요.")
            return
        
        if not self.selected_store_id:
            messagebox.showerror("오류", "매장을 먼저 조회하고 확인하세요.")
            return
        
        if not bay_number_text:
            messagebox.showerror("오류", "타석 번호를 선택하세요.")
            return
        
        # bay_number 추출 (예: "3번 타석(룸)" → 3)
        import re
        match = re.search(r'(\d+)', bay_number_text)
        if not match:
            messagebox.showerror("오류", "타석 번호를 올바르게 선택하세요.")
            return
        
        bay_number = int(match.group(1))
        
        # 할당된 타석인지 확인
        if "(할당됨)" in bay_number_text:
            response = messagebox.askyesno(
                "이미 할당됨",
                f"타석 번호 {bay_number}는 이미 할당되어 있습니다.\n그래도 등록하시겠습니까?",
                icon=messagebox.WARNING
            )
            if not response:
                return
        
        if not self.pc_info:
            messagebox.showerror("오류", "PC 정보를 수집할 수 없습니다.")
            return
        
        # 필수 정보 확인
        pc_unique_id = self.pc_info.get("unique_id")
        
        if not pc_unique_id:
            messagebox.showerror("오류", "PC 고유번호를 수집할 수 없습니다.")
            return
        
        # 등록 요청 (새로운 API)
        self.update_status("서버에 등록 요청 중...")
        self.register_button.config(state=tk.DISABLED)
        
        try:
            payload = {
                "store_id": self.selected_store_id,
                "pc_unique_id": pc_unique_id,
                "bay_number": bay_number,
                "bay_name": bay_name if bay_name else None
            }
            
            response = requests.post(
                f"{self.server_url}/api/pcs/register",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bay_id = data.get("bay_id")
                    bay_number_result = data.get("bay_number")
                    bay_name_result = data.get("bay_name")
                    
                    self.update_status("PC 등록이 완료되었습니다.")
                    self.update_status(f"매장: {self.selected_store_name}")
                    self.update_status(f"타석 번호: {bay_number_result}")
                    if bay_name_result:
                        self.update_status(f"타석 이름: {bay_name_result}")
                    
                    # 입력 필드 비활성화
                    self.code_entry.config(state=tk.DISABLED)
                    self.store_id_entry.config(state=tk.DISABLED)
                    self.lookup_button.config(state=tk.DISABLED)
                    self.confirm_button.config(state=tk.DISABLED)
                    self.bay_number_combo.config(state=tk.DISABLED)
                    self.bay_name_entry.config(state=tk.DISABLED)
                    self.register_button.config(state=tk.DISABLED)
                    
                    messagebox.showinfo(
                        "등록 완료",
                        f"PC 등록이 완료되었습니다.\n\n"
                        f"매장: {self.selected_store_name}\n"
                        f"타석 번호: {bay_number_result}\n"
                        f"{f'타석 이름: {bay_name_result}' if bay_name_result else ''}"
                    )
                else:
                    error_msg = data.get("error", "알 수 없는 오류")
                    self.update_status(f"등록 실패: {error_msg}", is_error=True)
                    messagebox.showerror("등록 실패", error_msg)
            elif response.status_code == 409:
                # 중복 할당
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", "이미 할당된 타석입니다.")
                except:
                    error_msg = "이미 할당된 타석입니다."
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
    
    # 상태 텍스트 태그 설정
    app.status_text.tag_config("error", foreground="red")
    app.status_text.tag_config("normal", foreground="green")
    
    root.mainloop()

if __name__ == "__main__":
    main()
