import json
from datetime import datetime, timedelta

from langchain_core.tools import tool

from app.services.markets_insights import MarketsInsightsService
from app.services.markets_news import MarketsNewsService


def build_get_markets_news_tool(markets_news_service: MarketsNewsService):
    @tool("get_markets_news")
    def get_markets_news(
        search_term: str = "",
        ticker: str = "",
        days: int = 1,
        size: int = 50,
    ) -> str:
        """Fetch recent market news articles.

        Args:
            search_term: Optional search term to filter news (e.g. sector, company, topic).
            ticker: Optional stock ticker symbol to filter by (e.g. AAPL, MSFT, NVDA).
            days: Number of days to look back (default 1).
            size: Number of articles to fetch (default 50, max 50).

        Returns:
            JSON string with the list of news articles.
        """
        actual_size = min(size, 50)
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        results, _ = markets_news_service.get_news(
            index_name="quaks_markets-news_latest",
            search_term=search_term if search_term else None,
            key_ticker=ticker if ticker else None,
            date_from=date_from,
            size=actual_size,
            include_text_content=True,
            include_key_ticker=True,
        )
        articles = []
        for hit in results:
            source = hit["_source"]
            articles.append({
                "headline": source.get("text_headline", ""),
                "summary": source.get("text_summary", ""),
                "content": source.get("text_content", ""),
                "source": source.get("key_source", ""),
                "date": source.get("date_reference", ""),
                "tickers": source.get("key_ticker", []),
            })
        return json.dumps(articles, ensure_ascii=False)

    return get_markets_news


def build_get_insights_news_tool(markets_insights_service: MarketsInsightsService):
    @tool("get_insights_news")
    def get_insights_news(
        date_from: str = "",
        size: int = 5,
    ) -> str:
        """Fetch AI-generated investor briefings.

        Args:
            date_from: Optional start date filter in yyyy-mm-dd format.
            size: Number of briefings to fetch (default 5, max 10).

        Returns:
            JSON string with the list of investor briefings.
        """
        actual_size = min(size, 10)
        results, _ = markets_insights_service.get_insights_news(
            index_name="quaks_insights-news",
            date_from=date_from if date_from else None,
            size=actual_size,
            include_report_html=True,
        )
        briefings = []
        for hit in results:
            source = hit["_source"]
            briefings.append({
                "date": source.get("date_reference", ""),
                "executive_summary": source.get("text_executive_summary", ""),
                "report_html": source.get("text_report_html", ""),
            })
        return json.dumps(briefings, ensure_ascii=False)

    return get_insights_news
