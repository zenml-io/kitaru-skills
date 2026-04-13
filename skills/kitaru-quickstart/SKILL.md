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
wait, memory, and the dashboard" in a single teaching session.

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

## Tutorial pacing rules

This is a tutorial, not a firehose. Throughout the session:

1. **After writing any non-trivial file**, stop and direct the user to open
   it. Give concrete line numbers from the file you just wrote, point out
   what to notice, and ask whether they want a walkthrough before you run it.
2. **After every phase**, summarize what happened in plain language, explain
   why it matters, and ask whether to continue or dig deeper.
3. **Prefer dashboard-first teaching**. The CLI is the scriptable surface;
   the dashboard is the visual "what just happened?" surface.
4. **Use venv-aware commands** from inside the demo project:
   `uv run kitaru ...`, `uv run python demo_flow.py`, and
   `uv run kitaru-mcp ...`.
5. Refer to the demo directory as `<DEMO_DIR>` and its absolute path as
   `<ABSOLUTE_DEMO_DIR>`. Capture the absolute path with `pwd` after
   creating the project.

---

## Phase 0: Environment setup and dashboard

1. **Check safety and avoid ancestor uv config traps**:
   - If the current directory has `src/`, `.git`, `package.json`,
     `pyproject.toml`, `uv.toml`, or other project markers, do not scaffold
     inside it by default.
   - `uv` can inherit ancestor `[tool.uv] exclude-newer = ...` settings and
     silently hide recent Kitaru releases. To avoid that trap, default to a
     neutral location such as `$HOME/kitaru-quickstart-demo` or `/tmp`.
   - If the user insists on a custom path, check for ancestor uv config first
     and explain the risk before proceeding.

2. **Verify prerequisites**:
   ```bash
   python3 --version
   uv --version
   ```
   Require Python 3.10+. If `uv` is missing, suggest:
   `curl -LsSf https://astral.sh/uv/install.sh | sh`

3. **Choose the demo project directory before creating anything**:
   ```bash
   cd "$HOME"
   if [ -e kitaru-quickstart-demo ]; then
     echo "kitaru-quickstart-demo already exists"
   fi
   ```

   If the directory already exists, ask whether to reuse it, create a suffixed
   directory such as `kitaru-quickstart-demo-2`, or delete/recreate it after
   explicit approval. Do not run `uv init` until the user has made that choice.

   Then create the approved directory and install Kitaru:

   ```bash
   DEMO_DIR="kitaru-quickstart-demo"  # or the approved suffixed name
   mkdir -p "$DEMO_DIR"
   cd "$DEMO_DIR"
   pwd
   uv init --no-workspace
   uv add 'kitaru[local,mcp]>=0.4.0'
   ```

   Store the printed `pwd` value as `<ABSOLUTE_DEMO_DIR>`.

   If `uv add` says only an older Kitaru version is available, explain that
   an ancestor `exclude-newer` setting may be filtering PyPI. Move the demo
   to a neutral path and retry. If it still fails, stop with the clear
   message that this quickstart needs Kitaru `>=0.4.0` because it uses
   module-level `kitaru.memory`.

4. **Initialize and verify Kitaru**:
   ```bash
   uv run kitaru --version
   uv run kitaru init
   uv run kitaru status
   ```

5. **Start the local server and open the dashboard**:
   ```bash
   uv run kitaru login
   ```

   Tell the user:

   > "Kitaru's local server should now be running. Open
   > http://127.0.0.1:8383 in your browser. Take a minute to look around —
   > the dashboard is where you'll be able to see executions, checkpoints,
   > waits, and replay behavior visually. Tell me when you've had a look and
   > we'll continue."

   Pause here and wait for acknowledgement. If local server startup fails
   because local dependencies are missing, rerun
   `uv add 'kitaru[local,mcp]>=0.4.0'` and retry once. If the dashboard is
   unavailable but `uv run kitaru status` works, ask whether to continue with
   CLI-only inspection.

---

