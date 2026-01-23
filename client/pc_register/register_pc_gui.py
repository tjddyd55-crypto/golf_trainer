#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PC 등록 프로그램 (GUI 버전) - API 명세서 v1.0 최종 통합본
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import requests
import sys
import re
from datetime import datetime

# pc_identifier 모듈 import (경로에 맞게 조정하세요)
try:
    from client.core.pc_identifier import get_pc_info
except ImportError:
    def get_pc_info():
        return {"unique_id": "TEST-PC-UUID-001", "hostname": "GOLF-PC-01"}

# 설정
DEFAULT_SERVER_URL = "https://golf-api-production-e675.up.railway.app"

class PCRegistrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("골프 트레이너 PC 등록 시스템 v1.1")
        self.root.geometry("650x950")
        
        self.pc_info = None
        self.server_url = DEFAULT_SERVER_URL
        self.selected_store_id = None
        self.selected_store_name = None
        self.selected_brand = None
        self.coordinate_id_map = {}

        self.create_ui()
        self.collect_pc_info()

    def create_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="골프 트레이너 PC 등록 시스템", font=("맑은 고딕", 16, "bold")).pack(pady=(0, 20))

        # PC 정보 영역
        info_frame = ttk.LabelFrame(main_frame, text="이 PC 정보", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        self.pc_info_text = tk.Label(info_frame, text="정보 수집 중...", font=("Consolas", 9), justify=tk.LEFT, anchor="w")
        self.pc_info_text.pack(fill=tk.X)

        # 영역 1: 매장 조회
        query_frame = ttk.LabelFrame(main_frame, text="[영역 1] 매장 조회", padding="10")
        query_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(query_frame, text="매장 아이디:").grid(row=0, column=0, sticky=tk.W, pady=5)
        store_input_frame = ttk.Frame(query_frame)
        store_input_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        self.store_id_entry = ttk.Entry(store_input_frame, width=15)
        self.store_id_entry.pack(side=tk.LEFT)
        self.lookup_button = ttk.Button(store_input_frame, text="조회", command=self.lookup_store)
        self.lookup_button.pack(side=tk.LEFT, padx=5)

        # 상세 정보 표시용 라벨들
        self.store_name_label = ttk.Label(query_frame, text="매장명: -")
        self.store_name_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.store_biz_label = ttk.Label(query_frame, text="사업자번호: -")
        self.store_biz_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.store_bays_label = ttk.Label(query_frame, text="총 타석 수: -")
        self.store_bays_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.confirm_button = ttk.Button(query_frame, text="이 매장으로 확정 및 타석 불러오기", command=self.confirm_store, state=tk.DISABLED)
        self.confirm_button.grid(row=4, column=0, columnspan=2, pady=10)

        # 영역 2: 타석 등록
        self.bay_reg_frame = ttk.LabelFrame(main_frame, text="[영역 2] PC 등록 (타석 할당)", padding="10")
        self.bay_reg_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.bay_reg_frame, text="선택된 매장:").grid(row=0, column=0, sticky=tk.W)
        self.bay_store_label = ttk.Label(self.bay_reg_frame, text="미선택", foreground="gray")
        self.bay_store_label.grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(self.bay_reg_frame, text="타석 번호:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.bay_number_var = tk.StringVar()
        self.bay_number_combo = ttk.Combobox(self.bay_reg_frame, textvariable=self.bay_number_var, state="disabled", width=30)
        self.bay_number_combo.grid(row=1, column=1, pady=5, padx=10)

        ttk.Label(self.bay_reg_frame, text="타석 별칭:").grid(row=2, column=0, sticky=tk.W)
        self.bay_name_entry = ttk.Entry(self.bay_reg_frame, width=33, state="disabled")
        self.bay_name_entry.grid(row=2, column=1, pady=5, padx=10)

        self.bay_register_button = ttk.Button(self.bay_reg_frame, text="이 PC를 해당 타석으로 등록", command=self.register_bay, state=tk.DISABLED)
        self.bay_register_button.grid(row=3, column=0, columnspan=2, pady=10)

        # 영역 3: 좌표 할당
        self.coord_frame = ttk.LabelFrame(main_frame, text="[영역 3] 좌표 할당", padding="10")
        self.coord_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.coord_frame, text="타석 선택:").grid(row=0, column=0, sticky=tk.W)
        self.coord_bay_var = tk.StringVar()
        self.coord_bay_combo = ttk.Combobox(self.coord_frame, textvariable=self.coord_bay_var, state="disabled", width=30)
        self.coord_bay_combo.grid(row=0, column=1, pady=5, padx=10)
        self.coord_bay_combo.bind("<<ComboboxSelected>>", self.on_coordinate_bay_change)

        ttk.Label(self.coord_frame, text="설정된 좌표:").grid(row=1, column=0, sticky=tk.W)
        self.current_coord_label = ttk.Label(self.coord_frame, text="데이터 없음", foreground="gray")
        self.current_coord_label.grid(row=1, column=1, sticky=tk.W, padx=10)

        ttk.Label(self.coord_frame, text="브랜드 선택:").grid(row=2, column=0, sticky=tk.W)
        self.brand_var = tk.StringVar()
        self.brand_combo = ttk.Combobox(self.coord_frame, textvariable=self.brand_var, state="disabled", width=30)
        self.brand_combo.grid(row=2, column=1, pady=5, padx=10)
        self.brand_combo.bind("<<ComboboxSelected>>", self.on_brand_change)

        ttk.Label(self.coord_frame, text="좌표 파일:").grid(row=3, column=0, sticky=tk.W)
        self.coord_var = tk.StringVar()
        self.coord_combo = ttk.Combobox(self.coord_frame, textvariable=self.coord_var, state="disabled", width=30)
        self.coord_combo.grid(row=3, column=1, pady=5, padx=10)

        self.coord_assign_button = ttk.Button(self.coord_frame, text="타석에 좌표 할당", command=self.register_coordinate, state=tk.DISABLED)
        self.coord_assign_button.grid(row=4, column=0, columnspan=2, pady=10)

        # 상태 로그
        status_frame = ttk.LabelFrame(main_frame, text="상태 로그", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, state=tk.DISABLED, font=("맑은 고딕", 9))
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def update_status(self, msg, is_error=False, success=False):
        self.status_text.config(state=tk.NORMAL)
        tag = "normal"
        if is_error: tag = "error"
        if success: tag = "success"
        
        self.status_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n", tag)
        self.status_text.tag_config("error", foreground="red")
        self.status_text.tag_config("success", foreground="green")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()

    def _parse_coordinate_display(self, display_val):
        if not display_val:
            return None, None
        match = re.match(r"^(?P<resolution>[^ ]+)\s+\(v(?P<version>\d+)\)\s+-\s+", display_val)
        if not match:
            return None, None
        resolution = match.group("resolution")
        version = match.group("version")
        if not re.match(r"^\d+x\d+$", resolution):
            return None, None
        return resolution, version

    def _build_coordinate_payload(self, bay_num, selected_filename, display_val):
        payload = {
            "store_id": self.selected_store_id,
            "bay_number": bay_num,
            "brand": self.selected_brand,
            "filename": selected_filename
        }
        resolution, version = self._parse_coordinate_display(display_val)
        if resolution and version and self.selected_brand:
            payload["coordinate_id"] = f"{self.selected_brand}-{resolution}-v{version}"
        return payload

    def _post_coordinate_assignment(self, payload):
        endpoints = ["/api/coordinates/assign-bay", "/api/coordinates/assign"]
        last_response = None
        for endpoint in endpoints:
            url = f"{self.server_url}{endpoint}"
            self.update_status(f"좌표 할당 요청: {url}")
            response = requests.post(url, json=payload, timeout=5)
            last_response = response
            content_type = response.headers.get("Content-Type", "")
            is_json = content_type.startswith("application/json")
            if response.status_code in (404, 405) and not is_json:
                continue
            return response, url
        return last_response, f"{self.server_url}{endpoints[-1]}"

    def collect_pc_info(self):
        self.pc_info = get_pc_info()
        self.pc_info_text.config(text=f"ID: {self.pc_info.get('unique_id')}\nHOST: {self.pc_info.get('hostname')}")

    def lookup_store(self):
        """명세서: GET /api/get_store?store_id=..."""
        sid = self.store_id_entry.get().strip().upper()
        if not sid: return
        
        try:
            self.update_status(f"매장 정보 조회 중: {sid}")
            res = requests.get(f"{self.server_url}/api/get_store", params={"store_id": sid}, timeout=5)
            data = res.json()
            
            if res.status_code == 200 and data.get("success"):
                self.selected_store_id = data.get("store_id")
                self.selected_store_name = data.get("store_name")
                
                # 명세서 기반 상세 정보 업데이트
                self.store_name_label.config(text=f"매장명: {self.selected_store_name}", foreground="blue")
                self.store_biz_label.config(text=f"사업자번호: {data.get('business_number', '정보없음')}")
                
                # 타석 목록을 미리 가져와서 개수 표시
                bay_res = requests.get(f"{self.server_url}/api/stores/{sid}/bays", timeout=5)
                bays_count = bay_res.json().get("bays_count", 0) if bay_res.status_code == 200 else "-"
                self.store_bays_label.config(text=f"총 타석 수: {bays_count}")
                
                self.confirm_button.config(state=tk.NORMAL)
                self.update_status("매장 조회 성공.")
            else:
                self.update_status(f"조회 실패: {data.get('error', '매장을 찾을 수 없음')}", True)
        except Exception as e:
            self.update_status(f"조회 오류: {e}", True)

    def confirm_store(self):
        try:
            url = f"{self.server_url}/api/stores/{self.selected_store_id}/bays"
            res = requests.get(url, timeout=5)
            data = res.json()
            
            bays = data.get("bays", [])
            options = [f"{b['bay_number']} ({b.get('bay_name') or '이름없음'})" for b in bays]
            
            self.bay_store_label.config(text=self.selected_store_name, foreground="black")
            self.bay_number_combo.config(values=options, state="readonly")
            self.bay_name_entry.config(state="normal")
            self.bay_register_button.config(state="normal")
            
            self.coord_bay_combo.config(values=options, state="readonly")
            self.brand_combo.config(values=["SGGOLF", "GOLFZON", "GOLFZONNEW", "GOLFZONPREMIUM"], state="readonly")
            
            self.update_status(f"타석 {len(bays)}개 로드 완료. 등록 절차를 진행하세요.")
            self.confirm_button.config(state=tk.DISABLED)
        except Exception as e:
            self.update_status(f"타석 정보 로드 실패: {e}", True)

    def register_bay(self):
        """명세서: POST /api/pcs/register"""
        try:
            bay_raw = self.bay_number_var.get()
            if not bay_raw: return
            bay_num = int(re.search(r'\d+', bay_raw).group())
            
            payload = {
                "store_id": self.selected_store_id,
                "pc_unique_id": self.pc_info.get("unique_id"),
                "bay_number": bay_num,
                "bay_name": self.bay_name_entry.get().strip()
            }
            
            res = requests.post(f"{self.server_url}/api/pcs/register", json=payload, timeout=5)
            data = res.json()
            
            if data.get("success"):
                self.update_status(f"타석 {bay_num}번에 PC 등록 완료!", success=True)
                messagebox.showinfo("완료", "PC 등록이 성공적으로 완료되었습니다.")
            else:
                self.update_status(f"등록 실패: {data.get('error')}", True)
        except Exception as e:
            self.update_status(f"서버 등록 오류: {e}", True)

    def on_coordinate_bay_change(self, event=None):
        """명세서 TODO 항목 예외 처리 보강"""
        try:
            bay_raw = self.coord_bay_var.get()
            bay_num = int(re.search(r'\d+', bay_raw).group())
            
            url = f"{self.server_url}/api/stores/{self.selected_store_id}/bays/{bay_num}/coordinates"
            res = requests.get(url, timeout=5)
            
            if res.text.strip(): # 응답이 비어있지 않은 경우만 파싱
                data = res.json()
                if data.get("success"):
                    c = data.get("coordinate", {})
                    self.current_coord_label.config(text=f"{c.get('brand')} ({c.get('resolution')})", foreground="blue")
                    return
            
            self.current_coord_label.config(text="미지정 (서버 데이터 없음)", foreground="gray")
        except Exception:
            self.current_coord_label.config(text="조회 불가", foreground="red")

    def on_brand_change(self, event=None):
        """[영역 3] 브랜드 선택 시 예전 샷 수집 프로그램 방식으로 좌표 로드"""
        brand = self.brand_var.get()
        if not brand: return
        self.selected_brand = brand
        
        try:
            self.update_status(f"{brand} 좌표 목록 로드 중...")
            # 예전 방식 엔드포인트: /api/coordinates/{brand_code}
            url = f"{self.server_url}/api/coordinates/{brand}"
            res = requests.get(url, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                
                # 예전 방식 응답 구조: data.get("success") 및 data.get("files")
                if data.get("success"):
                    files = data.get("files", [])
                    
                    if not files:
                        self.update_status(f"{brand} 브랜드의 좌표 파일이 없습니다.")
                        self.coord_combo.config(values=[], state="disabled")
                        return

                    options = []
                    self.coordinate_id_map = {}
                    
                    for f in files:
                        # 파일명(filename)을 ID로 사용하거나 조합하여 맵핑
                        # 예전 샷 수집 프로그램은 filename을 직접 호출하므로 filename 저장
                        fname = f.get('filename')
                        resolution = f.get('resolution', 'Unknown')
                        version = f.get('version', '1')
                        
                        display = f"{resolution} (v{version}) - {fname}"
                        options.append(display)
                        # 중요: 실제 할당할 때 사용할 고유 키값 저장
                        self.coordinate_id_map[display] = fname 
                    
                    self.coord_combo.config(values=options, state="readonly")
                    self.coord_assign_button.config(state="normal")
                    self.update_status(f"{brand} 좌표 목록 {len(files)}개 로드 성공.", success=True)
                else:
                    error_msg = data.get("error", "서버 응답 오류")
                    self.update_status(f"목록 로드 실패: {error_msg}", True)
            else:
                self.update_status(f"서버 오류 ({res.status_code})", True)
                
        except Exception as e:
            self.update_status(f"연결 오류: {str(e)}", True)
            self.coord_combo.config(values=[], state="disabled")

    def register_coordinate(self):
        """[영역 3] 타석에 좌표 할당 - 서버 명세에 맞춰 POST"""
        try:
            bay_raw = self.coord_bay_var.get()
            if not bay_raw: 
                messagebox.showwarning("경고", "타석을 먼저 선택해주세요.")
                return
                
            bay_num = int(re.search(r'\d+', bay_raw).group())
            display_val = self.coord_var.get()
            selected_filename = self.coordinate_id_map.get(display_val)
            
            if not selected_filename: 
                messagebox.showwarning("경고", "좌표 파일을 선택해주세요.")
                return

            payload = self._build_coordinate_payload(bay_num, selected_filename, display_val)
            
            payload_summary = (
                f"store_id={payload.get('store_id')}, "
                f"bay_number={payload.get('bay_number')}, "
                f"filename={payload.get('filename')}"
            )
            self.update_status(f"좌표 할당 요청 데이터: {payload_summary}")
            self.update_status("좌표 할당 데이터 전송 중...")
            res, used_url = self._post_coordinate_assignment(payload)

            if res is None:
                self.update_status("서버 응답이 없습니다. 네트워크 상태를 확인하세요.", is_error=True)
                return
            self.update_status(f"서버 응답 코드: {res.status_code} ({used_url})")

            # 1️⃣ 성공 범위 (200대) 확인
            if 200 <= res.status_code < 300:
                
                # 2️⃣ 응답 바디가 실제로 있고, JSON 형식인지 확인
                has_json = res.headers.get("Content-Type", "").startswith("application/json")
                
                if res.text.strip() and has_json:
                    data = res.json()
                    if data.get("success") is False:
                        self.update_status(f"할당 실패: {data.get('error')}", is_error=True)
                        return
                
                # 3️⃣ 성공 처리 (204 No Content나 바디 없는 200 포함)
                self.update_status(f"타석 {bay_num}번에 좌표 할당 완료", success=True)
                messagebox.showinfo("성공", "좌표 할당이 완료되었습니다.")
                self.on_coordinate_bay_change() # 화면 갱신

            else:
                # 서버 에러 메시지(res.text)가 있다면 로그에 같이 찍어주는 것이 디버깅에 유리합니다.
                has_json = res.headers.get("Content-Type", "").startswith("application/json")
                error_message = None
                if res.text.strip() and has_json:
                    try:
                        data = res.json()
                        error_message = data.get("error") or data.get("message")
                    except ValueError:
                        error_message = None
                if res.status_code in (404, 405) and not has_json:
                    self.update_status("서버에 좌표 할당 API가 없습니다. 서버를 최신 버전으로 배포하세요.", is_error=True)
                if error_message:
                    self.update_status(f"실패 (HTTP {res.status_code}): {error_message}", is_error=True)
                else:
                    error_preview = res.text[:50] if res.text.strip() else "(응답 없음)"
                    self.update_status(f"실패 (HTTP {res.status_code}): {error_preview}", is_error=True)

        except requests.exceptions.RequestException as e:
            self.update_status(f"네트워크 통신 오류: {str(e)}", is_error=True)
        except Exception as e:
            self.update_status(f"예상치 못한 오류: {str(e)}", is_error=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = PCRegistrationGUI(root)
    root.mainloop()