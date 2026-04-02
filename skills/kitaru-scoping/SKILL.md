---
name: kitaru-scoping
description: >-
  Scope and validate whether an agent workflow is well-suited for Kitaru's
  durable execution model, then design the flow architecture — checkpoint
  boundaries, wait points, replay anchors, memory-vs-artifact strategy,
  memory scope design, operator surface, and MVP scope. Runs a structured
  interview to help users identify what benefits from durability, what doesn't,
  what should live in memory versus artifacts, and where replay/resume
  boundaries should go. Produces a flow_architecture.md specification document.
  Use this skill whenever a user describes an agent workflow they want to make
  durable, asks whether Kitaru is right for their use case, seems unsure about
  where to place checkpoints or waits, needs to choose between SDK /
  KitaruClient / CLI / MCP control surfaces, asks how to handle cross-execution
  shared state, or arrives with a workflow that might be too simple or too
  complex for Kitaru. Also use when the user says "I want to build an agent"
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
  execution, approvals, retries, side effects, durable state, and reporting
  into a single tangled structure.
- **The over-checkpointed design**: every tiny helper is a checkpoint, which
  adds serialization cost without adding replay value.
- **The wrong tool problem**: the user needs streaming chat, sub-100ms serving,
  or a plain script rather than durable orchestration.
- **The fuzzy durability problem**: the workflow might be a good Kitaru fit, but
  nobody has decided where waits, replay anchors, memory boundaries, or side
  effects should live.

Your value is to turn that fog into a practical architecture.

## What Kitaru is

Kitaru is a durable execution layer for Python workflows built around four
user-facing surfaces:

- **SDK primitives**: `@flow`, `@checkpoint`, `wait()`, `log()`, `save()`,
  `load()`, `llm()`, `memory.configure()`, `memory.set()`, `memory.get()`,
  `memory.list()`, `memory.history()`, `memory.delete()`, plus configuration
  helpers (`configure`, `connect`, `create_stack`, `list_stacks`,
  `current_stack`, `use_stack`, `delete_stack`)
- **KitaruClient** (inspection and control of existing executions plus explicit
  memory/artifact administration): `executions.get / list / latest / logs /
  pending_waits / input / abort_wait / retry / resume / replay / cancel`,
  `artifacts.list / get`, and `memories.get / list / history / set / delete /
  scopes`
- **CLI control**: `kitaru login`, `kitaru run`, `kitaru executions ...`,
  `kitaru memory ...`, stack/model/secret commands (including remote stack
  creation for `kubernetes`, `vertex`, `sagemaker`, `azureml`), and runtime
  inspection commands
- **MCP control**: execution tools (`kitaru_executions_list/get/latest/run/
  input/retry/replay/cancel`), memory tools (`kitaru_memory_list/get/set/
  delete/history`), artifact tools, status, stack listing, and `manage_stack`
  (create/delete including remote stacks)

It also ships a **PydanticAI adapter** (`wrap(...)`, `hitl_tool(...)`) for agent
workloads that want Kitaru tracking without rewriting the whole control flow.

### Execution model

Kitaru uses durable rerun-from-top execution.

