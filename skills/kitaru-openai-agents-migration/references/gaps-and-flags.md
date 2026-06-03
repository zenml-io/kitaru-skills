# OpenAI Agents SDK Migration Gaps and Flags

Use this file when deciding whether a migration is safe to apply automatically.
The rule is: if replay, wait, state, side effects, secrets, or SDK resume
behavior may change, make that visible in code comments and in the migration
report.

## Severity levels

| Severity | Meaning | Required action |
|---|---|---|
| `LOW` | Cosmetic or documentation-only difference. | Migrate and mention in report. |
| `MEDIUM` | Behavior probably preserved, but settings or observability differ. | Migrate with caveat and verification step. |
| `HIGH` | Replay, wait, state, side-effect, or runtime behavior may change. | Require human review before applying or mark partial migration. |
| `BLOCKER` | Migration would be unsafe or impossible without source redesign. | Do not auto-migrate; generate redesign note and report entry. |

## Must-flag patterns

### Missing stable names

- **Severity:** `HIGH`, or `BLOCKER` if no stable name can be chosen.
- **Pattern:** `Agent(...)` without a stable `name=`, generated names based on
  timestamps/random IDs, or runner names that change per run.
- **Why it matters:** replay and dashboard inspection need stable labels. If the
  name changes every run, the system looks like a new path every time.
- **Action:** add a stable name or stop and request a naming decision.

### `Runner.run_sync` inside an active event loop

- **Severity:** `BLOCKER` for preserving sync shape.
- **Pattern:** async application code calling `Runner.run_sync(...)`.
- **Why it matters:** migrating to `runner.run_sync(...)` keeps the same event
  loop problem. The safe migration is `await runner.run(...)` or a caller
  restructure.
- **Action:** do not auto-migrate as sync. Propose async conversion.

### `checkpoint_strategy="calls"` inside an existing Kitaru checkpoint

- **Severity:** `BLOCKER`.
- **Pattern:** a `KitaruRunner(..., checkpoint_strategy="calls")` call inside an
  existing `@checkpoint` function.
- **Why it matters:** calls mode needs to create inner sibling checkpoints from
  flow scope. It cannot safely nest inside another checkpoint.
- **Action:** move the runner call to flow scope, switch to `runner_call`, or
  redesign the checkpoint boundary.

### Inferred approval/resume flows

- **Severity:** `HIGH`.
- **Pattern:** source code uses approval-capable tools or SDK interruption
  behavior but treats every result as completed.
- **Why it matters:** the run can stop and wait for a human. If migration ignores
  that, code may try to read `final_output` from an interrupted result.
- **Action:** add explicit `result.status` handling and use
  `wait_for_approval(...)` or `build_resume_request(...)` where appropriate.

### Interrupted results treated as completed

- **Severity:** `HIGH`.
- **Pattern:** direct `return str(result.final_output)` with no status check in a
  workflow that can interrupt.
- **Why it matters:** the returned value may be missing or misleading. Human
  approval state needs a branch.
- **Action:** require `if result.status != "completed": ...` handling.

### Non-serializable context without serializer/deserializer/cache identity

- **Severity:** `HIGH`, or `BLOCKER` for resume-dependent flows.
- **Pattern:** `context=` uses database sessions, clients, auth objects, file
  handles, cursors, or other complex objects with no serializer, deserializer,
  or cache identity.
- **Why it matters:** Kitaru can save the travel plan, but it cannot recreate a
  live badge unless the application explains how. Cache keys can also mix users
  or tenants if context identity is too vague.
- **Action:** add `context_cache_identity=...`; add `context_serializer=` and
  `context_deserializer=` for interrupted/resumed SDK state when needed.

### Ignored SDK version drift

- **Severity:** `MEDIUM` to `HIGH` depending on resume usage.
- **Pattern:** approval/resume migration assumes serialized OpenAI SDK state is
  stable across unknown SDK versions.
- **Why it matters:** resume depends on SDK state shape. Version drift can make a
  saved interrupted state impossible to resume.
- **Action:** document tested SDK version and add a verification step for
  interruption/resume.

### Side-effectful tools without idempotency

- **Severity:** `HIGH`; `BLOCKER` for payments, external writes, destructive
  changes, or customer-visible messages.
