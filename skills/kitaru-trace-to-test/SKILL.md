---
name: kitaru-trace-to-test
description: Turn one Langfuse incident trace into a safe Kitaru replay experiment and bounded CI regression gate.
disable-model-invocation: true
---

# Kitaru Trace to Test

Turn one production trace into a case file whose evidence can become a
regression test. Advance through the evidence ladder one checked rung at a time:

```text
trace → verified import → validated boundary → reproduced control
      → protected candidate → bounded rerun → CI gate
```

A run ends either **CI READY** or **STOPPED SAFELY**. A HOLD or FAIL is useful
evidence, not an invitation to spend until the result changes.

## Load the contracts progressively

Read only the material needed for the current rung:

1. Before the first update, read the evidence ladder and pause-card sections of
   [references/visual-evidence.md](references/visual-evidence.md).
2. In Phase 0, read the shipped/unsupported sections of
   [references/capabilities.md](references/capabilities.md) and the inspection
   section of
   [references/project-adaptation.md](references/project-adaptation.md).
3. In Phases 1 and 2, read trace selection and import commands.
4. In Phase 3, read boundary validation plus the DAG and boundary visual rules.
5. Before paid replay, read the verdict and cost visual rules.
6. Read [references/ci-gate.md](references/ci-gate.md) only after a qualifying
   candidate experiment.

## Interaction mode

Read `KITARU_TRACE_TO_TEST_MODE`.

| Value | Behavior |
|---|---|
| unset, empty, or `guided` | Pause after trace selection, preview, boundary selection, candidate evidence, and proposed file changes. |
| `demo` | Propose combining read-only findings and keeping narration tight. Confirm this mode in the first response before suppressing guided pauses. |
| anything else | Explain the accepted values and use `guided`. |

Demo mode reduces interruptions. It preserves these authorization gates:

1. registering or reusing an AgentVersion;
2. storing imported trace data;
3. making each exact paid replay request;
4. editing agent, scorer, protection, test, or CI files;
5. proceeding when attribution, tool effects, or evidence validity is ambiguous.

Use the user's structured question tool when available. Ask one decision per
pause unless a paid-execution card fully identifies the trace, candidate,
models, limits, and estimated spend.

## Case file

Keep resumable state in memory. If the run may cross sessions, offer a redacted
temporary state file under
`$TMPDIR/kitaru-trace-to-test/<case-slug>/state.json`. Write inside the
project only with approval.

Record:

```text
phase
source kind and non-secret locator
trace ID and selection reason
agent and source version
imported execution ID
validated boundary identifiers
candidate entrypoint and version
objective and expected protection IDs
approved trial, cost, token, and duration limits
control, candidate, and rerun experiment IDs
verdict and actual spend
CI test path and readiness
```

Permit approved project-relative source entrypoints and test paths because they
identify the code under review. Keep absolute user paths, trace-derived paths,
prompts, observation payloads, customer data, tool arguments, tool results,
credentials, and secrets out of the case file and visual report.

## Phase 0: Establish the agent under test

Inspect repository instructions and the installed Kitaru version. Verify
relevant CLI commands with local `--help` before executing them.

Use the project-adaptation contract to locate the source agent, candidate,
registration entrypoints, objective, protections, and tools. Classify every
relevant tool as read, write, or unknown.

Render:

- the evidence ladder with only this rung active;
- the adaptation table;
- a tool-safety table;
- a short explanation of what Kitaru will rerun in this agent.

If a stable PydanticAI agent entrypoint, meaningful objective, or domain
protection is missing, propose the smallest project change. Show the files and
behavior before editing.

Before calling `.register(...)`, show a registration pause card with the Kitaru
project, agent name, immutable label, entrypoint, and whether registration will
create or reuse an AgentVersion. Obtain approval for that persistent mutation.

**Completion criterion:** every required item is READY, every relevant tool has
a justified classification, and the user can see which agent behavior the
future experiment will test. Otherwise end or continue diagnostic-only as HOLD.

## Phase 1: Select one trace

Resolve the source as one of:

- exact Langfuse trace ID or URL;
- Langfuse observations JSONL;
- read-only discovery through a host-provided Langfuse or browser integration.

