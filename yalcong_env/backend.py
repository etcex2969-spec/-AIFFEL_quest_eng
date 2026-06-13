
from fastapi import FastAPI, HTTPException, Header

app = FastAPI()
SECRET_KEY = "super_secret_nyang"

# 조장님의 거대 엔진 함수를 여기로 복사해오세요!
def my_v4_5_engine():
    # 여기에 원래 있던 복잡한 로직이 들어갑니다냥!
    return {"status": "success", "data": "떵컴의 엔진 출력값"}

@app.get("/data")
def get_data(x_api_key: str = Header(None)):
    if x_api_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="보안 위반!")
    
    # 엔진을 가동해서 결과를 뽑아줍니다!
    result = my_v4_5_engine() 
    return result
