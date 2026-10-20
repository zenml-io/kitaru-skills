---
name: kitaru-model-swap
description: Help a user choose the right model for their agent from its own recorded traces, comparing quality, cost, speed, and openness. Use when a user asks which model is best for their agent, whether to switch or upgrade models, how an open, local, Ollama, cheaper, faster, or newer model would do, how to cut LLM cost or avoid provider lock-in, or wants to compare models on production traffic before shipping a change. Imports traces, sends each recorded model call to candidate models with the kitaru/model-swap analyzer, renders an HTML report, collects the user's verdicts on the differences, scores quality from those verdicts, and hands finalists to a replay experiment when the agent supports it.
---

# Kitaru model swap

Help the user choose the right model for their agent: better, cheaper, faster, or open. Kitaru sends each recorded model call, exactly as it was recorded, to candidate models and compares their answers. It does not re-run the agent, and it runs on the user's worker with the user's keys. The user's own verdicts on the differences decide quality; a replay experiment confirms the finalists end to end.

Recommend; do not decide. Never change the agent's configuration yourself.

## Core contract

- Run every Kitaru CLI command with `KITARU_ACTIVE_SKILL=kitaru-model-swap` set, and prefer `--output json --machine --non-interactive --no-browser`.
- Never ask for, read, echo, or store an API key in chat, files, parameters, or command lines you show. Keys go into a Kitaru provider connection through a command the user runs themselves, or into the worker's environment. Candidates only name the variable.
- Always run a dry run first and get explicit approval of the estimated spend before a run that calls paid endpoints. Always pass `max_spend_usd` on a paid run.
- Include the model the agent uses today as the `reference` candidate. It is compared like the others, and its agreement with its own recording is the noise floor.
- Agreement means "behaves like today's model", not "is right". Never present agreement as quality on its own; quality comes from the user's verdicts.
- Report provider failures (timeouts, rate limits, HTTP errors, empty replies, tool-call parse errors, refusals) as setup problems, never as model quality.
- Keep inferred tool schemas out of conclusions; say how many calls used them.
- Use Kitaru product terms: agent, session, node, import, analyzer, insight, connection, worker, annotation, cohort, evaluator, replay.

## Load references only when needed

- Read [references/model-swap-contract.md](references/model-swap-contract.md) before running any Kitaru command in this skill: exact commands, analyzer parameters, report fields, and annotation shape.
- Read [references/tool-schemas.md](references/tool-schemas.md) when the coverage shows `missing_tool_schema` skips, or before importing traces that are known to lack tool definitions.
- Read [references/verdict-quality.md](references/verdict-quality.md) before step 5 and whenever you report quality.

## 1. Set up and import

1. Check `kitaru status`. If Kitaru is missing or not logged in, install it (`uv add "kitaru[cli,worker]"`) and log in: `kitaru login --local` for a local server, or `kitaru login` / `kitaru login SERVER` for a managed or team server. Ask which one the user wants when it is not obvious.
2. Make sure a worker that claims analyzer tasks is running (`kitaru worker start --claim importer --claim analyzer --concurrency 10`). A local Ollama candidate needs the worker on the same machine as Ollama.
3. Find or register the agent, then import a recent, bounded slice of traces: the last 7 days from the user's trace provider through its importer and connection, or a JSONL export file. Use the matching Kitaru import guide for the provider. Route unsupported sources to `kitaru-importer-builder`.
4. Note the `import_id`.

If the user already has an import, reuse it.

## 2. Ask what matters, then choose candidates

Ask one question: what matters most for this agent right now: better answers, lower cost, faster replies, or not being locked to one provider? Several answers are fine. Use it to pick candidates and to lead the summary later.

Suggest a small set, one line each, covering those goals:

- the model the agent uses today, as the `reference`;
- one open-weight model on a hosted provider (`"open_weights": true`);
- one local model if Ollama is installed (`ollama list` shows what is available; base URL `http://localhost:11434/v1`, price zero, `"open_weights": true`);
- one cheaper tier and, when quality matters, one stronger model from the current provider.

For each paid candidate, find which environment variable will hold its key. If no connection exists, give the user the exact `kitaru connection create model-swap-keys --provider model-swap --set-secret NAME=... --default` command to run themselves, with placeholders instead of values. Then confirm the connection lists the expected `secret_keys` without reading values.

Ask about provider settings only when relevant: a model served without a tool-call parser needs `tool_call_format: "hermes"`; reasoning models may need `reasoning_effort`.

## 3. Estimate, approve, run

1. Run the analyzer with `"dry_run": true`, render the report, and show the user: calls per candidate, estimated spend per candidate and in total, and coverage (replayable versus skipped calls).
2. If coverage shows `missing_tool_schema`, follow [references/tool-schemas.md](references/tool-schemas.md) before going on.
3. Ask for approval of the spend and a cap. Run again without `dry_run` and with `max_spend_usd`.
4. If the run stopped early (`max_spend` or `time_budget`), say so and offer to rerun with a smaller `max_calls` or a higher cap.

## 4. Show the comparison

Render `kitaru insight report --import-id IMPORT_ID --out model-swap-report.html` and give the user the path. Lead with the report's **Best for** rows, ordered by what the user said matters, then summarize each candidate in plain words:

- how often it picks the same tool or gives the same answer as today's model, read against today's model's own noise floor, and per-argument agreement on structured fields;
- cost per call and per month, and why (price, tokens, reasoning tokens, retries);
- median and tail latency;
- whether it is open-weight;
- failures by category and what to change in provider settings.

Say plainly that these are similarities to today's model, and that the next step decides which answers are right.

## 5. Judge the differences

Walk through the disagreements in small batches of three to five, grouped by what the recorded model did, starting with the candidates the user is most interested in. For each, show both answers in one or two lines and ask: "Today's model did X; this candidate did Y. Which is right?" Offer: recorded correct, candidate correct, both acceptable, both wrong, unsure.

Store each answer as an annotation on the node with the exact command in the contract reference. Stop when the user wants to; then compute and show the verdict-backed quality per candidate following [references/verdict-quality.md](references/verdict-quality.md), including how many disagreements were reviewed. A candidate that differs from today's model can score higher than it.

## 6. Prove the finalists

Pick one or two finalists with the user from the verdict-backed quality and the goals from step 2.

Check whether the agent can replay with a model override: `kitaru agent version get AGENT@VERSION` and read `runtime_capabilities.overrides` in its run spec (it defaults to true when absent).

- **Overrides supported** (the agent records through an adapter such as Pydantic AI or OpenAI Agents): create a cohort from the reviewed sessions (`kitaru cohort create NAME --agent AGENT --session SESSION ...`), and hand off to the `kitaru-replay-experiment` skill with the cohort version, the finalist as the model override, and the user's verdicts as the accepted behavior for choosing or authoring an evaluator. That skill owns the tool policy, approval, and interpretation.
- **Overrides not supported** (imported, importer-backed agents): say that a full replay is not available for this agent, so the step-level comparison and verdicts are the evidence. Explain that recording the agent through a Kitaru adapter would make end-to-end replay possible, and offer `kitaru-adapter-builder` when the user wants that.

## 7. Recommend

End with a recommendation, not a decision, framed by the user's goals:

- the best candidate for each goal they named, with the evidence: verdict-backed quality and how many verdicts back it, cost per month, latency, openness, and replay results when available;
- calls or tools where today's model should stay, and why;
- what still needs a check: few reviewed disagreements, many failures, inferred schemas, reasoning-heavy steps.

Give the configuration change needed to switch, as the base URL and model name the agent would use, and do not apply it. Suggest rerunning the comparison on new traces when models or traffic change.