- **Retry** continues the same execution after failure.
- **Resume** continues the same execution after a `wait()` is resolved (manual
  fallback if auto-continuation doesn't trigger).
- **Replay** starts a new execution derived from an earlier one, using
  checkpoint selectors (not wait selectors) as replay anchors.
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
Stable memory scopes and important keys become the handles people use to inspect
or patch durable state later.

### Surface ownership

Not every surface can do every job:

- **Launching executions**: SDK flow objects (`.run()`), CLI
  (`kitaru run`), MCP (`kitaru_executions_run`) — **not** `KitaruClient`
- **Inspecting/controlling executions**: `KitaruClient`, CLI, MCP
- **Using module-level memory inside flow code**: SDK `kitaru.memory`
- **Explicit-scope memory administration**: `KitaruClient`, CLI, MCP
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
- Operator needs: who will inspect logs, replay work, submit wait input, seed
  or edit durable state, or cancel runs later

If the answer is thin, ask targeted follow-ups about side effects, human
intervention, durable shared state, and failure recovery.

### Memory-oriented discovery questions

Ask these when the workflow appears to need state beyond one execution:

- What information must survive across executions?
- Should that information be fetched by stable key, or is it really tied to one
  execution output?
- Who will seed or edit that state: flow code, admin scripts, a human operator,
  or an MCP assistant?
- Does the state belong at **namespace**, **flow**, or **execution** scope?
- Does the workflow need replay-frozen values, or is "latest durable state"
  acceptable?

These questions help you decide whether the design wants **memory** or
**artifacts**.

## Phase 2: Assess fit

Determine whether Kitaru is actually the right tool.

### Strong signals that Kitaru fits

- Expensive steps you do not want to redo during development or production
  recovery
- Human approval or correction points that must survive process restarts
- Multi-step workflows that benefit from replay after a checkpoint
- Operational debugging needs: logs, artifacts, execution history, audit trail
- Durable shared state that should survive across executions under stable keys

### Signals that Kitaru may be unnecessary

- One-shot LLM calls with little cost and no replay value
- Streaming chat UIs
- Low-latency request/response serving
- Simple automation scripts with no durable state
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
- memory operations that belong in the flow body

### Real runtime constraints to respect

These are not style preferences. They are actual implementation boundaries.

- Flows do not nest.
- Checkpoints do not nest.
- `wait()` can only run in the flow body, never inside a checkpoint.
- `save()` and `load()` require checkpoint scope.
- `kitaru.memory.*` is allowed in flow scope, but forbidden inside a
  checkpoint.
- Outside a flow, module-level memory use requires `memory.configure(scope=...)`
  first.
- Module-level memory uses the active configured scope; explicit `scope=` lives
  on client/CLI/MCP surfaces instead.
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

### Memory vs artifacts

This is one of the most important design choices.

Use **memory** when the workflow needs durable shared state addressed by stable
`key + scope` names.

Use **artifacts** when the value is an execution output or replay/debug boundary
that should stay tied to a specific run or checkpoint.

A simple test:

- If the workflow needs "the current repo style guide" or "the latest customer
  preference", that smells like **memory**.
- If the workflow needs "the exact draft produced in execution X" or "the exact
  retrieval output from checkpoint Y", that smells like an **artifact**.

Do not silently substitute memory for explicit checkpoint outputs. Memory is not
a drop-in replacement for replay-stable artifacts.

### Memory scope design

When memory is the right fit, choose the scope deliberately:

- **namespace**: shared durable state across many executions, users, or agents
- **flow**: state that naturally belongs to one flow name
- **execution**: state isolated to one run but still key-addressable

Important asymmetry to remember:

- Module-level `kitaru.memory` uses an **active scope** set by
  `memory.configure(...)` or the active flow name
- `KitaruClient.memories`, CLI memory commands, and MCP memory tools use
  **explicit scope** on each operation

Stable scope names become operator handles just like checkpoint and wait names
become operator handles.

### Side effects

Treat side effects like doors you should unlock carefully.

Good pattern:
1. plan or prepare in one checkpoint
2. `wait()` for approval if needed
3. commit the side effect in its own checkpoint

Isolate non-idempotent actions such as sending emails, creating PRs, or writing
to external systems.

## Phase 4: Choose the operator surface

Do not scope only the workflow code. Also scope how the workflow will be run and
operated.

Ask which surface will be used for each job:

- launch or deploy the flow
- inspect execution status
- read logs
- provide wait input
- abort a wait
- replay from a checkpoint
- cancel a stuck run
- inspect artifacts
- seed memory
- inspect or edit memory
- list memory scopes
- create/manage stacks

Use these rules:

- **SDK flow objects** for launching new executions from Python code
- **SDK `kitaru.memory`** for in-flow memory usage and outside-flow scripts that
  can work with one active configured scope
- **KitaruClient** for programmatic inspection and control of existing
  executions, plus explicit-scope memory administration
- **CLI** for human operators and shell-based workflows; also the only way to
  log in with managed workspace names/IDs
- **MCP** for agent tools and LLM-assisted operations

Important asymmetries to account for in the design:

| Capability | SDK | KitaruClient | CLI | MCP |
|---|---|---|---|---|
| Launch new execution | Yes (flow object) | No | Yes | Yes |
| Inspect execution | Limited | Yes | Yes | Yes |
| Resolve wait input | No | Yes | Yes | Yes |
| Abort wait | No | Yes | No | No |
| Resume paused execution | No | Yes | Yes | No |
| Replay execution | Yes (flow object) | Yes | Yes | Yes |
| Browse artifacts | No | Yes | No | Yes |
| List pending waits | No | Yes | No | No |
| Create local stack | Yes | No | Yes | Yes |
| Create remote stack | No | No | Yes | Yes |

### Memory-specific asymmetries

| Memory capability | SDK `kitaru.memory` | KitaruClient | CLI | MCP |
|---|---|---|---|---|
| Use memory inside flow code | Yes | No | No | No |
| Outside-flow memory script writes | Yes, after `memory.configure(...)` | Yes | No | No |
| Explicit-scope admin | Limited | Yes | Yes | Yes |
| List scopes | No | Yes (`memories.scopes()`) | Yes (`kitaru memory scopes`) | No |
| Versioned read | Yes (`memory.get(version=...)`) | Yes | No | Yes |
| Prefix list | No | Yes (`memories.list(..., prefix=...)`) | No | Yes |

## Phase 5: Replay strategy

Ask explicitly: "If this workflow fails or the requirements change, where would
you want to restart from without redoing everything before it?"

Then design replay anchors deliberately.

### Replay anchor rules

- Stable checkpoint names are the primary replay anchors
- `from_` targets checkpoint selectors (checkpoint name, invocation ID, or call
  ID) — wait selectors are not valid replay anchors
- Override keys use the `checkpoint.<selector>` namespace only; `wait.*`
  overrides are not supported in replay
- If the replayed execution reaches a wait, resolve it operationally via
  `input`, not via override keys
- Duplicate or vague names make replay painful later

### Memory replay caveat

Memory is durable, but it is not fully replay-frozen in the current release.

That means:

- replayed reads may observe newer memory values than the source execution saw
- replayed writes create new memory versions

If the user needs frozen replay semantics for a critical input, keep that input
as an explicit checkpoint output/artifact instead of shared memory.

When scoping, write down which checkpoint names are intended to be stable public
replay selectors.

## Phase 6: PydanticAI-specific guidance

When the user is building with PydanticAI, scope the workflow around the outer
agent turn, not every internal model call.

Use these rules:

- `wrap(...)` is for agent/model/tool tracking under Kitaru; wrap the agent once
  at module scope and reuse the wrapped reference
- keep explicit outer checkpoints with `type="llm_call"` around major agent
  turns for clear replay boundaries
- `hitl_tool(...)` is a tool marker/decorator that bridges tool-time approvals
  back to flow-level `wait(...)` — it is not the wait primitive itself
- deferred tool flows (`ApprovalRequired`, `CallDeferred`) are not supported in
  the current adapter; do not design a workflow around them
- MCP-backed toolsets are supported (via `KitaruMCPToolset`), so they can be
  part of the design if the user already relies on MCP tools
- only `run()` and `run_sync()` are explicitly synthetic-checkpointed at flow
  scope; do not assume `iter()` behaves identically

## Phase 7: Check anti-patterns

Review the proposed design for these smells:

- too many tiny checkpoints
- waits buried inside logic that belongs in the flow body
- nested checkpoints or attempts to call flows from flows
- memory operations planned inside checkpoints
- memory used where replay-frozen artifacts are required
- module-level memory designs that assume per-call `scope=`
- CLI or MCP operator plans that assume default memory scope inference
- side effects mixed into planning checkpoints
- artifact sharing with no naming strategy
- replay needs discussed abstractly but no concrete checkpoint names chosen
- memory scopes or keys left vague even though operators must inspect them later
- assuming CLI, client, and MCP all expose the same controls
- using `KitaruClient` to launch executions (it can't — use flow objects)
- using SDK `create_stack(...)` for remote stacks (it's local-only)
- PydanticAI designs that depend on deferred tools
- cross-flow artifact designs with no plan for how downstream flows receive
  upstream execution IDs

## Phase 8: Define the MVP flow

Push the user toward the smallest end-to-end durable slice that creates real
value.

The MVP should usually have:

- 2-4 checkpoints
- at most one wait unless human review is the core product
- one clear operator surface for the main operational tasks
- a deliberate memory decision (yes/no, and why)
- a small set of stable replay anchors (checkpoint names)
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
- **Launch / deploy**: [SDK flow object | CLI | MCP] (not KitaruClient)
- **Logs / inspection**: [KitaruClient | CLI | MCP]
- **Wait input**: [KitaruClient | CLI | MCP]
- **Wait abort**: [KitaruClient] (only surface with abort_wait)
- **Resume**: [KitaruClient | CLI] (not MCP)
- **Replay / cancel**: [surface]
- **Artifact inspection**: [KitaruClient | MCP] (not CLI)
- **Memory seed/update**: [SDK module API | KitaruClient | CLI | MCP]
- **Memory inspection**: [KitaruClient | CLI | MCP]
- **Memory scope listing**: [KitaruClient | CLI]
- **Stack management**: [SDK (local only) | CLI (local + remote) | MCP (local + remote)]

## Memory Strategy
- **Use memory?**: [yes/no]
- **Why memory vs artifacts?**: [brief reasoning]
- **Scopes**: [scope -> scope_type -> owner]
- **Keys**: [stable keys and what they store]
- **Seed/update surfaces**: [module API | KitaruClient | CLI | MCP]
- **Replay caveat**: [if relevant]

## Flow Design

### Flow: [name] (MVP)
- **Purpose**: [what it orchestrates]
- **Trigger**: [how it starts]
- **Checkpoints**:
  1. [checkpoint_name] — [what it does] -> [output type]
  2. [checkpoint_name] — [what it does] -> [output type]
- **Wait points**:
  - [wait_name] — [what decision/input is needed, schema type]
- **Replay anchors** (checkpoint selectors only):
  - [checkpoint_name] — [why this is a stable restart point]
- **Replay story**: [what can be regenerated without redoing everything]
- **Side effects**: [what external systems are touched and how they are guarded]

### Flow: [name] (Phase 2)
[Optional same structure]

## Cross-Flow Data
[If multiple flows exist, explain what artifacts are shared, who consumes them,
and how downstream flows obtain upstream execution IDs for `load(...)` calls. If
memory is shared across flows, name the scopes and key owners explicitly.]

## Naming Strategy
- **Stable checkpoint names** (replay anchors): [...]
- **Stable wait names** (operator input handles): [...]
- **Stable memory scopes / keys**: [...]
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
   memory decisions, memory scopes, and operator surfaces into implementation

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
