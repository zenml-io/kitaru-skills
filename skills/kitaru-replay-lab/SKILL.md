---
name: kitaru-replay-lab
description: >
  Replay lab for operating on existing Kitaru executions. Use when a user wants
  to recover a failed execution, reproduce a run, fork one replay experiment,
  compare replay output, debug replay divergence, replay a cohort, inspect a
  ReplaySubmission, or use SDK/CLI/MCP replay tools on real execution IDs.
  Triggers on kitaru replay lab, replay experiment, reproduce then fork,
  replay failed execution, replay cohort, execution recovery, replay diff,
  ReplaySubmission, `kitaru executions replay`, or `kitaru_executions_replay`.
---

# Kitaru Replay Lab

Use this skill when the user already has Kitaru executions and wants to recover,
experiment, compare, or debug with replay. This is an operations skill, not the
main authoring reference. For new workflow design, use `kitaru-scoping`; for
writing flows and checkpoints, use `kitaru-authoring`.

The lab rule is:

> **Reproduce first, fork second, diff third.**

A changed replay is only useful after a no-change replay proves the recorded run
can be reproduced faithfully. Otherwise the forked result may be showing replay
noise, changed code, changed external data, or a bad selector rather than the
thing the user meant to test.

## Replay lab loop

Follow these steps in order.

### 1. Classify the replay job

Ask or infer which job the user is doing:

- **Recovery** — a run failed and they want to reuse completed work.
- **Experiment** — they want to change one model, prompt profile, flow input,
  checkpoint result, replacement callable, or exact invocation.
- **Cohort** — they want to apply the same replay plan to many executions.
- **Diagnosis** — replay failed, diverged, skipped rows, or produced surprising
  output.
- **Comparison** — they already have original/replay IDs and want a diff or
  compare URL.

Completion criterion: the next replay command has a stated purpose and a known
source execution or explicit execution list.

### 2. Inspect before replaying

Use the interface the user is already working in:

- SDK/client: `KitaruClient().executions.get(...)`, `.list(...)`, `.latest(...)`
- CLI: `kitaru executions get`, `list`, `latest`, `logs`
- MCP: `kitaru_executions_get`, `kitaru_executions_list`, `get_execution_logs`

Check:

- source execution ID and status;
- flow name, checkpoint names, and repeated checkpoint calls;
- failure metadata and logs if this is recovery;
- whether a replay source module is likely importable from the current project;
- whether the replay may read mutable external data such as “latest customer
  record” or “current policy.”

Do not replay a running source execution. Wait for it to finish, cancel it, or
choose a terminal execution.

Completion criterion: you can name the source execution(s), the candidate `at`
selector, and any risk that could make the replay unfaithful.

### 3. Choose `at` deliberately

`at` is where Kitaru stops only reusing recorded outputs and starts doing live
work again.

Prefer selectors in this order:

1. an unambiguous checkpoint name;
2. a checkpoint invocation ID;
3. a checkpoint call ID;
4. a recorded model/tool call ID when that interface shows one.

If a checkpoint name appears several times, do not guess. Inspect the execution
and use an invocation or call ID.

Wait names are not replay anchors. If a replay reaches `wait()`, resolve it
with normal input tooling after the replay is running.

Completion criterion: `at` points to one recorded checkpoint invocation, tool
call, model call, or unambiguous checkpoint name.

### 4. Reproduce with no overrides

Run a no-change replay before changing behavior.

SDK:

```python
import kitaru

client = kitaru.KitaruClient()
baseline = client.executions.replay("kr-source", at="write_draft")
row = baseline.results[0]
print(row.original_exec_id, row.replay_exec_id, row.status, row.compare_url)
```

Flow object:

```python
baseline = content_pipeline.replay("kr-source", at="write_draft")
```

CLI:

```bash
kitaru executions replay kr-source --at write_draft --output json
```

MCP (`kitaru_executions_replay` arguments):

```json
{
  "exec_ids": ["kr-source"],
  "at": "write_draft",
  "wait": true,
  "on_error": "fail"
}
```

Completion criterion: the baseline replay produced a `ReplaySubmission` row with
a replay execution ID, or you can explain exactly why reproduction failed before
trying a fork.

### 5. Fork with one change

Change one thing at a time.

Use `flow_overrides` for top-level flow parameters:

```python
variant = client.executions.replay(
    "kr-source",
    at="write_draft",
    flow_overrides={"model": "openai:gpt-5-nano"},
)
```

Use `checkpoint_overrides` when every call with that checkpoint name should
change:

```python
variant = client.executions.replay(
    "kr-source",
    at="write_draft",
    checkpoint_overrides={"research": {"output": "edited notes"}},
)
```

Use `invocation_overrides` when only one recorded call should change:

```python
variant = client.executions.replay(
    "kr-source",
    at="lookup_policy_tool_2",
    invocation_overrides={
        "lookup_policy_tool_2": {"output": {"policy": "manual approval"}}
    },
)
```

Checkpoint and invocation overrides may use:

- `input` — replace target inputs, then rerun that target and downstream work;
- `output` — inject a target output; the target does not run;
- `code` — import a replacement callable when the target reruns;
- `model` — change a supported LLM checkpoint call only.

