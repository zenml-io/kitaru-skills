---
name: kitaru-workshop-tour
description: Guide the expanded 30-trace Kitaru returns-agent tour from deterministic population survey through evidence-selected human review, one relational evaluator, and one bounded replay comparison. Use only with a checkout that satisfies the expanded companion-template content contract. Route the smaller public example to kitaru-guided-tour, and route real agents, open-ended discovery, and production evidence to kitaru-investigation.
---

# Kitaru expanded tour

Use the expanded Kitaru returns-agent template to move from a deterministic
survey of 30 recorded traces, through a five-session human review and one
reusable evaluator, to one bounded experiment result.

## Experience contract

- Treat every visible progress update as part of the product explanation. Write
  for someone watching the screen who has not used Codex or Kitaru. Explain the
  returns-agent story, the Kitaru concept currently becoming visible, or the
  decision the human will make next.
- Never narrate file searches, reference loading, schema discovery, cache
  configuration, temporary files, parsing, shell quoting, retries, or other
  coding-agent mechanics. Resolve routine operational work quietly. If it
  blocks the tour, state the intended Kitaru action, the concrete blocker, and
  the smallest recovery in one concise update.
- At each meaningful transition, say what the tour is about to learn, why that
  matters, and what the user will be able to inspect or decide next. After the
  action, lead with the useful result rather than the command that produced it.
- Assume the user has not read the template agent. Explain each example from
  visible trace evidence, translate internal names into plain language, and
  never require missing code or product context to understand a question.
- Use names that already exist in Kitaru when naming product objects. Do not
  invent labels for steps, summaries, or collections, and do not present an
  internal implementation detail as a Kitaru concept. Prefer a plain sentence
  such as “Here is what the experiment will do” over “replay run card.”
- Lead with what the user is about to discover, not installation or evaluation
  terminology.
- Introduce only the Kitaru concept needed for the current action.
- When the coding-agent harness provides a native task, todo, or plan view,
  create a short visible outline before any readiness checks. Use four to six
  audience-meaningful tasks such as understanding the recorded runs, surveying
  the population, reviewing five cases, making a reusable check, and comparing
  one change. Mark tasks complete as their durable result becomes visible,
  including the final experiment task when its result has been explained, and
  revise the outline when the evidence changes the route. Do not put file
  reads, command discovery, cache work, or other agent mechanics in that view.
  If the harness has no task view, give the same compact outline once in the
  opening explanation rather than creating a separate artifact.
- Keep the conversation alive during long work, but send visible updates only
  when they give the audience a useful Kitaru fact, result, or next decision.
  Do not send standalone messages about loading references, looking up command
  forms, parsing results, or deciding what to inspect. Continue directly from
  the opening into read-only readiness checks. Wait only before the combined
  review write, after a frontend handoff, and before paid or live execution.
  Do not label these as pauses or turn them into timing instructions for a
  presenter.
- Prepare concise observations and exact evidence anchors for the reviewer.
  Tell them once that these are agent-prepared reading aids. Do not emphasize
  their annotations or treat an optional written note as proof of a behavior;
  the five verdicts carry the required human judgments.
- Use the Kitaru frontend four times: after import to view the sessions, then
  for the investigation review, the cohort and evaluator results, and the
  completed experiment run.
  Give direct links, explain what the user is looking at, then pause until they
  return. Do not interrupt the tour with frontend visits for routine objects.
- Survey all 30 sessions before selection, then keep the human review to five.
  Include at least one suspected problem, one boundary case,
  and one nearby comparison. Use the remaining cases to show distinct evidence,
  preferring additional suspected problems when complete traces support them.
  Inspect as many complete traces as needed, up to the full 30-session
  population.
- Ask the human to confirm an operating-guardrail parameter object, then offer
  a separate fast-path triage target for the recorded population. Only the
  operating guardrail is required for the main route and reused in replay.
  Require one human verdict for each of the five sessions; written answers and
  notes are optional.
- Reach a useful evaluator result without regenerating traces or making a paid
  model call. Continue into one bounded replay, but briefly explain the proposed
  run and ask before creating the experiment or starting paid or live execution.
- Before a model-backed replay, verify without exposing secrets that the worker
  runtime has the required provider credential. If availability cannot be
  verified, ask the user to configure it and restart the worker, then stop
  before creating the experiment or starting its run.
