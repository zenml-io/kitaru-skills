# Model-swap contract

Exact commands, parameters, and outputs for the `kitaru/model-swap` analyzer.
Verify against `kitaru schema` and `kitaru analyzer list` when the installed
version differs.

## Commands

Prefix every command with `KITARU_ACTIVE_SKILL=kitaru-model-swap` and add
`--output json --machine --non-interactive --no-browser`.

Run on an existing import. A dry run finishes quickly; for the paid run, wait up
to 900 seconds (the default local wait is 300) and pass an idempotency key, such
as `model-swap-IMPORT_ID-1`, that is new for each approved run:

```bash
kitaru import analyze IMPORT_ID \
  --analyzer kitaru/model-swap@latest \
  --analyzer-params 'kitaru/model-swap@latest=PARAMS_JSON' \
  --idempotency-key IDEMPOTENCY_KEY \
  --wait --timeout 900
```

A finished run returns a receipt with the settled `job` and its `tasks`. When
the local wait expires first, the command fails with error kind `timeout` and
`details.job_id`, `details.remote_continues: true`: the analysis is still
running on the worker. That is not a failure. Follow the job instead of
rerunning:

```bash
kitaru job watch JOB_ID --timeout 900
kitaru job get JOB_ID
```

Repeating the exact same `import analyze` command with the same idempotency key
returns the original job rather than starting, and paying for, a second
analysis. Use a new key only for a run the user has approved separately.

To run it as part of a new import instead, select it with
`kitaru session import ... --analyzer kitaru/model-swap@latest --analyzer-params 'kitaru/model-swap@latest=PARAMS_JSON'`.

Render the report (no model call):

```bash
kitaru insight report --import-id IMPORT_ID --out model-swap-report.html
```

The report renders the most recent model-swap run of the import; session links
use the dashboard URL the server reported when the analysis ran. The full
structured report is in the `metadata["kitaru.model_swap/v1"]` field of the
`model-swap-summary` insight, next to the rendered section under
`kitaru.report_section/v1`:
`kitaru insight list --filter '{"field":"import_id","op":"eq","value":"IMPORT_ID"}' --name model-swap-summary`.

Keys, set by the user in their own shell. The user exports each key first, so
the Kitaru command carries only a variable reference. `read -rs` keeps the key
off the screen and out of shell history; a plain `export NAME=...` also works
but is recorded in history unless the shell is set to skip it:

```bash
# Run by the user, never by the agent; paste the key when prompted.
read -rs OPENROUTER_API_KEY && export OPENROUTER_API_KEY
kitaru connection create model-swap-keys --provider model-swap \
  --set-secret OPENROUTER_API_KEY="$OPENROUTER_API_KEY" --default
```

The analyzer's provider is `model-swap`, so a default connection for that
provider is injected into its task. `kitaru connection get model-swap-keys`
lists `secret_keys` without values.

When an existing connection lacks a key a candidate needs, the user adds it with
`update`. An update replaces the whole secret map, so pass every key the
connection should keep, each from an exported variable:

```bash
kitaru connection update model-swap-keys \
  --set-secret OPENAI_API_KEY="$OPENAI_API_KEY" \
  --set-secret OPENROUTER_API_KEY="$OPENROUTER_API_KEY"
```

Every decision model, whether the judge or a decision candidate, needs its key
in the same connection, added the same way: `TYPESAFE_API_KEY` for Jev and
`OPENAI_API_KEY` for OpenAI Decisions (these defaults apply only on the default
URL); Clef always needs the variable named in its `api_key_env`, such as
`CLOUDFLARE_API_TOKEN`, and so does any decision model with a custom
`base_url`. Add it with `update`, passing every key the connection already
holds alongside it:

```bash
kitaru connection update model-swap-keys \
  --set-secret OPENAI_API_KEY="$OPENAI_API_KEY" \
  --set-secret OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  --set-secret TYPESAFE_API_KEY="$TYPESAFE_API_KEY"
```

A missing judge key fails the whole analysis at the start.

## Parameters