## Phase 1: Crash-and-replay demo

This is the core activation sequence. It must feel dramatic, not academic.

### Step 1: Load the track template

Read the template from `references/tracks/{track}.py` based on the user's
domain choice:

| Domain           | Template file  | Flow name       | Replay from      |
|------------------|----------------|-----------------|------------------|
| Research/content | `research.py`  | `research_flow` | `draft_content`  |
| Coding agent     | `coding.py`    | `coding_flow`   | `generate_patch` |
| Data pipeline    | `data.py`      | `data_flow`     | `transform`      |
| Support/triage   | `support.py`   | `support_flow`  | `draft_response` |

### Step 2: Customize the template

Adapt variable names, mock data, and print statements to the user's domain.

**CRITICAL**: Do NOT alter the placement, arguments, or syntax of `@flow`,
`@checkpoint`, `wait()`, `log()`, `memory.*`, or the `--replay` helper. Only
customize the internal business logic of checkpoint functions: string
content, mock data values, and explanatory print text.

### Step 3: Write and inspect the customized flow

Write the customized template to `demo_flow.py` in the project directory.
The template includes a pre-baked crash marked with:

```python
# --- QUICKSTART CRASH: remove this line to fix the simulated failure ---
raise Exception("Simulated ...")
# --- end crash ---
```

After writing the file, show line numbers:

```bash
nl -ba demo_flow.py | sed -n '1,180p'
```

Pause and tell the user to open `demo_flow.py`. Point out exact line ranges
for these items:

- the `@flow` function: this is the durable orchestration boundary;
- the `@checkpoint` functions: these are replay save points;
- `memory.get(...)` and `memory.set(...)`: these deliberately live in the
  flow body, not inside checkpoints;
- the simulated crash in the second meaningful checkpoint;
- the `wait(...)` gate that will pause for human input later;
- the `--replay <EXEC_ID>` helper at the bottom of the file.

Ask: "Want me to walk through any part of this before we run it?" Wait for
acknowledgement before proceeding.

### Step 4: Run the flow — it should crash

```bash
uv run python demo_flow.py
```

Read the output. Verify you see a traceback at the simulated crash in the
second checkpoint. Then ask the user to look at the dashboard: the failed
execution should now be visible in the runs list.

### Step 5: Explain the crash

Tell the user:

> "The flow crashed at the second checkpoint. In a traditional script,
> everything before that crash is just gone unless you built your own save
> system. With Kitaru, checkpoint 1 is already persisted. Think of it like a
> video game save point: we can fix the bug and resume from the save instead
> of replaying the whole level."

### Step 6: Fix the code

Remove the crash marker block from `demo_flow.py`:

```python
# --- QUICKSTART CRASH: remove this line to fix the simulated failure ---
raise Exception("Simulated ...")
# --- end crash ---
```

Show the diff or the relevant edited line range. Pause briefly and say what
changed before replaying.

### Step 7: Get the failed execution ID

From the crash output, or run:

```bash
uv run kitaru executions list --output json
```

Extract the execution ID of the failed run.

### Step 8: Replay from the failed checkpoint

Use the template's Python replay helper as the guided quickstart path:

```bash
uv run python demo_flow.py --replay <FAILED_EXEC_ID>
```

If this command prints an execution ID and then appears to keep running, that
is expected when the replay reaches the `wait()` gate. Leave that terminal
open. In a second terminal, run `cd <ABSOLUTE_DEMO_DIR>` before using the
input command. If the user chose the five-minute tour, resolve that wait now
with `uv run kitaru executions input <EXEC_ID> --value true` so the replay can
finish before handoff. If the user chose guided build, use the parked replay
execution as the bridge into Phase 2 instead of starting another run.

The helper calls `flow.replay(exec_id, from_="<CHECKPOINT_NAME>")` with the
track's replay checkpoint. This avoids the known local CLI fallback issue
where direct CLI replay can fail to resolve the flow object. If the helper is
not available for some reason, the CLI workaround is:

