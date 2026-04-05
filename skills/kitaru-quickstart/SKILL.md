---
name: kitaru-quickstart
description: >
  Interactive onboarding for new Kitaru users. Scaffolds a personalized demo
  flow, demonstrates crash recovery with replay, human-in-the-loop with
  wait(), durable memory across executions, and optional MCP integration.
  Use when a user mentions kitaru quickstart, getting started with kitaru,
  kitaru demo, kitaru onboarding, try kitaru, learn kitaru, what is kitaru,
  show me kitaru, kitaru tutorial, or wants to see what Kitaru does.
---

# Kitaru Quickstart

Build and run a working Kitaru demo tailored to the user's domain. Take
someone from "I've heard of Kitaru" to "I understand crash recovery, replay,
wait, and memory" in a single session.

> **Relationship to other skills**:
> - `/kitaru-quickstart` → activation and intuition (this skill)
> - `/kitaru-scoping` → design durability for a real workflow
> - `/kitaru-authoring` → refactor production code with Kitaru primitives

## Before you start

Ask three questions using the structured question tool (`AskUserQuestion` in
Claude Code, `request_user_input` in Codex) before generating any code. If
no structured question tool exists, ask in chat with short numbered
questions.

### Question 1: Domain

> Which workflow is closest to what you care about?

- **Research/content** — gather → draft → approve → publish
- **Coding agent** — analyze issue → generate patch → approve → merge
- **Data pipeline** — ingest → validate → transform → load
- **Support/triage** — classify → draft response → approve → escalate
- **Other**

