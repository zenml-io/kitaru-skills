# Model-swap contract

Exact commands, parameters, and outputs for the `kitaru/model-swap` analyzer. Verify against `kitaru schema` and `kitaru analyzer list` when the installed version differs.

## Commands

Prefix every command with `KITARU_ACTIVE_SKILL=kitaru-model-swap` and add `--output json --machine --non-interactive --no-browser`.

Run on an existing import:

```bash
kitaru import analyze IMPORT_ID \
  --analyzer kitaru/model-swap@latest \
  --analyzer-params 'kitaru/model-swap@latest=PARAMS_JSON' \
  --wait
```

Or select it on a new import with `kitaru session import ... --analyzer kitaru/model-swap@latest --analyzer-params 'kitaru/model-swap@latest=PARAMS_JSON'`.

Render the report (no model call):

```bash
kitaru insight report --import-id IMPORT_ID --out model-swap-report.html
```

The report renders the most recent model-swap run of the import; session links use the dashboard URL the server reported when the analysis ran. The full structured report is in the `metadata["kitaru.model_swap/v1"]` field of the `model-swap-summary` insight, next to the rendered section under `kitaru.report_section/v1`: `kitaru insight list --filter '{"field":"import_id","op":"eq","value":"IMPORT_ID"}' --name model-swap-summary`.

Keys, created by the user:

```bash
kitaru connection create model-swap-keys --provider model-swap \
  --set-secret OPENROUTER_API_KEY=... --default
```

The analyzer's provider is `model-swap`, so a default connection for that provider is injected into its task. `kitaru connection get model-swap-keys` lists `secret_keys` without values.

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
| `candidates` | required | 1 to 8. Unique `name`. At most one `reference`. |
| `dry_run` | `false` | Estimates only. |
| `max_spend_usd` | none | Requires a known price for every candidate and the judge. |
| `max_calls` | `100` | Sample spread across node names and models. |
| `tool_schemas` | `{}` | Tool name to parameters JSON schema. |
| `tool_descriptions` | `{}` | Tool name to description. |
| `use_recorded_tools` | `true` | Use definitions recorded on the call. |
| `infer_missing_schemas` | `false` | Loose schemas from recorded arguments; reported separately. |
| `sessions_per_month` | derived | Needed for monthly cost when the import spans less than a day. |
| `judge` | none | Candidate-shaped model ruling on argument or text differences. |
| `concurrency` | `4` | Up to 32. |
| `time_budget_seconds` | `600` | Up to 840; the task times out at 900 seconds. |
| `max_disagreements` | `200` | Kept in the report. |

Candidate fields: `name`, `base_url`, `model`, `api_key_env` (a variable name, never a key), `reference` (today's model), `open_weights` (true for open-weight models), `price` (`input_per_mtok`, `output_per_mtok`, optional `cached_input_per_mtok`, USD strings), `price_provider` (for example `openai`, for the bundled price lookup), `provider_settings`.

`provider_settings`: `tool_call_format` (`native`, `hermes`, `json_content`), `reasoning_effort`, `max_tokens`, `max_tokens_field` (`max_completion_tokens` or `max_tokens`), `temperature`, `extra_body`, `timeout_seconds` (default 120), `max_retries` (default 1).

## Report fields

Run-level: `best_for`, a list of `{goal, candidate, why}` for "Closest to today", "Cheapest", "Fastest" and "Best open model" (cheapest and fastest only among candidates within 10 points of the closest match; candidates failing over 20% of calls are excluded).

Per candidate: `open_weights`, `summary`, `answered`, `agreement` (counts per category), `agreement_rate` (exact), `tool_choice_rate`, `judged_equivalent`, `failures`, `failure_examples` (one detail per category, such as `HTTP 404`) and `failure_rate`, `by_tool` (agreement and per-argument agreement), `latency_seconds`, `tokens_per_call`, `retries`, `cost` (`per_call_usd`, `per_session_usd`, `per_month_usd`), `calls_not_run`. Dry runs carry `estimate` instead.

Agreement categories: `same_tool_same_args`, `same_tool_different_args`, `different_tool`, `text_instead_of_tool`, `same_text`, `different_text`, `tool_instead_of_text`.

Coverage: `llm_calls_seen`, `replayable`, `replayable_inferred`, `sampled`, `skipped` by reason (`missing_tool_schema`, `unsupported_input_format`, `non_text_content`, `unrecognized_recorded_output`, `failed_recorded_call`, `missing_inputs`), `schema_sources`, `calls_with_dropped_reasoning`.

Each disagreement: `candidate`, `session_id`, `node_id`, `node_name`, `group`, `agreement`, `recorded`, `candidate_answer`, `judge_equivalent`.

Run-level: `stopped_early` (`max_spend`, `time_budget`, or null), `spent_usd`, `notes`.

## Recording a review verdict

Annotate the disagreeing node:

```bash
kitaru annotation create \
  --session SESSION_ID \
  --selector '{"node_id": "NODE_ID"}' \
  --value '{"model_swap": {"candidate": "qwen3-local", "verdict": "candidate_correct", "note": "Both refunds are valid; the candidate asked for the order first."}}'
```

`verdict` is one of `recorded_correct`, `candidate_correct`, `both_acceptable`, `both_wrong`, `unsure`. Keep `note` to the user's own words. List them later with `kitaru annotation list --session SESSION_ID`.

## Limits

- Supported message shapes: OTel GenAI parts and OpenAI chat messages. Anthropic-format and LangChain-serialized messages, images, failed calls, and calls without inputs are skipped and counted.
- Recorded reasoning parts are not sent to candidates.
- Native-adapter recordings carry no tool definitions; pass `tool_schemas`.
- The analyzer needs network access from the worker to each endpoint.