```bash
PYTHONPATH=. uv run kitaru executions replay <FAILED_EXEC_ID> --from <CHECKPOINT_NAME>
```

### Step 9: Verify in the dashboard and explain

Read the replay output, then ask the user to inspect the dashboard. They
should be able to compare the failed source execution with the replayed
execution and see that earlier work was reused instead of repeated.

Tell the user:

> "The important thing is not just that the code ran after the fix. The
> important thing is where it restarted. Kitaru kept the completed checkpoint
> and replayed from the named boundary. That's the durable-execution trick:
> no burned tokens, no repeated API calls, no lost progress."

**Verification**: If replay fails, read the full output. First retry with the
`PYTHONPATH=.` CLI workaround above. If that also fails, stop and present the
error instead of looping.

End the phase with a plain-language recap and ask whether to continue. If
the user chose **five-minute tour**, skip to **Phase 5**.

---

## Phase 2: Human-in-the-loop with `wait()`

### Step 1: Explain before running

Before triggering the wait, tell the user:

> "The next run will reach a `wait()` gate. That means the execution parks
> safely and releases compute while it waits for input. The dashboard should
> show it as waiting, and the CLI can provide the input later."

### Step 2: Reach a waiting execution

If the Phase 1 replay is already parked at `wait()`, reuse that execution for
this phase. Do not start a second run just to demonstrate the same wait.

If there is no waiting execution yet, run the flow again:

```bash
uv run python demo_flow.py
```

The flow should pause at the `wait()` gate. Because `demo_flow.py` waits for
the final result, the terminal may stay occupied after it prints the execution
ID. That is expected. Leave it open and use a second terminal in
`<ABSOLUTE_DEMO_DIR>` to provide input. Show the user the waiting status in
the dashboard before resolving it.

### Step 3: Provide input

The quickstart templates have one pending wait at a time, so the CLI resolves
the single pending wait by execution ID. Do **not** pass a `--wait` flag.

```bash
uv run kitaru executions input <EXEC_ID> --value true
```

Wait names by track, useful for recognizing the dashboard entry:

| Track            | Wait name             |
|------------------|-----------------------|
| Research/content | `approve_draft`       |
| Coding agent     | `approve_merge`       |
| Data pipeline    | `approve_load`        |
| Support/triage   | `approve_escalation`  |

If an execution has multiple pending waits, switch to:

```bash
uv run kitaru executions input --interactive
```

### Step 4: Resume if needed

Input normally continues the execution. If it does not auto-continue:

```bash
uv run kitaru executions resume <EXEC_ID>
```

### Step 5: Verify and summarize

Confirm the flow completed successfully in both CLI output and the dashboard.
Then summarize:

> "The execution was paused without losing state. We gave it a value later,
> and it continued from the wait gate rather than starting over. This is how
> long-running agent workflows can include human approval without babysitting
> a live process."

Ask whether the user wants to continue to memory or discuss waits first.

---

## Phase 2.5: Durable memory demo

### Step 1: Explain memory

> "Kitaru memory lets a flow remember small pieces of state across
> executions. In this demo, the flow records the last topic/issue/source/ticket
> after approval, then reads it at the start of the next run."

### Step 2: Run the flow again with different input

Choose a different argument that makes sense for the track:

| Track            | Example second input              |
|------------------|-----------------------------------|
| Research/content | `"quantum computing"`             |
| Coding agent     | `"optimize database query speed"` |
| Data pipeline    | `"inventory_data_2026_q2.csv"`    |
| Support/triage   | `"login page returns 500 error"`  |

```bash
uv run python demo_flow.py "<new input>"
```

If the dashboard or log backend shows the early
`log(returning_user=True, ...)` metadata, point it out. If logs are sparse,
do not treat that as a failure — the durable proof comes from the CLI memory
inspection in the next steps. If the run pauses at `wait()`, resolve it with
the Phase 2 command so the final `memory.set(...)` call can write the new
value.

