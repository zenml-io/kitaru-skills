# Gemini Interactions Migration Gaps and Flags

Use this file when deciding whether a migration is safe to apply automatically.
The rule is: if replay, polling, provider state, environment, hosted tools,
side effects, secrets, or privacy may change, make that visible in comments and
in the migration report.

## Upstream docs checked

Checked on 2026-06-04 against current official docs:

- Gemini Interactions guide: https://ai.google.dev/gemini-api/docs/interactions
- Gemini Interactions API reference: https://ai.google.dev/api/interactions-api
- Antigravity Agent: https://ai.google.dev/gemini-api/docs/antigravity-agent
- Managed-agent environments: https://ai.google.dev/gemini-api/docs/agent-environment

Assumptions recorded here: the Interactions API is still Beta/preview-shaped;
`client.interactions.create(...)` creates an interaction resource;
`client.interactions.get(...)` retrieves an existing interaction;
`previous_interaction_id` uses server-side history; `store=true` is default and
needed for background/resume workflows; background interactions must be polled by
ID; Antigravity uses the `antigravity-preview-05-2026` agent, runs in a
Google-hosted environment, and does not support `background=True`.

## Kitaru adapter source checked

Checked against local Kitaru source/docs on 2026-06-04:

- `kitaru/src/kitaru/adapters/gemini/__init__.py`
- `kitaru/src/kitaru/adapters/gemini/_agent.py`
- `kitaru/src/kitaru/adapters/gemini/_types.py`
- `kitaru/src/kitaru/adapters/gemini/_policy.py`
- `kitaru/src/kitaru/adapters/gemini/_utils.py`
- `kitaru/docs/content/docs/adapters/gemini-interactions.mdx`

Kitaru assumptions: the only public checkpoint strategy is `interaction`; stable
statuses are `completed` and `requires_action`; `GeminiInteractionRequest.poll`
fetches an existing interaction; `GeminiInteractionRequest.antigravity(...)`
rejects `background=True`; runner calls inside existing checkpoints are blockers
and must be moved to flow scope; `GeminiInteractionCapturePolicy` defaults to not
saving raw input, raw interaction payloads, or step details.

## Severity levels

| Severity | Meaning | Required action |
|---|---|---|
| `LOW` | Cosmetic or documentation-only difference. | Migrate and mention in report. |
| `MEDIUM` | Behavior probably preserved, but settings, capture, or observability differ. | Migrate with caveat and verification step. |
| `HIGH` | Replay, polling, provider state, hosted-tool, side-effect, privacy, or runtime behavior may change. | Require human review before applying or mark partial migration. |
| `BLOCKER` | Migration would be unsafe or impossible without source redesign. | Do not auto-migrate; generate redesign note and report entry. |

## Must-flag patterns

### Unsupported granular checkpoint strategies

- **Severity:** `BLOCKER`.
- **Pattern:** `checkpoint_strategy="calls"`, `"runner_call"`, `"granular"`,
  `"model_call"`, `"tool_call"`, `"client_tools"`,
  `"antigravity_steps"`, `"managed_agent_steps"`, `"step"`, or `"run"`.
- **Why it matters:** Kitaru records one stable Gemini interaction response. It
  does not checkpoint Google-internal model, hosted-tool, web, code, MCP,
  Antigravity, sandbox, or managed-agent steps.
- **Action:** use `checkpoint_strategy="interaction"` or redesign.

### Unfinished background work treated as completed

- **Severity:** `HIGH`.
- **Pattern:** code treats `in_progress`, queued, running, incomplete, failed,
  cancelled, or otherwise non-stable statuses as successful outputs.
- **Why it matters:** replay would treat unfinished provider work as done.
- **Action:** only accept `completed` and `requires_action` as stable Kitaru
  boundaries. Poll the same `interaction_id` until stable or terminal.

### Duplicate background jobs while polling

- **Severity:** `HIGH`; `BLOCKER` for expensive or customer-visible jobs.
- **Pattern:** migration calls `GeminiInteractionRequest.start(...,
  background=True)` again when the source meant to poll an existing job.
- **Why it matters:** a new create call starts new provider work and can multiply
  cost or side effects.
- **Action:** use `GeminiInteractionRequest.poll(interaction_id=...)` for an
  existing background interaction.

### `requires_action` hidden inside provider-owned flow

- **Severity:** `HIGH`.
- **Pattern:** local tool execution, approval, filesystem writes, or API calls
  happen inside an opaque provider loop instead of after a stable
  `requires_action` response.
- **Why it matters:** Kitaru cannot checkpoint local work it never owns.
- **Action:** return to Kitaru flow scope, run local code or `kitaru.wait()`, then
  send `GeminiInteractionRequest.function_result(...)`.

