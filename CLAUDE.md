# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Shared, host-agnostic contributor guidance lives in [`AGENTS.md`](AGENTS.md).

## What this repo is

This repository contains **Kitaru Agent Skills** for [Kitaru](https://kitaru.ai) — ZenML's durable execution layer for Python agent workflows — plus Claude Code plugin packaging. It contains no application code; the deliverables are three Markdown skill files plus quickstart references that teach agent hosts how to onboard, scope, and author Kitaru workflows.

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
```

- **kitaru-quickstart** (`/kitaru-quickstart` in Claude Code) — interactive onboarding that scaffolds a personalized demo flow, demonstrates crash recovery with replay, human-in-the-loop with `wait()`, artifact capture, and optional MCP integration.
- **kitaru-scoping** (`/kitaru-scoping` in Claude Code) — validates whether a workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, artifact strategy, operator surface, MVP scope). Outputs a `flow_architecture.md`.
- **kitaru-authoring** (`/kitaru-authoring` in Claude Code) — reference guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, `KitaruClient`, CLI, MCP, deployments, secrets, and current adapter integrations: PydanticAI, OpenAI Agents, LangGraph, and Claude Agent SDK.

The intended user workflow is: quickstart → scope → author.

## How to work on this repo

There is no build step, no linter, no test suite. The deliverables are the three `SKILL.md` files plus the quickstart reference templates and setup guides. Quality comes from:

1. **Accuracy against the Kitaru SDK** — every primitive, API surface, and constraint described in the skills must match the current Kitaru release. Cross-reference with the [Kitaru SDK repo](https://github.com/zenml-io/kitaru) and [docs](https://kitaru.ai/docs).
2. **Completeness of asymmetry tables** — the skills document capability differences across SDK, KitaruClient, CLI, MCP, deployments, secrets, and adapter surfaces. These tables must stay synchronized between the scoping and authoring skills.
3. **Stable naming** — checkpoint names, wait names, artifact names, and operator handles are first-class concepts. Changes to naming conventions in the skills ripple into generated architecture documents.

## Key constraints when editing skills

- The SKILL.md frontmatter (`name`, `description`) is what Claude Code uses for skill matching and trigger detection. Keep trigger keywords accurate.
- All three skills share the same Kitaru domain model (surfaces, asymmetries, guardrails). Changes to one skill's representation of a constraint (e.g., "waits cannot go inside checkpoints") should be mirrored in the others.
- The authoring skill's "common mistakes checklist" and the scoping skill's "anti-patterns" section overlap intentionally — they serve different audiences (implementer vs architect).
- The quickstart skill's track templates in `references/tracks/` must use only real, documented Kitaru APIs. Template decorator placement is fixed; only internal business logic is customizable.
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
```
