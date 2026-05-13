from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from pydantic import Field

from app.domain.exceptions.base import DuplicateEntryError, UnauthorizedSkillError
from app.interface.mcp.prompt_registry import PromptRegistry
from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.schema import (
    AgentItem,
    PublishContentResult,
    _get_mcp_schema,
)

if TYPE_CHECKING:
    from app.core.container import Container


class DefaultToolRegistrar(McpRegistrar):
    """Registers the default Quaks MCP tools."""

    def __init__(self, prompt_registry: PromptRegistry) -> None:
        self._prompt_registry = prompt_registry

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        @mcp.tool(
            name="get_agent_list",
            description="List all AI agents registered on the Quaks platform. "
            "Returns each agent's ID, name, type, capabilities summary, "
            "and linked language model. Use this to discover what agents "
            "are available and what they can do.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def get_agent_list() -> list[AgentItem]:
            schema = _get_mcp_schema()
            agent_service = container.agent_service()
            agents = agent_service.get_agents(schema)
            return [
                AgentItem(
                    id=a.id,
                    agent_name=a.agent_name,
                    agent_type=a.agent_type,
                    agent_summary=a.agent_summary,
                    language_model_id=a.language_model_id,
                    is_active=a.is_active,
                )
                for a in agents
            ]

        @mcp.tool(
            name="publish_content_mcp",
            description="Publish AI-generated content (reports, briefings, analysis) "
            "to the Quaks platform. The content is queued for validation and "
            "then routed to the appropriate index based on the skill that "
            "produced it. Requires authentication — the author is identified "
            "from the access token. Only a curated set of skills is allowed "
            "to publish; calls from unknown skills are rejected. IMPORTANT: "
            "Convert any Markdown content to well-formed HTML before calling "
            "this tool.",
            annotations={"readOnlyHint": False, "openWorldHint": False},
        )
        async def publish_content_mcp(
            text_executive_summary: Annotated[
                str,
                Field(description="Concise executive summary of the content"),
            ],
            text_report_html: Annotated[
                str,
                Field(
                    description="Full report content in HTML format. "
                    "Convert Markdown to HTML before submitting."
                ),
            ],
            key_skill_name: Annotated[
                str,
                Field(
                    description="Name of the skill that generated this content "
                    "(e.g. '/news_analyst'). Calls from skills not in the "
                    "allowlist are rejected."
                ),
            ],
            language_model_name: Annotated[
                str,
                Field(
                    description="Name of the language model that generated this "
                    "content (e.g. 'claude-opus-4-7', 'gpt-5'). Persisted with "
                    "the published document for provenance and displayed to end "
                    "users."
                ),
            ],
        ) -> PublishContentResult:
            access_token = get_access_token()
            if access_token is None or not access_token.claims.get(
                "preferred_username"
            ):
                raise ValueError(
                    "Authentication required. No valid access token or username found."
                )
            author_username = access_token.claims["preferred_username"]

            try:
                svc = container.published_content_service()
                doc_id = svc.publish(
                    executive_summary=text_executive_summary,
                    report_html=text_report_html,
                    skill_name=key_skill_name,
                    author_username=author_username,
                    language_model_name=language_model_name,
                )
            except DuplicateEntryError:
                return PublishContentResult(
                    status="duplicate",
                    message="Content with this summary from this author already exists.",
                )
            except UnauthorizedSkillError:
                return PublishContentResult(
                    status="rejected",
                    message=f"Skill '{key_skill_name}' is not authorized to "
                    "publish content.",
                )

            return PublishContentResult(
                status="published",
                doc_id=doc_id,
                message=f"Content published successfully by {author_username}. "
                "It will be validated and routed to the appropriate index.",
            )

        registry = self._prompt_registry

        @mcp.tool(
            name="read_prompt_mcp",
            description="Load a Quaks workflow system prompt by name. Tool-based "
            "equivalent of reading the MCP resource at prompt://<name> or "
            "calling prompts/get for the same name — use whichever path your "
            "runtime exposes. Returns the raw template text (per-tenant "
            "override applied when available); any {{ CURRENT_TIME }} or "
            "{{ TICKERS }} placeholder in the returned text is for the model "
            "to substitute locally before applying the prompt. "
            "Available prompt names: news_analyst_coordinator, "
            "news_analyst_aggregator, news_analyst_reporter, "
            "financial_analyst_v1_coordinator, "
            "financial_analyst_v1_data_collector, "
            "financial_analyst_v1_fundamental_analyst, "
            "financial_analyst_v1_technical_analyst, "
            "financial_analyst_v1_consensus_reporter.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def read_prompt_mcp(
            name: Annotated[
                str,
                Field(
                    description="Prompt identifier (e.g. 'news_analyst_aggregator', "
                    "'financial_analyst_v1_data_collector'). Matches the "
                    "name segment of the corresponding prompt:// resource URI."
                ),
            ],
        ) -> str:
            try:
                return registry.resolve(name)
            except KeyError as exc:
                raise ValueError(str(exc)) from exc
