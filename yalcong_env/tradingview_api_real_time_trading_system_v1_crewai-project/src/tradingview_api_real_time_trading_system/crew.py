import os
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# 조장님이 새 가상공간 폴더에 예쁘게 배치하신 무기들 정확하게 로드냥!
from tradingview_api_real_time_trading_system.tools.trading_api_client import TradingAPIClientTool
from tradingview_api_real_time_trading_system.tools.technical_analyzer import TechnicalAnalyzer
from tradingview_api_real_time_trading_system.tools.trading_signal_processor import TradingSignalProcessor

@CrewBase
class TradingviewAPIRealTimeTradingSystemCrew:
    """TradingviewAPIRealTimeTradingSystem crew - 얄공 가상공간 초경량 고속 버전 뽱!"""

    def __init__(self):
        # 가성비 최고이자 속도가 가장 빠른 gpt-4o-mini 두뇌로 대동단결냥!
        self.base_llm = LLM(model="openai/gpt-4o-mini")

    @agent
    def real_time_api_data_collector(self) -> Agent:
        return Agent(
            config=self.agents_config["real_time_api_data_collector"],
            tools=[TradingAPIClientTool()],
            allow_delegation=False,
            max_iter=3,        # 25번 무한 루프 돌며 징징대던 것 3번으로 체중 감량!
            max_rpm=15,        # 거래소 API 차단 방지 가드레일 설치!
            verbose=True,
            llm=self.base_llm,
        )
        
    @agent
    def advanced_technical_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["advanced_technical_analyst"],
            tools=[TechnicalAnalyzer()],
            allow_delegation=False,
            max_iter=3,
            verbose=True,
            llm=self.base_llm,
        )

    @agent
    def risk_compliance_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_compliance_manager"],
            tools=[],
            allow_delegation=False,
            max_iter=3,
            verbose=True,
            llm=self.base_llm,
        )

    @agent
    def portfolio_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["portfolio_strategist"],
            tools=[],
            allow_delegation=False,
            max_iter=3,
            verbose=True,
            llm=self.base_llm,
        )

    @agent
    def trading_execution_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["trading_execution_specialist"],
            tools=[TradingSignalProcessor()],
            allow_delegation=False,
            max_iter=3,
            verbose=True,
            llm=self.base_llm,
        )

    # ==========================================
    # Tasks 정의 (yaml 파일과 1:1 매칭 완료냥!)
    # ==========================================
    @task
    def collect_market_data_via_api(self) -> Task:
        return Task(config=self.tasks_config["collect_market_data_via_api"])
    
    @task
    def generate_technical_signals(self) -> Task:
        return Task(config=self.tasks_config["generate_technical_signals"])
    
    @task
    def assess_risk_and_compliance(self) -> Task:
        return Task(config=self.tasks_config["assess_risk_and_compliance"])

    @task
    def optimize_portfolio_allocation(self) -> Task:
        return Task(config=self.tasks_config["optimize_portfolio_allocation"])

    @task
    def execute_trades_and_log(self) -> Task:
        return Task(config=self.tasks_config["execute_trades_and_log"])

    @crew
    def crew(self) -> Crew:
        """무거운 계층형 중간보고 싹 치우고, 순서대로 착착 달리는 고속도로 개통냥!"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # 초고속 순차형 가동!
            verbose=True,
            memory=False,                # 기가바이트급 기억 지우고 가볍게 출발냥!
        )
