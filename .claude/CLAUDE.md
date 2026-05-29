# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## General Guidelines

1. Before writing any code, describe your approach and wait for approval.

2. If the requirements I give you are ambiguous, ask clarifying questions before writing any code.

3. After you finish writing any code, list the edge cases and suggest test cases to cover them.

4. If a task requires changes to more than 3 files, stop and break it into smaller tasks first.

5. When there’s a bug, start by writing a test that reproduces it, then fix it until the test passes.

6. Every time I correct you, reflect on what you did wrong and come up with a plan to never make the same mistake again.

---

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Project Overview

Quaks is a multi-agent financial agents platform built on [Agent-Lab](https://github.com/bsantanna/agent-lab). It uses LLM-powered agents (LangChain/LangGraph) to perform asset management, market data analysis, and alpha-seeking tasks. The backend is Python/FastAPI, the frontend is Angular 20, and market data flows through Airflow DAGs into Elasticsearch.

## Relationship to Agent-Lab

Quaks is a reference implementation built on the generic [Agent-Lab](https://github.com/bsantanna/agent-lab) base: Quaks = Agent-Lab's generic core **plus** a financial product surface. Keep this boundary when changing shared code:

- **Quaks is the source of truth for generic code.** When you improve a generic concern (auth, MCP server/transport, shared schemas, infrastructure), it should be portable back into Agent-Lab unchanged. Avoid coupling generic code to financial specifics.
- **Specialized code stays only in Quaks** and must never be pushed to Agent-Lab: the Angular frontend (`app/static/frontend/**`), specialized agents (`app/services/agent_types/quaks/**`), markets/waitlist services and APIs, the financial MCP tools/schemas/exceptions, and the `quant`/`seo`/`quaks-generator` skills.
- When editing generic files that also carry wiring (e.g. `app/core/container.py`, `app/services/agent_types/registry.py`, the MCP server `instructions`), separate the generic change from the financial wiring so the generic part can be synced.

## Skills

- `/software-engineering` — Architecture, common commands (build, test, lint), and code conventions.
- `/seo` — SEO audit, meta tags, Open Graph, structured data, accessibility, Core Web Vitals, and page rank optimization.
- `/quant` — Quantitative finance analysis: valuation, risk metrics, options pricing, technical/fundamental analysis, factor models, and portfolio strategy.