### Step 3: Find the flow UUID for CLI memory inspection

Inside the flow body, module-level `kitaru.memory` resolves the active flow
scope automatically. Outside the flow, CLI/MCP/Client calls need an explicit
typed scope. For this quickstart, use the **flow UUID**, not the Python
function name.

Get the execution details:

```bash
uv run kitaru executions get <EXEC_ID> --output json
```

Extract `item.flow_id` from the JSON. If that is not obvious, run:

```bash
uv run kitaru memory scopes --output json
```

and choose the row where `scope_type` is `flow` and the scope corresponds to
the demo flow. Do not use `research_flow`, `coding_flow`, `data_flow`, or
`support_flow` as the CLI scope unless the current CLI explicitly reports
that exact value as the scope.

### Step 4: Inspect memory from the CLI

```bash
uv run kitaru memory list --scope <FLOW_ID> --scope-type flow
uv run kitaru memory get <MEMORY_KEY> --scope <FLOW_ID> --scope-type flow
```

Memory scope and key names by track:

| Track            | Flow function in code | Scope type | CLI scope value                  | Memory key    |
|------------------|-----------------------|------------|----------------------------------|---------------|
| Research/content | `research_flow`       | `flow`     | `flow_id` from execution details | `last_topic`  |
| Coding agent     | `coding_flow`         | `flow`     | `flow_id` from execution details | `last_issue`  |
| Data pipeline    | `data_flow`           | `flow`     | `flow_id` from execution details | `last_source` |
| Support/triage   | `support_flow`        | `flow`     | `flow_id` from execution details | `last_ticket` |

### Step 5: Explain

> "The code had the easy experience: inside the flow, memory knew which flow
> it belonged to. Operator tools need the explicit typed scope, so we used the
> flow UUID. This is like the difference between saying 'my house' while
> you're standing in it and giving someone the exact street address from
> outside."

Ask whether the user wants to continue to the CLI inspection tour.

---

## Phase 3: Inspect and explore

Frame this phase as: "The dashboard showed this visually; the CLI gives you
the same kind of state in scriptable form."

### Step 1: Show execution history

```bash
uv run kitaru executions list
```

### Step 2: Inspect a specific execution

```bash
uv run kitaru executions get <EXEC_ID>
```

Use this as the reliable inspection surface for status, flow name/ID,
checkpoint count, pending wait, and failure information.

### Step 3: View logs with correct expectations

```bash
uv run kitaru executions logs <EXEC_ID>
```

Do not promise that this always shows rich structured logs. On the default
local stack, log output may be sparse or say "No log entries found" depending
on the active log store and runtime setup. That is not a quickstart failure;
fall back to `executions get` and the dashboard.

### Step 4: Explain

> "The dashboard is the visual way to understand what happened. The CLI is
> the scriptable way to inspect the same executions, waits, checkpoints, and
> failures. Logs are useful when the active log backend captures them, but
> execution details are the dependable baseline."

End with a short recap and ask before continuing.

---

## Phase 4: MCP integration (opt-in)

Only run this phase if the user chose **guided build + MCP**.

### Step 1: Explain the value

> "I can configure your agent host so it can query Kitaru's execution state,
> provide input to waiting flows, and trigger replays through MCP. Because MCP
> hosts often launch outside your activated shell, we will point the host at
> the demo project's uv environment explicitly."

### Step 2: Detect the host

Check filesystem markers:

- `.claude/` → Claude Code
- `.cursor/` or `.cursorignore` → Cursor
- `.codex/` → Codex CLI

If no markers are found or multiple match, ask which host the user is using.

### Step 3: Verify the MCP extra and server command

Phase 0 installs the MCP extra. If that was skipped or changed, run:

```bash
uv add 'kitaru[local,mcp]>=0.4.0'
```

Then verify through the project environment:

```bash
uv run --directory <ABSOLUTE_DEMO_DIR> kitaru-mcp --help
```

### Step 4: Load the host-specific guide

Read the appropriate file from `references/hosts/{host}.md`:

