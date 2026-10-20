---
name: kitaru-model-swap
description: Find out what changes, and what it would cost, if an agent's model calls move to another model, using the user's own recorded traces. Use when a user asks whether they can switch models, move to an open, local, Ollama, or cheaper model, cut LLM cost, compare models on their production traffic, or check a model swap before shipping it. Imports a recent slice of traces, sends each recorded model call to candidate models with the kitaru/model-swap analyzer, renders an HTML report, reviews disagreements with the user, and ends with a per-call recommendation.
---

# Kitaru model swap

Answer one question from the user's own traces: if this agent's model calls move to another model, what changes and what would it cost? Kitaru sends each recorded model call, exactly as it was recorded, to candidate models and compares their answers with the recording. It does not re-run the agent, and it runs on the user's worker with the user's keys.

Recommend; do not decide. Never change the agent's configuration yourself.

## Core contract

- Run every Kitaru CLI command with `KITARU_ACTIVE_SKILL=kitaru-model-swap` set, and prefer `--output json --machine --non-interactive --no-browser`.
- Never ask for, read, echo, or store an API key in chat, files, parameters, or command lines you show. Keys go into a Kitaru provider connection through a command the user runs themselves, or into the worker's environment. Candidates only name the variable.
- Always run a dry run first and get explicit approval of the estimated spend before a run that calls paid endpoints. Always pass `max_spend_usd` on a paid run.
- Include the production model as a `reference` candidate. Without it, disagreement cannot be told apart from the model's own run-to-run variation.
- Report provider failures (timeouts, rate limits, HTTP errors, empty replies, tool-call parse errors, refusals) as setup problems, never as model quality.
- Keep inferred tool schemas out of conclusions; say how many calls used them.
- Use Kitaru product terms: agent, session, node, import, analyzer, insight, connection, worker.

## Load references only when needed

- Read [references/model-swap-contract.md](references/model-swap-contract.md) before running any Kitaru command in this skill: exact commands, analyzer parameters, report fields, and annotation shape.
- Read [references/tool-schemas.md](references/tool-schemas.md) when the coverage shows `missing_tool_schema` skips, or before importing traces that are known to lack tool definitions.

## 1. Set up and import

1. Check `kitaru status`. If Kitaru is missing or not logged in, install it (`uv add "kitaru[cli,worker]"`) and log in: `kitaru login --local` for a local server, or `kitaru login` / `kitaru login SERVER` for a managed or team server. Ask which one the user wants when it is not obvious.
2. Make sure a worker that claims analyzer tasks is running (`kitaru worker start --claim importer --claim analyzer --concurrency 10`). A local Ollama candidate needs the worker on the same machine as Ollama.
3. Find or register the agent, then import a recent, bounded slice of traces: the last 7 days from the user's trace provider through its importer and connection, or a JSONL export file. Use the matching Kitaru import guide for the provider. Route unsupported sources to `kitaru-importer-builder`.
4. Note the `import_id`.

If the user already has an import, reuse it.

## 2. Choose candidates

Ask which models to try. Suggest a small set, and explain each in one line:

- one open model on a hosted provider;
- one local model if Ollama is installed (`ollama list` shows what is available; base URL `http://localhost:11434/v1`, price zero);
- one cheaper tier of the user's current provider;
- the current production model as the `reference`.

For each paid candidate, find which environment variable will hold its key. If no connection exists, give the user the exact `kitaru connection create model-swap-keys --provider model-swap --set-secret NAME=... --default` command to run themselves, with placeholders instead of values. Then confirm the connection lists the expected `secret_keys` without reading values.

Ask about provider settings only when relevant: a model served without a tool-call parser needs `tool_call_format: "hermes"`; reasoning models may need `reasoning_effort`.

## 3. Estimate, approve, run

1. Run the analyzer with `"dry_run": true`, render the report, and show the user: calls per candidate, estimated spend per candidate and in total, and coverage (replayable versus skipped calls).
2. If coverage shows `missing_tool_schema`, follow [references/tool-schemas.md](references/tool-schemas.md) before going on.
3. Ask for approval of the spend and a cap. Run again without `dry_run` and with `max_spend_usd`.
4. If the run stopped early (`max_spend` or `time_budget`), say so and offer to rerun with a smaller `max_calls` or a higher cap.

## 4. Report

Render `kitaru insight report --import-id IMPORT_ID --out model-swap-report.html` and give the user the path. Summarize in plain words, per candidate:

- how often it picked the same tool as the recording (tool choice) and how often its answer or arguments matched exactly, read against the reference;
- per-argument agreement on structured fields such as actions and amounts;
- failures by category and what to change in provider settings;
- cost per call and per month, and why (price, tokens, reasoning tokens, retries);
- what the report says about coverage and reasoning that was not replayed.

Point out when the reference itself rarely agrees with its recording: exact agreement is then too strict, and per-argument agreement or a judge is the better signal.

## 5. Review disagreements with the user

Walk through the disagreements in small batches of three to five, grouped by what the recorded model did. For each, show both answers in one or two lines and ask: "The recorded model did X; the candidate did Y. Which is right?" Offer: recorded correct, candidate correct, both acceptable, both wrong, unsure.

Store each answer as an annotation on the node, so the decision is recorded and reusable. Use the exact command in the contract reference. Stop when the user wants to; record how many were reviewed.

## 6. Recommend

End with a recommendation, not a decision:

- which calls or tools can move to which candidate, with the evidence (agreement against the reference, reviewed disagreements, cost saved per month);
- which should stay on the current model, and why;
- what still needs a check (few samples, many failures, inferred schemas, reasoning-heavy steps).

Give the configuration change needed to switch, as the base URL and model name the agent would use, and do not apply it. Offer `kitaru-replay-experiment` for a full-agent replay of the change when the agent's adapter supports model overrides.
