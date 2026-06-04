# Gemini Interactions to Kitaru Concept Map

Use this map while classifying source code. The safe migration story is simple:
Google owns the hosted interaction runtime; Kitaru records one stable interaction
response that the adapter can honestly see.

## Mapping labels

- `direct`: Kitaru has a close adapter surface for the same outer behavior.
- `approximate`: Migration is possible, but replay, polling, hosted-tool,
  environment, capture, or credential behavior differs.
- `absent`: No safe automatic migration. The code needs redesign or explicit
  human review before migration.

## Core concepts

| Gemini Interactions source pattern | Kitaru target pattern | Mapping | Notes |
|---|---|---:|---|
| `genai.Client(...)` | `KitaruGeminiInteractionsRunner(client=...)` or `client_factory=...` | `direct` for client injection | Use `client_factory` when credentials/project/region are created per run. |
| `client.interactions.create(input=..., model=...)` | `runner.run/run_sync(GeminiInteractionRequest.start(input, model=...))` | `direct` | One stable model interaction response becomes one Kitaru checkpoint. |
| `client.interactions.create(input=..., agent=...)` | `GeminiInteractionRequest.start(input, agent=..., environment=...)` | `direct` for outer call | Agent internals remain Google-owned. |
| `client.interactions.get(interaction_id)` | `GeminiInteractionRequest.poll(interaction_id=...)` | `direct` | Polls an existing interaction; does not create duplicate provider work. |
| `previous_interaction_id=...` | `GeminiInteractionRequest.resume(input, previous_interaction_id=...)` | `direct` | Server-side history remains Google-owned and retained only while stored. |
| Function-result turn | `GeminiInteractionRequest.function_result(...)` | `direct` | Send a matching result after a prior `requires_action` response. |
| `status == "completed"` | `GeminiInteractionResult(status="completed")` | `direct` | Stable final response. |
| `status == "requires_action"` | `GeminiInteractionResult(status="requires_action")` | `approximate` | Stable handoff point, not a final answer. Return local work to Kitaru flow scope. |
| Background interaction creation | `GeminiInteractionRequest.start(..., background=True, store=True)` | `approximate` | The provider job is Google-owned. Poll by ID until stable. |
| In-progress/background status | Keep polling with `GeminiInteractionRequest.poll(...)` | `absent as final output` | Do not treat unfinished provider work as a successful checkpoint. |
| `store=True` | Preserve `store=True` | `direct` | Needed for server-side history and background interactions. |
| `store=False` | Preserve only when no resume/background behavior is needed | `approximate` | Stateless behavior changes later resume/poll expectations. |
| `model=...` | `model=...` | `direct` | Exactly one of `model` or `agent` must be set. |
| `agent=...` | `agent=...` | `direct` | Exactly one of `model` or `agent` must be set. |
| Both `model=` and `agent=` | Redesign to one target | `absent until fixed` | Kitaru request validation rejects mixed targets. |
| Model `generation_config` | `generation_config=...` on model requests | `direct` | Only valid for model interactions. |
| Agent `agent_config` | `agent_config=...` on agent requests | `direct` | Only valid for agent interactions. |
| Hosted tools / web / code execution / hosted MCP | Keep Google-owned; capture summaries only if policy allows | `approximate` | These are not granular Kitaru checkpoints. |
| Local function execution after `requires_action` | Kitaru-owned flow step, then `function_result(...)` | `approximate` | This is the safe place for local tool work or `kitaru.wait()`. |
| Antigravity agent ID | `GeminiInteractionRequest.antigravity(...)` | `direct` for preset | Uses the adapter's Antigravity preset; internals remain Google-owned. |
| Antigravity `environment="remote"` | Same preset/default environment | `approximate` | Google provisions or reuses a sandbox. Kitaru does not snapshot files. |
| Antigravity `background=True` | Do not use; bound with `timeout_s` | `absent` | Adapter rejects background mode for Antigravity. |
| Raw `interaction.steps` inspection | `GeminiInteractionResult.steps` summaries | `approximate` | Summaries are metadata-first, not full hosted-step replay. |
| `interaction.output_text` | `GeminiInteractionResult.output_text` | `direct` | Convenience final text when present. |
| Raw provider payload capture | `GeminiInteractionCapturePolicy(save_raw_interaction=True)` | `approximate` | Privacy-sensitive; opt in only after review. |
| Different projects/regions/credentials/client config | `KitaruGeminiInteractionsRunner(cache_identity="...")` | `direct` for cache separation | Stable, non-secret cache identity prevents cross-client cache reuse. |
| Runner inside existing Kitaru checkpoint | Move the runner call to flow scope | `absent` | Do not auto-migrate this shape. Replaying the outer checkpoint can call Google again and duplicate cost or hosted work. |
| `runtime="isolated"` checkpoint config | Use inline/default runtime | `absent` | Current adapter rejects isolated runtime because closures may capture live clients. |
| Non-serializable request payloads | Materialized strings/dicts/lists | `absent until redesigned` | Do not pass clients, streams, file handles, or checkpoint output handles. |
| Secrets in metadata/raw payloads | Use environment/secret manager | `absent until fixed` | Kitaru metadata/artifacts may be durable. |

## Boundary decision guide

Use `interaction` when:

- one stable Gemini Interactions response should be durable as a whole;
- the source already uses `client.interactions.create(...)` or `.get(...)`;
- hosted tool/agent work can remain Google-owned;
- the result envelope, step summaries, IDs, output text, and optional artifacts
  are enough.

Do not use this adapter when:

- the user needs Kitaru to replay each hosted tool, MCP, web, code execution, or
  Antigravity sandbox step;
- unfinished provider jobs are being treated as successful application work;
- replaying the whole interaction would duplicate an unsafe provider job;
- project/region/credential differences cannot be represented with a stable
  non-secret `cache_identity`.

## What Kitaru does not own

Kitaru does not own Google's hosted model loop, hosted tools, hosted MCP, web or
code execution, Antigravity sandbox files, environment reuse, server-side
interaction history, or background-job internals. If the source depends on those
internals being replayed as separate Kitaru units, mark the mapping
`approximate` or `absent` and explain the boundary clearly.
