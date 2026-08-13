---
name: kitaru-investigation
description: Guide users from agent code or recorded Kitaru sessions through an evidence-grounded investigation and into a versioned cohort and optional evaluator. Use when a user wants to get started with Kitaru, connect or inspect an existing agent, investigate a known bad or surprising session, discover failure modes across sessions, review or annotate traces, resume an investigation, define an observable behavior, create a cohort from reviewed evidence, or author an evaluator for an accepted behavior.
---

# Kitaru investigation

Conduct one continuous journey from imported sessions to accepted evidence. Keep the internal stages invisible unless a missing capability makes the boundary useful to the user.

Treat this skill as the front door to Kitaru. Meet the user at their current level of product knowledge and current amount of evidence. Help them reach the next useful state without making them learn Kitaru's object model first.

## Core contract

- Treat the human as the judge. Select, summarize, organize, and compile evidence; never turn an agent suggestion into a human label.
- Preserve durable Kitaru state. Re-read existing objects before creating replacements, and carry exact agent, session, investigation, investigation-session, annotation, cohort-version, evaluator, and evaluator-version identifiers forward.
- Separate observed behavior from desired behavior. A trace records what happened, not what should have happened or whether the external outcome was correct.
- Distinguish agent behavior, external dependency behavior, product purpose, and independent outcome evidence.
- Use open observations before proposing a taxonomy. Do not prime the first review batch with agent-generated failure categories.
- Explain any operation that creates remote state or consumes worker or model compute before running it. Require explicit acceptance of an exact behavior and cohort membership. Treat an evaluator card as a checksum of that accepted meaning; ask again only when it changes a boundary, equivalence, or missing-evidence rule.
- Prefer native Kitaru MCP operations. Use the structured CLI when a local file upload or built-in wait behavior is required. Do not bypass missing contracts with direct REST calls or ad hoc local state.
- Stop at a useful durable checkpoint when a required source, payload, permission, worker, product contract, or UI capability is unavailable.

## Keep the experience clear and pleasant

- Lead each response with the current state and the next useful action.
- Use plain language for the user's decisions and exact technical terms for persisted Kitaru objects.
- Ask for one meaningful judgment at a time. Do not turn the investigation into a long setup questionnaire.
- Keep explanations short during active review. Offer more detail when evidence is ambiguous or a write has important consequences.
- Use compact tables for repeated fields, worklists, progress, evidence comparisons, and candidate behaviors. Use prose first when it better explains a mechanism or decision.
- Summarize structured Kitaru output instead of dumping raw JSON. Preserve exact IDs, versions, warnings, and missing evidence in the summary.
- Show what came from the repository, traces, user, or agent reasoning so the user never has to guess why a claim appears.
- End each stage with a small checkpoint that makes resumption obvious.

## Meet the user where they are

Infer the starting point before asking a question:

| What the user has | Start here |
|---|---|
| Agent code but no Kitaru sessions | Help the user record the agent or import existing traces through the smallest verified Kitaru path, then continue without restarting intake. |
| Kitaru sessions but no suspected problem | Use cold-start discovery. |
| One concerning or surprising session | Use trace-first investigation. |
| An existing investigation ID | Resume it without repeating intake. |
| A reviewed behavior or cohort | Continue at cohort confirmation or evaluator authoring. |

For someone new to Kitaru, give a one-sentence orientation before using product terms: Kitaru records agent runs as evidence-rich sessions so the user can inspect what happened, find recurring behavior, and turn accepted findings into repeatable evaluation.

For a developer or trace expert, show exact versions, nodes, selectors, and transport details when they help. For a domain expert, lead with the user outcome, visible evidence, and ordinary-language judgment; keep IDs in compact checkpoint tables.

Do not preview the entire workflow when only the next step matters. Explain the next decision, why it matters, and what the user will get from it.

## Load references only when needed

- Read [references/investigation-method.md](references/investigation-method.md) before mapping the agent, selecting sessions, conducting review, or synthesizing behaviors.
- Read [references/kitaru-operations.md](references/kitaru-operations.md) before calling Kitaru CLI or MCP operations. Verify the installed command and tool schemas when they differ from the reference.
- Read [references/deterministic-evaluators.md](references/deterministic-evaluators.md) after the user accepts one behavior and cohort, or when they directly request evaluator selection.
- Read [references/evaluator-authoring.md](references/evaluator-authoring.md) only when no installed evaluator expresses the accepted criterion, or when the user directly requests custom evaluator authoring with equivalent reviewed evidence.

## Resolve the durable starting state

