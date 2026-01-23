# -*- coding: utf-8 -*-
"""
좌표 데이터 확인 스크립트 (API를 통한 확인)
"""
import requests
import json

SERVER_URL = "https://golf-api-production-e675.up.railway.app"

def check_coordinates():
    """API를 통해 좌표 데이터 확인"""
    print("=" * 60)
    print("좌표 데이터 확인 (API를 통한 확인)")
    print("=" * 60)
    print()
    
    brands = ["SGGOLF", "GOLFZON", "GOLFZONNEW", "GOLFZONPREMIUM"]
    total_count = 0
    brand_counts = {}
    
    print("1. 브랜드별 좌표 데이터 확인")
    print("-" * 60)
    
    for brand in brands:
        try:
            url = f"{SERVER_URL}/api/coordinates"
            params = {"brand": brand}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    files = data.get("files", [])
                    count = len(files)
                    brand_counts[brand] = count
                    total_count += count
                    print(f"  {brand}: {count}개")
                else:
                    brand_counts[brand] = 0
                    print(f"  {brand}: 0개 (응답 오류: {data.get('error', '알 수 없는 오류')})")
            elif response.status_code == 400:
                # brand 파라미터 필요
                brand_counts[brand] = 0
                print(f"  {brand}: 0개 (API 오류)")
            else:
                brand_counts[brand] = 0
                print(f"  {brand}: 서버 오류 ({response.status_code})")
                
        except requests.exceptions.Timeout:
            brand_counts[brand] = 0
            print(f"  {brand}: 타임아웃")
        except Exception as e:
            brand_counts[brand] = 0
            print(f"  {brand}: 오류 - {e}")
    
    print()
    print("2. 전체 좌표 데이터 개수")
    print("-" * 60)
    print(f"전체 좌표 데이터 개수: {total_count}개")
    print()
    
    print("3. 상세 데이터 목록 (브랜드별)")
    print("-" * 60)
    
    for brand in brands:
        if brand_counts.get(brand, 0) > 0:
            try:
                url = f"{SERVER_URL}/api/coordinates"
                params = {"brand": brand}
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        files = data.get("files", [])
                        print(f"\n[{brand}] 좌표 목록:")
                        for f in files:
                            filename = f.get("filename", "N/A")
                            resolution = f.get("resolution", "N/A")
                            version = f.get("version", "N/A")
                            created_at = f.get("created_at", "N/A")
                            print(f"  - {filename} (해상도: {resolution}, 버전: {version}, 생성일: {created_at})")
            except Exception as e:
                print(f"[{brand}] 조회 실패: {e}")
    
    print()
    print("=" * 60)
    print("조회 완료!")
    print("=" * 60)

if __name__ == "__main__":
    check_coordinates()