- Claude Code → `references/hosts/claude-code.md`
- Cursor → `references/hosts/cursor.md`
- Codex → `references/hosts/codex.md`
- Copilot → `references/hosts/copilot.md`
- Gemini → `references/hosts/gemini.md`

The server configuration should use this shape unless the host requires a
different wrapper:

```json
{
  "mcpServers": {
    "kitaru": {
      "command": "uv",
      "args": ["run", "--directory", "<ABSOLUTE_DEMO_DIR>", "kitaru-mcp"]
    }
  }
}
```

Do not configure this quickstart with a bare `kitaru-mcp` command unless the
user has installed Kitaru globally and explicitly asks for that form.

### Step 5: Ask for explicit consent

Before modifying any configuration file:

1. Show the exact file path that will be created or modified.
2. Show the exact content or diff that will be written.
3. Ask for explicit approval.

**Never write to MCP config files without consent.**

### Step 6: Apply configuration

Follow the host-specific guide to configure the MCP server. Merge into
existing JSON instead of overwriting other servers.

### Step 7: Demonstrate MCP tools

Show at least 3 MCP tools in action against the demo flow:

1. **List executions** — show the executions from earlier phases
2. **Inspect execution** — read status and details of a specific run
3. **Read logs if available** — explain sparse logs the same way as Phase 3

If a wait is currently pending, also demonstrate:
4. **Provide input** — resolve a wait via MCP

If applicable:
5. **Replay** — trigger a replay via MCP

For MCP memory tools, remind the user that scoped memory calls require both
`scope_type` and `scope`. For this quickstart, use `scope_type="flow"` and the
flow UUID discovered in Phase 2.5.

### Step 8: Handle failure

If MCP installation or configuration fails:

1. Read `references/mcp-config-guide.md`.
2. Explain the manual setup path to the user.
3. Continue to Phase 5 without MCP.

---

## Phase 5: Handoff, next steps, and teardown

### Step 1: Write `KITARU_NEXT_STEPS.md`

Write this file to the project directory, filling in the actual values from
the session:

````markdown
# Kitaru Quickstart — What You Built

