# ===== pc_identifier.py (PC 고유번호 수집 모듈) =====
"""
PC 고유번호 수집 모듈
main.py에서 import하여 사용
"""

import platform
import subprocess
import uuid
import hashlib

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
        pass
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
        pass
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
        pass
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
