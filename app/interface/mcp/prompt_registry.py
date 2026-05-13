from __future__ import annotations

from typing import Callable

PromptResolver = Callable[..., str]


class PromptRegistry:
    """Catalogue of model-callable prompts behind the ``read_prompt_mcp`` tool.

    Tools are the only MCP primitive guaranteed to be model-callable across every
    client (Claude Code, Claude.ai connectors, Hermes, Cursor, etc.). Resources
    and prompts are exposed by the server for spec-compliant clients but are not
    universally invokable mid-conversation — so this registry collects every
    pipeline prompt under a single tool surface. Each registrar contributes its
    prompts on construction; the default registrar reads from it at call time.
    """

    def __init__(self) -> None:
        self._resolvers: dict[str, PromptResolver] = {}

    def register(self, name: str, resolver: PromptResolver) -> None:
        if name in self._resolvers:
            raise ValueError(f"Prompt '{name}' is already registered")
        self._resolvers[name] = resolver

    def resolve(self, name: str, **kwargs) -> str:
        if name not in self._resolvers:
            available = ", ".join(sorted(self._resolvers)) or "<none>"
            raise KeyError(
                f"Unknown prompt name '{name}'. Available prompts: {available}"
            )
        return self._resolvers[name](**kwargs)

    def names(self) -> list[str]:
        return sorted(self._resolvers)

    def __contains__(self, name: str) -> bool:
        return name in self._resolvers
