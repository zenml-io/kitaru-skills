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

If the human declines to confirm a resource ceiling, stop successfully before selection and replay. Preserve the descriptive survey result, but do not silently substitute an agent-authored budget or claim that the four-evaluator population survey completed.

Show a compact table with one row per evaluator version and columns for expected, completed, failed, and missing. Selection begins only after the denominator is explicit for all four evaluators.

## Reduce the population deterministically

Build one cheap survey record per session from the pinned evaluator outputs, visible session-level inputs and outputs, terminal-action category, and resource metrics. Exclude full trace-node payloads at this stage, along with template tests, fixture-family labels, hidden expected outcomes, and ticket-to-answer mappings. The descriptive evaluators expose diagnostics, trajectory shape, tool health, and resource use; they do not establish a semantic policy violation.

Form stable strata from evaluation completeness, diagnostic and trajectory signals, terminal-action category, visible request and amount bands, tool-health result, and resource bands. Represent absent values with one explicit sentinel. Canonicalize each survey record as sorted-key JSON, sort set-like arrays, preserve sequence-valued evidence in its recorded order, and compute its SHA-256 digest. Canonicalize the stratum key the same way.

Build the shortlist with a fixed round-robin: sort non-empty strata by canonical stratum key, sort members within each stratum by evidence digest and then stable source-trace ID solely as a digest-collision fallback, and take one member from each stratum per round until six are selected or all strata are exhausted. If more than six strata exist, order strata first by evaluation completeness, then by the count of non-clean diagnostic, trajectory, tool-health, and resource results in descending order, then by canonical stratum key. This includes strong signals without allowing API order or a ticket identifier to become a quality signal.

Do not add randomness or use API order, session order, names, or ticket IDs as a quality signal. Keep unresolved records visible but never select one as an acceptable control merely because its evaluations are absent. Given the same visible survey records, a shuffled API listing must produce the same shortlist.

Shortlist no more than six sessions. Only then deep-read every node and full payload for that shortlist. Use that evidence to decide whether a relational policy/state-versus-action mismatch exists and assign three roles:

1. **Consequential problem:** a complete trace where an observable policy or state conflicts with a later action or outcome.
2. **Evidence-reading or boundary case:** a nearby trace whose node-level evidence changes or limits the apparent interpretation.
3. **Acceptable counterexample:** a nearby complete case that should remain outside the proposed problem.

For reproducible role assignment, canonicalize the visible deep-read evidence for each candidate and compute a second SHA-256 digest. Record whether each candidate satisfies each role's predicate above and one concise evidence reason. Process the roles in the listed order and choose the first unused eligible candidate by deep-read digest, using stable source-trace ID only as a digest-collision fallback. Before writing anything, rerun selection from the retained canonical records in reverse listing order and require the same shortlist and three role assignments.

If the evidence cannot support all three roles, stop with the ranked evidence and missing role instead of substituting a fixed answer-key selection.

## Write agent observations

For each selected session, write one or two concise ordinary annotations anchored to the smallest useful node, JSON field, or text span. Use the complete session only when no narrower selector carries the meaning.

Start every durable note with `Agent observation:`. State what the evidence shows and why it matters without asserting the human's judgment. Translate internal fields into ordinary language. Before creating a note, list existing manual annotations and reuse an exact selector-and-value match.

## Prepare the investigation

Keep one session-specific question per session. Ask a direct acceptability question grounded in the recorded values and behavior. Attach the most important observation selector as the primary highlight. Order the sessions consequential problem, nearby boundary case, acceptable counterexample.

For the consequential session, explicitly ask the reviewer to write one short evidence-grounded answer explaining what the highlighted evidence shows and whether the resulting action was acceptable. State this required answer in the investigation description and question. The answer belongs to that investigation session and question key. For all three sessions, ask for the whole-session verdict: Acceptable, Problematic, or Uncertain. Do not ask the coding agent to draft or submit any human field.

Give the investigation a valid machine name such as `expanded-returns-tour`, adding a short letter-or-digit suffix only when a distinct investigation is required. Put the readable title and the agent-versus-human division of labor in the description. Retain the exact investigation ID in the current task context.

## Preview and open the review

Before the combined write approval, show three compact rows:

| Session role | What the human will inspect | Why it matters |
|---|---|---|
| Consequential problem | The consequential action and governing evidence | Supplies the required written interpretation and verdict. |
| Nearby boundary | The nearby inconsistency or boundary | Tests whether the proposed relationship is too broad. |
| Acceptable counterexample | The acceptable behavior and evidence | Protects behavior that should not be swept into the problem. |

Adapt the descriptions to the selected traces. Do not show internal IDs, raw JSON, ranking machinery, or a research plan in the conversational lead.

## Read the human records

After the human selects Done, read answers and verdicts through their separate storage paths. Require:

- one human-authored answer for the consequential investigation-session ID and question key; and
- one whole-session verdict for each of the three investigation sessions.

An `Agent observation:` annotation cannot satisfy either requirement. Verdicts without the consequential answer remain incomplete. The answer without all three verdicts also remains incomplete. Report the exact missing field and return the same review link without creating a cohort or evaluator.

Lead with the human's choices and the evidence beside them. A verdict does not automatically endorse every agent observation.

If the records reject the proposed behavior, preserve that correction and create no cohort, evaluator, experiment, or replay for it. Offer one re-selection only after the human explicitly chooses to continue. That re-selection must use the already qualified candidates, reassign the same three roles from their read evidence, and repeat the human gate. Otherwise stop successfully. Do not run another population survey or steer the reviewer toward the original claim.

## Turn one confirmed relationship into a check

After the human confirms the relationship and every proposed cohort member has the required review record:

1. Freeze exactly the three reviewed source sessions in one immutable cohort version.
2. Define exactly one narrow deterministic behavior evaluator that compares observable policy or state evidence with a later action or outcome. A tool-presence check alone is insufficient.
3. Check the installed catalog first. If no configured evaluator expresses the relationship, scaffold local code without reading template tests or canonical labels.
4. Make the evaluator return an honest pass, fail, acceptable boundary, or unresolved outcome for missing or malformed evidence. Never map ticket or session IDs to answers.
5. Test pass, fail, and acceptable-boundary behavior against the three reviewed sessions. Test missing and malformed behavior with locally constructed degraded inputs, or an incomplete survey session when available. Preserve human/evaluator disagreement rather than changing the human records.
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

- the exact three-session cohort version;
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
