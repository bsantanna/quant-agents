from unittest.mock import MagicMock

import pytest

from app.interface.mcp.financial_analyst_v1_tool_registrar import (
    FinancialAnalystV1ToolRegistrar,
    _strip_execution_plan,
)
from app.interface.mcp.prompt_registry import PromptRegistry


def _passthrough_resolver():
    """Resolver mock that always returns the default template (no override)."""
    resolver = MagicMock()
    resolver.resolve.side_effect = lambda agent_type, setting_key, default_template: (
        default_template
    )
    return resolver


def _capturing_mcp():
    """Return (mcp_mock, tools, prompts, resources) where each dict captures fn by name."""
    tools: dict = {}
    prompts: dict = {}
    resources: dict = {}

    def tool(**kwargs):
        def inner(fn):
            tools[kwargs["name"]] = fn
            return fn

        return inner

    def prompt(**kwargs):
        def inner(fn):
            prompts[kwargs["name"]] = fn
            return fn

        return inner

    def resource(**kwargs):
        def inner(fn):
            resources[kwargs["name"]] = fn
            return fn

        return inner

    mcp = MagicMock()
    mcp.tool.side_effect = tool
    mcp.prompt.side_effect = prompt
    mcp.resource.side_effect = resource
    return mcp, tools, prompts, resources


class TestStripExecutionPlan:
    def test_strips_block(self):
        text = "Header\n\n## Execution Plan\n{{ EXECUTION_PLAN }}\n\nBody"
        assert _strip_execution_plan(text) == "Header\n\nBody"

    def test_no_block_leaves_text_untouched(self):
        text = "No placeholder here.\nJust text."
        assert _strip_execution_plan(text) == text

    def test_preserves_tickers_and_current_time(self):
        text = (
            "Current time: {{ CURRENT_TIME }}\n\n"
            "## Execution Plan\n{{ EXECUTION_PLAN }}\n\n"
            "Tickers: {{ TICKERS }}"
        )
        out = _strip_execution_plan(text)
        assert "{{ CURRENT_TIME }}" in out
        assert "{{ TICKERS }}" in out
        assert "EXECUTION_PLAN" not in out


class TestFinancialAnalystV1ToolRegistrar:
    def test_registers_tools(self):
        registrar = FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        )
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert "fetch_company_profile_mcp" in tool_names
        assert "fetch_stats_close_mcp" in tool_names
        assert "fetch_technical_indicators_mcp" in tool_names
        assert "fetch_portfolio_xray_mcp" in tool_names

    def test_registers_prompts(self):
        registrar = FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        )
        mcp = MagicMock()
        registrar.register_prompts(mcp)
        prompt_names = [call[1]["name"] for call in mcp.prompt.call_args_list]
        for role in (
            "coordinator",
            "data_collector",
            "fundamental_analyst",
            "technical_analyst",
            "consensus_reporter",
        ):
            assert f"financial_analyst_v1_{role}" in prompt_names

    def test_registers_resources(self):
        registrar = FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        )
        mcp = MagicMock()
        registrar.register_resources(mcp)
        resource_names = [call[1]["name"] for call in mcp.resource.call_args_list]
        for role in (
            "coordinator",
            "data_collector",
            "fundamental_analyst",
            "technical_analyst",
            "consensus_reporter",
        ):
            assert f"financial_analyst_v1_{role}" in resource_names

    def test_contributes_prompts_to_registry(self):
        registry = PromptRegistry()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver(), registry)
        for role in (
            "coordinator",
            "data_collector",
            "fundamental_analyst",
            "technical_analyst",
            "consensus_reporter",
        ):
            assert f"financial_analyst_v1_{role}" in registry

    def test_registry_resolve_returns_raw_template_minus_execution_plan(self):
        registry = PromptRegistry()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver(), registry)
        text = registry.resolve("financial_analyst_v1_data_collector")
        assert isinstance(text, str)
        assert text
        assert "{{ EXECUTION_PLAN }}" not in text
        assert "{{ CURRENT_TIME }}" in text
        assert "{{ TICKERS }}" in text


