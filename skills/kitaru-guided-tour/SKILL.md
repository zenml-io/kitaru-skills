---
name: kitaru-guided-tour
description: Give first-time users a short, value-first Kitaru tour with the public returns-agent template. Use when someone has no agent or traces of their own, arrives from Kitaru onboarding, asks for a demo, tutorial, quickstart, or guided example, wants the coding agent to prepare trace annotations before they judge sessions, or wants to experience Kitaru's value before learning the full investigation method. Prepare a three-session frontend review, let the human provide verdicts, then turn one accepted finding into a deterministic evaluator result. Route real agents, open-ended discovery, and production evidence to kitaru-investigation instead.
---

# Kitaru guided tour

Deliver an AHA before teaching the complete method. Use the public Kitaru
returns-agent template to move from recorded traces, through a short prepared
frontend review, to one reusable evaluator result.

## Experience contract

- Assume the user has not read the template agent and does not yet know how
  Kitaru works. Explain each example from the evidence visible in the review,
  translate internal names into plain language, and never require missing code
  or product context to understand a question.
- Act as a friendly guide, not an invisible automation runner. At each meaningful
  transition, explain what the tour is doing, why that step matters, what Kitaru
  concept it demonstrates, and what the user will be able to see or do next.
  Keep routine commands in the background.
- Lead with what the user is about to discover, not installation or evaluation
  terminology.
- Teach only the concept needed for the current action. Explain deeper Kitaru
  objects after the user has experienced why they matter.
- Prepare useful observations and exact evidence anchors for the reviewer. Tell
  them once that these are agent-prepared notes and their verdict is the human
  judgment.
- Use the Kitaru frontend for review. Give the direct review link, open it when
  the host provides an ordinary open-URL action and the user asks, then pause.
  Lead with a direct frontend link whenever a later created object or result has
  one; never make the user hunt for what the tour just produced.
- Keep the first tour to three sessions: one consequential problem, one subtle
  evidence-reading lesson, and one acceptable counterexample.
- Reach the evaluator AHA without regenerating traces or making a paid model
  call. Ask separately before any later replay that requires a model provider.
- Preserve the user's healthy selected Kitaru server, whether local or cloud.
  Do not switch servers merely because the public template documents a local
  quickstart.
- Resume durable agents, imports, sessions, exact-match annotations, cohorts,
  and evaluator versions before creating replacements. Resume an investigation
  and its verdicts only when this conversation holds its exact ID or the user
  explicitly identifies it as their review.
- Prefer one combined approval for the clearly previewed tutorial writes. Do
  not turn the tour into a sequence of permission prompts.

## Load the tour references

- Read [references/tutorial-narration.md](references/tutorial-narration.md)
  before the first user-facing explanation and use its teaching rhythm
  throughout setup, review, and the evaluator AHA.
- Read [references/starter-template.md](references/starter-template.md) before
  setup or when deciding whether the checkout is the canonical public template.
- Read [references/tour-method.md](references/tour-method.md) before selecting
  sessions, writing observations, creating the review, or producing the AHA.
- Read [references/kitaru-operations.md](references/kitaru-operations.md) before
  any Kitaru CLI or MCP operation. Treat installed schemas as authoritative.

## Establish the tutorial route

Begin read-only.

1. Look for a candidate template checkout. If none exists, inspect the current
   canonical template README through the trusted source, choose a new
   `kitaru-template` destination in the current workspace, tell the user where
   it will be created, and ask before cloning the repository. After approval,
   clone and verify it. Never overwrite an existing destination.
   Use this route only when the resulting project root matches the public
   template contract in `starter-template.md`.
2. Establish CLI and MCP readiness through `kitaru-operations.md`. Explain and
   ask before installing the frozen project environment or changing host MCP
   configuration. Treat MCP as preferred but optional when the CLI can complete
   the tour.
3. Inspect Kitaru connectivity and keep using the healthy selected server. Only
   offer the template's isolated local server when no usable server is selected,
   and ask before starting or selecting it. Then inspect the exact registered
   `returns-resolver` agent version, relevant import jobs, and the complete
   imported population carrying the `returns-baseline` tag.
4. Resume matching durable state. Perform only missing setup steps from the
   verified template README, with one clear explanation and approval before
   environment changes, service starts, registration, or import.
5. Stop and route to `kitaru-investigation` when the template was materially
   customized, the user supplies their own agent or evidence, or the requested
   conclusion needs a defensible open-ended investigation.

Do not ask a first-time user to choose a framework, trace provider, review
method, or sampling strategy on the canonical route.

## Orient in three short beats

Before selecting the tour, explain:

