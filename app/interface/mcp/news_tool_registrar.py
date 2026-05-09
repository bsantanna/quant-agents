from __future__ import annotations

from datetime import datetime, timedelta
from html import unescape
from typing import TYPE_CHECKING, Annotated, Optional

from fastmcp import FastMCP
from jinja2.sandbox import SandboxedEnvironment
from pydantic import Field

from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.schema import (
    InsightsNewsItem,
    InsightsNewsList,
    NewsItem,
    NewsList,
)
from app.interface.mcp.user_prompt_resolver import UserPromptResolver
from app.services.agent_types.quaks.insights.news.prompts import (
    AGGREGATOR_SYSTEM_PROMPT,
    COORDINATOR_SYSTEM_PROMPT,
    EXECUTION_PLAN,
    REPORTER_SYSTEM_PROMPT,
)

if TYPE_CHECKING:
    from app.core.container import Container

_AGENT_TYPE = "quaks_news_analyst"

_ROLE_SETTING_KEYS = {
    "coordinator": "coordinator_system_prompt",
    "aggregator": "aggregator_system_prompt",
    "reporter": "reporter_system_prompt",
}

_DEFAULT_TEMPLATES = {
    "coordinator": COORDINATOR_SYSTEM_PROMPT,
    "aggregator": AGGREGATOR_SYSTEM_PROMPT,
    "reporter": REPORTER_SYSTEM_PROMPT,
}


_JINJA_ENV = SandboxedEnvironment()


def _render_prompt(template_str: str, current_time: str | None = None) -> str:
    if current_time is not None and not current_time.strip():
        raise ValueError("current_time must be a non-empty string when provided")
    template = _JINJA_ENV.from_string(template_str)
    resolved_time = current_time or datetime.now().strftime("%a %b %d %Y %H:%M:%S %z")
    return template.render(
        CURRENT_TIME=resolved_time,
        EXECUTION_PLAN=EXECUTION_PLAN,
    )