For JSONL, enumerate trace identities without writing. Preserve the selected
trace with `--trace-id <selected-trace-id>` in preview and write commands. For
remote Langfuse, verify the supported `kitaru[langfuse]` dependency before
requesting credentials. Without an exact ID, explain that Kitaru cannot discover
traces, show the
candidate criteria from the adaptation contract, and help the user select in
Langfuse.

Render a candidate table. Recommend one trace and explain:

- what failed or warrants investigation;
- what recorded tool evidence exists;
- what remains for the candidate to decide;
- why this trace is representative or incident-relevant;
- whether it appears capable of comparable replay.

Pause with a trace-selection evidence card in guided mode.

**Completion criterion:** exactly one trace ID is selected for a concrete reason.
Never guess or infer a remote trace ID.

## Phase 2: Preview and import

Run Kitaru's dry-run preview first. Validate:

- exactly one trace is selected and its ID equals the chosen trace;
- source attribution is verified or explicitly caller-attributed;
- no version conflict or rejected outcome exists;
- graph integrity and fragmentation are disclosed;
- importer root-input readiness is reported;
- message-history readiness remains unknown until Phase 3 validates a boundary;
- the exact destination stack name or ID is present in the preview command;
- the user understands that raw evidence can contain sensitive data.

Render an import evidence table and explain what will be stored, where it will
be stored, the stack's reported storage accessibility, and that importing calls
neither the model nor the agent's tools. Show message-history boundary status as
HOLD with `adapter validation pending`.

Pause for explicit storage consent only when the preview reports
`selected_trace_count == 1`. Then reuse the identical `--trace-id` and
`--stack` selectors, adding `--write` and `--confirm-data-storage`.

Accept a successful created, resumed, or unchanged outcome and capture the
exact imported execution ID. Inspect it with the normal execution surface.

**Completion criterion:** one immutable imported execution ID exists and the
case file records the attribution and readiness result. Any conflict stops
before storage.

## Phase 3: Map the evidence and choose a boundary

Load normalized imported replay evidence. Draw the sanitized imported DAG from
observation IDs, names, kinds, statuses, and parent relationships.

Enumerate and adapter-validate complete model-message and tool-result boundaries
using the project-adaptation contract. Render:

1. the imported DAG;
2. a boundary table with observation, kind, sequence, occurrence, call ID, and
   validation state;
3. a boundary diagram separating the immutable prefix from live candidate work;
4. a tool-safety diagram showing exact-match response service and blocked
   misses.

Recommend the boundary that preserves the strongest recorded world while
leaving the candidate a meaningful decision. Explain this in the user's agent:

- which earlier model and tool work becomes fixed evidence;
- which candidate model calls run again and incur cost;
- which recorded tool responses can be served;
- that none of the candidate's live tool callables run during imported replay;
- that an exact match returns stored evidence and every miss is blocked;
- what a blocked miss would mean for the verdict.

Pause for boundary selection in guided mode.

If no message-history boundary validates, offer one root-input diagnostic. Mark
the case HOLD and state that it cannot become a comparable CI gate.

**Completion criterion:** one adapter-validated boundary is selected, or the
case is explicitly limited to a root-input HOLD.

## Phase 4: Reproduce the recorded path

When the source-compatible implementation is executable, prepare one control
replay from the selected boundary. Require explicit trial, USD, token, and
duration limits. Show a paid-execution card naming the exact request and
idempotency key, then obtain approval before calling the model. If the installed
API cannot enforce `RegressionLimits`, stop rather than run unbounded.

Validate and display:

| Evidence | Required result |
|---|---|
| Comparability | `recorded_path_comparable` |
| Recorded responses | every eligible response served |
| Blocked calls | 0 |
| Path divergences | 0 |
| Objective | passed |
| Protections | every expected protection present and passed |

Explain which parts of the original execution were reused and which were
recomputed. Relate every miss or divergence to the agent's current tool schema
or behavior.

**Completion criterion:** the control reproduces comparable recorded-path
evidence. Otherwise HOLD and diagnose boundary or schema drift before testing a
candidate.

If the historical implementation cannot be executed, state that the missing
control weakens causal confidence. Ask whether to continue with the candidate as
a labeled diagnostic rather than silently treating it as equivalent evidence.

