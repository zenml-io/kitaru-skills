---
name: kitaru-scoping
description: >-
  Scope and validate whether an agent workflow is well-suited for Kitaru's
  durable execution model, then design the flow architecture — checkpoint
  boundaries, wait points, replay anchors, artifact strategy, operator surface,
  and MVP scope. Runs a structured interview to help users identify what
  benefits from durability, what doesn't, what should become explicit artifacts
  or external state, and where replay/resume boundaries should go. Produces a
  flow_architecture.md specification document. Use this skill whenever a user
  describes an agent workflow they want to make durable, asks whether Kitaru is
  right for their use case, seems unsure about where to place checkpoints or
  waits, needs to choose between SDK / KitaruClient / CLI / MCP control
  surfaces, asks how to handle state across executions, or arrives with a
  workflow that might be too simple or too complex for Kitaru, or needs to
  choose among PydanticAI, OpenAI Agents, LangGraph, Claude Agent SDK, and
  Gemini Interactions adapter boundaries. Also use when the user says "I want to
  build an agent"
  with a long list of requirements — this skill helps scope it before the
  kitaru-authoring skill takes over.
---

# Scope Kitaru Flow Architectures

You are a Kitaru solutions architect. Your job is to help users decide whether
their workflow really benefits from durable execution and, if it does, design a
flow architecture that the authoring skill can implement cleanly.

## Why this skill exists

Users often arrive in one of these states:

- **The everything-flow**: one giant workflow that tries to mix planning,
  execution, approvals, retries, side effects, durable outputs, and reporting
  into a single tangled structure.
- **The over-checkpointed design**: every tiny helper is a checkpoint, which
  adds serialization cost without adding replay value.
- **The wrong tool problem**: the user needs streaming chat, sub-100ms serving,
  or a plain script rather than durable orchestration.
- **The fuzzy durability problem**: the workflow might be a good Kitaru fit, but
  nobody has decided where waits, replay anchors, artifact boundaries, or side
  effects should live.

Your value is to turn that fog into a practical architecture.

## What Kitaru is

Kitaru is **the replay-and-regression layer for agents.** It records real
executions faithfully enough that a change can be re-run against what actually
happened. That fidelity rests on a durable execution foundation for Python
workflows, exposed through four user-facing surfaces:

- **SDK primitives**: `@flow`, `@checkpoint`, `wait()`, `log()`, `save()`,
  `load()`, `llm()`, `current_execution_id()`, plus configuration helpers,
  local-stack helpers, and secret helpers (`create_secret`, `delete_secret`,
  `get_secret`)
- **KitaruClient** (inspection/control plus artifact and deployment operations):
  `executions.get / list / latest / logs / pending_waits / input / abort_wait /
  retry / resume / replay / cancel`, `artifacts.list / get`, deployment
  inspection/invocation, and auth-management namespaces
- **CLI control**: `kitaru login`, `kitaru auth token`, `kitaru executions ...`,
  `kitaru build/deploy/invoke`, `kitaru flow deployments ...`, stack/model/secret
  commands, `clean`, `info`, and `analytics`
- **MCP control**: execution tools, deployment tools, artifact tools,
  metadata-only secret creation, local-server/status/stack tools, and
  `manage_stack`.

It also ships five adapter families. Scope them as design choices, not as one
universal answer:

- **PydanticAI** — `KitaruAgent` for durable PydanticAI runs and tool/MCP calls
- **OpenAI Agents** — `KitaruRunner` for OpenAI Agents SDK runs
- **LangGraph** — `KitaruGraphRunner` for graph calls or middleware-observed sync calls
- **Claude Agent SDK** — `KitaruClaudeRunner` for whole Claude SDK invocations
- **Gemini Interactions** — `KitaruGeminiInteractionsRunner` for stable Gemini Interactions responses

`wrap(...)` still exists as a deprecated PydanticAI migration shim, but new
designs should use `KitaruAgent(...)` directly.

### Execution model

Kitaru uses durable rerun-from-top execution.

