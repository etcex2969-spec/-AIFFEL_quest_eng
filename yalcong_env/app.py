# -*- coding: utf-8 -*-
"""
app.py
- Trading Insight Orchestrator v4.5 프론트엔드 상황판 (Streamlit 전용)
- 사령관(조장님) 인증 도어락 가드레일 및 트레이딩뷰 실시간 차트 완벽 연동
- FastAPI 백엔드 기지국(Port 8000)과 데이터 동기화 완료
"""

import streamlit as st
import streamlit.components.v1 as components
import requests

# 1. 스트림릿 기본 페이지 설정 (넓은 화면 모드 및 타이틀)
st.set_page_config(page_title="Yalcong Orchestrator v4.5", layout="wide")

st.title("🏆 Trading Insight Orchestrator v4.5")
st.caption("사령관(얄공 조장님) 전용 실시간 자산운용 및 멀티 에이전트 상황판")

# 백엔드 기지국 주소 정의 (로컬 가상환경 기준 포트 8000)
BACKEND_URL = "http://localhost:8000"

# 2. 보안 가드레일: 사령관 인증 도어락 세팅
st.sidebar.header("🛡️ 보안 시스템")
password = st.sidebar.text_input("사령관 암호를 입력하십쇼냥!", type="password")

if password == "nyang1234":
    st.sidebar.success("✅ 인증 성공! 시스템 전산망이 개통되었습니다냥!")
    
    # 레이아웃을 2분할하여 왼쪽은 AI 제어판, 오른쪽은 차트판으로 구성
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("📡 AI 오케스트레이션 제어 센터")
        instruction = st.text_input("사령관 지시어 입력 (예: 비상, 위험, 분석 시작)", placeholder="여기에 지시를 내리십쇼냥!")
        risk_threshold = st.slider("리스크 허용 임계치 (%)", 0.0, 100.0, 50.0)
        
        if st.button("🚀 오케스트레이션 엔진 가동! 뽱!", use_container_width=True):
            if not instruction:
                st.warning("⚠️ 지시어가 비어있습니다냥! 사령관님!")
            else:
                with st.spinner("🧠 LangGraph 멀티 에이전트 파이프라인 구동 중..."):
                    try:
                        # 백엔드 주방에 AI 연산 요청 전송
                        payload = {
                            "instruction": instruction,
                            "risk_level_threshold": risk_threshold
                        }
                        response = requests.post(f"{BACKEND_URL}/orchestrate", json=payload)
                        
                        if response.status_code == 200:
                            res_data = response.json()
                            st.success(f"🎯 처리 완료! (상태: {res_data['status']})")
                            st.info(f"📊 리스크 점수: {res_data['risk_score']}%")
                            st.markdown(f"**🤖 AI 리포트:**\n{res_data['ai_report']}")
                            st.caption(f"🐾 실행 경로: { ' -> '.join(res_data['flow_path']) }")
                            st.caption(f"🕒 타임스탬프: {res_data['timestamp']}")
                        else:
                            st.error(f"❌ 백엔드 응답 실패 (코드: {response.status_code})")
                    except Exception as e:
                        st.error(f"⚠️ 백엔드 주방 연결 실패! uvicorn이 켜져있는지 확인하십쇼냥! 에러: {e}")
                        
    with col2:
        st.subheader("📈 척이의 선물 - 실시간 트레이딩뷰 차트 모니터")
        
        # 심볼 선택 숏컷 제공 (원화 환율 및 비트코인 등)
        selected_symbol = st.selectbox(
            "분석할 자산 심볼 선택", 
            ["FX_IDC:USDKRW", "BINANCE:BTCUSDT", "NASDAQ:AAPL", "TVC:GOLD"]
        )
        
        with st.spinner("📊 백엔드로부터 차트 위젯 공급받는 중..."):
            try:
                # 백엔드 기지국에서 트레이딩뷰 HTML 코드를 징발해옵니다냥!
                chart_resp = requests.get(f"{BACKEND_URL}/tradingview?symbol={selected_symbol}")
                if chart_resp.status_code == 200:
                    chart_data = chart_resp.json()
                    # 스트림릿 화면에 트레이딩뷰 위젯을 안전하게 박아넣기!
                    components.html(chart_data['widget_html'], height=520, scrolling=True)
                else:
                    st.error("❌ 백엔드에서 차트 위젯 코드를 가져오지 못했습니다냥!")
            except Exception as e:
                st.error(f"⚠️ 차트 기지국 연결 실패! 에러: {e}")

else:
    # 암호를 입력하지 않았거나 틀렸을 때 나타나는 차단 화면
    if password:
        st.sidebar.error("❌ 암호가 틀렸습니다냥! 누구냐 넌! 🚫")
    st.warning("🔒 암호를 입력하셔야 척이의 선물 차트와 AI 상황판을 볼 수 있습니다냥!")
    st.info("💡 오른쪽 사이드바에서 사령관 암호표(`nyang1234`)를 제출해 주십쇼냥!")
