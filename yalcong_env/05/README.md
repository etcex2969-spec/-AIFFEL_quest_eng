

🏆 Trading Insight Orchestrator v4.5 (yalcong_env)


본 리포지토리는 인공지능 멀티 에이전트 자율 분석 기술과 고도의 리스크 관리를 결합한 인간 개입형(Human-in-the-Loop) 반자동 자산운용 의사결정 인프라 v4.5의 구동 및 배포용 통합 저장소입니다.

🛠️ 1. 내 텅컴(로컬 가상환경) 구동 인프라 셋업

본 시스템은 외부 패키지 충돌 방지를 위해 파이썬 가상환경(yalcong_env) 내에서 완전 독립 구동하도록 설계되었습니다.

# 1단계: 프로젝트 작업 폴더로 이동
cd C:/Projects/trading_v4_5/

# 2단계: 가상환경 비밀 서랍 개방
conda activate yalcong_env

# 3단계: 실전
 배포를 위한 핵심 부품(라이브러리) 일괄 장전
pip install fastapi uvicorn pydantic streamlit requests


🚀 2. 2포트 독립 배포 가동 시나리오 (디커플링 아키텍처)

모델배포개론 02~04단의 설계 지침에 따라, 서버 통전 지연 및 UI 렉 현상을 원천 방지하기 위해 백엔드와 프론트엔드를 독립 포트로 격리 가동합니다.

🔌 포트 ①: 백엔드 엔진실 기지국 개통 (Port 8000)

# Conda 창 ① 열기
conda activate yalcong_env
python trading_orchestrator_v4_5.py


동작 실체: 8000번 포트에서 Pydantic v2 데이터 검수 및 LangGraph 기반의 Stateful 에이전트 분석기가 24시간 실시간 대기합니다.

🖥️ 포트 ②: 프론트엔드 상황판 화면단 개통 (Port 8501)

# Conda 창 ② 열기
conda activate yalcong_env
streamlit run app_streamlit.py --server.address 0.0.0.0


동작 실체: 8501번 포트에서 스마트폰 원격 제어를 전면 수용하는 화려한 뷰판(View) 및 인간 개입 상황판 UI가 가동됩니다.

📱 3. 안방 침대에서 스마트폰으로 원격 제어망 접속하는 법

내 텅컴의 내부 IP 주소(예: 192.168.0.15)를 윈도우 cmd 창에서 ipconfig 명령어로 확인합니다.

침대에 누워서 스마트폰 브라우저에 http://내똥컴IP주소:8501을 입력하여 접속합니다.

실시간 보고서와 기술 지표 뷰판을 감상하다가 위험 감지 시, 상황판 빈칸에 Emergency를 치고 사격 개시를 누르거나 물리 EMERGENCY (비상벨) 단추를 눌러 시스템 전체를 즉시 전원 강제 셧다운(FROZEN) 시킵니다.

💾 4. 깃허브(GitHub) 소스코드 푸시(Push) 치트키 명령어

님의 피땀 눈물이 담긴 코드를 깃허브 원격 안방에 안전하게 박제하여 과제를 제출하는 콘솔 명령어입니다.

# 1. 내 작업실 폴더를 깃(Git) 영토로 선포!
git init

# 2. 깃허브 공식 우주 주소와 연동망 결합!
git remote add origin [https://github.com/조장님아이디/레포지토리이름.git](https://github.com/조장님아이디/레포지토리이름.git)

# 3. 변경된 실물 파일 3총사 카트리지에 전부 적재!
git add .

# 4. 역사적인 v4.5 최종 배포 도장 쾅쾅 커밋!
git commit -m "feat: complete human-in-the-loop orchestrator v4.5 fullstack"

# 5. 깃허브 우주 영토 메인 스트림으로 최종 폭격 전송!!! 뽱!!!
git push -u origin main