- Start or restart a user-controlled worker with `--concurrency 10`. Use
  `KITARU_WORKER_CONCURRENCY=10` only when the launch surface exposes worker
  settings through environment variables instead of CLI options.
- Run this expanded route against a Kitaru Cloud server. Preserve a healthy
  selected cloud server. If none is selected, ask for its URL and authenticate
  through an inherited `KITARU_API_KEY` or the normal interactive login flow.
  Never print credential values or switch to a local server.
- Resume durable agents, imports, sessions, exact-match annotations, cohorts,
  evaluator versions, experiments, and runs before creating replacements.
  Resume an investigation and its verdicts only when this conversation holds
  its exact ID or the user explicitly identifies it as their review.
- After every durable transition, retain the exact Kitaru ID and stable source
  mapping in the current task context. Re-read by those values after an
  uncertain write. Do not create an external checkpoint artifact.
- Prefer one combined approval for the clearly previewed review writes. Do
  not turn the tour into a sequence of permission prompts.

## Load the tour references

- Read [references/functional-explanations.md](references/functional-explanations.md)
  before the first user-facing explanation and apply its functional explanation
  rules throughout setup, review, evaluation, and replay.
- Read [references/starter-template.md](references/starter-template.md) before
  setup or when deciding whether the checkout satisfies the companion contract.
- Read [references/tour-method.md](references/tour-method.md) before selecting
  sessions, writing observations, creating the review, or interpreting results.
- Read [references/kitaru-operations.md](references/kitaru-operations.md) before
  any Kitaru CLI or MCP operation. Treat installed schemas as authoritative.

## Orient the audience

Before any readiness inspection or Kitaru operation, give a concise opening:

1. Explain that a coding agent is an assistant that can read the template,
   operate Kitaru through the available tools, and ask before consequential
   changes. It is not the returns agent being evaluated.
2. Explain that the tour will use the template's synthetic returns and delivery
   agent and its recorded runs to show the full Kitaru method: inspect evidence,
   make human judgments, turn one confirmed relationship into a repeatable
   check, and compare one bounded change.
3. State that the agent will first verify the prepared environment, then use the
   visible task outline to show where the tour is going. Do not imply that a
   server, imported population, or worker is already available before checking.

Create the harness-native task outline described above, then continue directly
into the readiness checks. End the opening with the first useful thing the tour
will establish, not with an internal setup description or a request to proceed.

## Establish the template route

Begin read-only.

1. Look for a candidate expanded-template checkout and verify its compact
   readiness contract through `starter-template.md` before trusting its README.
   Do not infer compatibility from its directory, remote, or branch. If none
   exists, report the missing companion checkout; do not substitute another
   template or fabricated outputs. If that checkout cannot be obtained, offer
   `kitaru-guided-tour` with the public template as the supported smaller route.
2. Establish the template environment, CLI, worker, and MCP package readiness
   through `starter-template.md` and `kitaru-operations.md`. Install the whole
   frozen template environment instead of adding packages piecemeal. Explain
   and ask before changing the environment or host MCP configuration. Treat MCP
   as preferred but optional when the CLI can complete the tour. If host MCP
   configuration is added or changed, tell the user to restart or reload the
   coding-agent host process or IDE, retain the exact resume state in the
   current task context, and do not claim that the current task can discover the
   new tools. Before the restart, give the user a compact copy-back resume block
   containing the template path, selected server, exact agent-version and import
   job IDs, any investigation ID, the frozen operating-guardrail parameters,
   and any confirmed fast-path target.
   This in-chat handoff is not an external checkpoint artifact.
3. Inspect Kitaru Cloud connectivity through the known-good environment and
   command forms in `kitaru-operations.md`. Then inspect the exact registered
   `returns-resolver` agent version, relevant import jobs, and the complete
   30-session imported population carrying the `returns-baseline` tag.
4. Resume matching durable state. Perform only missing setup steps from the
   verified template README, with one clear explanation and approval before
   environment changes, service starts, registration, or import.
5. Stop and route to `kitaru-investigation` when the template was materially
   customized, the user supplies their own agent or evidence, or the requested
   conclusion needs a defensible open-ended investigation.

Do not ask a first-time user to choose a framework, trace provider, review
method, or sampling strategy on the compatible route.

