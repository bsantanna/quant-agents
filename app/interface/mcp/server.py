from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastmcp import FastMCP
from mcp.types import Icon

from app.interface.mcp.registrar import McpRegistrar

if TYPE_CHECKING:
    from app.core.container import Container


_SERVER_INSTRUCTIONS = """Quaks is a multi-agent financial intelligence platform.

Available tools:
- get_agent_list: Discover AI agents available on the platform.
- get_markets_news_mcp: Search and retrieve market news articles filtered by ticker, topic, or date range.
- get_insights_news_mcp: Retrieve AI-generated investor briefings with executive summaries.
- publish_content_mcp: Publish AI-generated content (reports, briefings) to the platform. Requires authentication. Content must be in HTML format.
- read_prompt_mcp: Load a Quaks workflow system prompt by name (universal, tool-based way to load prompts that are also exposed as MCP prompts and as resources at uri prompt://<name>). Use this inside multi-step skills to fetch the system prompt for the current step when your client does not surface MCP prompts/resources as model-callable.
- fetch_company_profile_mcp: Fetch company metadata, valuation multiples, profitability, growth, analyst ratings, and ownership data for a single ticker.
- fetch_stats_close_mcp: Fetch latest OHLCV price stats and percent variance for a single ticker over a date range.
- fetch_technical_indicators_mcp: Fetch RSI, MACD, EMA crossover, and ADX indicators for a single ticker over a date range.
- fetch_portfolio_xray_mcp: Generate a Morningstar-style Portfolio X-Ray for a list of tickers (style box, sectors, regions, weighted-average stats).

Available prompts (news_analyst workflow):
- news_analyst_coordinator: System prompt for the coordinator step — answers user questions directly (QA mode) or routes to the aggregator for briefing generation.
- news_analyst_aggregator: System prompt for the aggregator step — collects and prioritizes market news by economic impact. Use with get_markets_news_mcp tool.
- news_analyst_reporter: System prompt for the reporter step — groups articles, writes summaries, and produces the final HTML briefing.

Available prompts (financial_analyst_v1 workflow):
- financial_analyst_v1_coordinator: System prompt for the coordinator step — answers investment questions directly, or routes batch requests (prefixed 'BATCH_ETL') to the data collector.
- financial_analyst_v1_data_collector: System prompt for the data collector step — fetches company profile, price stats, technical indicators, and news for each ticker. Use with fetch_company_profile_mcp, fetch_stats_close_mcp, fetch_technical_indicators_mcp, and get_markets_news_mcp.
- financial_analyst_v1_fundamental_analyst: System prompt for the fundamental analyst step — produces a BUY/HOLD/SELL recommendation per ticker from valuation, profitability, growth, and risk analysis.
- financial_analyst_v1_technical_analyst: System prompt for the technical analyst step — produces a BUY/HOLD/SELL recommendation per ticker from ADX, EMA, RSI, and MACD signals.
- financial_analyst_v1_consensus_reporter: System prompt for the consensus reporter step — merges both recommendations, allocates USD 10,000 across tickers, and produces the final HTML report with an ALLOCATION: line.

To replicate the full News Analyst workflow:
1. Use news_analyst_coordinator prompt with user's question. If the user wants a briefing, proceed to step 2.
2. Use news_analyst_aggregator prompt + get_markets_news_mcp tool to collect and prioritize news.
3. Use news_analyst_reporter prompt with the aggregated news to produce the final HTML briefing.

To replicate the full Financial Analyst workflow (pass tickers to each prompt):
1. Use financial_analyst_v1_coordinator with the user's question. If the user wants full analysis, proceed to step 2.
2. Use financial_analyst_v1_data_collector + fetch_company_profile_mcp, fetch_stats_close_mcp, fetch_technical_indicators_mcp, and get_markets_news_mcp to collect data per ticker.
3. Call fetch_portfolio_xray_mcp to get a Morningstar-style portfolio breakdown.
4. Use financial_analyst_v1_fundamental_analyst with the collected data to produce fundamental recommendations.
5. Use financial_analyst_v1_technical_analyst with the indicator data to produce technical recommendations.
6. Use financial_analyst_v1_consensus_reporter to merge both views into the final HTML report.

Pagination: The news tools return a `cursor` field. To get the next page, pass the cursor value back in the next call. When cursor is null, there are no more results.

Date format: All dates use yyyy-mm-dd format (e.g. 2025-01-15).
"""


def build_mcp_server(
    container: Container,
    registrars: list[McpRegistrar],
) -> FastMCP:
    config = container.config()
    auth = _build_auth(config)

    base_url = config.get("api_base_url", "")
    mcp = FastMCP(
        name=os.getenv("SERVICE_NAME", "Quaks"),
        version=os.getenv("SERVICE_VERSION", "snapshot"),
        instructions=_SERVER_INSTRUCTIONS,
        auth=auth,
        icons=[Icon(src=f"{base_url}/logo.svg", mimeType="image/svg+xml")],
    )

    for registrar in registrars:
        registrar.register_tools(mcp, container)
        registrar.register_prompts(mcp)
        registrar.register_resources(mcp)

    return mcp


def _build_auth(config: dict):
    if not config["auth"]["enabled"]:
        return None

    from cryptography.fernet import Fernet
    from fastmcp.server.auth import OAuthProxy
    from fastmcp.server.auth.jwt_issuer import derive_jwt_key
    from fastmcp.server.auth.providers.jwt import JWTVerifier
    from key_value.aio.stores.redis import RedisStore
    from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

    auth_url = config["auth"]["url"]
    realm = config["auth"]["realm"]
    realm_base = f"{auth_url}/realms/{realm}"
    upstream_client_secret = config["auth"]["client_secret"]

    jwt_signing_key = derive_jwt_key(
        high_entropy_material=upstream_client_secret,
        salt="fastmcp-jwt-signing-key",
    )
    storage_encryption_key = derive_jwt_key(
        high_entropy_material=jwt_signing_key.decode(),
        salt="fastmcp-storage-encryption-key",
    )

    client_storage = FernetEncryptionWrapper(
        key_value=RedisStore(url=config["broker"]["url"]),
        fernet=Fernet(key=storage_encryption_key),
        raise_on_decryption_error=False,
    )

    return OAuthProxy(
        upstream_authorization_endpoint=f"{realm_base}/protocol/openid-connect/auth",
        upstream_token_endpoint=f"{realm_base}/protocol/openid-connect/token",
        upstream_client_id=config["auth"]["client_id"],
        upstream_client_secret=upstream_client_secret,
        token_verifier=JWTVerifier(
            jwks_uri=f"{realm_base}/protocol/openid-connect/certs",
            issuer=realm_base,
            audience="account",
            required_scopes=["openid", "profile", "email"],
        ),
        base_url=f"{config['api_base_url']}/mcp",
        client_storage=client_storage,
    )