1. The sample agent resolves synthetic return and delivery requests with lookup,
   policy, shipment, refund, replacement, and escalation tools.
2. Kitaru preserved ten complete historical runs, including the model and tool
   evidence needed to understand what actually happened.
3. The coding agent will prepare three observations in Kitaru; the user will
   inspect the evidence and decide whether each complete session is acceptable,
   problematic, or uncertain.

Then continue. Do not explain cohorts or evaluator versions yet.

## Prepare one guided review

Follow `tour-method.md` to inspect every candidate trace and assemble the
three-session tour. Before writing, show a compact preview of what happened in
each session, why it matters, and the evidence that will be highlighted. Write
the preview for someone seeing both the agent and Kitaru for the first time.
Avoid an exhaustive investigation plan.

Ask once to:

- add the three sessions' agent observations as ordinary Kitaru annotations;
- create one fixed investigation with the prepared questions and highlights;
- open the resulting frontend review.

After approval, create or resume the annotations and investigation through the
verified operations. Keep agent observations short and start each durable note
with `Agent observation:` so it remains understandable outside this chat.
Never write the user's verdict for them.

## Hand off to the frontend

Lead with the direct review action. Use this conversational shape:

> **Open the guided review:** [Review in Kitaru](RESOLVED_URL)
>
> I prepared the highlighted observations. Your part is to inspect the trace
> evidence and choose **Acceptable**, **Problematic**, or **Uncertain** for each
> session. You can leave the written answer blank unless you want to add or
> correct something.
>
> Select **Done** after the last session, then return here and I will show you
> what your judgments make possible.

Pause. Do not duplicate the review in chat while the frontend route works.

## Deliver the AHA

When the user returns:

1. Re-read the investigation, its ordered sessions, manual annotations,
   question-answer coverage, and verdict coverage.
2. Lead with what the user decided. Explain how each verdict now sits beside
   the exact recorded evidence that motivated the review.
3. If the user has judged every proposed cohort member, including at least one
   problematic target and one acceptable counterexample, propose one observable
   behavior that best explains the difference. Ask one short confirmation
   before turning it into a reusable check.
4. If the user accepts that behavior, create an exact cohort version from the
   confirmed target and counterexample sessions. Check the installed evaluator
   catalog before authoring code.
5. Select or create one narrow deterministic evaluator, test it, register an
   immutable version, and run it across the complete prepared baseline
   population.
6. Report the useful result first: how many sessions matched, which reviewed
   examples explain the result, and one important limitation. Include direct
   links to the cohort, evaluator, and evaluation results whenever Kitaru
   returns them.

If the verdicts do not support a problem, or the user rejects the proposed
behavior, do not force an evaluator into the story. Show the useful negative
result: the prepared concern did not survive human review. Offer one more
bounded prepared review or stop successfully there.

If the review is partial, stop before behavior confirmation, cohort creation,
or evaluator work. Report what the persisted verdicts already show and keep the
same review link available for completion.

Use ordinary language before object names. For example:

> You marked two sessions problematic because the agent bypassed approval.
> Kitaru has preserved those judgments beside the policy and refund events. I
> turned that behavior into a reusable check, and it found the same pattern in
> 2 of the 10 recorded sessions.

Only then explain that the frozen examples are a cohort and the reusable check
is an evaluator version.

## Continue from value

Offer two next steps:

- **Use my own agent:** continue with `kitaru-investigation`, carrying the tour's
  method explanation but none of its synthetic conclusions.
- **Test an improvement:** continue with `kitaru-replay-experiment`, carrying
  the exact accepted behavior, cohort version, evaluator version, candidate
  idea, and an explicit tool policy. Explain model work and cost before replay.

Stopping after the evaluator result is a complete successful tour.

## Preserve a pleasant failure path

- If the template setup is incomplete, state the current checkpoint and the one
  missing action. Do not dump a generic setup checklist.
- If the imported sessions or full node payloads are unavailable, stop before
  inventing observations.
- If an annotation or investigation write may have succeeded despite a dropped
  response, re-read state before retrying.
- If the review URL cannot be resolved, preserve the created investigation and
  report the broken handoff with its exact ID and one retry action.
- If fewer than three useful sessions exist, use the smaller honest tour and say
  what teaching moment is missing.
- If the user stops after only part of the review, summarize the persisted
  verdicts and what they already show. Offer the same link for the remaining
  stops, but do not withhold the partial value or treat prepared observations as
  missing human judgments.
- If the user disagrees with an agent observation, treat that correction as part
  of the lesson. Do not defend the prepared note or silently convert it into a
  human conclusion.
