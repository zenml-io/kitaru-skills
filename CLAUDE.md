# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Shared, host-agnostic contributor guidance lives in [`AGENTS.md`](AGENTS.md).

## What this repo is

This repository contains **Kitaru Agent Skills** for [Kitaru](https://kitaru.ai) — ZenML's durable execution layer for Python agent workflows — plus Claude Code plugin packaging. It contains no application code; the deliverables are nine Markdown skills plus quickstart and migration references that teach agent hosts how to onboard, scope, author, and migrate Kitaru workflows.

Claude Code distribution is supported through the `.claude-plugin/` metadata and the Claude Code marketplace entry `zenml-io/kitaru-skills`.

## Repository structure

```
.claude-plugin/
  plugin.json         # Claude Code plugin identity, version, keywords
  marketplace.json    # Claude Code marketplace listing metadata
skills/
  kitaru-quickstart/SKILL.md       # Interactive onboarding → demo flow
  kitaru-quickstart/references/    # Track templates, host guides, MCP config
  kitaru-scoping/SKILL.md          # Structured interview → flow_architecture.md
  kitaru-authoring/SKILL.md        # Authoring guide for flows, checkpoints, waits, artifacts, etc.
  kitaru-replay-lab/SKILL.md       # Replay operations lab for real executions
  kitaru-pydantic-ai-migration/     # PydanticAI to KitaruAgent migration skill + references
  kitaru-openai-agents-migration/   # OpenAI Agents SDK to KitaruRunner migration skill + references
  kitaru-langgraph-migration/       # LangGraph to KitaruGraphRunner migration skill + references
  kitaru-claude-agent-sdk-migration/ # Claude Agent SDK to KitaruClaudeRunner migration skill + references
  kitaru-gemini-interactions-migration/ # Gemini Interactions to KitaruGeminiInteractionsRunner migration skill + references
```

- **kitaru-quickstart** (`/kitaru-quickstart` in Claude Code) — interactive onboarding that scaffolds a personalized demo flow, demonstrates crash recovery with replay, human-in-the-loop with `wait()`, artifact capture, and optional MCP integration.
- **kitaru-scoping** (`/kitaru-scoping` in Claude Code) — validates whether a workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, artifact strategy, operator surface, MVP scope). Outputs a `flow_architecture.md`.
- **kitaru-authoring** (`/kitaru-authoring` in Claude Code) — reference guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, `KitaruClient`, CLI, MCP, deployments, secrets, and current adapter integrations: PydanticAI, OpenAI Agents, LangGraph, Claude Agent SDK, and Gemini Interactions.
- **kitaru-replay-lab** (`/kitaru-replay-lab` in Claude Code) — operational lab for real executions: reproduce first, fork one change, inspect `ReplaySubmission`, diff results, replay cohorts, and diagnose waits, skipped rows, failures, and divergence.
- **kitaru-pydantic-ai-migration** (`/kitaru-pydantic-ai-migration` in Claude Code) — conservative migration guide for existing PydanticAI code moving to `KitaruAgent`, with direct/approximate/absent classification and a migration report.
- **kitaru-openai-agents-migration** (`/kitaru-openai-agents-migration` in Claude Code) — conservative migration guide for existing OpenAI Agents SDK code moving to `KitaruRunner`, `OpenAIRunRequest`, and `OpenAIRunResult`, with approval/resume, context, and side-effect risk reporting.
- **kitaru-langgraph-migration** (`/kitaru-langgraph-migration` in Claude Code) — conservative migration guide for existing LangGraph/LangChain code moving to `KitaruGraphRunner`, with `graph_call` vs middleware-backed `calls` boundary reporting.
- **kitaru-claude-agent-sdk-migration** (`/kitaru-claude-agent-sdk-migration` in Claude Code) — conservative migration guide for existing Claude Agent SDK code moving to `KitaruClaudeRunner`, with one-invocation checkpointing and Claude-owned tool/Bash/MCP/workspace caveats.
- **kitaru-gemini-interactions-migration** (`/kitaru-gemini-interactions-migration` in Claude Code) — conservative migration guide for existing Gemini Interactions, Google GenAI Interactions, or Antigravity managed-agent code moving to `KitaruGeminiInteractionsRunner`, with `requires_action`, polling, function-result, and Google-owned internals reporting.

