# Capability contract

Read this file during preflight and whenever a command or API assumption is
uncertain. Verify the installed Kitaru version and local `--help` output before
using a copied command.

## Shipped workflow

| Capability | Current contract |
|---|---|
| JSONL import | Import one or more Langfuse traces from an observations JSONL export. |
| Remote import | Fetch one known `langfuse://trace/<id>` through Langfuse's observations API. |
| Preview | Import is dry-run by default. It validates the selection and reports what would be stored. |
| Storage | Writing requires `--write --confirm-data-storage`. Raw rows can contain sensitive data. |
| Attribution | Each import declares one registered Agent and one exact AgentVersion. |
| Imported record | The imported execution is immutable historical evidence. Native checkpoint resume, retry, and cancel are refused. |
| Imported replay | A registered PydanticAI `KitaruAgent` can replay from root input or a validated message-history boundary. |
| Recorded tools | A recorded response is served only when tool name and arguments match exactly. A miss is blocked and never calls the original tool callable. |
| Evaluation | Objectives and agent protections produce a persisted experiment and a PASS, HOLD, or FAIL verdict. |
| Bounded rerun | `RegressionLimits` can limit trials, reported cost, reported tokens, and duration between trials. |
| CI assertion | `result.assert_pass()` raises for HOLD and FAIL. |
| Idempotency | An identical logical request with the same idempotency key returns the stored attempt instead of submitting another trial. |

## Unsupported or narrower than the product story

- Kitaru does not list, search, or rank remote Langfuse traces. It fetches an
  exact trace ID. Trace discovery must come from the user, a JSONL export, the
  Langfuse UI, or a host-provided Langfuse/browser integration.
- Treat imported replay as PydanticAI-only unless the installed Kitaru docs
  explicitly establish another adapter.
- Root-input replay is a counterfactual. It does not establish recorded-path
  comparability.
- A message-history replay requires a complete adapter-validated model-message
  or tool-result boundary.
- There is no generic visual editor for replacing arbitrary imported checkpoint
  outputs. Do not describe candidate replay as arbitrary checkpoint mutation.
- Operational limits do not interrupt provider calls already running inside one
  trial. Tool turns and output retries can make the final trial exceed a cost or
  token threshold before Kitaru can stop a later trial.
- Do not promise Langfuse score writeback, derived investigation status,
  fixture-staleness verification, synthetic case generation, or generic replay
  across every adapter.
- Making a test part of a required merge gate is a repository and CI setting,
  not an effect of `assert_pass()` alone.

## Import commands

For a JSONL preview:

```bash
kitaru import langfuse <export.jsonl> \
  --source-project-id <project-id> \
  --agent <agent-name> \
  --agent-version <exact-version> \
  --stack <exact-stack-name-or-id>
```

For a known remote trace:

```bash
kitaru import langfuse "langfuse://trace/<trace-id>" \
  --agent <agent-name> \
  --agent-version <exact-version> \
  --stack <exact-stack-name-or-id>
```

The remote form reads `LANGFUSE_PUBLIC_KEY`,
`LANGFUSE_SECRET_KEY`, and optionally `LANGFUSE_BASE_URL` or
`LANGFUSE_HOST`. Never print their values.

Show the exact stack selector and its reported storage accessibility in the
consent card. Reuse the identical preview command for the write so the
destination cannot drift.

After the preview and explicit consent, append:

```text
--write --confirm-data-storage
```

Accept only a successful `created`, `resumed`, or `unchanged` outcome with
an exact imported execution ID.

## Imported replay API

Root-input diagnostic:

```python
result = candidate.replay(
    imported_execution_id,
    imported_mode="root_input",
    on_error="collect",
    idempotency_key=key,
    repeats=1,
    scorers=[objective],
)
```

Comparable message-history attempt:

```python
result = candidate.replay(
    imported_execution_id,
    imported_mode="message_history",
    imported_boundary=boundary,
    on_error="collect",
    idempotency_key=key,
    repeats=1,
    scorers=[objective],
)
```

Build `boundary` from immutable replay evidence using
`ImportedReplayBoundary` and validate it with
`prepare_imported_replay_history(...,
fallback_policy=ImportedReplayFallbackPolicy.BLOCK)`.

Rerun an exact frozen experiment:

```python
from kitaru import RegressionLimits

rerun = candidate.replay(
    experiment=experiment_id,
    idempotency_key=key,
    repeats=1,
    scorers=[objective],
    limits=RegressionLimits(
        max_trials=1,
        max_cost_usd=approved_cost,
        max_incurred_tokens=approved_tokens,
        max_duration_seconds=approved_seconds,
    ),
)
rerun.assert_pass()
```

Prefer the exact experiment ID over a suite name once the evidence becomes a
regression gate.
