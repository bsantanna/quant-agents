from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Optional

from fastmcp import FastMCP
from pydantic import Field

from app.interface.mcp.prompt_registry import PromptRegistry
from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.user_prompt_resolver import UserPromptResolver
from app.services.agent_types.quaks.insights.financial_analyst.v1.company_profile_summary import (
    summarize_company_profile,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.indicators_summary import (
    summarize_technical_indicators,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.portfolio_xray import (
    compute_xray_data,
    format_xray_text,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.prompts import (
    CONSENSUS_REPORTER_SYSTEM_PROMPT,
    COORDINATOR_SYSTEM_PROMPT,
    DATA_COLLECTOR_SYSTEM_PROMPT,
    FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
    TECHNICAL_ANALYST_SYSTEM_PROMPT,
)

if TYPE_CHECKING:
    from app.core.container import Container

_AGENT_TYPE = "quaks_financial_analyst_v1"

_ROLE_SETTING_KEYS = {
    "coordinator": "coordinator_system_prompt",
    "data_collector": "data_collector_system_prompt",
    "fundamental_analyst": "fundamental_analyst_system_prompt",
    "technical_analyst": "technical_analyst_system_prompt",
    "consensus_reporter": "consensus_reporter_system_prompt",
}

_DEFAULT_TEMPLATES = {
    "coordinator": COORDINATOR_SYSTEM_PROMPT,
    "data_collector": DATA_COLLECTOR_SYSTEM_PROMPT,
    "fundamental_analyst": FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
    "technical_analyst": TECHNICAL_ANALYST_SYSTEM_PROMPT,
    "consensus_reporter": CONSENSUS_REPORTER_SYSTEM_PROMPT,
}

_ROLE_PROMPT_NAMES = {
    "coordinator": "financial_analyst_v1_coordinator",
    "data_collector": "financial_analyst_v1_data_collector",
    "fundamental_analyst": "financial_analyst_v1_fundamental_analyst",
    "technical_analyst": "financial_analyst_v1_technical_analyst",
    "consensus_reporter": "financial_analyst_v1_consensus_reporter",
}

_EXECUTION_PLAN_BLOCK = re.compile(r"## Execution Plan\n\{\{ EXECUTION_PLAN \}\}\n\n?")


def _strip_execution_plan(text: str) -> str:
    return _EXECUTION_PLAN_BLOCK.sub("", text)


class FinancialAnalystV1ToolRegistrar(McpRegistrar):
    """Registers MCP tools, prompts, and resources for the quaks_financial_analyst_v1 agent."""

    def __init__(
        self,
        user_prompt_resolver: UserPromptResolver,
        prompt_registry: PromptRegistry,
    ) -> None:
        self._user_prompt_resolver = user_prompt_resolver
        for role, prompt_name in _ROLE_PROMPT_NAMES.items():
            prompt_registry.register(
                prompt_name,
                lambda role=role, **_: self._resolve_prompt(role),
            )

    def _resolve_prompt(self, role: str) -> str:
        template = self._user_prompt_resolver.resolve(
            agent_type=_AGENT_TYPE,
            setting_key=_ROLE_SETTING_KEYS[role],
            default_template=_DEFAULT_TEMPLATES[role],
        )
        return _strip_execution_plan(template)

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        @mcp.tool(
            name="fetch_company_profile_mcp",
            description="Fetch company metadata, valuation multiples "
            "(P/E, forward P/E, P/B, P/S), profitability (margins, ROE, ROA), "
            "growth rates, analyst ratings, dividend yield, market cap, beta, "
            "52-week high/low, sector, country, and ownership data for a single "
            "stock ticker. Source: Elasticsearch metadata index.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_company_profile_mcp(
            ticker: Annotated[
                str,
                Field(description="Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'NVDA')"),
            ],
        ) -> dict:
            svc = container.markets_stats_service()
            doc = svc.get_company_profile(
                index_name="quaks_stocks-metadata_latest",
                key_ticker=ticker.upper(),
            )
            return summarize_company_profile(doc)

        @mcp.tool(
            name="fetch_stats_close_mcp",
            description="Fetch latest OHLCV price stats and percent variance over "
            "a date range for a single stock ticker. Defaults to the last 365 days. "
            "Source: Elasticsearch EOD index.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_stats_close_mcp(
            ticker: Annotated[
                str,
                Field(description="Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'NVDA')"),
            ],
            start_date: Annotated[
                Optional[str],
                Field(
                    description="Start date in yyyy-mm-dd format. Defaults to 365 days ago."
                ),
            ] = None,
            end_date: Annotated[
                Optional[str],
                Field(description="End date in yyyy-mm-dd format. Defaults to today."),
            ] = None,
        ) -> dict:
            svc = container.markets_stats_service()
            resolved_end = end_date or datetime.now().strftime("%Y-%m-%d")
            resolved_start = start_date or (
                datetime.now() - timedelta(days=365)
            ).strftime("%Y-%m-%d")
            return svc.get_stats_close(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker.upper(),
                start_date=resolved_start,
                end_date=resolved_end,
            )

        @mcp.tool(
            name="fetch_technical_indicators_mcp",
            description="Fetch technical indicators (RSI-14, MACD 12/26/9, "
            "EMA 10/20 crossover, ADX-14) for a single stock ticker over "
            "a date range. Defaults to the last 365 days. "
            "Source: Elasticsearch EOD index.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_technical_indicators_mcp(
            ticker: Annotated[
                str,
                Field(description="Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'NVDA')"),
            ],
            start_date: Annotated[
                Optional[str],
                Field(
                    description="Start date in yyyy-mm-dd format. Defaults to 365 days ago."
                ),
            ] = None,
            end_date: Annotated[
                Optional[str],
                Field(description="End date in yyyy-mm-dd format. Defaults to today."),
            ] = None,
        ) -> dict:
            svc = container.markets_stats_service()
            resolved_end = end_date or datetime.now().strftime("%Y-%m-%d")
            resolved_start = start_date or (
                datetime.now() - timedelta(days=365)
            ).strftime("%Y-%m-%d")
            index_name = "quaks_stocks-eod_latest"
            key = ticker.upper()
            rsi = svc.get_indicator_rsi(
                index_name=index_name,
                key_ticker=key,
                start_date=resolved_start,
                end_date=resolved_end,
                period=14,
            )
            macd = svc.get_indicator_macd(
                index_name=index_name,
                key_ticker=key,
                start_date=resolved_start,
                end_date=resolved_end,
                short_window=12,
                long_window=26,
                signal_window=9,
            )
            ema = svc.get_indicator_ema(
                index_name=index_name,
                key_ticker=key,
                start_date=resolved_start,
                end_date=resolved_end,
                short_window=10,
                long_window=20,
            )
            adx = svc.get_indicator_adx(
                index_name=index_name,
                key_ticker=key,
                start_date=resolved_start,
                end_date=resolved_end,
                period=14,
            )
            return summarize_technical_indicators(rsi, macd, ema, adx)

        @mcp.tool(
            name="fetch_portfolio_xray_mcp",
            description="Generate a Morningstar-style Portfolio X-Ray for a list "
            "of stock tickers: investment style box (size x value/growth), sector "
            "breakdown (Cyclical/Sensitive/Defensive), world region exposure, "
            "weighted-average stats (P/E, P/B, margins, ROE, beta), and top holdings. "
            "Uses equal weighting across tickers. Returns a compact text summary.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_portfolio_xray_mcp(
            tickers: Annotated[
                str,
                Field(
                    description="Comma-separated stock ticker symbols (e.g. 'AAPL,MSFT,NVDA')"
                ),
            ],
        ) -> str:
            svc = container.markets_stats_service()
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
            data = compute_xray_data(svc, ticker_list)
            return format_xray_text(data)

    def register_prompts(self, mcp: FastMCP) -> None:
        @mcp.prompt(
            name="financial_analyst_v1_coordinator",
            description="System prompt for the Financial Analyst coordinator step. "
            "Returns the raw template; the model substitutes any "
            "{{ CURRENT_TIME }} / {{ TICKERS }} placeholders locally before use.",
        )
        def financial_analyst_v1_coordinator() -> str:
            return self._resolve_prompt("coordinator")

        @mcp.prompt(
            name="financial_analyst_v1_data_collector",
            description="System prompt for the Financial Analyst data collector step. "
            "Returns the raw template; the model substitutes any "
            "{{ CURRENT_TIME }} / {{ TICKERS }} placeholders locally before use.",
        )
        def financial_analyst_v1_data_collector() -> str:
            return self._resolve_prompt("data_collector")

        @mcp.prompt(
            name="financial_analyst_v1_fundamental_analyst",
            description="System prompt for the Financial Analyst fundamental analyst step. "
            "Returns the raw template; the model substitutes any "
            "{{ CURRENT_TIME }} / {{ TICKERS }} placeholders locally before use.",
        )
        def financial_analyst_v1_fundamental_analyst() -> str:
            return self._resolve_prompt("fundamental_analyst")

        @mcp.prompt(
            name="financial_analyst_v1_technical_analyst",
            description="System prompt for the Financial Analyst technical analyst step. "
            "Returns the raw template; the model substitutes any "
            "{{ CURRENT_TIME }} / {{ TICKERS }} placeholders locally before use.",
        )
        def financial_analyst_v1_technical_analyst() -> str:
            return self._resolve_prompt("technical_analyst")

        @mcp.prompt(
            name="financial_analyst_v1_consensus_reporter",
            description="System prompt for the Financial Analyst consensus reporter step. "
            "Returns the raw template; the model substitutes any "
            "{{ CURRENT_TIME }} / {{ TICKERS }} placeholders locally before use.",
        )
        def financial_analyst_v1_consensus_reporter() -> str:
            return self._resolve_prompt("consensus_reporter")

    def register_resources(self, mcp: FastMCP) -> None:
        @mcp.resource(
            uri="prompt://financial_analyst_v1_coordinator",
            name="financial_analyst_v1_coordinator",
            description="System prompt for the Financial Analyst coordinator step.",
        )
        def resource_coordinator() -> str:
            return self._resolve_prompt("coordinator")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_data_collector",
            name="financial_analyst_v1_data_collector",
            description="System prompt for the Financial Analyst data collector step.",
        )
        def resource_data_collector() -> str:
            return self._resolve_prompt("data_collector")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_fundamental_analyst",
            name="financial_analyst_v1_fundamental_analyst",
            description="System prompt for the Financial Analyst fundamental analyst step.",
        )
        def resource_fundamental_analyst() -> str:
            return self._resolve_prompt("fundamental_analyst")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_technical_analyst",
            name="financial_analyst_v1_technical_analyst",
            description="System prompt for the Financial Analyst technical analyst step.",
        )
        def resource_technical_analyst() -> str:
            return self._resolve_prompt("technical_analyst")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_consensus_reporter",
            name="financial_analyst_v1_consensus_reporter",
            description="System prompt for the Financial Analyst consensus reporter step.",
        )
        def resource_consensus_reporter() -> str:
            return self._resolve_prompt("consensus_reporter")
