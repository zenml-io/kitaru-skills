# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is a **Claude Code skills plugin** for [Kitaru](https://kitaru.ai) — ZenML's durable execution layer for Python agent workflows. It contains no application code; the deliverables are two Markdown skill files that teach Claude Code how to scope and author Kitaru workflows.

The plugin is distributed via the Claude Code marketplace as `zenml-io/kitaru-skills`.

## Repository structure

```
.claude-plugin/
  plugin.json         # Plugin identity, version, keywords
  marketplace.json    # Marketplace listing metadata
skills/
  kitaru-scoping/SKILL.md    # Structured interview → flow_architecture.md
  kitaru-authoring/SKILL.md  # Authoring guide for flows, checkpoints, waits, memory, etc.
```

- **kitaru-scoping** (`/kitaru-scoping`) — validates whether a workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, memory strategy, operator surface, MVP scope). Outputs a `flow_architecture.md`.
- **kitaru-authoring** (`/kitaru-authoring`) — reference guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, `kitaru.memory`, `KitaruClient`, CLI, MCP, and PydanticAI adapter integrations.

The intended user workflow is: scope first → author second.

## How to work on this repo

There is no build step, no linter, no test suite. The deliverables are the two `SKILL.md` files. Quality comes from:

1. **Accuracy against the Kitaru SDK** — every primitive, API surface, and constraint described in the skills must match the current Kitaru release. Cross-reference with the [Kitaru SDK repo](https://github.com/zenml-io/kitaru) and [docs](https://kitaru.ai/docs).
2. **Completeness of asymmetry tables** — the skills document capability differences across four surfaces (SDK, KitaruClient, CLI, MCP). These tables must stay synchronized between the two skill files.
3. **Stable naming** — checkpoint names, wait names, memory scopes, and operator handles are first-class concepts. Changes to naming conventions in the skills ripple into generated architecture documents.

## Key constraints when editing skills

- The SKILL.md frontmatter (`name`, `description`) is what Claude Code uses for skill matching and trigger detection. Keep trigger keywords accurate.
- Both skills share the same Kitaru domain model (surfaces, asymmetries, guardrails). Changes to one skill's representation of a constraint (e.g., "waits cannot go inside checkpoints") should be mirrored in the other.
- The authoring skill's "common mistakes checklist" and the scoping skill's "anti-patterns" section overlap intentionally — they serve different audiences (implementer vs architect).
- Plugin version is in `.claude-plugin/plugin.json` — bump it when publishing updates.

## Installation methods (for testing)

```bash
# Marketplace
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru

# Manual (for local development)
mkdir -p .claude/skills/kitaru-scoping .claude/skills/kitaru-authoring
cp skills/kitaru-scoping/SKILL.md .claude/skills/kitaru-scoping/SKILL.md
cp skills/kitaru-authoring/SKILL.md .claude/skills/kitaru-authoring/SKILL.md
```
