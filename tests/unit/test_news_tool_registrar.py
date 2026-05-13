from unittest.mock import MagicMock

import pytest

from app.interface.mcp.news_tool_registrar import (
    NewsToolRegistrar,
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


def _news_hit(doc_id="n1", ticker=None, content=True):
    source = {
        "text_headline": "Tech Rally",
        "text_summary": "Stocks up",
        "text_content": "Full content body" if content else "",
        "key_source": "reuters",
        "date_reference": "2025-01-10",
    }
    if ticker is not None:
        source["key_ticker"] = ticker
    return {"_id": doc_id, "_source": source}


def _insights_hit(doc_id="i1", report_html=True, language_model_name=None):
    source = {
        "date_reference": "2025-01-10",
        "text_executive_summary": "Summary",
    }
    if report_html:
        source["text_report_html"] = "<p>Report</p>"
    if language_model_name is not None:
        source["key_language_model_name"] = language_model_name
    return {"_id": doc_id, "_source": source}


class TestStripExecutionPlan:
    def test_strips_block(self):
        text = "Header\n\n## Execution Plan\n{{ EXECUTION_PLAN }}\n\nBody"
        assert _strip_execution_plan(text) == "Header\n\nBody"

    def test_strips_block_without_trailing_blank(self):
        text = "## Execution Plan\n{{ EXECUTION_PLAN }}\nBody"
        assert _strip_execution_plan(text) == "Body"

    def test_no_block_leaves_text_untouched(self):
        text = "No placeholder here.\nJust text."
        assert _strip_execution_plan(text) == text

    def test_preserves_other_placeholders(self):
        text = (
            "Current time: {{ CURRENT_TIME }}\n\n"
            "## Execution Plan\n{{ EXECUTION_PLAN }}\n\n"
            "Tickers: {{ TICKERS }}"
        )
        out = _strip_execution_plan(text)
        assert "{{ CURRENT_TIME }}" in out
        assert "{{ TICKERS }}" in out
        assert "EXECUTION_PLAN" not in out


class TestNewsToolRegistrar:
    def test_registers_tools(self):
        registrar = NewsToolRegistrar(_passthrough_resolver(), PromptRegistry())
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert "get_markets_news_mcp" in tool_names
        assert "get_insights_news_mcp" in tool_names

    def test_registers_prompts(self):
        registrar = NewsToolRegistrar(_passthrough_resolver(), PromptRegistry())
        mcp = MagicMock()
        registrar.register_prompts(mcp)
        prompt_names = [call[1]["name"] for call in mcp.prompt.call_args_list]
        assert "news_analyst_coordinator" in prompt_names
        assert "news_analyst_aggregator" in prompt_names
        assert "news_analyst_reporter" in prompt_names

    def test_registers_resources(self):
        registrar = NewsToolRegistrar(_passthrough_resolver(), PromptRegistry())
        mcp = MagicMock()
        registrar.register_resources(mcp)
        resource_names = [call[1]["name"] for call in mcp.resource.call_args_list]
        assert "news_analyst_coordinator" in resource_names
        assert "news_analyst_aggregator" in resource_names
        assert "news_analyst_reporter" in resource_names

    def test_contributes_prompts_to_registry(self):
        registry = PromptRegistry()
        NewsToolRegistrar(_passthrough_resolver(), registry)
        assert "news_analyst_coordinator" in registry
        assert "news_analyst_aggregator" in registry
        assert "news_analyst_reporter" in registry

    def test_registry_resolve_returns_raw_template_minus_execution_plan(self):
        registry = PromptRegistry()
        NewsToolRegistrar(_passthrough_resolver(), registry)
        text = registry.resolve("news_analyst_aggregator")
        assert isinstance(text, str)
        assert text
        assert "{{ EXECUTION_PLAN }}" not in text
        assert "{{ CURRENT_TIME }}" in text


class TestGetMarketsNewsMcp:
    @pytest.mark.asyncio
    async def test_batch_default_omits_content(self):
        container = MagicMock()
        container.markets_news_service.return_value.get_news.return_value = (
            [_news_hit(ticker=["AAPL"])],
            "cursor-1",
        )
        mcp, tools, _, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_tools(
            mcp, container
        )

        result = await tools["get_markets_news_mcp"]()

        assert len(result.items) == 1
        assert result.items[0].content is None
        assert result.items[0].tickers == ["AAPL"]
        assert result.cursor == "cursor-1"
        call_kwargs = container.markets_news_service.return_value.get_news.call_args[1]
        assert call_kwargs["include_text_content"] is False
        assert call_kwargs["date_from"] is not None

    @pytest.mark.asyncio
    async def test_batch_with_include_content_returns_full_body(self):
        container = MagicMock()
        container.markets_news_service.return_value.get_news.return_value = (
            [_news_hit()],
            None,
        )
        mcp, tools, _, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_tools(
            mcp, container
        )

        result = await tools["get_markets_news_mcp"](include_content=True)
        assert result.items[0].content == "Full content body"

    @pytest.mark.asyncio
    async def test_id_fetch_forces_full_content_and_skips_date_default(self):
        container = MagicMock()
        container.markets_news_service.return_value.get_news.return_value = (
            [_news_hit(doc_id="single")],
            None,
        )
        mcp, tools, _, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_tools(
            mcp, container
        )

        result = await tools["get_markets_news_mcp"](id="single")

        assert result.items[0].content == "Full content body"
        call_kwargs = container.markets_news_service.return_value.get_news.call_args[1]
        assert call_kwargs["id"] == "single"
        assert call_kwargs["date_from"] is None
        assert call_kwargs["include_text_content"] is True

    @pytest.mark.asyncio
    async def test_size_clamped_to_range(self):
        container = MagicMock()
        container.markets_news_service.return_value.get_news.return_value = ([], None)
        mcp, tools, _, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_tools(
            mcp, container
        )

        await tools["get_markets_news_mcp"](size=15)
        assert (
            container.markets_news_service.return_value.get_news.call_args[1]["size"]
            == 15
        )


class TestGetInsightsNewsMcp:
    @pytest.mark.asyncio
    async def test_batch_without_report_html(self):
        container = MagicMock()
        container.markets_insights_service.return_value.get_insights_news.return_value = (
            [_insights_hit(language_model_name="claude-opus-4-7")],
            "cur",
        )
        mcp, tools, _, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_tools(
            mcp, container
        )

        result = await tools["get_insights_news_mcp"]()

        assert len(result.items) == 1
        assert result.items[0].report_html is None
        assert result.items[0].language_model_name == "claude-opus-4-7"
        assert result.cursor == "cur"

    @pytest.mark.asyncio
    async def test_include_report_html(self):
        container = MagicMock()
        container.markets_insights_service.return_value.get_insights_news.return_value = (
            [_insights_hit()],
            None,
        )
        mcp, tools, _, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_tools(
            mcp, container
        )

        result = await tools["get_insights_news_mcp"](include_report_html=True)
        assert result.items[0].report_html == "<p>Report</p>"

    @pytest.mark.asyncio
    async def test_id_fetch(self):
        container = MagicMock()
        container.markets_insights_service.return_value.get_insights_news.return_value = (
            [_insights_hit(doc_id="brief-1")],
            None,
        )
        mcp, tools, _, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_tools(
            mcp, container
        )

        await tools["get_insights_news_mcp"](id="brief-1")
        call_kwargs = (
            container.markets_insights_service.return_value.get_insights_news.call_args[
                1
            ]
        )
        assert call_kwargs["id"] == "brief-1"


class TestPromptsAndResources:
    def test_prompt_functions_return_raw_strings(self):
        mcp, _, prompts, _ = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_prompts(
            mcp
        )

        for name in (
            "news_analyst_coordinator",
            "news_analyst_aggregator",
            "news_analyst_reporter",
        ):
            result = prompts[name]()
            assert isinstance(result, str)
            assert result
            assert "{{ EXECUTION_PLAN }}" not in result

    def test_resource_functions_return_raw_strings(self):
        mcp, _, _, resources = _capturing_mcp()
        NewsToolRegistrar(_passthrough_resolver(), PromptRegistry()).register_resources(
            mcp
        )

        for name in (
            "news_analyst_coordinator",
            "news_analyst_aggregator",
            "news_analyst_reporter",
        ):
            result = resources[name]()
            assert isinstance(result, str)
            assert result
            assert "{{ EXECUTION_PLAN }}" not in result


class TestUserOverrideWiring:
    """Verify each prompt/resource delegates to the resolver with the right keys."""

    _EXPECTED = [
        ("coordinator", "coordinator_system_prompt"),
        ("aggregator", "aggregator_system_prompt"),
        ("reporter", "reporter_system_prompt"),
    ]

    def test_prompts_call_resolver_with_role_specific_keys(self):
        resolver = MagicMock()
        resolver.resolve.return_value = "RESOLVED"
        mcp, _, prompts, _ = _capturing_mcp()
        NewsToolRegistrar(resolver, PromptRegistry()).register_prompts(mcp)

        for role, setting_key in self._EXPECTED:
            resolver.resolve.reset_mock()
            result = prompts[f"news_analyst_{role}"]()
            assert result == "RESOLVED"
            kwargs = resolver.resolve.call_args.kwargs
            assert kwargs["agent_type"] == "quaks_news_analyst"
            assert kwargs["setting_key"] == setting_key
            assert kwargs["default_template"]
            assert "render" not in kwargs

    def test_resources_call_resolver_with_role_specific_keys(self):
        resolver = MagicMock()
        resolver.resolve.return_value = "RESOLVED"
        mcp, _, _, resources = _capturing_mcp()
        NewsToolRegistrar(resolver, PromptRegistry()).register_resources(mcp)

        for role, setting_key in self._EXPECTED:
            resolver.resolve.reset_mock()
            result = resources[f"news_analyst_{role}"]()
            assert result == "RESOLVED"
            kwargs = resolver.resolve.call_args.kwargs
            assert kwargs["agent_type"] == "quaks_news_analyst"
            assert kwargs["setting_key"] == setting_key

    def test_user_override_strips_execution_plan(self):
        resolver = MagicMock()
        resolver.resolve.return_value = (
            "User template\n## Execution Plan\n{{ EXECUTION_PLAN }}\n\nBody"
        )
        mcp, _, prompts, _ = _capturing_mcp()
        NewsToolRegistrar(resolver, PromptRegistry()).register_prompts(mcp)

        result = prompts["news_analyst_coordinator"]()
        assert "{{ EXECUTION_PLAN }}" not in result
        assert "User template" in result
        assert "Body" in result
