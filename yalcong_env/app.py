
import streamlit as st
import requests

# 1. 보안 도어락
password = st.text_input("암호 입력:", type="password")
if password != "nyang1234":
    st.stop()

# 2. 엔진 데이터 불러오기 (백엔드 호출)
def get_engine_result():
    response = requests.get("http://127.0.0.1:8000/data", headers={"x-api-key": "super_secret_nyang"})
    return response.json() if response.status_code == 200 else None

# 3. 화면 그리기 (기존 코드의 UI 부분만 여기로!)
st.title("v4.5 거대 엔진 대시보드")
if st.button("엔진 가동!"):
    data = get_engine_result()
    st.write(data) # 여기에 차트 코드를 넣으세요!