## Demo summary
- **Domain**: [user's chosen domain]
- **Flow**: [flow name] with [N] checkpoints
- **Demo directory**: [absolute path]
- **Dashboard**: http://127.0.0.1:8383
- **Demonstrated**: crash recovery, replay[, wait(), memory, MCP]

## Commands worth remembering

```bash
uv run kitaru status
uv run kitaru executions list
uv run kitaru executions get <EXEC_ID>
uv run python demo_flow.py --replay <FAILED_EXEC_ID>
uv run kitaru executions input <EXEC_ID> --value true
uv run kitaru memory list --scope <FLOW_ID> --scope-type flow
```

## Kitaru primitives used

| Primitive | What it does | Where you saw it |
|---|---|---|
| `@flow` | Durable orchestration boundary | `demo_flow.py` |
| `@checkpoint` | Replay-safe unit of work | `demo_flow.py` |
| `wait()` | Human-in-the-loop gate | `demo_flow.py` |
| `log()` | Structured metadata when supported by the log backend | `demo_flow.py` |
| `memory.set/get` | Cross-execution durable state | `demo_flow.py` |
| `replay` | Re-execute from a checkpoint boundary | `demo_flow.py --replay` |

## Cleanup options

- Keep the demo directory if you want to experiment more.
- Stop the local server / disconnect when finished:
  `uv run kitaru logout`
- Preview project cleanup from inside the demo directory:
  `uv run kitaru clean project --dry-run`
- Delete the demo directory only after confirming the exact path:
  `rm -rf [absolute path]`

## Next steps
- **`/kitaru-scoping`** — Design durability for a real workflow
- **`/kitaru-authoring`** — Refactor existing code with Kitaru primitives

## Resources
- [Kitaru documentation](https://kitaru.ai/docs)
- [ZenML Slack](https://zenml.io/slack)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)
````

Adjust the "Demonstrated" line and primitives table based on which phases
actually ran. Five-minute tour only shows dashboard setup, crash recovery,
and replay.

After writing the file, pause and tell the user to open it. Ask whether the
summary matches what they learned.

### Step 2: Offer next steps

> "Your quickstart is complete! Here's what you can do next:"
>
> - **`/kitaru-scoping`** if you want to design durability for a real
>   workflow
> - **`/kitaru-authoring`** if you have existing code you'd like to
>   refactor with Kitaru primitives

### Step 3: Offer cleanup, defaulting to keep

Ask whether the user wants to keep or remove the demo. Default to keeping it.
If they want cleanup:

1. If the local server is running, suggest `uv run kitaru logout`.
2. If MCP config was added, offer to remove only the `kitaru` MCP entry.
   Show the exact diff and require approval.
3. If they want to delete the demo directory, show `<ABSOLUTE_DEMO_DIR>` and
   ask for explicit approval before running `rm -rf <ABSOLUTE_DEMO_DIR>`.
4. If they want to reset Kitaru state instead of deleting files, start with
   `uv run kitaru clean project --dry-run` and explain what would be removed.

Never silently delete the demo directory or modify global MCP configuration.

---

## Guardrails

Enforce these rules throughout the entire session:

1. **Template integrity**: Never alter the placement, arguments, or syntax
   of `@flow`, `@checkpoint`, `wait()`, `log()`, `memory.*`, `save()`, or
   `load()` decorators or calls. Only customize internal business logic and
   explanatory text. Preserve the template's `--replay` helper.

2. **Scope limit**: Keep generated code under 150 lines. Use mock functions
   with `time.sleep()` to simulate latency. Do not implement real API
   connections or complex data processing.

3. **Tutorial pacing**: After writing code, stop for inspection. After each
   phase, summarize and ask whether to continue.

4. **Verification**: After every terminal command, read the output and
   verify success before proceeding. Never assume a command worked.

5. **Failure recovery**: If a step fails, explain the error, apply a fix,
   and retry once. If it fails again, present the error to the user and ask
   for guidance. Do not loop.

6. **MCP consent**: Never write to MCP config files without showing the user
   the exact diff and receiving explicit approval.

7. **No blanket shell approval**: Do not request broad shell preapproval from
   the user.

8. **Memory placement**: `memory.*` calls belong in the flow body only,
   never inside checkpoints. CLI/MCP memory inspection needs explicit typed
   scopes; for this quickstart's flow memory, use `scope_type=flow` and the
   `flow_id`, not the Python function name.

9. **Real commands only**: Use only documented Kitaru CLI commands and this
   quickstart's validated forms:
   - Install: `uv add 'kitaru[local,mcp]>=0.4.0'`
   - Local server/dashboard: `uv run kitaru login`, then open
     `http://127.0.0.1:8383`
   - Guided replay: `uv run python demo_flow.py --replay <id>`
   - CLI replay workaround: `PYTHONPATH=. uv run kitaru executions replay <id> --from <checkpoint>`
   - Wait input: `uv run kitaru executions input <id> --value <json>`
   - There is no `kitaru ui`, `kitaru dashboard`, or top-level `kitaru run`
     command in this quickstart.

10. **Logs expectations**: Do not promise that `kitaru executions logs` always
    returns rich structured logs. Empty or sparse logs on the default local
    setup are acceptable; use `executions get` and the dashboard as the
    reliable baseline.

11. **MCP command shape**: Do not configure MCP with a bare `kitaru-mcp` in
    this quickstart. Use `command: "uv"` with
    `args: ["run", "--directory", "<ABSOLUTE_DEMO_DIR>", "kitaru-mcp"]`.

12. **No API key requirements**: The quickstart must run without API keys,
    cloud credentials, or external service accounts.

13. **Checkpoint outputs must be serializable**: All mock return values from
    checkpoints must be JSON-serializable: strings, numbers, lists, and dicts.