### Missing `interaction_id` or unstable previous interaction

- **Severity:** `HIGH` for resume/poll workflows.
- **Pattern:** code resumes or polls without preserving a materialized
  `interaction_id` / `previous_interaction_id`.
- **Why it matters:** Google uses the ID to find server-side history or the
  background job. Without it, the app may start a new interaction.
- **Action:** store stable IDs outside transient local variables when later turns
  depend on them.

### `store=False` used with resume or background expectations

- **Severity:** `HIGH`.
- **Pattern:** `store=False` while the source expects `previous_interaction_id`,
  background polling, or server-side history.
- **Why it matters:** stateless interactions do not provide the same stored
  server-side resource behavior.
- **Action:** use `store=True` for resume/background workflows or redesign as a
  stateless full-history request.

### Missing `cache_identity` across projects/regions/credentials

- **Severity:** `HIGH`.
- **Pattern:** the same runner name and request can run under different Google
  projects, regions, credentials, endpoints, clients, or environments with no
  stable `cache_identity`.
- **Why it matters:** Kitaru's cache key cannot inspect live client internals.
  Replay could reuse a dev result in a prod-shaped run, or cross credential
  boundaries accidentally.
- **Action:** add a stable, non-secret `cache_identity`, for example
  `"project/region"` or `"credential-alias/global"`.

### Antigravity internals assumed Kitaru-durable

- **Severity:** `HIGH`.
- **Pattern:** migration claims Kitaru snapshots Antigravity sandbox files,
  web/code execution, environment reuse, managed-agent planning, or filesystem
  operations.
- **Why it matters:** Google owns those internals. Kitaru records the returned
  stable interaction response and summaries only.
- **Action:** persist important file IDs, exported artifacts, or application
  decisions explicitly outside the hosted sandbox.

### Antigravity background mode

- **Severity:** `BLOCKER`.
- **Pattern:** `GeminiInteractionRequest.antigravity(..., background=True)` or a
  plan to make Antigravity use background polling.
- **Why it matters:** Kitaru's Antigravity preset rejects `background=True`, and
  current Google docs say the Antigravity agent does not support background mode.
- **Action:** use foreground Antigravity with `timeout_s`, or avoid the preset.

### Model/agent target mix-up

- **Severity:** `BLOCKER` until fixed.
- **Pattern:** request sets both `model=` and `agent=`, neither target, or puts
  `generation_config` on agent requests / `agent_config` on model requests.
- **Why it matters:** Kitaru validates exactly one target and target-specific
  config fields.
- **Action:** split into separate model or agent requests and use the matching
  config field.

### Raw provider payload capture without privacy review

- **Severity:** `MEDIUM`, or `HIGH` for customer data, source code, secrets,
  incident data, regulated data, or sensitive tool arguments.
- **Pattern:** migration enables `save_input=True`, `save_raw_interaction=True`,
  or `save_steps=True` by default.
- **Why it matters:** raw prompts, provider payloads, tool arguments, generated
  files, step contents, and user data may be durable artifacts.
- **Action:** choose an explicit `GeminiInteractionCapturePolicy(...)` and record
  what is saved.

### Runner call inside existing Kitaru checkpoint

- **Severity:** `BLOCKER`.
- **Pattern:** `KitaruGeminiInteractionsRunner.run/run_sync(...)` called from a
  `@kitaru.checkpoint` body.
- **Why it matters:** replaying the outer checkpoint may call Google again and
  duplicate hosted work, sandbox mutations, or API cost.
- **Action:** do not auto-migrate this shape. Move the runner call to flow
  scope and report it as a required manual restructuring step.

### Secrets in prompts, metadata, manifests, or raw payloads

- **Severity:** `BLOCKER`.
- **Pattern:** API keys/tokens are passed as prompts, request metadata,
  `cache_identity`, logs, manifests, or raw payload artifacts.
- **Why it matters:** Kitaru may store request metadata and artifacts durably.
- **Action:** use environment variables or a secret manager; remove secrets from
  prompts, metadata, cache identities, manifests, and logs.

## Required report entry shape

```markdown
- Severity: HIGH
- Source location: path/to/gemini_agent.py:123
- Pattern: background job was recreated instead of polled
- Migration action: changed to `GeminiInteractionRequest.poll(interaction_id=...)`
- Why it matters: creating a second interaction duplicates Google-hosted work and cost
- Required human decision: confirm where the original `interaction_id` is stored
```

## Code comment shape

```python
# TODO(migration): This path can run under different Google projects/regions but
# has no cache_identity. Add a stable non-secret identity before relying on
# Kitaru replay, or cached dev results could be reused in a prod-shaped run.
```