```json
{
  "dry_run": false,
  "max_spend_usd": "2",
  "max_calls": 100,
  "candidates": [
    {
      "name": "gpt-5-nano",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-5-nano",
      "api_key_env": "OPENAI_API_KEY",
      "reference": true
    },
    {
      "name": "qwen3-32b",
      "base_url": "https://openrouter.ai/api/v1",
      "model": "qwen/qwen3-32b",
      "api_key_env": "OPENROUTER_API_KEY",
      "open_weights": true
    },
    {
      "name": "qwen3-local",
      "base_url": "http://localhost:11434/v1",
      "model": "qwen3:8b",
      "price": {"input_per_mtok": "0", "output_per_mtok": "0"},
      "provider_settings": {"max_tokens": 2048, "max_tokens_field": "max_tokens"}
    }
  ]
}
```

| Parameter | Default | Notes |
|---|---|---|
| `candidates` | `[]` | 0 to 8; give `candidates`, `decision_candidates`, or both; names unique across both lists. At most one `reference`. |
| `dry_run` | `false` | Estimates only. |
| `max_spend_usd` | none | Requires a known price for every candidate, every decision candidate, and the judge; the analyzer refuses the run otherwise. Decision models have no bundled price, so give each decision candidate and a decision judge an explicit `price`. When a candidate sets `max_tokens`, each call reserves its full `max_tokens` output, and the analyzer refuses to start if one call's reservation alone exceeds the cap. |
| `max_calls` | `100` | Sample spread across node names and models. |
| `tool_schemas` | `{}` | Tool name to parameters JSON schema. |
| `tool_descriptions` | `{}` | Tool name to description. |
| `use_recorded_tools` | `true` | Use definitions recorded on the call. |
| `infer_missing_schemas` | `false` | Loose schemas from recorded arguments; reported separately. |
| `sessions_per_month` | derived | Needed for monthly cost when the import spans less than a day. |
| `decision_candidates` | `[]` | 0 to 4 decision models answering the decision parts of each decision or partial call: `{"name": "jev", "kind": "jev", "price": {...}}`, same fields, defaults, and key rules as a decision `judge` (without `equivalent_at`), plus a `name` unique across both candidate lists. They run first, before the LLM candidates, sharing `max_spend_usd` and `time_budget_seconds`; the LLM candidates get what is left. Their dry-run estimate is at `decision_candidates[].estimate`. |
| `judge` | none | Rules on `same_tool_different_args` and `different_text` disagreements only, never on a different tool choice, and orders the review. A decision model: `{"kind": "jev"}` (TypeSafe, key `TYPESAFE_API_KEY`, default model `jev-latest`; may require early access), `{"kind": "clef", "base_url": "https://api.cloudflare.com/client/v4/accounts/ACCOUNT_ID/ai/run/@cf/cloudflare/clef", "api_key_env": "CLOUDFLARE_API_TOKEN"}` (always pass `base_url`, the account's run URL, and `api_key_env`; model `clef` (default) or `clef-flash`), or `{"kind": "openai_decisions"}` (key `OPENAI_API_KEY`, default model `gpt-6-luna`). Every kind has a default model (`jev-latest`, `clef`, `gpt-6-luna`), and an explicit `null` for any field falls back to its default. Optional `equivalent_at` (above 0.5, up to 1; default 0.8), `model`, `api_key_env`, `base_url`, `price`, `timeout_seconds`. When `base_url` is overridden, `api_key_env` must be given explicitly; no default key is sent to a custom URL. Give `price` whenever `max_spend_usd` is set, since decision models have no bundled price. Or a candidate-shaped chat model without `kind`. Judge spend counts against `max_spend_usd` and its time against `time_budget_seconds`; the dry-run estimate leaves judge spend out. |
| `concurrency` | `4` | Up to 32. |
| `time_budget_seconds` | `600` | Up to 840; the task times out at 900 seconds. Shared by decision candidates (first), LLM candidates, and the judge. |
| `max_disagreements` | `200` | Kept in the report. |
| `min_mix_calls` | `20` | Answered calls a candidate needs on a step before the best mix can move that step to it; smaller steps stay on today's model. |
| `repeats` | `1` | 1 to 5 attempts per call per candidate; agreement, judge and disagreements use the first; per-candidate `consistency` gives `any_match_rate` and `all_match_rate`. Multiplies calls and spend. |
| `excluded_origins` | `{}` | Map of `lab`, `lab_country`, `host`, `host_region` to disallowed values (case-insensitive), e.g. `{"lab_country": ["CN"]}`. Excluded candidates are compared but never recommended. |

Candidate fields: `name`, `base_url`, `model`, `origin` (`lab`, `lab_country`, `host`, `host_region`; declared, not verified), `api_key_env` (a variable name,
never a key), `reference` (today's model), `open_weights` (true for open-weight
models), `price` (`input_per_mtok`, `output_per_mtok`, optional
`cached_input_per_mtok`, USD strings), `price_provider` (for example `openai`,
for the bundled price lookup), `provider_settings`.

`provider_settings`: `api` (`chat_completions`, default, or `responses` for
OpenAI's `/responses`, which OpenAI's reasoning models need to call tools with
reasoning on; tool calls then come back natively, so leave `tool_call_format`
at `native`), `tool_call_format` (`native`, `hermes`, `json_content`),
`reasoning_effort`, `max_tokens`, `max_tokens_field` (`max_completion_tokens` or
`max_tokens`), `temperature`, `extra_body`, `timeout_seconds` (default 120),
`max_retries` (default 1).

## Report fields

Run-level: `best_for`, a list of `{goal, candidate, why}` for "Closest to
today", "Cheapest", "Fastest" and "Best open model" (cheapest and fastest only
among candidates within 10 points of the closest match; candidates failing over
20% of calls are excluded).