Begin with read-only inspection.

1. Resolve the registered agent and its exact version when possible.
2. Confirm that relevant sessions exist and identify their agent versions.
3. Look for an investigation identifier in the request, recent structured output, or Kitaru state. Do not infer identity from a non-unique name when an exact ID is available.
4. Re-read any matching investigation, its ordered sessions, and its annotations before deciding what comes next.
5. If registration or import is incomplete, orient the user and help them complete the smallest verified setup step needed to produce relevant sessions. Ask whether they need to record the current agent or import existing traces only when the answer is not apparent. Then continue without restarting intake.

Route from state rather than asking the user to choose an internal stage:

```text
sessions ready, no investigation
  -> map context, choose the entry path, and create a bounded investigation

investigation pending or in progress
  -> resume the same worklist and report completed, skipped, and remaining sessions

reviewed evidence, no accepted behavior
  -> synthesize provisional behaviors or collect a bounded follow-up batch

accepted behavior, no cohort version
  -> confirm exact membership and create a cohort version

cohort version ready, no evaluator version
  -> select an installed evaluator or author one narrow custom evaluator

evaluator version ready
  -> stop successfully or hand exact evidence to kitaru-replay-experiment
```

### Continue from frontend onboarding

The light Kitaru frontend onboarding may direct the user to this skill. Treat it as the doorway, not as the owner of the investigation. Use any agent, repository, and session context it provides. Do not send the user back into a circular handoff.

When sessions are not ready, guide the smallest current registration, recording, or import path through supported Kitaru CLI, MCP, or frontend actions. Verify the installed Kitaru surface before giving exact commands. Re-read the registered agent and available sessions afterward, and do not ask the user to repeat information Kitaru now exposes.

Route a missing integration only when it blocks the sessions needed for this investigation:

- If the user has existing traces but no built-in importer supports their provider or export format, continue with `kitaru-importer-builder`. Carry forward the provider, export shape, target agent and version, current registration or import state, and investigation goal.
- If the user needs in-process recording but no supported adapter covers the installed framework and invocation mode, continue with `kitaru-adapter-builder`. Carry forward the repository, public agent entrypoint, language, installed framework and Kitaru versions, requested recording fidelity, target agent and version, and investigation goal.

Use one route based on the evidence. Do not bounce between builder skills merely because either mentions the other as an alternative. Resume this investigation only when relevant sessions are usable or the builder returns an exact blocker; preserve its checkpoint instead of repeating discovery.

## Map the agent before interviewing the user

Resolve the source repository and public agent entrypoint. Prefer the current coding-agent workspace when it contains the registered agent, but reconcile it with the registered version and the versions attached to reviewed sessions.

Stop and ask for the correct source when the workspace, registered revision, and session versions conflict enough that inspecting the current checkout could explain the wrong program.

Inspect only the public entrypoint and reachable code needed to understand prompts, model calls, control flow, routing, retries, stopping, repository-defined tools, memory, session behavior, permissions, and external dependencies. Do not install packages, start services, invoke credentials, or mutate external state during this mapping.

Show a concise context brief with four lenses:

- agent behavior;
- external environment;
- purpose;
- evidence.

Prefer this user-facing table when the claims fit cleanly:

| Lens | What is established | Provenance | What remains unknown |
|---|---|---|---|
| Agent behavior | ... | Repository or trace evidence | ... |
| External environment | ... | Repository, trace, or user evidence | ... |
| Purpose | ... | Usually user-confirmed | ... |
| Evidence | ... | Tests, traces, issues, or external outcomes | ... |

Mark each claim as repository-derived, trace-derived, user-supplied, or unknown. Name the source revision, important paths, reconstruction differences, and observability gaps. Ask only for facts the code and traces cannot establish, such as the important user job, business rule, channel constraint, required handoff, prohibited outcome, or independent evidence of success.

The current investigation API has no public write path for this structured context. Keep the confirmed brief visible in chat and do not disguise it as arbitrary investigation metadata or save it to an untracked local file as if that were durable product state.

## Choose the entry path

Infer the path from the user's evidence. If their intent is still ambiguous, offer one simple choice:

| Start from one session | Explore a session population |
|---|---|
| "I have a session I want to understand." | "I want to discover recurring problems or unexpectedly good behavior." |
| Uses a small seed-led worklist. | Uses a bounded diverse sample. |

Use the user's language in the conversation. Keep `trace-first` and `cold-start` as internal workflow names unless the distinction helps explain a decision.

### Trace-first

Use this path when the user supplies or identifies a seed session.