The intended user workflow is: quickstart → scope → author → replay lab for new work with real executions, or migration skill → report review → author → replay lab for existing PydanticAI, OpenAI Agents SDK, LangGraph, Claude Agent SDK, or Gemini Interactions code.

## How to work on this repo

There is no build step, no linter, no test suite. The deliverables are the nine `SKILL.md` files plus the quickstart and migration reference files. Quality comes from:

1. **Accuracy against the Kitaru SDK** — every primitive, API surface, and constraint described in the skills must match the current Kitaru release. Cross-reference with the [Kitaru SDK repo](https://github.com/zenml-io/kitaru) and [docs](https://kitaru.ai/docs).
2. **Completeness of asymmetry tables** — the skills document capability differences across SDK, KitaruClient, CLI, MCP, deployments, secrets, and adapter surfaces. These tables must stay synchronized between the scoping and authoring skills.
3. **Stable naming** — checkpoint names, wait names, artifact names, and operator handles are first-class concepts. Changes to naming conventions in the skills ripple into generated architecture documents.

## Key constraints when editing skills

- The SKILL.md frontmatter (`name`, `description`) is what Claude Code uses for skill matching and trigger detection. Keep trigger keywords accurate.
- All nine skills share the same Kitaru domain model (surfaces, asymmetries, guardrails). Changes to one skill's representation of a constraint (e.g., "waits cannot go inside checkpoints") should be mirrored where relevant.
- The authoring skill's "common mistakes checklist" and the scoping skill's "anti-patterns" section overlap intentionally — they serve different audiences (implementer vs architect).
- The quickstart skill's track templates in `references/tracks/` must use only
  real Kitaru APIs for the soon-to-be-released Kitaru `0.19.0` API. Template
  decorator placement is fixed; only internal business logic is customizable.
  Replay examples in this PR/branch must use `at` / `--at` consistently.
- Keep replay API language synchronized with the current Kitaru replay docs: use
  `at` / `--at`, `flow_overrides`, `checkpoint_overrides`,
  `invocation_overrides`, and `ReplaySubmission`. Do not regress to old `from_`,
  `--from`, flat `overrides=...`, or `--override checkpoint.*` examples,
  except when explicitly warning users not to use the old API.
- Replay override constraints matter: `code` overrides are only valid for
  recorded `tool_call` targets, `model` overrides are only valid for supported
  `llm_call` targets, and `output` overrides need a downstream consumer rather
  than neutralizing terminal side effects.
- CLI wait abort exists as `kitaru executions input <exec_id> --abort`; do not
  describe KitaruClient as the only wait-abort surface.
- MCP secret support is metadata-only creation through `kitaru_secrets_create`;
  do not document MCP secret read/delete unless the Kitaru source adds those
  tools.
- Native durable memory APIs were removed in Kitaru 0.11.0. Do not reintroduce old native-memory wording or recommend a Kitaru-owned durable key-value state API. Use external/application-owned stores for mutable cross-execution state and pass explicit values or stable references into flows.
- Plugin version is in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — bump all version fields consistently when publishing updates.

## Installation methods (for Claude Code testing)

```bash
# Marketplace
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru

# Manual (for local development)
mkdir -p .claude/skills
cp -R skills/kitaru-quickstart .claude/skills/
cp -R skills/kitaru-scoping .claude/skills/
cp -R skills/kitaru-authoring .claude/skills/
cp -R skills/kitaru-replay-lab .claude/skills/
cp -R skills/kitaru-pydantic-ai-migration .claude/skills/
cp -R skills/kitaru-openai-agents-migration .claude/skills/
cp -R skills/kitaru-langgraph-migration .claude/skills/
cp -R skills/kitaru-claude-agent-sdk-migration .claude/skills/
cp -R skills/kitaru-gemini-interactions-migration .claude/skills/
```
