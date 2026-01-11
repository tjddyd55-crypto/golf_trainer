# ===== register_pc.py (매장 PC 등록 스크립트) =====
"""
매장 PC 등록 스크립트
PC 고유번호를 수집하여 서비스에 등록 요청
"""

import platform
import subprocess
import uuid
import hashlib
import requests
import json
import sys

def get_cpu_id():
    """CPU ID 수집 (Windows)"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'ProcessorId'],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                cpu_id = lines[1].strip()
                if cpu_id:
                    return cpu_id
    except Exception as e:
        print(f"CPU ID 수집 실패: {e}")
    return None

def get_machine_guid():
    """Windows Machine GUID 수집"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ['reg', 'query', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography', '/v', 'MachineGuid'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'MachineGuid' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[-1]
    except Exception as e:
        print(f"Machine GUID 수집 실패: {e}")
    return None

def get_mac_address():
    """MAC 주소 수집"""
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0, 2*6, 2)][::-1])
        return mac
    except Exception:
        pass
    return None

def get_system_uuid():
    """시스템 UUID 수집"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ['wmic', 'csproduct', 'get', 'UUID'],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                system_uuid = lines[1].strip()
                if system_uuid and system_uuid != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
                    return system_uuid
    except Exception as e:
        print(f"System UUID 수집 실패: {e}")
    return None

def generate_pc_unique_id():
    """PC 고유 ID 생성 (여러 정보 조합)"""
    identifiers = []
    
    # 1. CPU ID
    cpu_id = get_cpu_id()
    if cpu_id:
        identifiers.append(f"CPU:{cpu_id}")
    
    # 2. Machine GUID
    machine_guid = get_machine_guid()
    if machine_guid:
        identifiers.append(f"GUID:{machine_guid}")
    
    # 3. System UUID
    system_uuid = get_system_uuid()
    if system_uuid:
        identifiers.append(f"UUID:{system_uuid}")
    
    # 4. MAC Address
    mac = get_mac_address()
    if mac:
        identifiers.append(f"MAC:{mac}")
    
    # 5. 호스트명
    hostname = platform.node()
    if hostname:
        identifiers.append(f"HOST:{hostname}")
    
    # 모든 식별자를 조합하여 해시 생성
    if identifiers:
        combined = "|".join(identifiers)
        unique_id = hashlib.sha256(combined.encode()).hexdigest()[:32].upper()
        return unique_id
    
    # 모든 방법 실패 시 랜덤 UUID 사용
    return str(uuid.uuid4()).replace("-", "").upper()[:32]

def get_pc_info():
    """PC 정보 수집"""
    return {
        "unique_id": generate_pc_unique_id(),
        "hostname": platform.node(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "processor": platform.processor(),
        "cpu_id": get_cpu_id(),
        "machine_guid": get_machine_guid(),
        "system_uuid": get_system_uuid(),
        "mac_address": get_mac_address(),
    }

def register_pc_to_server(server_url, store_name, bay_name, pc_name, pc_info):
    """서버에 PC 등록 요청"""
    try:
        payload = {
            "store_name": store_name,
            "bay_name": bay_name,
            "pc_name": pc_name,
            "pc_info": pc_info
        }
        
        response = requests.post(
            f"{server_url}/api/register_pc",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ PC 등록 성공!")
                print(f"   매장: {store_name}")
                print(f"   타석: {bay_name}")
                print(f"   PC 이름: {pc_name}")
                print(f"   PC 고유번호: {pc_info['unique_id']}")
                print()
                print("=" * 60)
                print("⚠️ 중요: 슈퍼 관리자의 승인을 기다려야 합니다.")
                print("   승인 후 샷 수집 프로그램을 실행할 수 있습니다.")
                print("=" * 60)
                return True
            else:
                print(f"❌ 등록 실패: {data.get('message', '알 수 없는 오류')}")
                return False
        else:
            print(f"❌ 서버 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 등록 요청 실패: {e}")
        return False

def main():
    print("=" * 60)
    print("매장 PC 등록")
    print("=" * 60)
    print()
    
    # PC 정보 수집
    print("PC 정보 수집 중...")
    pc_info = get_pc_info()
    print(f"PC 고유번호: {pc_info['unique_id']}")
    print(f"호스트명: {pc_info['hostname']}")
    print()
    
    # 사용자 입력
    print("등록 정보를 입력하세요:")
    print("(이 정보는 슈퍼 관리자가 PC를 구분하는 데 사용됩니다)")
    print()
    store_name = input("매장명: ").strip()
    bay_name = input("타석번호/룸번호 (예: 1번, A타석, 101호): ").strip()
    pc_name = input("PC 이름 (예: 타석1-PC, 룸A-PC): ").strip()
    
    if not store_name or not bay_name or not pc_name:
        print("❌ 모든 정보를 입력해야 합니다.")
        return 1
    
    print()
    print("입력한 정보 확인:")
    print(f"  매장명: {store_name}")
    print(f"  타석번호: {bay_name}")
    print(f"  PC 이름: {pc_name}")
    print()
    confirm = input("위 정보가 맞습니까? (Y/n): ").strip().lower()
    if confirm and confirm != 'y' and confirm != 'yes':
        print("등록이 취소되었습니다.")
        return 1
    
    # 서버 URL 입력
    server_url = input("\n서버 URL (예: https://user.railway.app, 엔터 시 기본값): ").strip()
    if not server_url:
        server_url = "https://user.railway.app"
    
    # 등록 요청
    print()
    print("서버에 등록 요청 중...")
    success = register_pc_to_server(server_url, store_name, bay_name, pc_name, pc_info)
    
    if success:
        print()
        print("=" * 60)
        print("등록 완료!")
        print("=" * 60)
        return 0
    else:
        print()
        print("=" * 60)
        print("등록 실패. 다시 시도해주세요.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