1. Resolve the exact seed session and read its complete nodes and payloads.
2. Ask for the suspected behavior in ordinary language if it is not already clear.
3. Select a small worklist containing the seed, plausible related sessions, and at least one deliberately dissimilar counterexample.
4. Treat the suspicion as a search direction, not a label.

### Cold-start

Use this path when the user has a bounded population but no confident starting failure.

1. Define the eligible session population and time or version boundary. Exclude the durable importer smoke-test tag carried from a builder checkpoint with `kitaru session list --tag TAG` when available, plus any known smoke-test session IDs and disposable-agent or isolated-source markers.
2. Run selected low-cost deterministic analyses explicitly. Import alone must not trigger analysis.
3. Build a diverse initial worklist, normally 15 to 30 sessions, using roughly 60 to 70 percent coverage-oriented examples and 30 to 40 percent random examples.
4. Record the population, seed, selection method revision, and reason each session was selected.
5. Describe this batch as a discovery pilot, not evidence of saturation or prevalence.

## Create or resume the investigation

Use a small fixed question contract. Default to:

- `observation`: a required free-text account of what the reviewer observes;
- `verdict`: an optional whole-session value of `acceptable`, `problematic`, or `uncertain` when it helps sorting;
- at most one direction-specific question when the investigation has an explicit focus.

Do not persist a large fixed taxonomy. Keep adaptive follow-up reasoning in the coding-agent conversation. When a systematically different question is needed, create a bounded follow-up investigation instead of changing the active investigation.

Before creation, show the user the agent, bounded population, ordered worklist size, fixed questions, and the fact that this will create remote state. Then create one investigation with its complete fixed worklist.

Preview a non-trivial worklist as a compact table:

| Position | Session | Why selected | Review status |
|---:|---|---|---|
| 1 | Exact ID | Seed, coverage, random, suspected match, or counterexample | Pending |

Generate neutral summarized views when useful. Every view item must point through selectors to canonical session-node evidence. Do not place unsupported conclusions or provisional failure labels in the first unprimed batch.

After creation, return a checkpoint card:

| Field | Value |
|---|---|
| Agent | Exact ID and version when known |
| Investigation | Exact ID |
| Mode | Trace-first or cold-start |
| Sessions | Count |
| Questions | Stable keys |
| Next action | Frontend review or in-chat fallback |

## Hand off to review

Prefer one continuous Kitaru frontend review block when the product exposes an investigation review link or an agreed URL constructor. Use only the opaque investigation identifier in the URL. Do not encode session lists, questions, or judgments in query parameters.

Present the handoff explicitly:

```text
[Go to the Kitaru frontend now]

Review investigation <id>. Add a written observation for each reviewed session,
attach observations to exact nodes when relevant, and complete or skip each item.
Return here when you are ready for me to re-read the persisted review state.
```

Pause for the human review. After the user returns, re-read the investigation, linked-session statuses, and annotations. Do not treat "done" as proof that the worklist is complete. Report any remaining or skipped items and let the user continue or deliberately finish with the current evidence.

### In-chat fallback

When the frontend is not yet available, conduct the same review against the same durable investigation through MCP or structured CLI:

1. Read one complete session and its nodes, including required payloads.
2. Present the final output, a compact neutral execution outline, the relevant tool or model evidence, and the selection reason.
3. Ask the user for an open observation before offering any hypothesis.
4. Persist the user's words as the investigation answer, adding a canonical selector when the observation concerns an exact node or payload.
5. Record the optional verdict only when the user supplies or confirms it.
6. Mark the linked session completed only after required answers are persisted; mark it skipped only when the user deliberately skips it.
7. Continue through a bounded block without asking the user to copy IDs or annotation text between systems.

Never write a model-generated observation on the user's behalf.

## Alternate breadth and depth

Wait until the initial open-review batch has enough human evidence before exposing provisional hypotheses. For cold-start discovery, require at least four non-empty observations across at least three distinct scenarios before the first synthesis. This unlocks a provisional hypothesis, not a saturation claim.

After a possible behavior appears:

1. Search for related sessions with high recall.
2. Include a dissimilar counterexample before settling on a definition.
3. Present suspected matches as agent suggestions with their evidence and uncertainty.
4. Require the human to accept, reject, or mark each suggestion uncertain before treating it as reviewed evidence.
5. Revisit earlier sessions when criteria drift reveals a materially different behavior.

The current API cannot append sessions to an investigation or persist a typed suggestion and disposition. Use a new bounded follow-up investigation when more review is needed. State that boundary plainly. Do not store an agent suggestion as a human annotation or pretend chat-only disposition is durable product provenance.