class TestFetchCompanyProfileMcp:
    @pytest.mark.asyncio
    async def test_calls_service_with_uppercased_ticker_and_summarizes(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_company_profile.return_value = {
            "key_ticker": "AAPL",
            "name": "Apple",
            "sector": "Technology",
            "description": "A long description that should be dropped",
            "pe_ratio": 30.0,
        }
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_tools(mcp, container)

        result = await tools["fetch_company_profile_mcp"](ticker="aapl")

        assert result["identity"]["ticker"] == "AAPL"
        assert result["identity"]["name"] == "Apple"
        assert result["identity"]["sector"] == "Technology"
        assert "description" not in str(result)
        call_kwargs = (
            container.markets_stats_service.return_value.get_company_profile.call_args[
                1
            ]
        )
        assert call_kwargs["key_ticker"] == "AAPL"
        assert call_kwargs["index_name"] == "quaks_stocks-metadata_latest"

    @pytest.mark.asyncio
    async def test_empty_doc_returns_empty_dict(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_company_profile.return_value = {}
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_tools(mcp, container)

        result = await tools["fetch_company_profile_mcp"](ticker="XYZ")
        assert result == {}


class TestFetchStatsCloseMcp:
    @pytest.mark.asyncio
    async def test_defaults_date_range(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_stats_close.return_value = {
            "latest_close": 100
        }
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_tools(mcp, container)

        result = await tools["fetch_stats_close_mcp"](ticker="AAPL")

        assert result == {"latest_close": 100}
        call_kwargs = (
            container.markets_stats_service.return_value.get_stats_close.call_args[1]
        )
        assert call_kwargs["start_date"] is not None
        assert call_kwargs["end_date"] is not None
        assert call_kwargs["key_ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_explicit_date_range(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_stats_close.return_value = {}
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_tools(mcp, container)

        await tools["fetch_stats_close_mcp"](
            ticker="MSFT", start_date="2026-01-01", end_date="2026-04-01"
        )

        call_kwargs = (
            container.markets_stats_service.return_value.get_stats_close.call_args[1]
        )
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-04-01"


class TestFetchTechnicalIndicatorsMcp:
    @pytest.mark.asyncio
    async def test_calls_all_four_indicators_and_summarizes(self):
        container = MagicMock()
        svc = container.markets_stats_service.return_value
        svc.get_indicator_rsi.return_value = [
            {"date": "2025-01-01", "rsi": 50.0, "position": 1},
            {"date": "2025-01-02", "rsi": 55.0, "position": 1},
        ]
        svc.get_indicator_macd.return_value = [
            {
                "date": "2025-01-01",
                "macd": 1.0,
                "signal": 0.5,
                "histogram": 0.5,
                "short_ema": 0.0,
                "long_ema": 0.0,
                "position": 1,
            }
        ]
        svc.get_indicator_ema.return_value = [
            {"date": "2025-01-01", "ema_short": 110.0, "ema_long": 105.0, "position": 1}
        ]
        svc.get_indicator_adx.return_value = [
            {
                "date": "2025-01-01",
                "adx": 30.0,
                "plus_di": 25.0,
                "minus_di": 15.0,
                "position": 1,
            }
        ]
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_tools(mcp, container)

        result = await tools["fetch_technical_indicators_mcp"](ticker="nvda")

        assert set(result.keys()) == {"rsi", "macd", "ema", "adx"}
        assert result["rsi"]["latest"]["value"] == 55.0
        assert result["rsi"]["latest"]["regime"] == "BULLISH"
        assert result["macd"]["latest"]["regime"] == "BULLISH"
        assert result["ema"]["latest"]["regime"] == "BULLISH"
        assert result["adx"]["latest"]["regime"] == "TRENDING"
        assert svc.get_indicator_rsi.call_args[1]["key_ticker"] == "NVDA"
        assert svc.get_indicator_rsi.call_args[1]["period"] == 14
        assert svc.get_indicator_macd.call_args[1]["short_window"] == 12
        assert svc.get_indicator_macd.call_args[1]["long_window"] == 26
        assert svc.get_indicator_macd.call_args[1]["signal_window"] == 9
        assert svc.get_indicator_ema.call_args[1]["short_window"] == 10
        assert svc.get_indicator_ema.call_args[1]["long_window"] == 20
        assert svc.get_indicator_adx.call_args[1]["period"] == 14


class TestFetchPortfolioXrayMcp:
    @pytest.mark.asyncio
    async def test_returns_text_summary(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_company_profile.return_value = {
            "name": "Apple",
            "sector": "Technology",
            "country": "US",
            "market_capitalization": 3_000_000_000_000,
            "pe_ratio": 30,
        }
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_tools(mcp, container)

        result = await tools["fetch_portfolio_xray_mcp"](tickers="aapl,msft")

        assert isinstance(result, str)
        assert "PORTFOLIO X-RAY" in result

    @pytest.mark.asyncio
    async def test_empty_profiles_returns_fallback(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_company_profile.return_value = {}
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_tools(mcp, container)

        result = await tools["fetch_portfolio_xray_mcp"](tickers="XXXX")

        assert result == "No metadata available."


class TestPromptsAndResources:
    _ROLES = (
        "coordinator",
        "data_collector",
        "fundamental_analyst",
        "technical_analyst",
        "consensus_reporter",
    )

    def test_prompt_functions_return_raw_strings(self):
        mcp, _, prompts, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_prompts(mcp)

        for role in self._ROLES:
            result = prompts[f"financial_analyst_v1_{role}"]()
            assert isinstance(result, str)
            assert result
            assert "{{ EXECUTION_PLAN }}" not in result

    def test_resource_functions_return_raw_strings(self):
        mcp, _, _, resources = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(
            _passthrough_resolver(), PromptRegistry()
        ).register_resources(mcp)

        for role in self._ROLES:
            result = resources[f"financial_analyst_v1_{role}"]()
            assert isinstance(result, str)
            assert result
            assert "{{ EXECUTION_PLAN }}" not in result


class TestUserOverrideWiring:
    """Verify each prompt/resource delegates to the resolver with the right keys."""

    _EXPECTED = [
        ("coordinator", "coordinator_system_prompt"),
        ("data_collector", "data_collector_system_prompt"),
        ("fundamental_analyst", "fundamental_analyst_system_prompt"),
        ("technical_analyst", "technical_analyst_system_prompt"),
        ("consensus_reporter", "consensus_reporter_system_prompt"),
    ]

    def test_prompts_call_resolver_with_role_specific_keys(self):
        resolver = MagicMock()
        resolver.resolve.return_value = "RESOLVED"
        mcp, _, prompts, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(resolver, PromptRegistry()).register_prompts(
            mcp
        )

        for role, setting_key in self._EXPECTED:
            resolver.resolve.reset_mock()
            result = prompts[f"financial_analyst_v1_{role}"]()
            assert result == "RESOLVED"
            kwargs = resolver.resolve.call_args.kwargs
            assert kwargs["agent_type"] == "quaks_financial_analyst_v1"
            assert kwargs["setting_key"] == setting_key
            assert kwargs["default_template"]
            assert "render" not in kwargs

    def test_resources_call_resolver_with_role_specific_keys(self):
        resolver = MagicMock()
        resolver.resolve.return_value = "RESOLVED"
        mcp, _, _, resources = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(resolver, PromptRegistry()).register_resources(
            mcp
        )

        for role, setting_key in self._EXPECTED:
            resolver.resolve.reset_mock()
            result = resources[f"financial_analyst_v1_{role}"]()
            assert result == "RESOLVED"
            kwargs = resolver.resolve.call_args.kwargs
            assert kwargs["agent_type"] == "quaks_financial_analyst_v1"
            assert kwargs["setting_key"] == setting_key

    def test_user_override_strips_execution_plan(self):
        resolver = MagicMock()
        resolver.resolve.return_value = (
            "User template\n## Execution Plan\n{{ EXECUTION_PLAN }}\n\nBody"
        )
        mcp, _, prompts, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(resolver, PromptRegistry()).register_prompts(
            mcp
        )

        result = prompts["financial_analyst_v1_consensus_reporter"]()
        assert "{{ EXECUTION_PLAN }}" not in result
        assert "User template" in result
        assert "Body" in result
