<div align="center">
  <img src="logo.svg" alt="Quaks Logo" width="200" />
</div>

<h2 align="center"><a href="https://github.com/bsantanna/quaks">Quaks</a></h2>
<h3 align="center">Hermes Agent Plugin</h3>

---

## Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com/) v0.10.0 or later
- An interactive session for the first MCP connection (browser-based OAuth)

## Install

```sh
hermes plugins install bsantanna/quaks --enable
```

The install command clones this repo into `~/.hermes/plugins/quaks/` and loads
[`plugin.yaml`](../plugin.yaml) at the repo root. On first load the plugin's
[`__init__.py`](../__init__.py) registers two skills with Hermes' plugin
manager and patches the Quaks MCP server into `~/.hermes/config.yaml`.

## Usage

Plugin-bundled skills do **not** appear in `hermes skills list` or in the
agent's default `<available_skills>` index — Hermes treats them as opt-in
explicit loads. The agent loads one by calling the `skill_view` tool:

```text
skill_view(name="quaks:news-analyst")
skill_view(name="quaks:financial-analyst-v1")
```

A natural-language prompt is usually enough to trigger the right load — for
example:

- "give me a quaks news briefing"
- "analyze AAPL, MSFT, NVDA with quaks financial analyst"
- "ask the quaks news analyst: what's happening with NVDA?"

Once loaded, the SKILL.md body becomes the agent's instructions for the rest
of the workflow.

## What's Included

### MCP Server

The plugin patches `~/.hermes/config.yaml` to register the Quaks MCP server:

```yaml
mcp_servers:
  quaks.ai:
    url: https://quaks.ai/mcp/
    auth: oauth
```

`auth: oauth` triggers Hermes' built-in OAuth 2.1 + PKCE flow (dynamic client
registration, browser-based authorization, on-disk token persistence). On the
first connection Hermes opens (or prints) the authorization URL — complete
the consent in your browser and Hermes caches the tokens for subsequent runs.

Tools exposed:

| Tool | Description |
|------|-------------|
| `get_markets_news_mcp` | Retrieve latest market news articles with optional filters (search term, ticker, days, size) |
| `get_insights_news_mcp` | Retrieve pre-generated investor briefings |
| `get_agent_list` | List available Quaks agents |
| `fetch_company_profile_mcp` | Company metadata, valuation multiples, profitability, growth, analyst ratings |
| `fetch_stats_close_mcp` | OHLCV price stats and percent variance for a single ticker |
| `fetch_technical_indicators_mcp` | RSI, MACD, EMA crossover, ADX for a single ticker |
| `fetch_portfolio_xray_mcp` | Morningstar-style Portfolio X-Ray for a basket of tickers |
| `publish_content_mcp` | Publish a generated report to the Quaks platform (requires auth) |

### Skills

| Skill | Description |
|-------|-------------|
| `quaks:news-analyst` | Investor briefing pipeline and financial news Q&A |
| `quaks:financial-analyst-v1` | Fundamental + technical stock analysis with USD 10,000 allocation |

## MCP auto-config behavior

The patch applied by [`__init__.py`](../__init__.py) is **idempotent and
non-destructive**:

- Adds `mcp_servers.quaks.ai` only if absent.
- Preserves all other content in the file.
- Creates the file (with `mkdir -p` on the parent directory) if it does not
  exist yet.
- Skips entirely with a warning if the existing YAML is malformed — your file
  is never overwritten in that case.
- Writes atomically (tempfile + rename) so an interrupted run cannot leave a
  truncated config.

If you'd rather configure it by hand, paste the contents of
[`plugins/quaks-agents/hermes/mcp_servers.yaml`](../plugins/quaks-agents/hermes/mcp_servers.yaml)
into `~/.hermes/config.yaml`.

## Updating

```sh
hermes plugins update quaks
```

## Uninstall

```sh
hermes plugins remove quaks
```

Removing the plugin does **not** strip the `quaks.ai` entry from
`~/.hermes/config.yaml`. If you want to fully clean up, also delete the
`mcp_servers.quaks.ai` block from your config.