## Offer insight as evidence grows

After each completed review batch, give the user a short synthesis before asking what to do next:

| Insight | Evidence | Why it matters | What could change it | Best next evidence |
|---|---|---|---|---|
| One concrete, observable pattern | Exact reviewed sessions and selectors | User, product, cost, safety, or reliability consequence | Main ambiguity or counterexample | One bounded follow-up session or action |

Include unexpectedly good behavior when it teaches the user something useful about the agent. Distinguish a repeated pattern from a one-off anomaly and a confirmed behavior from a provisional hypothesis. Never turn the observed count in an adaptive sample into a prevalence claim.

Prefer a small number of consequential insights over a long inventory. Connect each insight to a concrete next choice: review another contrasting session, refine the behavior, accept a cohort, inspect missing external evidence, or stop because the current question is answered.

## Synthesize reviewed behavior

Use only persisted human observations and explicit dispositions. Preserve the original open-code text even when a later structured label exists.

Propose one to three candidates. For each candidate include:

- a provisional title;
- one observable binary definition;
- the initial conditions under which it matters;
- the independent outcome evidence needed to judge it;
- supporting reviewed session IDs and selectors;
- reviewed counterexample session IDs and selectors;
- the main unresolved ambiguity.

When presenting more than one candidate, add a compact comparison table after the evidence-grounded explanation:

| Candidate | Binary definition | Supporting evidence | Counterexample | Main ambiguity |
|---|---|---|---|---|
| ... | ... | Exact session and node references | Exact reviewed reference | ... |

Separate agent failures from dependency failures. A service error becomes evidence about the agent only when the accepted criterion concerns the agent's response to that error.

Ask the user to accept, edit, or reject one exact candidate. Silence, conversational momentum, and acceptance of a similar earlier draft do not count.

## Create the cohort checkpoint

After exact behavior acceptance:

1. List the exact positive session IDs proposed for membership and the reviewed counterexamples excluded from membership.
2. Explain that cohort creation writes remote versioned state.
3. Require confirmation of the exact membership.
4. Create the cohort and immutable first cohort version through the supported Kitaru operation.
5. Re-read the result and return the exact cohort and cohort-version identifiers.

Do not encode prevalence claims from an adaptive discovery sample.

If the user wants repeatable measurement, continue with [references/deterministic-evaluators.md](references/deterministic-evaluators.md). Run relevant descriptive evaluators first, then prefer an installed configured evaluator that directly expresses the accepted criterion. Pin its exact evaluator version and parameters. Only continue to [references/evaluator-authoring.md](references/evaluator-authoring.md) when the installed catalog cannot express the criterion.

If the cause is an obvious prompt ambiguity, missing capability, ordinary software bug, or dependency failure, recommend the direct fix. Add an evaluator only when preserving the case as a regression check is useful.

Finish evaluator work with factual evidence, not a maturity label:

| Field | Value |
|---|---|
| Evaluator | Exact evaluator and evaluator-version IDs |
| Parameters | Exact parameters or configuration hash |
| Implementation checks | Passed, failed, or not run |
| Kitaru load/signature check | Passed, failed, or not run |
| Reviewed fixtures | Count and verdict coverage |
| Human agreement | Measured facts or not measured |
| Held-out evaluation | Measured facts or not run |
| Freshness limitations | Exact known change or none observed |
| Supports | Exploration, known-case regression, or an exact user-defined gate |
| Does not support | Stronger claims the evidence cannot establish |

Investigation may stop successfully at this checkpoint. If the user wants to test one change, continue with `kitaru-replay-experiment` and carry the accepted behavior, exact cohort-version ID, evaluator-version IDs and parameters, factual evidence and limitations, candidate agent-version ID when known, proposed override, explicit tool policy, intended use, and any user-defined gate. Do not route back through investigation merely to choose a candidate.

## Preserve failure honesty

- If the frontend is missing, use the in-chat fallback; do not invent a dashboard route.
- If agent source cannot be resolved safely, stop before presenting a code-grounded context brief.
- If full trace payloads are unavailable, identify the missing evidence and do not silently summarize truncated input.
- If the worker is unavailable, create no fiction about completed analyses or evaluations.
- If a mutating response is dropped, read current state before retrying because general request idempotency is not guaranteed.
- If the user wants to abandon an investigation, leave it incomplete or skip unwanted sessions. Do not use destructive deletion as cancellation; deletion also removes linked sessions and investigation answers.
- If label isolation is not server-enforced, do not claim blinded evaluator validation.