class NewsToolRegistrar(McpRegistrar):
    """Registers news-related MCP tools, prompts, and resources."""

    def __init__(self, user_prompt_resolver: UserPromptResolver) -> None:
        self._user_prompt_resolver = user_prompt_resolver

    def _resolve_prompt(self, role: str, current_time: str | None = None) -> str:
        return self._user_prompt_resolver.resolve(
            agent_type=_AGENT_TYPE,
            setting_key=_ROLE_SETTING_KEYS[role],
            default_template=_DEFAULT_TEMPLATES[role],
            render=lambda t: _render_prompt(t, current_time=current_time),
        )

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        @mcp.tool(
            name="get_markets_news_mcp",
            description="Search and retrieve recent market news articles. "
            "Articles include headline, summary, source, date, and related "
            "ticker symbols. Results are optimized for LLM consumption. "
            "Supports filtering by ticker symbol, free-text search, and "
            "date range. Returns up to 15 articles per page with cursor-based "
            "pagination. Full article text is omitted by default to keep "
            "listings lean — pass `id` to fetch a single article in full, "
            "or set `include_content=true` to force full content in batch "
            "responses. When `id` is provided, all other filters are ignored.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def get_markets_news_mcp(
            id: Annotated[
                Optional[str],
                Field(
                    description="Fetch a single article by its document id. "
                    "When set, all other filters are ignored and full content "
                    "is always returned."
                ),
            ] = None,
            search_term: Annotated[
                Optional[str],
                Field(
                    description="Free-text search filter (e.g. 'artificial intelligence', 'earnings')"
                ),
            ] = None,
            key_ticker: Annotated[
                Optional[str],
                Field(
                    description="Stock ticker symbol to filter by (e.g. 'AAPL', 'MSFT', 'NVDA')"
                ),
            ] = None,
            date_from: Annotated[
                Optional[str],
                Field(
                    description="Start date filter in yyyy-mm-dd format. Defaults to yesterday."
                ),
            ] = None,
            date_to: Annotated[
                Optional[str],
                Field(
                    description="End date filter in yyyy-mm-dd format. Defaults to today."
                ),
            ] = None,
            cursor: Annotated[
                Optional[str],
                Field(
                    description="Pagination cursor from a previous response to fetch the next page"
                ),
            ] = None,
            size: Annotated[
                int,
                Field(description="Number of articles to return (1-15)", ge=1, le=15),
            ] = 3,
            include_content: Annotated[
                bool,
                Field(
                    description="Set to true to include full article text in each result. "
                    "Off by default because article text is bulky. Automatically enabled "
                    "when fetching a single article by id."
                ),
            ] = False,
        ) -> NewsList:
            svc = container.markets_news_service()
            resolved_from = (
                None
                if id
                else date_from
                or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            )
            content_requested = include_content or id is not None

            results, sort = svc.get_news(
                index_name="quaks_markets-news_latest",
                id=id,
                search_term=search_term,
                key_ticker=key_ticker,
                date_from=resolved_from,
                date_to=date_to,
                size=min(max(size, 1), 15),
                cursor=cursor,
                include_text_content=content_requested,
                include_key_ticker=True,
            )

            items = [
                NewsItem(
                    id=h.get("_id"),
                    headline=unescape(h["_source"].get("text_headline") or ""),
                    summary=unescape(h["_source"].get("text_summary") or ""),
                    content=unescape(h["_source"].get("text_content") or "")
                    if content_requested
                    else None,
                    source=h["_source"].get("key_source", ""),
                    date=h["_source"].get("date_reference", ""),
                    tickers=h["_source"].get("key_ticker"),
                )
                for h in results
            ]
            return NewsList(items=items, cursor=sort)

        @mcp.tool(
            name="get_insights_news_mcp",
            description="Retrieve AI-generated investor briefings produced by "
            "Quaks analyst agents. Each briefing contains an executive summary "
            "and optionally the full HTML report. Use this to get synthesized "
            "market intelligence and analysis. Returns up to 15 briefings "
            "per page with cursor-based pagination. When `id` is provided, "
            "fetches that single briefing and ignores all other filters.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def get_insights_news_mcp(
            id: Annotated[
                Optional[str],
                Field(
                    description="Fetch a single briefing by its document id. "
                    "When set, all other filters are ignored."
                ),
            ] = None,
            date_from: Annotated[
                Optional[str],
                Field(description="Start date filter in yyyy-mm-dd format"),
            ] = None,
            date_to: Annotated[
                Optional[str],
                Field(description="End date filter in yyyy-mm-dd format"),
            ] = None,
            cursor: Annotated[
                Optional[str],
                Field(
                    description="Pagination cursor from a previous response to fetch the next page"
                ),
            ] = None,
            size: Annotated[
                int,
                Field(description="Number of briefings to return (1-15)", ge=1, le=15),
            ] = 3,
            include_report_html: Annotated[
                bool,
                Field(
                    description="Set to true to include the full HTML report in each briefing. "
                    "Increases response size significantly."
                ),
            ] = False,
        ) -> InsightsNewsList:
            svc = container.markets_insights_service()

            results, sort = svc.get_insights_news(
                index_name="quaks_insights-news",
                id=id,
                date_from=date_from,
                date_to=date_to,
                size=min(max(size, 1), 15),
                cursor=cursor,
                include_report_html=include_report_html,
            )

            items = [
                InsightsNewsItem(
                    id=h.get("_id"),
                    date=h["_source"].get("date_reference", ""),
                    executive_summary=unescape(
                        h["_source"].get("text_executive_summary") or ""
                    ),
                    report_html=unescape(h["_source"].get("text_report_html") or "")
                    if include_report_html
                    else None,
                    language_model_name=h["_source"].get("key_language_model_name"),
                )
                for h in results
            ]
            return InsightsNewsList(items=items, cursor=sort)

    def register_prompts(self, mcp: FastMCP) -> None:
        @mcp.prompt(
            name="news_analyst_coordinator",
            description="System prompt for the News Analyst coordinator step. "
            "In QA mode, this prompt instructs the LLM to answer financial "
            "questions using investor briefings from get_insights_news_mcp. "
            "In briefing mode (input 'BATCH_ETL'), it routes to the aggregator. "
            "Returns a ready-to-use system prompt with current timestamp.",
        )
        def news_analyst_coordinator(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt (e.g. 'Mon Apr 06 2026 18:46:44'). Defaults to server time."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt("coordinator", current_time=current_time)

        @mcp.prompt(
            name="news_analyst_aggregator",
            description="System prompt for the News Analyst aggregator step. "
            "Instructs the LLM to collect market news via get_markets_news_mcp, "
            "sort articles by economic impact, and write a market mood summary. "
            "Returns a ready-to-use system prompt with current timestamp and execution plan.",
        )
        def news_analyst_aggregator(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt (e.g. 'Mon Apr 06 2026 18:46:44'). Defaults to server time."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt("aggregator", current_time=current_time)

        @mcp.prompt(
            name="news_analyst_reporter",
            description="System prompt for the News Analyst reporter step. "
            "Instructs the LLM to group aggregated articles by topic, write "
            "4-paragraph summaries (what happened, why it matters, bigger picture, "
            "what to watch), and produce the final investor briefing in HTML format. "
            "Returns a ready-to-use system prompt with current timestamp and execution plan.",
        )
        def news_analyst_reporter(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt (e.g. 'Mon Apr 06 2026 18:46:44'). Defaults to server time."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt("reporter", current_time=current_time)

    def register_resources(self, mcp: FastMCP) -> None:
        @mcp.resource(
            uri="prompt://news_analyst_coordinator",
            name="news_analyst_coordinator",
            description="System prompt for the News Analyst coordinator step.",
        )
        def resource_coordinator() -> str:
            return self._resolve_prompt("coordinator")

        @mcp.resource(
            uri="prompt://news_analyst_aggregator",
            name="news_analyst_aggregator",
            description="System prompt for the News Analyst aggregator step.",
        )
        def resource_aggregator() -> str:
            return self._resolve_prompt("aggregator")

        @mcp.resource(
            uri="prompt://news_analyst_reporter",
            name="news_analyst_reporter",
            description="System prompt for the News Analyst reporter step.",
        )
        def resource_reporter() -> str:
            return self._resolve_prompt("reporter")