Per candidate: `name`, `model`, `reference`, `price` (null when no price is
known; the rendered dry run then shows "unknown price"), `open_weights`,
`summary`, `calls_sent` (calls sent to the candidate, including failures),
`answered` (calls with a comparable reply, excluding calls with inferred tool
schemas), `agreement` (counts per category over `answered`), `agreement_rate`
(exact), `agreement_interval`, `tool_choice_rate`, `tool_choice_interval`
(each interval a Wilson 95% `[low, high]`, null with no calls),
`judged_equivalent`, `judged_different`,
`judged_unsure`, `judge_failures` (failure category to count, for judge calls
that did not return a ruling), `failures`, `failure_examples`
(one detail per category, such as `HTTP 404`) and `failure_rate`, `by_tool`
(agreement and per-argument agreement), `latency_seconds`, `tokens_per_call`,
`retries`, `cost` (`per_call_usd`, `per_session_usd`, `per_month_usd`),
`calls_not_run`. Dry runs carry `estimate` instead.

Agreement categories: `same_tool_same_args`, `same_tool_different_args`,
`different_tool`, `text_instead_of_tool`, `same_text`, `different_text`,
`tool_instead_of_text`.

Coverage: `llm_calls_seen`, `replayable`, `replayable_inferred`, `sampled`,
`skipped` by reason (`missing_tool_schema`, `unsupported_input_format`,
`non_text_content`, `unrecognized_recorded_output`, `failed_recorded_call`,
`missing_inputs`), `schema_sources`, `calls_with_dropped_reasoning`.

Each disagreement: `candidate`, `session_id`, `node_id`, `node_name`, `group`,
`agreement`, `schema_source` (`recorded`, `supplied`, `inferred`, or `none`),
`recorded`, `candidate_answer` (both truncated excerpts), `judge_equivalent`
(true, false, or null when unsure or not judged), `judge_probability` (decision
judges only), `judge_failure` (the failure category when the judge call failed,
otherwise null). Which disagreements the report keeps is chosen independently
of the judge, first by group and then by candidate; within each group they are
then ordered different, then unsure or not judged, then equivalent. The list
includes calls with inferred schemas, which `answered` and `agreement` leave
out.

Run-level: `disagreements` (at most `max_disagreements` entries),
`disagreements_total` (all disagreements across candidates before truncation,
including inferred-schema calls), `stopped_early` (`max_spend`, `time_budget`,
or null), `spent_usd`, `notes`.

The run identity is the `id` of the `model-swap-summary` insight that carries
the report. Dry runs also write one, so for review use the newest summary whose
report has `dry_run: false`, and record its `id` with every verdict.

## Recording a review verdict

Annotate the disagreeing node:

```bash
kitaru annotation create \
  --session SESSION_ID \
  --selector '{"node_id": "NODE_ID"}' \
  --value '{"model_swap": {"run": "INSIGHT_ID", "candidate": "qwen3-local", "model": "qwen3:8b", "verdict": "candidate_correct", "note": "Both refunds are valid; the candidate asked for the order first."}}'
```

