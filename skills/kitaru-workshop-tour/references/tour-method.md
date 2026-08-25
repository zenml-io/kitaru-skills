# Expanded tour method

Use this method to reduce the complete 30-session population to one small human review, then turn one confirmed relationship into a population check and bounded comparison. Keep selection deterministic and evidence-led. Do not use fixture labels or fixed answers.

## Survey the complete population

Resolve exactly 30 imported `returns-baseline` sessions through the exact import job and agent version. Page through every listing. Retain the session ID, source trace mapping, and stable session inputs in the current task context.

Run these exact installed evaluators together across all 30 sessions in one 90-pair evaluation job:

- `kitaru/session-diagnostics@1`
- `kitaru/trajectory-signals@1`
- `kitaru/tool-health@1`

Do not rely on automatic batching or split this descriptive survey. Read the terminal job and all paginated results. For each evaluator version, account for 30 expected pairs as completed, failed, or missing. A failed terminal task still belongs in accounting. Do not treat a missing or failed result as a clean score.

Configure `kitaru/resource-budget@1` separately because adding it to the descriptive survey would exceed the 100-pair request cap. From the historical evidence, propose at least one meaningful ceiling for the resource condition being measured and ask the human to confirm it. Use only supported fields:

- `max_duration_seconds`
- `max_cost`
- `max_total_tokens`
- `max_nodes`
- `max_llm_calls`
- `max_tool_calls`

At least one field is required. Include `max_cost` when cost is part of the condition. After confirmation, freeze the exact parameter object in the current task context and run one separate 30-pair resource-budget job. Account for its completed, failed, and missing results independently. Reuse the identical evaluator version and parameter object in replay.

Show the proposed parameter object and explain each ceiling in one compact
table. Do not call it confirmed or start the resource-budget job until the human
explicitly accepts that exact object. An approval for registration, import, or
other setup does not confirm the budget.

If the human declines to confirm a resource ceiling, stop successfully before selection and replay. Preserve the descriptive survey result, but do not silently substitute an agent-authored budget or claim that the four-evaluator population survey completed.

Show a compact table with one row per evaluator version and columns for
expected, completed, failed, and missing. Then show the audience-facing
findings summary and small session matrix defined in
`functional-explanations.md`. Selection begins only after both the denominator
and the useful findings are visible.

## Find five useful review cases

Build one compact survey record per session from the pinned evaluator outputs,
visible session-level inputs and outputs, terminal-action category, and resource
metrics. Exclude template tests, fixture-family labels, hidden expected
outcomes, and ticket-to-answer mappings. The descriptive evaluators expose
diagnostics, trajectory shape, tool health, and resource use; they do not
establish a semantic policy violation.

Use the compact records to identify promising cases across different final
actions, policy conditions, operational signals, and resource results. Begin
with cases whose visible evidence suggests a possible mismatch between policy
or state and a later action or outcome. Also retain nearby cases that may show
where the apparent problem stops.

Use a stable reading order: sort first by the number of named descriptive
signals, then place resource-budget failures before passes and unresolved
results, and use the Kitaru session ID only as a final tie-breaker. This order
only decides which complete trace to read next; it does not assign a review
role or establish that a behavior is problematic.

Read complete node payloads for promising cases in small batches. Continue
until the evidence supports a five-case selection or all 30 sessions have been
read. Do not stop at an arbitrary candidate count, and do not use ticket IDs,
API order, or fixture knowledge as quality signals.

The five cases must include:

1. at least one **suspected problem**, a complete trace where observable policy
   or state appears to conflict with a later action or outcome;
2. at least one **boundary case**, whose node-level evidence limits the
   apparent interpretation; and
3. at least one **nearby comparison**, a complete case that appears to follow
   the relevant policy or state relationship.

Fill the remaining cases with distinct evidence. Prefer additional suspected
problems when the complete traces support them, otherwise use a second boundary
or comparison. A tool failure, escalation, high cost, or unusual trajectory is
not automatically a behavior problem.

For every proposed case, record one concise reason and the exact node or field
that supports it. Before writing review objects, challenge each role against the
complete evidence. A tool failure, escalation, high cost, or unusual trajectory
is not automatically a behavior problem. The suggested relationship must
explain why the suspected case may be problematic and why the nearby comparison
may be acceptable.

If the full population cannot support a five-case selection containing a
suspected problem, boundary, and comparison, stop with the evidence read and
the missing kind of evidence instead of substituting a fixed answer-key
selection.

## Write agent observations

For each selected session, write one or two concise ordinary annotations anchored to the smallest useful node, JSON field, or text span. Use the complete session only when no narrower selector carries the meaning.

Start every durable note with `Agent observation:`. State what the evidence shows and why it matters without asserting the human's judgment. Translate internal fields into ordinary language. Before creating a note, list existing manual annotations and reuse an exact selector-and-value match.

## Prepare the investigation

Keep one session-specific question per session. Ask a direct acceptability
question grounded in the recorded values and behavior. Attach the most
important observation selector as the primary highlight. Order the sessions as
suspected problems first, then boundaries, then comparisons.

Ask for the whole-session verdict on all five sessions: Acceptable,
Problematic, or Uncertain. The frontend may also expose a written-answer field,
but it is optional. Do not ask the reviewer to repeat the verdict in prose. If
the question invites a note, ask for complementary reasoning such as which
evidence mattered or what action should have happened instead. Do not ask the
coding agent to draft or submit any human field.

