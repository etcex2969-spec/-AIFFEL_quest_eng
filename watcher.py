import os
import time
import json
import re
import sys
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
    import yfinance as yf

SYSTEM_MONITOR_FILE = "src/security_monitoring_alert_automation/system_traffic.log"
OUTPUT_DIR = "output"

def get_financial_context():
    """금융 데이터를 가져올 때 발생하는 메모리 릭 및 연결 지연 방지"""
    try:
        # fast_info 접근 시 발생할 수 있는 램 부하를 최소화하기 위해 보수적으로 접근
        btc = yf.Ticker("BTC-USD").fast_info.get('last_price', 0.0)
        nasdaq = yf.Ticker("^IXIC").fast_info.get('last_price', 0.0)
        if btc == 0.0 or nasdaq == 0.0:
            return "금융 데이터 망 수신 대기 중"
        return f"현재 비트코인: ${btc:,.2f}, 나스닥 지수: {nasdaq:,.2f}"
    except Exception:
        return "금융 데이터 망 연결 유지 중"

def create_file_handoff_run(attack_details: str):
    """[파일 기반 핸드오프] 런 단위의 독립된 격리 폴더 및 01_raw 파일 생성"""
    finance_info = get_financial_context()
    
    ip_match = re.search(r'IP\s+([0-9.]+)', attack_details)
    attacker_ip = ip_match.group(1) if ip_match else "정체불명"
    
    # 런 아이디 생성 (예: run_20260623_153022)
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_path = os.path.join(OUTPUT_DIR, run_id)
    os.makedirs(run_path, exist_ok=True)
    
    # 01_raw_attack.json 단계 파일 저장
    raw_file_path = os.path.join(run_path, "01_raw_attack.json")
    payload = {
        "run_id": run_id,
        "ip": attacker_ip,
        "details": attack_details,
        "captured_finance": finance_info,
        "status": "collected"
    }
    
    with open(raw_file_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
        
    # main.py가 감지할 수 있도록 pending_approval.json에도 미처리 런 정보 등록
    APPROVAL_FILE = "pending_approval.json"
    if not os.path.exists(APPROVAL_FILE):
        with open(APPROVAL_FILE, 'w', encoding='utf-8') as f: json.dump([], f)
        
    try:
        with open(APPROVAL_FILE, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            if not any(req.get('run_id') == run_id for req in data):
                data.append({
                    "run_id": run_id,
                    "ip": attacker_ip,
                    "details": f"{attack_details} (자율 융합 분석 대기 중)",
                    "captured_finance": finance_info
                })
                f.seek(0); json.dump(data, f, indent=4, ensure_ascii=False); f.truncate()
    except Exception:
        pass

def watch_loop():
    if not os.path.exists(SYSTEM_MONITOR_FILE):
        os.makedirs(os.path.dirname(SYSTEM_MONITOR_FILE), exist_ok=True)
        with open(SYSTEM_MONITOR_FILE, 'w', encoding='utf-8') as f: f.write("[INFO] 시스템 가동\n")

    while True:
        try:
            with open(SYSTEM_MONITOR_FILE, 'r', encoding='utf-8') as f: 
                lines = f.readlines()
            for line in lines[-5:]:
                if any(k in line for k in ["ATTACK", "CRITICAL", "해킹"]):
                    create_file_handoff_run(line.strip())
                    with open(SYSTEM_MONITOR_FILE, 'w', encoding='utf-8') as f: 
                        f.write("[INFO] 파일 기반 파이프라인 트리거 완료.\n")
                    break
        except Exception:
            pass
        
        # ⏳ [램 보호 조치] 탐색 주기를 10초에서 30초로 변경하여 컴파일러와 디스크에 휴식기 제공!
        time.sleep(30)

if __name__ == "__main__":
    watch_loop()