`run` is the `model-swap-summary` insight `id` and `model` is the candidate's
`model` from the report, so a verdict from an earlier run, or for a candidate
name later reused with another model, is never matched to the wrong answer.
`verdict` is the user's exact choice: one of `recorded_correct`,
`candidate_correct`, `both_acceptable`, `both_wrong`, `unsure`. Keep `note` to
the user's own words.

List a session's annotations later (up to 1000 per page; follow `--cursor` when
more remain):

```bash
kitaru annotation list \
  --filter '{"field":"session_id","op":"eq","value":"SESSION_ID"}' \
  --size 1000
```

## Limits

- Supported message shapes: OTel GenAI parts and OpenAI chat messages.
  Anthropic-format and LangChain-serialized messages, images, failed calls, and
  calls without inputs are skipped and counted.
- Recorded reasoning parts are not sent to candidates.
- Native-adapter recordings carry no tool definitions; pass `tool_schemas`.
- The analyzer needs network access from the worker to each endpoint.

## Data sent to decision services

A decision candidate is sent, for each call it answers, the rebuilt
conversation (including the system prompt and tool results), the tool names and
descriptions, argument names, and enum values. A judge is sent both answers it
compares. Recorded trace content therefore leaves the worker for that service
(TypeSafe, Cloudflare, or OpenAI). Tell the user before they opt in.

## Decision-model fit

Every report carries `decision_shapes`: `calls`, `decision`, `partial`,
`generative` counts, `recorded_cost_share` per shape, `reasons` (why calls are
not fully decisions, such as `free-form arguments: order_id` or `several tool
calls at once`), and `by_node`. Calls with inferred tool schemas are classified
generative, because inferred schemas are not trusted for decisions.

Each entry of `decision_candidates` in the report has `name`, `kind`, `model`,
`price`, `calls_asked`, `calls_not_run` (calls left unrun when the spend cap or
time budget ran out), `answered`, `failures`, `tool_choice_rate`,
`argument_rates` (per enum or boolean argument), `decisions_match_rate` (all
decisions of a call matched), `decision_calls` and
`decision_calls_match_rate`, `cost_per_call_usd` (over all asked calls,
decision parts only), `decision_call_cost_usd` and
`recorded_decision_call_cost_usd` (only calls whose shape is `decision`), and
`latency_p50_seconds`. Dry runs carry `estimate` (`calls`, `spend_usd`) at
`decision_candidates[].estimate` instead.

For savings, compare `decision_call_cost_usd` with
`recorded_decision_call_cost_usd`: a decision model can replace the recorded
model entirely only on decision-shaped calls. `cost_per_call_usd` covers just
the decision parts of partial calls, which still need an LLM for the rest, so
never compare it with a full recorded cost per call.

## Best mix and cost per task

Run-level `best_mix` (null in dry runs or when no step can move) has `groups`,
one per step, each with `group` (the step, named by what comes just before the
call and so visible to a router: `first turn`, `after a user message`, or
`after TOOL` for the tool result the model is reading), `share` of sampled
calls, `calls`, `candidate` (null means today's model), `rate`,
`cost_per_call_usd`, `too_few_calls` (no candidate answered `min_mix_calls` of
the step's calls) and `noisy_reference` (today's model does not match its own
recording there, so nothing can move). Run-level fields: `min_calls`,
`today_source` (`reference replay` when a reference candidate ran, since
recorded calls often hit a warm prompt cache that replays do not, otherwise
`recording`), and `cost` and `recorded_cost` projections. A step moves only to a
non-excluded, non-reference candidate that answered at least `min_mix_calls` of
its calls, whose kind of action there (same tools, or a text answer) matches
within 10 points of the reference's, and that is cheaper than today.
`best_for` then includes a "Best mix" row. Treat the mix as a shortlist to
confirm with a full replay.

Per candidate, `excluded`, `origin`, `consistency` (null unless `repeats` > 1)
and `tokens_per_call` (input, cached input, output, reasoning) are reported.
The `notes` always say per-session and monthly costs assume the recorded number
of steps; cost per task needs a full replay.