Use `skip` only when a later recorded call should reuse its saved output even
though `at` would normally rerun it. Do not skip and override the same target.

Completion criterion: the variant replay has one intentional change and its
`ReplaySubmission` has been inspected for results, failures, skipped rows, and
compare URLs.

### 6. Account for the whole `ReplaySubmission`

Do not report only the first replay ID when the submission contains failures or
skipped parents.

Read and summarize:

- `submission.summary`
- `submission.results[*].original_exec_id`
- `submission.results[*].replay_exec_id`
- `submission.results[*].status`
- `submission.results[*].compare_url` or `submission.compare_url`
- `submission.failures[*].reason`
- `submission.skipped[*].reason`

For multi-execution replay, prefer `wait=True` only when the user wants to block
for all children. Otherwise report submitted replay IDs and tell the user how to
inspect them.

Completion criterion: every source execution is accounted for as submitted,
completed, failed, or skipped.

### 7. Diff before concluding

Compare the observed source, reproduced baseline, and forked variant.

SDK:

```python
execution_diff = kitaru.diff("kr-source", "kr-baseline", "kr-variant")
```

CLI:

```bash
kitaru executions diff kr-source kr-baseline kr-variant --output json
```

For several originals, use `kitaru.diff_matrix(...)` or
`kitaru executions diff-matrix ...` after replay children exist.

Explain the result as a story:

1. what the original did;
2. whether the no-change replay reproduced it;
3. what single change the fork made;
4. what changed downstream;
5. whether cost, latency, output, or failure behavior improved.

Completion criterion: the user gets a concrete interpretation, not just a link
or raw JSON.

## Cohort replay

Cohort selection is separate from replay. First resolve the execution IDs, then
replay the explicit list.

CLI dry-run / selection flow:

```bash
kitaru executions cohort \
  --flow content_pipeline \
  --at write_draft \
  --order-by -display_cost_usd \
  --limit 10 \
  --output json
```

Then replay the chosen IDs:

```bash
kitaru executions replay kr-a kr-b kr-c \
  --at write_draft \
  --flow-overrides '{"model":"openai:gpt-5-nano"}' \
  --tag replay-lab-model-swap \
  --wait \
  --on-error collect \
  --output json
```

MCP does not expose a dedicated cohort resolver or diff tool in the current
public server. Use CLI or SDK to resolve cohorts and diff results. In MCP-only
flows, list and inspect candidate executions first, then call
`kitaru_executions_replay` with explicit `exec_ids`.

Completion criterion: the user approved or inspected the selected execution list
before replay submission.

## Failure and diagnosis rules

### Reproduction failed

Stop before running a variant. Inspect:

- wrong or ambiguous `at`;
- source module import failure;
- missing local dependencies;
- changed code shape;
- changed external mutable data;
- provider/API behavior that was not captured as a Kitaru checkpoint.

### Divergence

Divergence means the replayed call sequence no longer matches the source. For
example, the source recorded:

```text
research -> write_draft -> publish
```

but current code runs:

```text
research -> classify_customer -> write_draft -> publish
```

Kitaru stops because it cannot safely line old recorded values up with new code.
Do not treat a divergent replay as a trustworthy experiment.

### Waits during replay

Replay cannot pre-fill waits. Do not use `wait.*` override keys. If the replayed
execution reaches a wait, resolve it with:

- SDK/client: `client.executions.input(exec_id, wait="name", value=...)`
- CLI: `kitaru executions input <exec_id> --value ...`
- MCP: `kitaru_executions_input`

### Runtime-only overrides

`code` overrides and targeted `model` overrides may require the Kitaru flow
wrapper to be importable from the current project. If Kitaru falls back to a
lower-level replay path, it may reject those overrides. Run replay from the
project directory or remove the runtime-only override.

## Adapter honesty

Kitaru replays what it recorded as Kitaru checkpoints. Do not promise hidden
provider or framework internals are replayable.

- PydanticAI and OpenAI Agents can have finer model/tool call checkpoints when
  configured for supported granular modes.
- LangGraph graph state remains LangGraph-owned unless Kitaru middleware
  actually records supported sync model/tool calls.
- Claude Agent SDK replay is one invocation checkpoint; Kitaru does not replay
  Claude-internal Bash, MCP, hooks, permissions, custom tools, or workspace file
  effects granularly.
- Gemini Interactions replay is one stable interaction response; Kitaru does not
  replay Google-hosted tools, managed-agent steps, MCP, web/code execution, or
  Antigravity sandbox internals granularly.

If a side effect must be safe under replay, put it in a Kitaru checkpoint that
Kitaru can see, make it idempotent, or record an explicit artifact/reference for
inspection.

## Do not regress to old replay APIs

Do not invent or recommend:

- `from_=` or `--from` replay selectors;
- flat `overrides=...` replay arguments;
- `--override checkpoint.*` examples;
- `checkpoint.<selector>` override namespaces;
- `wait.*` replay overrides;
- replaying a running source execution;
- trusting a fork when the no-change replay did not reproduce.