After a successful import and provenance check, resolve the agent sessions URL
through `kitaru-operations.md`, explain that it is the population before any
judgment has been made, and wait for the user to return. Do not begin the
deterministic survey until they do.

## Prepare one expanded review

Follow `tour-method.md` to run the 90-pair descriptive survey, obtain human
confirmation for the separately configured operating-budget survey and, when
accepted, the fast-path resource survey. Account for all results, explain what
the evaluators measure and found, and inspect complete traces until a meaningful
five-case selection is supported.
Before writing, show a compact preview of what happened in each selected session, why
it matters, and the evidence that will be highlighted. Treat the first role as
a suspected problem until the human judges it. Avoid an exhaustive
investigation plan or internal selection machinery.

Ask once to:

- add the five sessions' agent observations as ordinary Kitaru annotations;
- create one fixed investigation with the evidence-grounded questions and
  highlights;
- open the resulting frontend review.

After approval, create or resume the annotations and investigation through the
verified operations. Keep agent observations short and start each durable note
with `Agent observation:` so it remains understandable outside this chat.
Never write the user's answer or verdict for them.

## Hand off to the frontend

Lead with the direct review action. Provide the resolved review link, distinguish
the agent-prepared observations from the human records, and ask the user to
record one verdict for each session. Explain that written notes are optional
and useful only when the reviewer wants to record reasoning that the verdict
does not capture. Tell them how to complete the frontend review and return to
the task.

Pause. Do not duplicate the review in chat while the frontend route works.

## Create and run the evaluator

When the user returns:

1. Re-read the investigation, its ordered sessions, manual annotations,
   optional written answers, and verdict coverage.
2. Lead with what the user decided. Explain how each verdict now sits beside
   the exact recorded evidence that motivated the review.
3. If all five verdicts are present, including at least one problematic target,
   and the selected boundary and comparison support a human-confirmed
   relationship, propose one observable relationship that best explains the
   difference. Ask one short confirmation before turning it
   into a reusable check. Treat optional notes as context, not as a required
   label or independent confirmation.
4. If the user accepts that relationship, create an exact cohort version from
   all five reviewed sessions. Check the installed evaluator catalog before
   authoring code.
5. Select or create exactly one relational deterministic evaluator. Test pass,
   fail, and acceptable-boundary behavior against the reviewed sessions. Test
   missing and malformed evidence with locally constructed degraded inputs, or
   with an incomplete survey session when one exists. Register an immutable
   version only after these cases behave honestly, then run it across all 30
   baseline sessions.
6. Account for expected, completed, failed, and missing results, then inspect
   the bounded pass/fail/unresolved sample from `tour-method.md` before making a
   population interpretation.
7. Report the useful result first: what matched, which reviewed examples
   explain the result, and one important limitation. Resolve the cohort and
   evaluator links through `kitaru-operations.md`.

Then show the cohort and evaluator pages defined in `kitaru-operations.md`.
Explain that the cohort freezes the examples the user
judged and the evaluator page records the exact reusable rule. Pause and wait
for the user to return before preparing the experiment.

If the verdicts do not support the proposed behavior, preserve that correction
and create no cohort, evaluator, experiment, or replay for it. Offer one
re-selection from the remaining population only after the user explicitly
chooses to continue; otherwise stop successfully.

If any verdict is missing, stop before behavior confirmation, cohort creation,
or evaluator work. Report the exact missing verdict and keep the same review
link available for completion. Never block on an empty written-answer field.

Use ordinary language before object names. Report the relationship the human
actually confirmed, the reviewed sessions and evidence that support it, and the
exact match, non-match, failed, and missing counts from the current run. Only
then explain that the frozen examples are a cohort and the reusable check is an
evaluator version.

## Finish with one experiment

After the user returns from the cohort and evaluator pages:

1. Explain that the recorded sessions showed what happened before; an
   experiment starts fresh tasks from the same stored top-level inputs to test
   one changed condition.
2. Propose one system-prompt clarification grounded in the accepted behavior.
   Keep the returns-agent model fixed and do not
   start an automatic prompt search or introduce an unrelated model change.