## Phase 5: Run the protected candidate

Freeze the selected trace and boundary. Construct an idempotency key from the
trace, boundary, candidate version, scorer set, protection set, repeats, and
limits.

Start with one repeat, `on_error="collect"`, and explicit
`RegressionLimits`. If the installed API cannot enforce the limits, stop rather
than run unbounded.

Before execution, render:

- the candidate and exact version;
- the question this comparison answers;
- objective and threshold;
- each protection and its forbidden behavior;
- provider/model calls expected to run;
- low, base, and high cost estimates, or `unknown`;
- trial, USD, token, and duration limits;
- the within-trial overshoot warning.

Pause for authorization of this one exact request and idempotency key.

After execution, render the verdict diagram, protection table, comparability,
recorded-response hits and misses, blocked calls, divergences, child execution
IDs, reason codes, and actual usage.

Interpret evidence in this order:

1. any failed protection produces FAIL;
2. otherwise incomplete comparability produces HOLD;
3. otherwise an unmet objective produces FAIL;
4. only comparable evidence with objective and protections passing produces
   PASS.

Explain what the result means for this agent. For example, distinguish "the
candidate achieved the requested outcome" from "the candidate attempted a
forbidden write while doing so."

**Completion criterion:** one persisted candidate experiment has every expected
objective and protection plus a fully explained PASS, HOLD, or FAIL verdict.
Stop this candidate path on HOLD or FAIL unless the user authorizes a concrete
code or evidence correction.

## Phase 6: Widen or rerun the evidence

If more representative traces exist, offer to widen the experiment. Show which
members have validated comparable boundaries before spending. Root-input-only
members cannot make the comparable subset pass.

For the gate candidate, prepare a rerun of the exact experiment ID with
explicit limits and a caller-chosen or deterministically derived idempotency
key. Show a new paid-execution card and obtain approval for the exact rerun plus
one identical idempotency check. Then run the request twice with the same key
and verify:

- the experiment ID is unchanged;
- no new trial or child execution was submitted;
- no additional replay spend was incurred.

Render forecast versus actual cost and the final evidence ladder.

**Completion criterion:** the exact bounded rerun is PASS and the idempotency
check returns the same stored attempt. Otherwise end STOPPED SAFELY.

## Phase 7: Prepare the regression gate

Read the CI reference. Propose deterministic scorer, protection, recorded-tool,
boundary, and idempotency tests before the paid live gate.

Before generating an enabled recurring gate, obtain standing CI authorization
with a visual card that shows:

- workflow triggers and expected run frequency;
- the AgentVersion registration performed for each commit;
- credential and provider scope;
- maximum spend per run and estimated monthly or scheduled spend;
- retry and idempotency behavior;
- who can disable or change the gate.

Without standing authorization, generate the live test disabled behind an
explicit environment opt-in and credential skip.

Generate the project-specific CI test only after showing:

- exact target path;
- exact frozen experiment ID;
- candidate registration and entrypoint;
- idempotency strategy;
- objective and protections;
- limits;
- live-provider markers, explicit opt-in, and credential skip behavior;
- expected pull-request and scheduled-suite cost;
- whether recurring CI execution has standing authorization.

Run the narrowest available non-live validation. Run the live gate only under a
separate paid authorization unless it was included in the exact Phase 6
authorization.

Explain that `assert_pass()` fails the test, while repository branch
protection must make the containing CI job required before it blocks a merge.

**Completion criterion:** the proposed or approved test targets the exact
experiment, uses a commit-derived candidate version, explicit limits, a stable
idempotency key, `assert_pass()`, repository live markers, credential skipping,
and an explicit opt-in unless recurring spend has standing authorization. Report
merge-gate wiring and recurring authorization separately.

## Finish

Render the final report defined by the visual-evidence contract.

Use **CI READY** only when import, boundary, control, protected candidate,
bounded rerun, idempotency, and test-artifact criteria all pass.

Otherwise use **STOPPED SAFELY** with the precise phase, HOLD or FAIL reason,
preserved evidence IDs, actual spend, and one corrective next action.

Do not automatically make another paid attempt with a fresh key, commit files,
push changes, or change branch-protection settings.
