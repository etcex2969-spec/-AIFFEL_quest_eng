import os
import json
import pandas as pd
from datetime import datetime
from crewai import Agent, Crew, Task, LLM

# 떵컴 램 세이빙용 초경량 뇌 고정 (대시보드와 동일)
crew_llm = LLM(model="ollama/llama3.2:3b", base_url="http://host.docker.internal:11434")

LOG_FILE = "agent_learning_log.json"

def run_historical_backtest(csv_file_path):
    """과거 금융 데이터를 쪼개어 깨비에게 백테스팅 성찰 교육을 시키는 엔진"""
    if not os.path.exists(csv_file_path):
        print(f"❌ 에러: {csv_file_path} 파일이 존재하지 않습니다.")
        print("💡 팁: 과거 비트코인 일봉/분봉 데이터 CSV를 이 이름으로 배치해주세요!")
        return

    print("📈 [1단계] 파이썬 코드가 과거 금융 거래 데이터를 고속 스캔 중...")
    # CSV 로드
    df = pd.read_csv(csv_file_path)
    
    # 🚨 [결정론적 필터 게이트] 
    # 무작정 LLM에 다 밀어 넣으면 램이 터지므로, 거래량이 평균보다 3배 이상 터진 '특이일'만 코드로 자율 선별
    if 'Volume' in df.columns and 'Close' in df.columns:
        heavy_traffic_days = df[df['Volume'] > df['Volume'].mean() * 3]
    else:
        # 컬럼명이 다를 경우를 대비한 폴백 (앞부분 5개 행만 우선 샘플링)
        heavy_traffic_days = df.head(5)
        
    print(f"🎯 선별 완료: 총 {len(heavy_traffic_days)}건의 중요 매매 타이밍 포착. 깨비 훈련을 시작합니다.")
    
    # 기존 장부 로드
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as lf:
            try: log_data = json.load(lf)
            except: log_data = []
    else:
        log_data = []

    # 훈련 시작 (과거 데이터 성찰 루프)
    for idx, row in heavy_traffic_days.head(5).iterrows(): # 램 보호를 위해 우선 5개만 시범 조준
        date_val = row.get('Date', row.get('date', f"과거시점_{idx}"))
        price_val = row.get('Close', row.get('close', 0.0))
        vol_val = row.get('Volume', row.get('volume', 0.0))
        
        print(f"📂 [과거 런 가동] {date_val} 당시 시황 추출 및 깨비 수송 중...")
        
        evaluator = Agent(
            role='백테스팅 전문 매매 깨비',
            goal='과거 특정 시점의 시황을 분석하여 자산 방어 및 매수 적합성을 판별하라.',
            backstory='과거의 차트 패턴과 시장 심리를 융합하여 최적의 타점을 찾아내는 노련한 사냥꾼.',
            llm=crew_llm
        )
        
        task = Task(
            description=f"과거 시점: {date_val} | 당시 가격: ${price_val:,.2f} | 거래량: {vol_val:,.2f}. 이 타이밍에 자산을 지키거나 공격적인 매수를 집행하는 것이 타당한지 과거 타점 분석 결과를 점잖게 한 줄로 요약하시오.",
            expected_output="담백하고 명확한 매매 타점 성찰록 한 줄",
            agent=evaluator
        )
        
        crew = Crew(agents=[evaluator], tasks=[task])
        try:
            reflection_result = str(crew.kickoff())
            print(f"💡 깨비의 성찰 결과: {reflection_result}")
            
            # 메인 장부에 학습 결과 영구 누적
            log_data.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "alert_report": f"[과거 백테스팅 훈련] 시점: {date_val} (종가: ${price_val:,.2f})\n📊 깨비의 백테스트 반성록: {reflection_result}"
            })
        except Exception as e:
            print(f"⚠️ 깨비 기동 중 에러 발생 (건너뜀): {e}")

    # 최종 장부 저장
    with open(LOG_FILE, 'w', encoding='utf-8') as lf:
        json.dump(log_data, lf, indent=4, ensure_ascii=False)
        
    print("✨ 백테스팅 성찰 훈련 완료! 메인 장부에 기록되었습니다. 대시보드(장부)를 새로고침 해보세요.")

if __name__ == "__main__":
    # 시범용 가상 파일 이름 지정
    run_historical_backtest("historical_btc_data.csv")