Give the investigation a valid machine name such as `expanded-returns-tour`, adding a short letter-or-digit suffix only when a distinct investigation is required. Put the readable title and the agent-versus-human division of labor in the description. Retain the exact investigation ID in the current task context.

## Preview and open the review

Before the combined write approval, show five compact rows:

| Selected case | What the human will inspect | Why it matters |
|---|---|---|
| Suspected problem | The action and governing evidence that may conflict | Tests whether the apparent problem is real. |
| Boundary case | The evidence that limits the apparent claim | Tests whether the relationship is too broad. |
| Distinct evidence | A second policy condition or action outcome | Shows whether the relationship repeats. |
| Nearby comparison | Similar behavior and its governing evidence | Protects behavior that should not be swept into the problem. |
| Distinct evidence | A final acceptable or limiting case | Shows that the comparison is not a one-off. |

Adapt the descriptions to the selected traces. Do not show internal IDs, raw JSON, ranking machinery, or a research plan in the conversational lead.

## Read the human records

After the human selects Done, read the five whole-session verdicts. Read any
written answers as optional context, but do not require them and do not treat
their mere presence as evidence that the reviewer understood or endorsed the
agent-prepared observation. An `Agent observation:` annotation cannot satisfy a
missing verdict. Report an exact missing verdict and return the same review link
without creating a cohort or evaluator.

Lead with the human's choices and the evidence beside them. A verdict does not automatically endorse every agent observation.

If the verdicts reject the proposed behavior, preserve that correction and
create no cohort, evaluator, experiment, or replay for it. Offer one re-selection
only after the human explicitly chooses to continue. Continue inspecting the
remaining population rather than rerunning the deterministic survey or steering
the reviewer toward the original claim.

## Turn one confirmed relationship into a check

After all five verdicts are present, at least one target is Problematic, the selected boundary and comparison support a human-confirmed relationship, and every proposed cohort member has the required review record:

1. Freeze exactly the five reviewed source sessions in one immutable cohort version.
2. Define exactly one narrow deterministic behavior evaluator that compares observable policy or state evidence with a later action or outcome. A tool-presence check alone is insufficient.
3. Check the installed catalog first. If no configured evaluator expresses the relationship, scaffold local code without reading template tests or canonical labels.
4. Make the evaluator return an honest pass, fail, acceptable boundary, or unresolved outcome for missing or malformed evidence. Never map ticket or session IDs to answers.
5. Test pass, fail, and acceptable-boundary behavior against the five reviewed sessions. Test missing and malformed behavior with locally constructed degraded inputs, or an incomplete survey session when available. Preserve human/evaluator disagreement rather than changing the human records.
6. Register one immutable evaluator version through the supported parent-then-version operation.
7. Run that exact version across all 30 baseline sessions and account for expected, completed, failed, and missing results. Keep failed and missing results in the population denominator and outside any pass-rate denominator.

Before interpreting the population, inspect at most six evaluator outputs: up to two predicted passes, two predicted failures, and two unresolved results, chosen by the same canonical evidence digest. If a category has fewer than two results, inspect what exists and report the gap. If the spot-check exposes a rule mismatch, revise and register a new evaluator version, rerun that version across all 30 sessions, replace the reported accounting, and repeat the bounded spot check; otherwise narrow the conclusion without changing versions. The evaluator version handed to replay must be the version that produced the reported population accounting. Do not call the table human-validated.

## Explain the evaluator result

Use this order:

1. State the human-confirmed relationship.
2. State what Kitaru preserved that made it inspectable.
3. State the complete 30-session accounting and bounded spot-check result.
4. Name one limitation, such as the synthetic population, unresolved evidence, or missing external outcome evidence.
5. Explain the cohort and evaluator version only after the result is clear.

Lead with the frontend links resolved through `kitaru-operations.md`. Ask the user to inspect the frozen examples and exact evaluator, then pause until they return.

## Hand off one bounded replay

After the user returns, hand execution to the unchanged `kitaru-replay-experiment` skill. Do not copy its orchestration. Supply a fixed run specification:

- the exact five-session cohort version;
- the exact source-matched `returns-resolver` agent-version ID;
- the exact behavior evaluator version and parameters;
- `kitaru/tool-health@1`;
- `kitaru/resource-budget@1` with the frozen human-confirmed parameter object;
- one system-prompt clarification that directly addresses the confirmed relationship without embedding expected answers;
- the fixed `openai:gpt-5-nano` returns-agent model;
- `evaluate_baselines=true`; and
- an explicit tool policy whose default is history from `baseline` with `on_miss=fail`, plus exact passthrough overrides for `lookup_order`, `get_return_policy`, `check_shipping`, `issue_refund`, `create_replacement`, and `escalate_to_human`.

The restrictive default prevents an unexpected seventh tool from executing. The six named passthrough tools call deterministic local functions against a fresh in-memory store for each task. Keep cohort, model, candidate condition, evaluator versions, evaluator parameters, tool policy, and baseline comparison fixed unless the human explicitly changes the question and re-approves the run.

Let the replay skill verify adapter support, provider and worker readiness, configuration drift, approval, execution, cancellation, and exact result accounting. Resume through exact experiment and run IDs. Interpret the behavior evaluator, tool health, resource budget, completeness, and uncertainty together. Report `improved`, `regressed`, `trade-off`, or `inconclusive` for these reviewed cases only. Do not make a production, deployment, prevalence, or winner claim.
