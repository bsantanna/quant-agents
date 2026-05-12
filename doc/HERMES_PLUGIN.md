<div align="center">
  <img src="logo.svg" alt="Quaks Logo" width="200" />
</div>

<h2 align="center"><a href="https://github.com/bsantanna/quaks">Quaks</a></h2>
<h3 align="center">Hermes Agent Plugin</h3>

---


Hermes-side entry point for the Quaks financial agents collection. Mirrors the
Claude Code plugin defined under [`plugins/quaks-agents/.claude-plugin/`](../plugins/quaks-agents/.claude-plugin/plugin.json)
and reuses the same skill files under [`plugins/quaks-agents/skills/`](../skills/).

## Install

```sh
hermes plugins install bsantanna/quaks --enable
```

The install command clones this repo into `~/.hermes/plugins/quaks/` and loads
[`plugin.yaml`](../plugin.yaml) at the repo root. On first load the
plugin's [`__init__.py`](../../../__init__.py) registers two skills:

- `news-analyst` — investor briefing / market news QA
- `financial-analyst-v1` — fundamental + technical stock analysis with allocation

Both are then available as slash commands (`/news-analyst`, `/financial-analyst-v1`)
and can also be triggered by natural-language references.

## MCP server auto-config

The skills depend on the Quaks MCP server (`https://quaks.ai/mcp/`) for tools
and prompts. Hermes plugins cannot auto-register MCP servers via the plugin
manifest, so the registration shim patches `~/.hermes/config.yaml` directly.

The patch is **idempotent and non-destructive**:

- Adds a `mcp_servers.quaks.ai` entry only if one is not already present.
- Preserves all other content in the file.
- Creates the file (with `mkdir -p` on the parent directory) if it does not
  exist yet.
- Skips entirely with a warning if the existing YAML is malformed — your file
  is never overwritten in that case.

If you'd rather configure it by hand, paste the contents of
[`mcp_servers.yaml`](./mcp_servers.yaml) into `~/.hermes/config.yaml` (merging
with any existing `mcp_servers:` block).

## Authentication

Some tools (notably `publish_content_mcp`) require an authenticated MCP
session. Hermes' OAuth flow for HTTP MCP servers is documented in the
[Hermes MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp).

## Relationship to the Claude plugin

| Concern              | Claude                                           | Hermes                                       |
| -------------------- | ------------------------------------------------ | -------------------------------------------- |
| Plugin manifest      | `plugins/quaks-agents/.claude-plugin/plugin.json` | `plugin.yaml` (repo root)                    |
| Marketplace listing  | `.claude-plugin/marketplace.json` (repo root)    | n/a — `hermes plugins install <owner>/<repo>` |
| Skill files          | `plugins/quaks-agents/skills/*/SKILL.md`         | same files, loaded via `ctx.register_skill`  |
| MCP server config    | `plugins/quaks-agents/.mcp.json` (auto-loaded)   | patched into `~/.hermes/config.yaml`         |
| Slash command prefix | `/quaks-agents:<skill>`                          | `/<skill>` (no namespace)                    |

Skill content is single-sourced — editing a `SKILL.md` updates the behavior
seen by both Claude Code and Hermes.
