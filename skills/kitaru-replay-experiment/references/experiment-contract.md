# Current Kitaru experiment contract

Verify the installed CLI, MCP schemas, API models, and adapter documentation before operating. This reference describes the current v2 contract and may age.

## Honest replay semantics

An experiment run creates one fresh agent task per session in an exact cohort version. The task receives the historical session's stored top-level inputs after applying the experiment replay override. The override can replace the model, system prompt, prompt, or model parameters when the selected adapter construction path supports it.

This path does not restore an arbitrary conversation checkpoint, process memory, adapter instance state, filesystem, external service state, or other hidden world state. Explain every material missing state before asking the user to run the experiment.

## Experiment and run operations

Prefer these current MCP operations:

| Need | MCP operation |
|---|---|
| Read exact registry resources and versions | `kitaru_registry_read` |
| Create or update an experiment | `kitaru_experiments_manage` |
| Start an experiment run | `kitaru_workflow_start` with `operation=experiment_run` |
| Read runs, per-case replays, and replay jobs | `kitaru_activity_read`: `get` kind `experiment_run`, `list` kind `replay` filtered by `experiment_run_id`, `list_children` kind `experiment_run_jobs` |
| Request cancellation | `kitaru_workflow_cancel` with `operation=experiment_run`, available only in destructive MCP mode; otherwise use `kitaru experiment run cancel` |

The structured CLI equivalents are:

```text
kitaru experiment create NAME --agent AGENT --evaluator EVALUATOR@VERSION --evaluator-params 'EVALUATOR@VERSION={"threshold":0.8}' ...
kitaru experiment get EXPERIMENT
kitaru replay create BASELINE_UUID --evaluator EVALUATOR@VERSION --evaluator-params 'EVALUATOR@VERSION={"threshold":0.8}' --baseline-evaluation-mode if_missing
kitaru experiment run start EXPERIMENT --cohort-version UUID --agent AGENT@VERSION --baseline-evaluation-mode if_missing
kitaru experiment run get RUN_UUID --aggregate
kitaru replay list --filter '{"field":"experiment_run_id","op":"eq","value":"RUN_UUID"}'
kitaru experiment run jobs RUN_UUID
kitaru experiment run watch RUN_UUID
kitaru experiment run cancel RUN_UUID
```

Use JSON objects for `--override` and `--tool-policy`. `experiment create` and `replay create` accept `--evaluator-connection EVALUATOR@VERSION=CONNECTION` for an evaluator that needs a non-default provider connection; MCP evaluator selections carry only `evaluator_id`, `version`, and `params`, so create such an experiment through the CLI. Repeat `--evaluator-params 'EVALUATOR@VERSION=JSON_OBJECT'` for configured evaluators that need parameters; each token must exactly match a selected `--evaluator` token. Verify `kitaru schema` or installed help before relying on example syntax. Creating an experiment and starting a run are non-idempotent remote writes. Watching is read-only. Cancellation requests settlement but does not wait. Deleting a run immediately removes its replay jobs and tasks and is not a cancellation mechanism.

An experiment requires at least one exact evaluator selection; MCP experiment create and update accept at most 10. An omitted evaluator version resolves to latest in the API model, but this skill always pins a version. Configuration can be updated only before the experiment has runs; use a new experiment for a changed condition afterward.

An evaluator parent gets its agent scope at creation, and evaluator updates or version registration cannot change it. A non-null value limits it to experiments, replays, and single-agent evaluation batches for that exact agent. A null `agent_id` means the evaluator was created workspace-global; agent deletion has been a soft delete since Kitaru 0.24.0 and leaves a scoped evaluator's `agent_id` in place. Before creating the experiment, re-read every parent and confirm that a global evaluator's criterion, implementation, and intended reuse fit the experiment's agent. Exclude it when that fit cannot be established.

## Replay configuration

Current replay override fields are `model`, `system_prompt`, `prompt`, and `model_params`.

The agent version's run spec declares `runtime_capabilities`. `overrides` and
`tool_policies` both default to `true`. Before creating a replay or experiment,
read the declaration and compare it with the requested configuration:

| Declaration | Allowed configuration |
|---|---|
| `overrides: false` | No replay override |
| `tool_policies: false` | Explicit `passthrough` for the default and every named tool |

The server rejects an incompatible replay or experiment configuration with 422.
An importer-backed adapter cannot intercept model or tool calls because it
imports the provider trace after the agent runs. Its agent version must declare
`runtime_capabilities: {overrides: false, tool_policies: false}` in the run
spec; the user writes this, and the fields otherwise default to `true`. Without
the declaration the server accepts an override or substituting policy, and the
adapter fails the replay at task time. It can only perform an unchanged fresh
run with live tools. Do not treat an
`on_miss` setting as a workaround: history and static policies themselves are
not allowed.

A tool policy has a required `default` configuration and optional per-tool overrides. Current configurations are:

- `passthrough`: execute the live tool;
- `history`: read a recorded call from `baseline`, `cohort_version`, or `agent` scope;
- `static`: return the first matching exact or subset case;
- `llm`: generate a synthetic tool result with a named model. The API stores this configuration, but no shipped adapter executes it: the PydanticAI, LangGraph, OpenAI Agents, Claude Agent SDK, Mastra, and Vercel AI adapters all reject it, so every replay would fail. Use `static` cases for simulated results unless the installed adapter's documentation says it supports `llm`.

