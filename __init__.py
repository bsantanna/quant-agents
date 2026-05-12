"""Hermes plugin entry point for the Quaks financial agents collection.

Loaded by Hermes after `hermes plugins install bsantanna/quaks`. Registers the
bundled skills (news-analyst, financial-analyst-v1) and ensures the user's
Hermes config has the quaks.ai MCP server entry so the skills can call its
tools and prompts.

The skill files live at plugins/quaks-agents/skills/*/SKILL.md and are shared
verbatim with the Claude Code plugin manifest under .claude-plugin/.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PLUGIN_ROOT = Path(__file__).parent
SKILLS_DIR = PLUGIN_ROOT / "plugins" / "quaks-agents" / "skills"

MCP_SERVER_NAME = "quaks.ai"
MCP_SERVER_CONFIG = {"url": "https://quaks.ai/mcp/"}

HERMES_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"


def register(ctx) -> None:
    _register_skills(ctx)
    _ensure_mcp_server(HERMES_CONFIG_PATH)


def _register_skills(ctx) -> None:
    if not SKILLS_DIR.is_dir():
        logger.warning("Quaks skills directory not found at %s", SKILLS_DIR)
        return

    for child in sorted(SKILLS_DIR.iterdir()):
        skill_md = child / "SKILL.md"
        if not (child.is_dir() and skill_md.exists()):
            continue
        try:
            ctx.register_skill(child.name, skill_md)
        except Exception:
            logger.exception("Failed to register Quaks skill %s", child.name)


def _ensure_mcp_server(config_path: Path) -> None:
    """Idempotently add the quaks.ai MCP server to the user's Hermes config.

    Never overwrites an existing entry under the same name — if the user has
    already configured `quaks.ai` (possibly pointing elsewhere), their value
    wins and we leave it alone. The write is atomic (tempfile + os.replace)
    so an interrupted or concurrent run cannot leave the file truncated.
    """
    try:
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as fh:
                loaded = yaml.safe_load(fh)
            if loaded is None:
                existing = {}
            elif not isinstance(loaded, dict):
                raise yaml.YAMLError(
                    f"expected a mapping at the top level, got {type(loaded).__name__}"
                )
            else:
                existing = loaded
        else:
            existing = {}
    except yaml.YAMLError as exc:
        logger.warning(
            "Quaks: ~/.hermes/config.yaml is not valid YAML (%s). "
            "Skipping MCP server auto-config — see "
            "plugins/quaks-agents/hermes/mcp_servers.yaml for a manual snippet.",
            exc,
        )
        return

    servers = existing.get("mcp_servers")
    if not isinstance(servers, dict):
        servers = {}
        existing["mcp_servers"] = servers

    if MCP_SERVER_NAME in servers:
        return

    servers[MCP_SERVER_NAME] = MCP_SERVER_CONFIG

    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=config_path.parent, prefix=".quaks_tmp_", suffix=".yaml"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(existing, fh, sort_keys=False)
        os.replace(tmp_path, config_path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    logger.info("Quaks: added %s MCP server to %s", MCP_SERVER_NAME, config_path)
