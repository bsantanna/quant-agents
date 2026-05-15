import json
import re
from datetime import datetime, timedelta

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import Literal

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import (
    SupervisedWorkflowAgentBase,
    AgentUtils,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1 import (
    FINANCIAL_ANALYST_V1_AGENTS,
    FINANCIAL_ANALYST_V1_AGENT_CONFIGURATION,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.prompts import (
    CONSENSUS_REPORTER_SYSTEM_PROMPT,
    COORDINATOR_SYSTEM_PROMPT,
    DATA_COLLECTOR_SYSTEM_PROMPT,
    EXECUTION_PLAN,
    FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
    TECHNICAL_ANALYST_SYSTEM_PROMPT,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.state import (
    FinancialAnalystState,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.company_profile_summary import (
    summarize_company_profile,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.indicators_summary import (
    summarize_technical_indicators,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.portfolio_xray import (
    compute_xray_data,
    format_xray_html,
    format_xray_text,
)
from app.services.agent_types.quaks.insights.tools import build_get_markets_news_tool
from app.services.markets_news import MarketsNewsService
from app.services.markets_stats import MarketsStatsService
from app.services.tasks import TaskProgress


class QuaksFinancialAnalystV1Agent(SupervisedWorkflowAgentBase):
    def __init__(
        self,
        agent_utils: AgentUtils,
        markets_stats_service: MarketsStatsService,
        markets_news_service: MarketsNewsService,
    ):
        super().__init__(agent_utils)
        self.markets_stats_service = markets_stats_service
        self.markets_news_service = markets_news_service

    def create_default_settings(self, agent_id: str, schema: str):
        prompts = {
            "coordinator_system_prompt": COORDINATOR_SYSTEM_PROMPT,
            "data_collector_system_prompt": DATA_COLLECTOR_SYSTEM_PROMPT,
            "fundamental_analyst_system_prompt": FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
            "technical_analyst_system_prompt": TECHNICAL_ANALYST_SYSTEM_PROMPT,
            "consensus_reporter_system_prompt": CONSENSUS_REPORTER_SYSTEM_PROMPT,
        }
        for key, value in prompts.items():
            self.agent_setting_service.create_agent_setting(
                agent_id=agent_id,
                setting_key=key,
                setting_value=value,
                schema=schema,
            )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(FinancialAnalystState)
        workflow_builder.add_edge(START, "coordinator")
        workflow_builder.add_node("coordinator", self.get_coordinator)
        workflow_builder.add_node("data_collector", self.get_data_collector)
        workflow_builder.add_node("fundamental_analyst", self.get_fundamental_analyst)
        workflow_builder.add_node("technical_analyst", self.get_technical_analyst)
        workflow_builder.add_node("consensus_reporter", self.get_consensus_reporter)
        workflow_builder.add_node("portfolio_xray", self.get_portfolio_xray)
        workflow_builder.add_edge("data_collector", "portfolio_xray")
        workflow_builder.add_edge("portfolio_xray", "fundamental_analyst")
        workflow_builder.add_edge("fundamental_analyst", "technical_analyst")
        workflow_builder.add_edge("technical_analyst", "consensus_reporter")
        workflow_builder.add_edge("consensus_reporter", END)
        return workflow_builder

    def get_input_params(self, message_request: MessageRequest, schema: str) -> dict:
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id, schema
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }

        tickers = self._parse_tickers(message_request.message_content)

        template_vars = {
            "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
            "EXECUTION_PLAN": EXECUTION_PLAN,
            "TICKERS": ", ".join(tickers)
            if tickers
            else "To be determined from user query",
            "FINANCIAL_ANALYST_AGENTS": FINANCIAL_ANALYST_V1_AGENTS,
            "FINANCIAL_ANALYST_AGENT_CONFIGURATION": FINANCIAL_ANALYST_V1_AGENT_CONFIGURATION,
        }

        return {
            "agent_id": message_request.agent_id,
            "schema": schema,
            "query": message_request.message_content,
            "tickers": tickers,
            "execution_plan": EXECUTION_PLAN,
            "coordinator_system_prompt": self.parse_prompt_template(
                settings_dict, "coordinator_system_prompt", template_vars
            ),
            "data_collector_system_prompt": self.parse_prompt_template(
                settings_dict, "data_collector_system_prompt", template_vars
            ),
            "fundamental_analyst_system_prompt": self.parse_prompt_template(
                settings_dict, "fundamental_analyst_system_prompt", template_vars
            ),
            "technical_analyst_system_prompt": self.parse_prompt_template(
                settings_dict, "technical_analyst_system_prompt", template_vars
            ),
            "consensus_reporter_system_prompt": self.parse_prompt_template(
                settings_dict, "consensus_reporter_system_prompt", template_vars
            ),
            "fundamental_recommendation": "",
            "technical_recommendation": "",
            "consensus_verdict": "",
            "allocation_weights": "",
            "portfolio_xray_html": "",
            "messages": [HumanMessage(content=message_request.message_content)],
        }

    @staticmethod
    def _parse_tickers(message_content: str) -> list[str]:
        """Extract ticker symbols from BATCH_ETL messages only.

        Only BATCH_ETL triggers the full analysis pipeline.
        Supports: BATCH_ETL AAPL MSFT, BATCH_ETL AAPL,MSFT,NVDA
        """
        content = message_content.strip()
        if not content.startswith("BATCH_ETL"):
            return []
        content = content.replace("BATCH_ETL", "").strip()
        tokens = re.split(r"[,\s]+", content)
        tickers = [t.upper() for t in tokens if re.match(r"^[A-Z]{1,5}$", t.upper())]
        return tickers

    def _build_tools(self):
        markets_stats_service = self.markets_stats_service
        markets_news_service = self.markets_news_service

        @tool("fetch_company_profile")
        def fetch_company_profile(ticker: str) -> str:
            """Fetch company metadata, valuation multiples, analyst ratings, and ownership data.

            Args:
                ticker: Stock ticker symbol (e.g. AAPL, MSFT, NVDA).

            Returns:
                JSON string with company profile data.
            """
            doc = markets_stats_service.get_company_profile(
                index_name="quaks_stocks-metadata_latest",
                key_ticker=ticker,
            )
            return json.dumps(
                summarize_company_profile(doc), ensure_ascii=False, default=str
            )

        @tool("fetch_stats_close")
        def fetch_stats_close(ticker: str) -> str:
            """Fetch latest price stats including OHLCV and percent variance for a ticker.

            Args:
                ticker: Stock ticker symbol (e.g. AAPL, MSFT, NVDA).

            Returns:
                JSON string with price stats.
            """
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            result = markets_stats_service.get_stats_close(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )
            return json.dumps(result, ensure_ascii=False, default=str)

        @tool("fetch_technical_indicators")
        def fetch_technical_indicators(ticker: str) -> str:
            """Fetch technical indicators (RSI, MACD, EMA, ADX) for a ticker.

            Args:
                ticker: Stock ticker symbol (e.g. AAPL, MSFT, NVDA).

            Returns:
                JSON string with technical indicator values.
            """
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            rsi = markets_stats_service.get_indicator_rsi(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                period=14,
            )
            macd = markets_stats_service.get_indicator_macd(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                short_window=12,
                long_window=26,
                signal_window=9,
            )
            ema = markets_stats_service.get_indicator_ema(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                short_window=10,
                long_window=20,
            )
            adx = markets_stats_service.get_indicator_adx(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                period=14,
            )
            return json.dumps(
                summarize_technical_indicators(rsi, macd, ema, adx),
                ensure_ascii=False,
                default=str,
            )

        return [
            fetch_company_profile,
            fetch_stats_close,
            fetch_technical_indicators,
            build_get_markets_news_tool(markets_news_service),
            self._build_xray_tool(),
        ]

    def _build_xray_tool(self):
        markets_stats_service = self.markets_stats_service

        @tool("fetch_portfolio_xray")
        def fetch_portfolio_xray(tickers: str) -> str:
            """Generate an X-Ray analysis for a combination of stock tickers.

            Provides Morningstar-style breakdown including investment style box,
            sector classification, geographic exposure, valuation stats,
            and composition details. Uses equal weighting across all tickers.

            Args:
                tickers: Comma-separated ticker symbols (e.g. "AAPL,MSFT,NVDA").

            Returns:
                Text summary of the X-Ray analysis.
            """
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
            data = compute_xray_data(markets_stats_service, ticker_list)
            return format_xray_text(data)

        return fetch_portfolio_xray

    def _invoke_chain(self, agent_id, schema, system_prompt, messages):
        """Invoke a simple system+messages chain and return a single AIMessage."""
        chat_model = self.get_chat_model(agent_id, schema)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("placeholder", "{messages}"),
            ]
        )
        chain = prompt | chat_model
        response = chain.invoke({"messages": messages})
        return response

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """Remove markdown code fences and inline formatting from LLM output."""
        # Remove ```html ... ``` wrappers
        text = re.sub(r"^```\w*\n?", "", text.strip())
        text = re.sub(r"\n?```$", "", text.strip())
        # Remove inline markdown: *text*, **text**, _text_, __text__
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
        text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
        return text.strip()

    @staticmethod
    def _get_last_named_message(messages, name):
        """Return the last message with the given name, or None."""
        for msg in reversed(messages):
            if getattr(msg, "name", None) == name:
                return msg
        return None

    def get_coordinator(
        self, state: FinancialAnalystState
    ) -> Command[Literal["data_collector", "__end__"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]
        query = state["query"]
        tickers = state["tickers"]

        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Query -> {query}")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=f"Analyzing query: {query}",
            )
        )

        is_batch = query.strip().startswith("BATCH_ETL")

        if tickers:
            self.logger.info(
                f"Agent[{agent_id}] -> Coordinator -> Tickers: {tickers} -> data_collector"
            )
            return Command(
                goto="data_collector",
                update={
                    "messages": [
                        AIMessage(
                            content=f"Proceeding with financial analysis for: {', '.join(tickers)}",
                            name="coordinator",
                        )
                    ]
                },
            )

        if is_batch:
            self.logger.info(
                f"Agent[{agent_id}] -> Coordinator -> BATCH_ETL without tickers"
            )
            return Command(
                goto=END,
                update={
                    "messages": [
                        AIMessage(
                            content="BATCH_ETL requires ticker symbols. Example: BATCH_ETL AAPL,MSFT,NVDA",
                            name="coordinator",
                        )
                    ]
                },
            )

        # QA mode: answer directly, with portfolio X-ray tool available
        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> QA mode")
        chat_model = self.get_chat_model(agent_id, schema)
        coordinator = create_react_agent(
            model=chat_model,
            tools=[self._build_xray_tool()],
            prompt=state["coordinator_system_prompt"],
        )
        response = coordinator.invoke(state)
        return Command(
            goto=END,
            update={"messages": response["messages"]},
        )

    def get_data_collector(
        self, state: FinancialAnalystState
    ) -> Command[Literal["fundamental_analyst"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        tickers_str = ", ".join(state["tickers"])
        self.logger.info(f"Agent[{agent_id}] -> Data Collector -> {tickers_str}")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=f"Collecting financial data for {tickers_str}...",
            )
        )

        chat_model = self.get_chat_model(agent_id, schema)
        data_collector = create_react_agent(
            model=chat_model,
            tools=self._build_tools(),
            prompt=state["data_collector_system_prompt"],
        )
        response = data_collector.invoke(state)

        # Extract the final summary (last AI message) from the react agent
        collected_data = (
            response["messages"][-1].content if response["messages"] else ""
        )

        self.logger.info(f"Agent[{agent_id}] -> Data Collector -> Complete")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Financial data collected.",
            )
        )
        return Command(
            update={
                "messages": [AIMessage(content=collected_data, name="data_collector")]
            },
            goto="fundamental_analyst",
        )

    def get_fundamental_analyst(
        self, state: FinancialAnalystState
    ) -> Command[Literal["technical_analyst"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Fundamental Analyst")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Running fundamental analysis...",
            )
        )

        # Pass collected data + X-Ray text context
        data_msg = self._get_last_named_message(state["messages"], "data_collector")
        xray_msg = self._get_last_named_message(state["messages"], "portfolio_xray")
        data_content = data_msg.content if data_msg else ""
        if xray_msg:
            data_content += f"\n\n{xray_msg.content}"
        messages = [HumanMessage(content=data_content)]

        response = self._invoke_chain(
            agent_id, schema, state["fundamental_analyst_system_prompt"], messages
        )

        self.logger.info(f"Agent[{agent_id}] -> Fundamental Analyst -> Complete")
        return Command(
            update={
                "messages": [
                    AIMessage(content=response.content, name="fundamental_analyst")
                ],
                "fundamental_recommendation": response.content,
            },
            goto="technical_analyst",
        )

    def get_technical_analyst(
        self, state: FinancialAnalystState
    ) -> Command[Literal["consensus_reporter"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Technical Analyst")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Running technical analysis...",
            )
        )

        # Pass collected data + X-Ray text context
        data_msg = self._get_last_named_message(state["messages"], "data_collector")
        xray_msg = self._get_last_named_message(state["messages"], "portfolio_xray")
        data_content = data_msg.content if data_msg else ""
        if xray_msg:
            data_content += f"\n\n{xray_msg.content}"
        messages = [HumanMessage(content=data_content)]

        response = self._invoke_chain(
            agent_id, schema, state["technical_analyst_system_prompt"], messages
        )

        self.logger.info(f"Agent[{agent_id}] -> Technical Analyst -> Complete")
        return Command(
            update={
                "messages": [
                    AIMessage(content=response.content, name="technical_analyst")
                ],
                "technical_recommendation": response.content,
            },
            goto="consensus_reporter",
        )

    @staticmethod
    def _extract_executive_summary(html: str) -> str:
        match = re.search(r"<blockquote>(.*?)</blockquote>", html, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_allocation(html: str) -> dict:
        """Extract allocation weights from ALLOCATION: TICKER=XX,... in report HTML."""
        match = re.search(r"ALLOCATION:\s*([\w=,.\s()]+)", html)
        if not match:
            return {}
        weights = {}
        for pair in match.group(1).strip().split(","):
            pair = pair.strip()
            if "=" in pair:
                ticker, pct = pair.split("=", 1)
                # Strip parentheses in case LLM wraps ticker as (SYMBOL)
                ticker = ticker.strip().strip("()")
                try:
                    weights[ticker] = float(pct.strip().strip("()"))
                except ValueError:
                    continue
        return weights

    def get_consensus_reporter(self, state: FinancialAnalystState):
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Consensus Reporter")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Building consensus and formatting final report...",
            )
        )

        # Pass analyst recommendations + X-Ray text — stripped of markdown
        fundamental = self._strip_markdown_fences(state["fundamental_recommendation"])
        technical = self._strip_markdown_fences(state["technical_recommendation"])
        xray_msg = self._get_last_named_message(state["messages"], "portfolio_xray")
        input_parts = [
            f"FUNDAMENTAL ANALYSIS:\n{fundamental}",
            f"TECHNICAL ANALYSIS:\n{technical}",
        ]
        if xray_msg:
            input_parts.append(xray_msg.content)
        messages = [HumanMessage(content="\n\n".join(input_parts))]

        response = self._invoke_chain(
            agent_id, schema, state["consensus_reporter_system_prompt"], messages
        )

        report_html = self._strip_markdown_fences(response.content)
        executive_summary = self._extract_executive_summary(report_html)
        allocation = self._extract_allocation(report_html)

        self.logger.info(f"Agent[{agent_id}] -> Consensus Reporter -> Complete")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=executive_summary[:200]
                if executive_summary
                else report_html[:200],
            )
        )
        return {
            "messages": [AIMessage(content=report_html, name="consensus_reporter")],
            "consensus_verdict": report_html,
            "executive_summary": executive_summary,
            "allocation_weights": json.dumps(allocation) if allocation else "",
        }

    def get_portfolio_xray(self, state: FinancialAnalystState):
        agent_id = state["agent_id"]
        tickers = state["tickers"]

        if not tickers:
            return {"portfolio_xray_html": ""}

        self.logger.info(f"Agent[{agent_id}] -> Portfolio X-Ray")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Generating Portfolio X-Ray...",
            )
        )

        # Runs before analysts — always equal-weight at this stage
        xray_data = compute_xray_data(self.markets_stats_service, tickers)
        xray_html = format_xray_html(xray_data)
        xray_text = format_xray_text(xray_data)

        self.logger.info(f"Agent[{agent_id}] -> Portfolio X-Ray -> Complete")
        return {
            "portfolio_xray_html": xray_html,
            "messages": [AIMessage(content=xray_text, name="portfolio_xray")],
        }

    def format_response(self, workflow_state: MessagesState) -> (str, dict):
        consensus_html = workflow_state.get("consensus_verdict", "")
        xray_html = workflow_state.get("portfolio_xray_html", "")
        executive_summary = workflow_state.get("executive_summary", "")

        if consensus_html:
            # Batch mode: X-Ray first, then consensus report
            if xray_html:
                report_html = xray_html + "\n<hr>\n" + consensus_html
            else:
                report_html = consensus_html
        else:
            # QA mode: use last message content
            report_html = workflow_state["messages"][-1].content

        response_data = {
            "executive_summary": executive_summary,
            "report_html": report_html,
            "fundamental_recommendation": workflow_state.get(
                "fundamental_recommendation", ""
            ),
            "technical_recommendation": workflow_state.get(
                "technical_recommendation", ""
            ),
            "consensus_verdict": consensus_html,
            "allocation_weights": workflow_state.get("allocation_weights", ""),
            "portfolio_xray_html": xray_html,
            "messages": [
                json.loads(message.model_dump_json())
                for message in workflow_state["messages"]
            ],
        }
        return report_html, response_data

    # --- Abstract method stubs (not used — graph uses deterministic edges) ---

    def get_planner(
        self, state: FinancialAnalystState
    ) -> Command[Literal["supervisor"]]:
        return Command(goto="supervisor")

    def get_supervisor(self, state: FinancialAnalystState) -> Command:
        return Command(goto=END)

    def get_reporter(
        self, state: FinancialAnalystState
    ) -> Command[Literal["supervisor"]]:
        return Command(goto="supervisor")
