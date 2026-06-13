import os

from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tradingview_api_real_time_trading_system.tools.trading_api_client import TradingAPIClientTool
from tradingview_api_real_time_trading_system.tools.technical_analyzer import TechnicalAnalyzer
from tradingview_api_real_time_trading_system.tools.trading_signal_processor import TradingSignalProcessor





@CrewBase
class TradingviewAPIRealTimeTradingSystemCrew:
    """TradingviewAPIRealTimeTradingSystem crew"""

    
    @agent
    def real_time_api_data_collector(self) -> Agent:
        
        
        return Agent(
            config=self.agents_config["real_time_api_data_collector"],
            
            
            tools=[				TradingAPIClientTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                
                
            ),
            
        )
        
    
    @agent
    def advanced_technical_analyst(self) -> Agent:
        
        
        return Agent(
            config=self.agents_config["advanced_technical_analyst"],
            
            
            tools=[				TechnicalAnalyzer()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                
                
            ),
            
        )
        
    
    @agent
    def trading_signal_processor(self) -> Agent:
        
        
        return Agent(
            config=self.agents_config["trading_signal_processor"],
            
            
            tools=[				TradingSignalProcessor()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                
                
            ),
            
        )
        
    

    
    @task
    def collect_market_data_via_api(self) -> Task:
        return Task(
            config=self.tasks_config["collect_market_data_via_api"],
            markdown=False,
            
            
        )
    
    @task
    def generate_technical_signals(self) -> Task:
        return Task(
            config=self.tasks_config["generate_technical_signals"],
            markdown=False,
            
            
        )
    
    @task
    def process_trading_signals(self) -> Task:
        return Task(
            config=self.tasks_config["process_trading_signals"],
            markdown=False,
            
            
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the TradingviewAPIRealTimeTradingSystem crew"""

        # Custom manager agent for hierarchical process
        manager_agent = Agent(
            role="Crew Manager",
            goal="Coordinate the team to achieve the objective efficiently",
            backstory="An experienced manager skilled in delegation and coordination",
            llm=LLM(model="anthropic/claude-fable-5"),
            allow_delegation=True,
        )

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.hierarchical,
            verbose=True,


            manager_agent=manager_agent,


            chat_llm=LLM(model="openai/gpt-4o-mini"),
        )