History and static misses support `fail`, `error_result`, or `passthrough`. Omitted experiment tool policy currently resolves to passthrough. Require an explicit policy for a tool-using run.

History lookup matches tool name plus canonical JSON arguments. With baseline scope, a zero-based `occurrence` selects the nth match in recorded order, so repeated identical calls replay their own results. Without `occurrence`, every scope returns its latest match. Wider scopes reject a set `occurrence`. A match does not prove that a stateful or time-sensitive result is faithful. Broader scopes can borrow data from another case.

## Adapter capability boundary

Resolve the installed adapter, exact version, and construction path. Current examples that must be re-verified:

- OpenAI Agents supports `passthrough`, `static`, and `history` overrides for named ordinary, direct, enabled, non-approval `FunctionTool`s on the starting agent. The policy `default` must be `passthrough`. History rejects a tool with an SDK timeout. LLM, hosted, MCP, programmatic, agent-as-tool, and handoff-target substitutions are rejected.
- LangGraph support differs between a direct compiled-graph wrapper and a supported factory path. The factory path can install model and tool middleware; direct wrappers reject unsupported overrides instead of guessing.
- PydanticAI projects the recorded prompt and message history into the replayed run by default. With `use_task_inputs_as_prompt=False` (kitaru-pydantic-ai 0.4.0), the application supplies the conversation instead. History held elsewhere, such as on an agent instance, is not restored.
- Claude Agent SDK substitutes only tools declared through `replayable_sdk_mcp_server()`. A substituting policy must use an empty `static` default with `on_miss: fail`. The server accepts a `model_params` override, but the adapter rejects it at run start.
- Vercel AI replays non-streaming `generate()` and `generateText` with `history`, `static`, or `passthrough` for local executable tools. Agent `stream()` rejects during replay; provider-executed, dynamic, and approval-gated tools are unsupported.
- Mastra replays `generate()` and `stream()` and replays memory-dependent calls from a recorded conversation snapshot. Working and observational memory need the opt-in `createMemoryReplayAgent()` factory, which accepts only the exact Mastra release sets its documentation lists.
- Importer-backed adapters for Langfuse, Braintrust, LangSmith, Logfire, and
  Arize Phoenix import a completed provider trace. Their run specs disable
  overrides and non-passthrough tool policies.

See the version-matched [adapter documentation](https://docs.zenml.io/kitaru/adapters) for each adapter's full replay contract. Unsupported capability is a blocker. The user cannot approve past it.

## Mutable and asynchronous state

An agent version's public run spec and capabilities can currently be updated in place. Canonically serialize and hash the complete public models recorded for approval, then re-read them immediately before creation and execution. Do not inspect secret values. If a hash changes, invalidate approval and explain that the configuration changed. Treat the hash as an internal comparison mechanism, not a Kitaru object or user-facing concept. These reads do not freeze the configuration a worker later resolves, and a transient mutation can escape pre-run and post-run checks. Require immutable runtime identity for a user-defined gate or live-effect run; otherwise narrow the use to exploration, report this residual risk, and return `cannot evaluate` for the gate.

Experiment runs are asynchronous and report `running`, `canceling`, `completed`, `failed`, or `canceled`. Progress counts pending, evaluating, completed, failed, canceled, and total replays. A run settles `failed` when any replay failed or was canceled, so read per-case outcomes rather than treating `failed` as no completed cases. For complete accounting, page through the run's replays filtered by `experiment_run_id`: each carries `baseline_session_id`, `result_session_id`, `status`, and `error`. Replay jobs carry status and error but no session identity. Since Kitaru 0.27.7, MCP job and experiment-run reads include worker-coverage warnings; check them when a run stays pending.

## Baseline evaluation and provenance

Replay creation and experiment-run start use `baseline_evaluation_mode`, which defaults to `if_missing`:

- `none` does not score the baseline session;
- `if_missing` adopts the latest existing baseline evaluation only when the session, evaluator version, and parameters all match, and otherwise schedules a fresh one; and
- `force` always schedules a fresh baseline evaluation.

Use `if_missing` for the normal comparison. Use `force` only when the hypothesis or evaluator behavior requires measurements recomputed in the current run, because it adds evaluator work and cost. The deprecated REST-only `evaluate_baselines` boolean maps false to `none` and true to `if_missing`; do not use it in current CLI or SDK instructions and never send both fields.

Each replay links the exact baseline and result measurements used for its comparison. Experiment-run aggregates read only those links, so later evaluations of either session cannot change the run's statistics. They group by evaluator version, evaluation name, and data type; manual evaluations are excluded. Read them with `kitaru experiment run get RUN --aggregate`, `client.experiment_runs.get_evaluation_aggregates(...)`, or `GET /api/v1/experiment-runs/{id}/evaluation-aggregates` (public since Kitaru 0.27.3); MCP `kitaru_activity_read` does not return them. Each group exposes evaluator identity and baseline and result stats: `count`, `mean`, `min`, `max`, `pass_rate`, `value_counts` for categorical results, and score-scale values. `min_score`, `max_score`, or `target_score` is null for one side when its linked rows do not all share that field and value. The aggregate retains paired values for the 50 most recent replays; read exact per-session evidence and all of the run's replays for complete paired changes, failures, canceled cases, and missingness.

No public CLI or MCP operation currently computes a winner, release policy, statistical significance judgment, or CI verdict.