3. Continue with the unchanged `kitaru-replay-experiment`, carrying the exact
   source-matched `returns-resolver` agent-version ID; five-session cohort;
   behavior evaluator; `kitaru/tool-health@1`;
   `kitaru/resource-budget@1` with its frozen operating-guardrail parameters;
   `openai:gpt-5-nano` as the fixed returns model;
   proposed system-prompt override; `evaluate_baselines=true`; and an explicit
   tool policy. Use default history from `baseline` with `on_miss=fail`, then
   exact passthrough overrides for the six verified in-memory tools. The
   restrictive default prevents any unexpected tool from running.
4. Let that skill verify adapter support and briefly explain the proposed run.
   Explain provider and worker readiness, model work, cost uncertainty, missing
   restored state, and possible tool effects. Obtain its required approval
   before experiment creation or run start.
5. After the run settles, lead with the experiment page from
   `kitaru-operations.md`. Explain which recorded cases were replayed, what
   changed, how the candidate compared, and what the result cannot establish.
   Pause until the user returns, then answer their questions and leave the exact
   investigation, cohort version, evaluator version, experiment, and run IDs
   and links in the final summary.

The normal successful tour ends after the user has inspected this experiment
result. If they decline the run or execution is blocked, preserve the proposed
conditions and cohort and evaluator links without claiming that the experiment
completed.

## Offer an optional resource optimization coda

After the completed experiment has been inspected, briefly offer a separate
cost or tool-efficiency improvement as an optional next step. Begin it only if
the user opts in. Do not automatically start a second loop or imply that the
behavior fix was insufficient.

1. Select five recorded sessions with the clearest fast-path triage evidence,
   preferring runs that missed the target while still having complete evidence.
   If no fast-path target was run or it found no candidates, use the clearest
   resource-heavy sessions instead.
   Preview the selection and obtain confirmation before freezing it in a
   separate cohort. This is an objective resource sample, not a substitute for
   human semantic review.
2. Read the traces to identify the likely resource driver. Do not assume that a
   shorter answer reduces tool calls, or that fewer tool calls preserve policy
   behavior.
3. Propose one narrow candidate change. Show the exact prompt or configuration
   difference and explain how Kitaru will apply it as an experiment override,
   rather than editing the checked-in agent or deploying a change.
   Wait for the user to inspect and discuss this proposal before creating the
   experiment configuration.
4. Carry the existing behavior evaluator, tool health, and operating guardrail
   into replay. Compare the candidate's recorded cost, duration, and tool calls
   directly with the same baseline cases; the fast-path target selected the
   cases but is not an experiment gate. Let `kitaru-replay-experiment` obtain
   explicit approval before the paid replay.
5. Report the resource change and every behavior or tool trade-off together.
   Do not claim an optimization succeeded when cost fell by breaking the
   behavior evaluator or increasing unresolved evidence.

Afterward, offer **Use my own agent** through `kitaru-investigation`, carrying
the tour's method explanation but none of its synthetic conclusions.

## Preserve a pleasant failure path

- If the template setup is incomplete, state the current checkpoint and the one
  missing action. Do not dump a generic setup checklist.
- If the imported sessions or full node payloads are unavailable, stop before
  inventing observations.
- If the exact import and agent version do not resolve exactly 30 distinct usable
  sessions, stop. Report the resolved count, every rejected member and reason,
  and the import job IDs inspected. Re-read the import job before proposing any
  retry, and never rerun it merely to top up the population.
- If an annotation or investigation write may have succeeded despite a dropped
  response, re-read state before retrying.
- If the review URL cannot be resolved, preserve the created investigation and
  report the broken handoff with its exact ID and one retry action.
- If the complete population cannot support a five-case selection containing a
  suspected problem, boundary, and comparison, stop and say which evidence is
  missing. Do not substitute a fixed answer-key selection.
- If the user stops after only part of the review, summarize the persisted
  verdicts and what they already show. Offer the same link for missing verdicts,
  but do not treat agent observations or optional notes as human judgments.
- In a fresh task, require an exact investigation, cohort version, evaluator
  version, experiment, or run ID or link before resuming human-derived state.
  Read the identified object and its relationships to recover the remaining
  IDs. Do not guess from names or create replacements merely because the prior
  task context is unavailable.
- If the user disagrees with an agent observation, treat that correction as part
  of the evidence. Do not defend the agent observation or silently convert it
  into a human conclusion.
- If adapter support, model credentials, a worker, or a safe tool policy blocks
  the experiment, preserve the proposed conditions and explain the missing
  condition. Do not fall back to live passthrough or call the tour complete.