- **Pattern:** tools send email/Slack, charge cards, mutate databases, create
  tickets, write files, or call external APIs without idempotency keys.
- **Why it matters:** replay may call the tool again. Concrete bad outcome:
  customer receives two refund emails or a card is charged twice.
- **Action:** require an application-owned idempotency key or move the side
  effect behind a reviewed durable boundary.

### Hosted/native tool internals treated as granularly replayable

- **Severity:** `HIGH`.
- **Pattern:** migration claims Kitaru can checkpoint provider-hosted tools as if
  they were local `@function_tool` calls.
- **Why it matters:** provider-owned internals are not local Python functions
  Kitaru can wrap.
- **Action:** describe them as OpenAI/provider-owned behavior; use
  `runner_call` if the outer result is enough, or redesign if granular replay is
  required.

### Capture policy saves sensitive OpenAI run data by default

- **Severity:** `MEDIUM`, or `HIGH` for regulated data, approval payloads,
  customer support transcripts, or internal incident workflows.
- **Pattern:** migration accepts default `OpenAICapturePolicy` without checking
  whether prompts, final outputs, run state, interruption payloads, response
  items, or usage should be durably stored.
- **Why it matters:** the old app may have treated a prompt or approval payload
  as transient. After migration, Kitaru may preserve it so replay and inspection
  work. That is useful, but it changes the data-retention story.
- **Action:** choose an explicit `OpenAICapturePolicy(...)` and record the
  decision in the migration report.

### API keys passed as flow parameters or logged

- **Severity:** `BLOCKER`.
- **Pattern:** `def flow(openai_api_key: str): ...`, request metadata containing
  secrets, or logs that print tokens.
- **Why it matters:** flow inputs, metadata, and logs may become visible durable
  records. Secrets do not belong there.
- **Action:** use environment variables or Kitaru secret configuration. Remove
  secret-bearing parameters and logs before migration.

### Raw SDK result objects returned from checkpoints

- **Severity:** `HIGH` to `BLOCKER`.
- **Pattern:** a Kitaru checkpoint returns a live OpenAI SDK result object that
  may not be serializable.
- **Why it matters:** checkpoint outputs must be serializable. A live object can
  fail persistence or replay.
- **Action:** return `OpenAIRunResult`, a simple value, or an explicit external
  artifact reference.

### Raw nested SDK runner calls outside Kitaru

- **Severity:** `MEDIUM` if intentionally ephemeral, `HIGH` if expected to be
  durable or replayable.
- **Pattern:** a tool, guardrail, or helper uses `agents.Runner.run(...)`
  directly while the main workflow uses `KitaruRunner`.
- **Why it matters:** Kitaru only sees the main doorway. The nested call can
  spend tokens or perform work again on replay.
- **Action:** either wrap the nested agent with its own `KitaruRunner` or mark it
  intentionally outside Kitaru's durable boundary.

### `runtime="isolated"`

- **Severity:** `BLOCKER`.
- **Pattern:** migration attempts to force isolated runtime for this adapter.
- **Why it matters:** the OpenAI Agents adapter rejects isolated runtime.
- **Action:** use a supported runtime path or redesign the deployment target.

### `calls` mode with simple `.wait()` expectations

- **Severity:** `MEDIUM` to `HIGH`.
- **Pattern:** user expects `flow.run(...).wait()` to return a single result from
  a calls-mode flow.
- **Why it matters:** calls mode creates peer checkpoints; no one checkpoint is
  obviously the final flow value. `.wait()` can raise
  `KitaruAmbiguousFlowResultError`.
- **Action:** switch to `runner_call` or teach the caller to inspect artifacts
  through UI/client surfaces.

## Required report entry shape

For each flagged item, include:

```markdown
- Severity: HIGH
- Source location: path/to/file.py:123
- Pattern: side-effectful `@function_tool` without idempotency
- Migration action: not auto-migrated
- Why it matters: replay could send the customer email twice
- Required human decision: add an idempotency key or keep this tool outside
  automatic replay
```

## Code comment shape

When writing migrated code around an unresolved gap, use a concrete comment:

```python
# TODO(migration): This tool sends a customer-visible email. Add an
# idempotency key before relying on Kitaru replay for this boundary.
```

Avoid vague comments such as `# TODO: check this`.