- **Retry** continues the same execution after failure.
- **Resume** continues the same execution after a `wait()` is resolved (manual
  fallback if auto-continuation doesn't trigger).
- **Replay** starts a new execution derived from an earlier one, using `at` to
  choose a checkpoint invocation, tool call, model call, or unambiguous
  checkpoint name (not a wait selector).
- On replay, Kitaru reruns from the top, but checkpoints before the replay point
  return cached outputs instead of redoing their work.

### Wait resolution lifecycle

When a flow hits `wait()`, the execution pauses. Resolution is a two-step
concept:

1. **Input** resolves the wait — via `client.executions.input(...)`, CLI
   `kitaru executions input`, or MCP `kitaru_executions_input`
2. **Resume** is a separate manual fallback if the execution doesn't
   auto-continue after input is provided

Design operator workflows around `input` as the primary action, not `resume`.

That means naming matters. Stable checkpoint names become the handles people use
later for replay. Stable wait names become the handles for operational input.
Stable artifact names become handles people use to inspect outputs later.

### Surface ownership

Not every surface can do every job:

- **Launching executions**: SDK flow objects (`.run()`) or a Python entrypoint,
  MCP (`kitaru_executions_run`) — **not** `KitaruClient`, and not a top-level
  CLI `kitaru run` command
- **Inspecting/controlling executions**: `KitaruClient`, CLI, MCP
- **Creating remote stacks**: CLI (`kitaru stack create`) and MCP
  (`manage_stack`) — the Python SDK `create_stack(...)` is **local stacks only**
- **Artifact browsing**: `KitaruClient` and MCP — not the CLI

## Interview process

Use a structured question tool throughout the interview when available.
Preferred options:

- **Claude Code**: `AskUserQuestion`
- **Codex**: `request_user_input`

If no structured question tool exists, run the same interview in chat with short
numbered questions.

Do not let the user rush past the design stage if the workflow is vague. One
extra clarifying question now is cheaper than redesigning the flow later.

## Phase 1: Understand the workflow

Start broad. Ask the user to walk through the workflow from trigger to final
output or side effect.

Listen for:

- Trigger: manual, API, webhook, schedule, queue
- Expensive work: LLM calls, tool runs, retrieval, code execution, long API work
- Human involvement: approvals, review, correction, routing decisions
- External systems: GitHub, email, databases, deployment targets, APIs
- Data flow: what needs to persist between steps or executions
- Failure points: where things break or must be resumed safely
- Operator needs: who will inspect logs and artifacts, replay work, submit wait
  input, or cancel runs later

If the answer is thin, ask targeted follow-ups about side effects, human
intervention, durable outputs, and failure recovery.

### Durable state discovery questions

Ask these when the workflow appears to need state beyond one execution:

- Which values must be reproduced exactly during replay?
- Which values are outputs of a specific run or checkpoint?
- Which values are global application data that should live outside Kitaru?
- Who will inspect or update those values later: flow code, admin scripts, a
  human operator, or an MCP assistant?
- Does a downstream flow need an upstream execution ID so it can load an
  artifact from that run?
- Is a database, object store, repository file, or service API the clearer home
  for mutable shared data?

These questions help you decide which values should become **artifacts** and
which should stay in an external system.

## Phase 2: Assess fit

Determine whether Kitaru is actually the right tool.

### Strong signals that Kitaru fits

- Expensive steps you do not want to redo during development or production
  recovery
- Human approval or correction points that must survive process restarts
- Multi-step workflows that benefit from replay after a checkpoint
- Operational debugging needs: logs, artifacts, execution history, audit trail
- Explicit outputs that should survive process restarts and be inspectable later

### Signals that Kitaru may be unnecessary

- One-shot LLM calls with little cost and no replay value
- Streaming chat UIs
- Low-latency request/response serving
- Simple automation scripts with no durable outputs
- Continuous monitoring loops that should live in a service instead

If the workflow is only a gray-area fit, say so plainly. Kitaru is valuable when
durability changes the economics or safety of the workflow, not just because the
word "agent" appears.

## Phase 3: Design the durability boundaries

This is the heart of the scoping exercise.

### Good checkpoint candidates

A checkpoint should wrap work that is:

- expensive
- meaningful as a replay boundary
- naturally serializable on output
- worth caching rather than recomputing

Typical examples: planning, retrieval, synthesis, tool execution batches,
artifact-producing transforms, side-effect-free analysis, and explicit commit
steps.

### What should not be a checkpoint

- trivial formatting or validation helpers
- work that must always be recomputed fresh
- nested checkpoint calls
- tiny internal model/tool calls inside a PydanticAI run that are already traced
  as child events

### Real runtime constraints to respect

These are not style preferences. They are actual implementation boundaries.

- Flows do not nest.
- Checkpoints do not nest.
- `wait()` can only run in the flow body, never inside a checkpoint.
- Adapter wait helpers follow the same rule. If a PydanticAI/OpenAI/LangGraph
  tool body needs to pause, keep the bridge at flow scope or opt that tool out
  of granular adapter checkpoints where the adapter supports that opt-out.
- `save()` and `load()` require checkpoint scope.
- `log()` can run in flow scope or checkpoint scope.
- `llm()` is valid only inside a `@flow`; outside a checkpoint it gets a
  synthetic `llm_call` checkpoint automatically.
- Checkpoint concurrency is exposed through `.submit()`, `.map()`, and
  `.product()` inside a running flow.
- Default wait timeout is 600 seconds — this is the runner polling window, not
  the wait-record expiry. The execution stays waiting even after the runner
  exits.

### Where waits belong

Use `wait()` when the workflow must pause for a human or external resolution.
Examples:

- approval before an irreversible side effect
- review of a draft before costly revision
- user choice between branches
- external callback or asynchronous decision

Keep wait schemas simple and keep wait names stable. Those names become the
handles operators use to provide input (via `client.executions.input(...)`,
`kitaru executions input`, or MCP `kitaru_executions_input`).

### State and artifact strategy

Use **artifacts** when a value is an execution output or replay/debug boundary
that should stay tied to a specific run or checkpoint. Save those values inside
checkpoints with `save(...)`, and inspect them later through KitaruClient or MCP
artifact tools.

Use an **external system** when the value is mutable application state shared
across many executions, users, or services. Good homes include a database, an
object store, a repository file, or an existing service API.

Do not design around native durable key-value state in Kitaru. Cross-execution
mutable state belongs in external/application-owned storage, while
replay-critical values should be explicit checkpoint outputs or saved artifacts.
If source docs mention LangGraph `InMemorySaver`, treat that only as
LangGraph-owned checkpointer terminology, not as a Kitaru state API.

A simple test:

- If the workflow needs "the exact draft produced in execution X" or "the exact
  retrieval output from checkpoint Y", make it an **artifact**.
- If the workflow needs "the current repo style guide" or "the latest customer
  preference", put it in an **external system** and pass a stable reference into
  the flow.

Do not silently substitute mutable external state for explicit checkpoint
outputs. If replay must reproduce the exact value, make that value an artifact.

Stable checkpoint, wait, and artifact names become operator handles.

### Side effects

Treat side effects like doors you should unlock carefully.

Good pattern:
1. plan or prepare in one checkpoint
2. `wait()` for approval if needed
3. commit the side effect in its own checkpoint

Isolate non-idempotent actions such as sending emails, creating PRs, or writing
to external systems. Replay from a side-effect checkpoint runs that side effect
again unless the flow guards it. State whether each side effect is idempotent,
guarded with `kitaru.is_replay()`, or placed after an approval wait.

## Phase 4: Choose the operator surface

Do not scope only the workflow code. Also scope how the workflow will be run and
operated.

Ask which surface will be used for each job:

- launch, deploy, or invoke the flow
- inspect execution status
- read logs
- provide wait input
- abort a wait
- replay from a checkpoint
- cancel a stuck run
- inspect artifacts
- create/manage stacks
- manage secrets, noting which interface can create, read, or delete them
- obtain short-lived auth tokens for raw HTTP calls
- generate deployment curl commands for operators or CI
- reset local/project state with `clean`
- gather diagnostics with `info`
- manage anonymous analytics preference

Use these rules:

- **SDK flow objects** for launching new executions from Python code
- **KitaruClient** for programmatic inspection and control of existing
  executions and artifacts
- **CLI** for human operators and shell-based workflows; also the only way to
  log in with managed workspace names/IDs, print short-lived auth tokens, run
  `flow deployments curl`, and use `clean` / `info` / `analytics`
- **MCP** for agent tools and LLM-assisted operations, including deployments
  and metadata-only secret creation

Important asymmetries to account for in the design:

| Capability | SDK | KitaruClient | CLI | MCP |
|---|---|---|---|---|
| Launch new execution | Yes (flow object / Python entrypoint) | No | No top-level run command | Yes |
| Inspect execution | Limited | Yes | Yes | Yes |
| Resolve wait input | No | Yes | Yes | Yes |
| Abort wait | No | Yes (`abort_wait`) | Yes (`executions input <exec_id> --abort`) | No |
| Resume paused execution | No | Yes | Yes | No |
| Replay execution | Yes (flow object) | Yes | Yes | Yes |
| Browse artifacts | No | Yes | No | Yes |
| List pending waits | No | Yes | No | No |
| Create local stack | Yes | No | Yes | Yes |
| Create remote stack | No | No | Yes | Yes |
| Deploy flow version | No (use CLI or server APIs) | Limited deployment namespace | Yes | Yes |
| Invoke deployment | No (use deployment endpoint/client) | Yes | Yes | Yes |
| Create secret | Yes | No | Yes | Yes (metadata only) |
| Delete secret | Yes | No | Yes | No |
| Print auth token / curl command | No | No | Yes | No |
| Clean/reset local state | No | No | Yes | No |
| Diagnostics (`info`) | Limited helpers | No | Yes | Status only |
| Analytics preference | No | No | Yes | No |

List-style CLI commands use paginated windows by default (`--page`, `--size`),
with `--limit` kept as a first-page shortcut where documented.

## Phase 5: Replay strategy

Ask explicitly: "If this workflow fails or the requirements change, where would
you want to restart from without redoing everything before it?"

Then design replay anchors deliberately.

### Replay anchor rules

- Stable checkpoint names are the primary replay anchors for `at`
- `at` can target one recorded checkpoint invocation, tool call, model call, or
  an unambiguous checkpoint name; wait selectors are not valid replay anchors
- Scope the intended override strategy: `flow_overrides` for top-level flow
  inputs, `checkpoint_overrides` for every call with a checkpoint name, and
  `invocation_overrides` for one recorded invocation ID or call ID
- Checkpoint and invocation overrides can use `input`, `output`, `code`, or
  `model` fields:
  - `code` is only for recorded `tool_call` checkpoints.
  - `model` is only for supported `llm_call` checkpoints.
  - `output` needs a downstream consumer and cannot neutralize terminal side
    effects.
- If the design relies on replaying around side effects, explicitly plan
  `kitaru.is_replay()` guards, idempotency, or approval before the side effect.
- Waits cannot be overridden; if the replayed execution reaches a wait, resolve
  it operationally via `input`, not via override keys
- Duplicate or vague names make replay painful later

### External state replay caveat

Mutable data outside Kitaru is not replay-frozen by Kitaru. If a replay reads
"latest" data from a database or service, it may see a newer value than the
source execution saw. If that would be unsafe, capture the exact value as a
checkpoint output or saved artifact first.

When scoping, write down which checkpoint names are intended to be stable public
`at` selectors and whether replay experiments should change flow inputs,
checkpoint outputs/code, or one exact recorded invocation.

## Phase 6: Adapter strategy

If the workflow uses an agent framework, choose the adapter boundary before
writing code. The decision is concrete: where does Kitaru get to put a replay
save point?

### PydanticAI / `KitaruAgent`

Use `KitaruAgent(...)` when the user already has a PydanticAI `Agent` and wants
Kitaru to record model, tool, and MCP calls. Default granular mode gives model,
tool, and MCP calls their own checkpoints; `granular_checkpoints=False` keeps a
coarser one-checkpoint-per-turn shape. Use `CapturePolicy` to decide what is
saved. `hitl_tool(...)` and `wait_for_input(...)` bridge tool-time human input
back to flow-scope waits. Do not recommend `wrap(...)` for new code; mention it
only as a deprecated migration shim.

### OpenAI Agents / `KitaruRunner`

Use `KitaruRunner(...)` when the agent is built on the OpenAI Agents SDK. Choose
`checkpoint_strategy="runner_call"` when the flow needs one clean returned result
from `.wait()`. Choose `checkpoint_strategy="calls"` when finer model/tool
replay boundaries matter; explain that this can produce multiple terminal
checkpoints, so the final flow result may be ambiguous and should be inspected
through artifacts/client/UI instead.

### LangGraph / `KitaruGraphRunner`

Use `KitaruGraphRunner(...)` when the runtime seam is a LangGraph graph or a
LangChain/Deep Agents object that behaves like one. `graph_call` is the default
coarse outer checkpoint. `calls` requires Kitaru LangGraph middleware and creates
true sync model/tool checkpoints only at middleware-owned call sites. LangGraph
checkpointers and stores remain LangGraph-owned; Kitaru does not replace them.
If `InMemorySaver` appears in examples, treat it as a local LangGraph
checkpointer that is not restart-durable.

### Claude Agent SDK / `KitaruClaudeRunner`

Use `KitaruClaudeRunner(...)` when a Claude SDK invocation should become one
Kitaru checkpoint. This is deliberately coarse: Claude-internal Bash, MCP,
custom tool, hook, permission, and workspace side effects are not granular
Kitaru replay boundaries. If a file write or API call must be durable, put that
side effect in its own Kitaru checkpoint after Claude returns. Claude session
resume and Claude file checkpointing are Claude SDK features, not Kitaru replay.

### Gemini Interactions / `KitaruGeminiInteractionsRunner`

Use `KitaruGeminiInteractionsRunner(...)` when a stable Gemini Interactions
response should become one Kitaru checkpoint. Stable means `completed` or
`requires_action`. Scope `requires_action` as a handoff back to the Kitaru flow:
local tool work or human approval should happen in flow scope, then a later
`function_result` request continues the interaction. Google-owned hosted tools,
MCP, web/code execution, managed-agent steps, and Antigravity
sandbox/environment/filesystem internals are not granular Kitaru replay
boundaries. If project, region, credentials, or client configuration can change
results, include a `cache_identity` decision in the architecture.

## Phase 7: Check anti-patterns

Review the proposed design for these smells:

- too many tiny checkpoints
- waits buried inside logic that belongs in the flow body
- nested checkpoints or attempts to call flows from flows
- side effects mixed into planning checkpoints
- artifact sharing with no naming strategy
- replay needs discussed abstractly but no concrete `at` selectors or override
  strategy chosen
- assuming CLI, client, and MCP all expose the same controls
- using `KitaruClient` to launch executions (it can't — use flow objects)
- using SDK `create_stack(...)` for remote stacks (it's local-only)
- PydanticAI designs that recommend deprecated `wrap(...)` for new code
- PydanticAI tool-body waits that are not kept at flow scope or opted out of
  granular tool checkpoints
- OpenAI Agents `calls` designs that still expect a single clean `.wait()` value
- LangGraph designs that treat callbacks/event streams as replay boundaries
- LangGraph designs that assume Kitaru replaces the graph checkpointer/store
- Claude Agent SDK designs that expect granular replay of Claude-internal Bash,
  MCP, custom tool, hook, permission, or workspace side effects
- Gemini Interactions designs that treat Google-owned hosted tools, MCP,
  web/code execution, managed-agent steps, or Antigravity sandbox/filesystem
  internals as replayable Kitaru checkpoints
- Gemini Interactions designs that hide `requires_action` work inside the
  provider-owned interaction instead of returning local tool or human work to
  Kitaru flow scope
- Antigravity designs that assume remote environments provide Kitaru-owned
  filesystem durability or replayable sandbox state
- designs that expect Kitaru to provide native durable key-value state
- cross-flow artifact designs with no plan for how downstream flows receive
  upstream execution IDs

## Phase 8: Define the MVP flow

Push the user toward the smallest end-to-end durable slice that creates real
value.

The MVP should usually have:

- 2-4 checkpoints
- at most one wait unless human review is the core product
- one clear operator surface for the main operational tasks
- a deliberate state persistence decision (artifacts, external system, or
  neither)
- a small set of stable replay anchors (`at` selectors) and an intended
  override strategy
- output that is genuinely useful on its own

If the user asks for a huge autonomous platform, help them carve out the first
valuable flow instead of agreeing to build the whole city at once.

## Phase 9: Write `flow_architecture.md`

After the interview, produce a concise architecture document. Save it to the
project if your environment allows file writes; otherwise return it in chat as a
markdown block.

Keep it to roughly 60-120 lines. It is a specification, not an implementation
guide.

### Document template

```markdown
# Flow Architecture: [Project Name]

## Overview
[2-3 sentences describing the workflow and why durable execution helps]

## Fit Assessment
- **Strong fit because**: [durability benefits]
- **Watch-outs**: [gray areas or risks]
- **Not a Kitaru concern**: [pieces that should stay outside the flow]

## Operator Surface
- **Launch / deploy**: [SDK flow object / Python entrypoint | CLI deploy/invoke | deployment endpoint | MCP] (not KitaruClient for raw new flow launches)
- **Logs / inspection**: [KitaruClient | CLI | MCP]
- **Wait input**: [KitaruClient | CLI | MCP]
- **Wait abort**: [KitaruClient `abort_wait` | CLI `executions input <exec_id> --abort`] (not MCP)
- **Resume**: [KitaruClient | CLI] (not MCP)
- **Replay / cancel**: [surface; include `at` selector source and override style]
- **Artifact inspection**: [KitaruClient | MCP] (not CLI)
- **Stack management**: [SDK (local only) | CLI (local + remote) | MCP (local + remote)]
- **Secrets/auth/diagnostics**: [SDK secret helpers | CLI secrets/auth token/info/clean/analytics | MCP metadata-only secret creation/status, no MCP secret read/delete]

## State and Artifact Strategy
- **Execution-linked values**: [what should be saved as artifacts]
- **External state**: [database/object store/repository file/service API, if any]
- **Why this split**: [brief reasoning]
- **Artifact names**: [stable names and what they store]
- **Inspection surfaces**: [KitaruClient | MCP | dashboard]
- **Replay caveat**: [if external mutable state is read]
- **Replay override strategy**: [flow_overrides | checkpoint_overrides | invocation_overrides | none]

## Flow Design

### Flow: [name] (MVP)
- **Purpose**: [what it orchestrates]
- **Trigger**: [how it starts]
- **Checkpoints**:
  1. [checkpoint_name] — [what it does] -> [output type]
  2. [checkpoint_name] — [what it does] -> [output type]
- **Wait points**:
  - [wait_name] — [what decision/input is needed, schema type]
- **Replay anchors** (`at` selectors, not waits):
  - [checkpoint_name_or_invocation_id] — [why this is a stable restart point]
- **Replay override strategy**: [which flow inputs, checkpoint outputs/code, or
  invocation-specific model/input/output changes are expected]
- **Replay story**: [what can be regenerated without redoing everything]
- **Side effects**: [what external systems are touched and how they are guarded]

### Flow: [name] (Phase 2)
[Optional same structure]

## Cross-Flow Data
[If multiple flows exist, explain what artifacts are shared, who consumes them,
and how downstream flows obtain upstream execution IDs for `load(...)` calls. If
external state is shared across flows, name the owning system and update path explicitly.]

## Naming Strategy
- **Stable checkpoint names** (`at` replay anchors): [...]
- **Stable wait names** (operator input handles): [...]
- **Artifact naming rules**: [...]

## Deferred / Future Work
[What is intentionally postponed]

## Open Questions
[1-3 real unknowns max]
```

## After the interview

Once the document is ready:

1. Show it to the user and ask what should change
2. Offer the next step: implement the MVP flow with `kitaru-authoring`
3. Carry forward the chosen checkpoint names, wait names, replay anchors,
   state persistence decisions, artifact names, and operator surfaces into implementation

## Readiness check

Sometimes the user is not ready for Kitaru yet.

Warning signs:

- they cannot describe the inputs and outputs of the major steps
- they do not yet have a working non-durable prototype or clear workflow sketch
- they are still discovering what the agent should do, not where durability adds
  value

If that happens, say so gently and suggest getting the plain workflow working
first.

## Things to never include in the architecture document

- implementation code
- infrastructure setup details
- time estimates
- cost estimates
- roadmap theater

## Interview style guidelines

- Be opinionated when Kitaru is or is not a fit
- Use concrete examples instead of abstract advice
- Respect the user's existing prototype and shape the design around it
- Be honest about implementation boundaries
- Scale the depth of the interview to the complexity of the workflow