If the user picks "other" and their use case does not map to any track,
suggest they describe their architecture in the
[ZenML Slack](https://zenml.io/slack) or open an issue on
[zenml-io/kitaru](https://github.com/zenml-io/kitaru) so it can be scoped
properly. Then default to the research/content track for the demo.

### Question 2: Runtime

> Which runtime should the demo use?

- **Raw Python** (default) — no dependencies beyond Kitaru, uses mock
  functions with `time.sleep()`
- **PydanticAI** — uses `TestModel`, no API keys needed
- **Simplest working path** — you choose

For v1, use the raw Python track template regardless of choice. If the user
specifically requests PydanticAI, complete the quickstart in raw Python and
then offer `/kitaru-authoring` for PydanticAI conversion.

### Question 3: Depth

> How deep today?

- **Five-minute tour** — crash → replay demo only
- **Guided build** — full walkthrough
- **Guided build + MCP** — full walkthrough with MCP integration

## Depth routing

| Depth              | Phases              |
|--------------------|---------------------|
| Five-minute tour   | 0 → 1 → 5          |
| Guided build       | 0 → 1 → 2 → 2.5 → 3 → 5 |
| Guided build + MCP | 0 → 1 → 2 → 2.5 → 3 → 4 → 5 |

---

## Phase 0: Environment setup

1. **Check safety**: Is the current directory safe to modify?
   - If it has `src/`, `.git` with uncommitted changes, `package.json`,
     `pyproject.toml`, or other project markers: ask the user and default to
     creating `./kitaru-quickstart-demo/`.
   - If it is empty or a scratch directory: work here.

2. **Verify Python**: `python3 --version` (require 3.10+)

3. **Verify uv**: `uv --version`
   - If missing, suggest:
     `curl -LsSf https://astral.sh/uv/install.sh | sh`

4. **Create project and install Kitaru**:
   ```bash
   mkdir -p kitaru-quickstart-demo
   cd kitaru-quickstart-demo
   uv init --no-workspace
   uv add kitaru
   ```

5. **Initialize Kitaru**: `kitaru init`

6. **Verify**: `kitaru status`

If any step fails, explain the error, apply a fix, and retry once. If it
fails again, present the error to the user and ask for guidance.

---

## Phase 1: Crash-and-replay demo

This is the core activation sequence. It must feel dramatic, not academic.

### Step 1: Load the track template

Read the template from `references/tracks/{track}.py` based on the user's
domain choice:

| Domain          | Template file  | Flow name        |
|-----------------|---------------|------------------|
| Research/content| `research.py` | `research_flow`  |
| Coding agent    | `coding.py`   | `coding_flow`    |
| Data pipeline   | `data.py`     | `data_flow`      |
| Support/triage  | `support.py`  | `support_flow`   |

### Step 2: Customize the template

Adapt variable names, mock data, and print statements to the user's domain.

**CRITICAL**: Do NOT alter the placement, arguments, or syntax of `@flow`,
`@checkpoint`, `wait()`, `log()`, or `memory.*` calls. Only customize the
internal business logic of checkpoint functions (string content, mock data
values, variable names).

### Step 3: Write the customized flow

Write the customized template to `demo_flow.py` in the project directory.
The template includes a pre-baked crash marked with:

```python
# --- QUICKSTART CRASH: remove this line to fix the simulated failure ---
raise Exception("Simulated ...")
# --- end crash ---
```

### Step 4: Run the flow (it will crash)

```bash
uv run python demo_flow.py
```

Read the output. Verify you see a traceback at the second checkpoint.

### Step 5: Explain the crash

Tell the user:

> "The flow crashed at the second checkpoint. In a traditional script,
> everything from checkpoint 1 would be lost — you'd rerun the entire
> pipeline and redo all that work. With Kitaru, checkpoint 1's output is
> saved to the local SQLite database. Let's fix the crash and replay from
> exactly where it broke."

### Step 6: Fix the code

Remove the lines between `# --- QUICKSTART CRASH ---` and
`# --- end crash ---` from `demo_flow.py`.

### Step 7: Get the execution ID

From the crash output, or run:

```bash
kitaru executions list --output json
```

Extract the execution ID of the failed run.

### Step 8: Replay from the failed checkpoint

```bash
kitaru executions replay <EXEC_ID> --from <CHECKPOINT_NAME>
```

Checkpoint names by track:

| Track           | Replay from       |
|-----------------|-------------------|
| Research/content| `draft_content`   |
| Coding agent    | `generate_patch`  |
| Data pipeline   | `transform`       |
| Support/triage  | `draft_response`  |

### Step 9: Verify and explain

Read the replay output. Verify that checkpoint 1 was loaded from cache (not
re-executed). Then tell the user:

> "Notice that the first checkpoint was loaded from cache and skipped —
> only the second checkpoint onwards re-executed. That's crash recovery
> with zero wasted work. In production, this means no burned tokens, no
> repeated API calls, no lost progress."

**Verification**: If the output does not show caching behavior, read the
full output, diagnose the issue, and retry once.

If the user chose **five-minute tour**, skip to **Phase 5**.

---

## Phase 2: Human-in-the-loop with `wait()`

### Step 1: Run the flow again

The crash is now fixed. Run the flow:

```bash
uv run python demo_flow.py
```

The flow will pause at the `wait()` gate.

### Step 2: Explain the pause

> "The flow is now paused at a wait gate. In production, your agent
> releases compute while waiting — no idle containers burning money. The
> execution state is safely persisted. A human (or another agent) can
> provide input whenever they're ready."

### Step 3: Provide input

```bash
kitaru executions input <EXEC_ID> --wait <WAIT_NAME> --value true
```

Wait names by track:

| Track           | Wait name            |
|-----------------|----------------------|
| Research/content| `approve_draft`      |
| Coding agent    | `approve_merge`      |
| Data pipeline   | `approve_load`       |
| Support/triage  | `approve_escalation` |

### Step 4: Resume if needed

If the execution does not auto-continue:

```bash
kitaru executions resume <EXEC_ID>
```

### Step 5: Verify completion

Confirm the flow completed successfully and show the final output.

---

## Phase 2.5: Durable memory demo

### Step 1: Explain memory

> "Kitaru has durable memory — your flows can remember state across
> executions. The flow you just ran stored some context. Let's run it
> again with different input and watch it remember."

### Step 2: Run the flow again with different input

Choose a different argument that makes sense for the track:

| Track           | Example second input             |
|-----------------|----------------------------------|
| Research/content| `"quantum computing"`            |
| Coding agent    | `"optimize database query speed"`|
| Data pipeline   | `"inventory_data_2026_q2.csv"`   |
| Support/triage  | `"login page returns 500 error"` |

```bash
uv run python demo_flow.py "<new input>"
```

### Step 3: Point out the memory detection

The flow logs should show it detected the previous input from memory. Point
this out to the user.

### Step 4: Inspect memory from the CLI

```bash
kitaru memory list --scope <FLOW_NAME>
kitaru memory get last_topic --scope <FLOW_NAME>
```

Memory key names by track:

| Track           | Flow name       | Memory key     |
|-----------------|-----------------|----------------|
| Research/content| `research_flow` | `last_topic`   |
| Coding agent    | `coding_flow`   | `last_issue`   |
| Data pipeline   | `data_flow`     | `last_source`  |
| Support/triage  | `support_flow`  | `last_ticket`  |

### Step 5: Explain

> "Memory persists across executions under stable keys. Your agent can
> accumulate knowledge, preferences, or context over time. Operators can
> inspect or edit that state from the CLI, Python client, or MCP tools."

---

## Phase 3: Inspect and explore

### Step 1: Show execution history

```bash
kitaru executions list
```

### Step 2: Inspect a specific execution

```bash
kitaru executions get <EXEC_ID>
```

### Step 3: View structured logs

```bash
kitaru executions logs <EXEC_ID>
```

### Step 4: Explain

> "Every checkpoint, wait, memory operation, and log call is tracked.
> This gives you full observability into what your agent did, when, and
> why — without building custom logging infrastructure."

---

## Phase 4: MCP integration (opt-in)

Only run this phase if the user chose **guided build + MCP**.

### Step 1: Explain the value

> "I can configure your environment so I can directly query Kitaru's
> execution database, provide input to waiting flows, and trigger
> replays — all through natural language."

### Step 2: Detect the host

Check filesystem markers:

- `.claude/` → Claude Code
- `.cursor/` or `.cursorignore` → Cursor
- `.codex/` → Codex CLI

If no markers found or multiple matches, ask the user which host they are
using.

### Step 3: Install the MCP extra

```bash
uv add kitaru --extra mcp
```

### Step 4: Load the host-specific guide

Read the appropriate file from `references/hosts/{host}.md`:

- Claude Code → `references/hosts/claude-code.md`
- Cursor → `references/hosts/cursor.md`
- Codex → `references/hosts/codex.md`
- Copilot → `references/hosts/copilot.md`
- Gemini → `references/hosts/gemini.md`

### Step 5: Ask for explicit consent

Before modifying any configuration file:

1. Show the exact file path that will be created or modified.
2. Show the exact content or diff that will be written.
3. Ask for explicit approval.

**Never write to MCP config files without consent.**

### Step 6: Apply configuration

Follow the host-specific guide to configure the MCP server.

### Step 7: Demonstrate MCP tools

Show at least 3 MCP tools in action against the demo flow:

1. **List executions** — show the executions from earlier phases
2. **Inspect execution** — read status and details of a specific run
3. **Read logs** — show structured logs from a checkpoint

If a wait is currently pending, also demonstrate:
4. **Provide input** — resolve a wait via MCP

If applicable:
5. **Replay** — trigger a replay via MCP

### Step 8: Handle failure

If MCP installation or configuration fails:

1. Read `references/mcp-config-guide.md`
2. Explain the manual setup path to the user
3. Continue to Phase 5 without MCP

---

## Phase 5: Handoff and next steps

### Step 1: Write `KITARU_NEXT_STEPS.md`

Write this file to the project directory, filling in the actual values from
the session:

```markdown
# Kitaru Quickstart — What You Built

## Demo summary
- **Domain**: [user's chosen domain]
- **Flow**: [flow name] with [N] checkpoints
- **Demonstrated**: crash recovery, replay[, wait(), memory, MCP]

## Kitaru primitives used

| Primitive | What it does | Where you saw it |
|---|---|---|
| `@flow` | Durable orchestration boundary | `demo_flow.py` |
| `@checkpoint` | Replay-safe unit of work | `demo_flow.py` |
| `wait()` | Human-in-the-loop gate | `demo_flow.py` |
| `log()` | Structured metadata | `demo_flow.py` |
| `memory.set/get` | Cross-execution durable state | `demo_flow.py` |
| `replay` | Re-execute from a checkpoint | CLI |

## Next steps
- **`/kitaru-scoping`** — Design durability for a real workflow
- **`/kitaru-authoring`** — Refactor existing code with Kitaru primitives

## Resources
- [Kitaru documentation](https://kitaru.ai/docs)
- [ZenML Slack](https://zenml.io/slack)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)
```

Adjust the "Demonstrated" line and primitives table based on which phases
actually ran (five-minute tour only shows crash recovery and replay).

### Step 2: Offer next steps

> "Your quickstart is complete! Here's what you can do next:"
>
> - **`/kitaru-scoping`** if you want to design durability for a real
>   workflow
> - **`/kitaru-authoring`** if you have existing code you'd like to
>   refactor with Kitaru primitives

---

## Guardrails

Enforce these rules throughout the entire session:

1. **Template integrity**: Never alter the placement, arguments, or syntax
   of `@flow`, `@checkpoint`, `wait()`, `log()`, `memory.*`, `save()`, or
   `load()` decorators or calls. Only customize the internal business
   logic of checkpoint functions.

2. **Scope limit**: Keep generated code under 150 lines. Use mock functions
   with `time.sleep()` to simulate latency. Do not implement real API
   connections or complex data processing.

3. **Verification**: After every terminal command, read the output and
   verify success before proceeding. Never assume a command worked.

4. **Failure recovery**: If a step fails, explain the error, apply a fix,
   and retry once. If it fails again, present the error to the user and
   ask for guidance. Do not loop.

5. **MCP consent**: Never write to MCP config files without showing the
   user the exact diff and receiving explicit approval.

6. **No blanket shell approval**: Do not request broad shell preapproval
   from the user.

7. **Memory placement**: `memory.*` calls belong in the flow body only,
   never inside checkpoints.

8. **Real commands only**: Use only documented Kitaru CLI commands:
   - Replay: `kitaru executions replay <id> --from <checkpoint>`
     (not `kitaru replay`)
   - There is no `kitaru ui` command
   - There is no top-level `kitaru run` command
   - Wait input: `kitaru executions input <id> --wait <name> --value <val>`

9. **No API key requirements**: The quickstart must run without any API
   keys, cloud credentials, or external service accounts.

10. **Checkpoint outputs must be serializable**: All mock return values from
    checkpoints must be JSON-serializable (strings, numbers, lists, dicts).
