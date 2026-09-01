# Hosted tour method

Use the preloaded ticket-resolver traces to reach one concrete insight quickly. This is a teaching route, not a representative audit.

## Sustain the learning arc

The tour tells one story rather than demonstrating a list of Kitaru features:

| Phase | User's question | Concept to teach | What the page makes visible |
|---|---|---|---|
| Observe | What did the returns agent actually do? | A session preserves one execution: customer input, model decisions, tool evidence, action, and reply. Recording is evidence, not a verdict. | The ten imported sessions and the details of one representative session. |
| Judge | Which decisions were acceptable, and why? | A trace can reveal facts that the final reply hides. Human verdicts establish the behavior boundary; prepared observations only focus attention. | Three contrasting sessions, their evidence highlights, and the user's verdict controls. |
| Define | Can that judgment become a repeatable check? | A cohort freezes the reviewed examples. An evaluator versions the accepted relationship so it can be applied consistently to past and future sessions. | The evaluator's rule, version, source, and baseline results. |
| Compare | Did a specific change improve the behavior? | Replay reruns the same cases with one prompt change while holding the model, inputs, tools, cohort, and evaluator fixed. This supports a narrow comparison, not a general quality claim. | The exact baseline/candidate run and per-session differences. |

Before every phase, give the user a reason to care before performing work. After every phase, interpret the result and use it to motivate the next phase. Use one short paragraph before the work and one evidence-led paragraph afterward. Do not expose file creation, command construction, help lookup, polling, retries, or tool names unless an actual blocker requires one recovery choice from the user.

Use these transition goals, adapting the words to the evidence:

- **Into sessions:** “The agent is registered and its ten past runs are now sessions. This page answers our first question: what did it actually do?” Tell the user to open one representative ticket and notice its input, tool evidence, action, and reply. Open the page and end the turn before selecting the later review cases or reading their payloads.
- **Into review:** “A session tells us what happened, but not whether it was right. We will compare a suspected problem, a trace-dependent case, and a nearby acceptable case so your judgment defines the boundary.” Preview the three cases before writing or opening the review.
- **Into the evaluator:** Lead with the relationship the user confirmed. Explain the cohort and evaluator as two parts of preserving that decision, then state what the evaluator will count across the ten-session baseline. Do not introduce them as resources that merely need to be created.
- **Into replay:** Lead with the baseline finding and its limitation. Explain the one prompt instruction being changed and why holding everything else fixed makes the comparison meaningful.
- **At the end:** Resolve the story. State what the original agent did, what the user judged, what rule was encoded, and what changed or failed to change under replay. Then explain that the same loop can be applied to the user's own agent and traces.

Do not allow implementation friction to become the narrative. If a command needs correction, recover silently and resume at the same educational beat. If recovery changes the product result, explain only that consequence.

## Prepare three evidence stops

This is guided onboarding, not an open-ended policy investigation or an unbiased labeling exercise. The user is learning how Kitaru connects trace evidence, human judgment, and reusable evaluation. Do not make them discover the template's policy, infer the intended behavior from code, or hunt through tool payloads before they can answer.

For the unchanged checked-in population, prefer these three stable evidence stops by external ticket identity after verifying their recorded facts:

1. **ticket-003, suspected problem:** The accessories policy permits unused returns for 14 days. The order was delivered 20 days ago, but the agent issued a $48 refund instead of escalating the unsupported exception. The expected onboarding verdict is **Problematic**.
2. **ticket-009, acceptable boundary:** The apparel return is within its 30-day window. The customer requested $120 for an $80 order, and the agent refunded only the $80 actually paid. The expected onboarding verdict is **Acceptable**.
3. **ticket-008, trace-dependent safeguard:** The order record shows that a refund had already been issued. The agent did not issue a duplicate refund and escalated the missing-payment complaint for human review. The expected onboarding verdict is **Acceptable**.

These expected verdicts are teaching guidance, not records of the user's judgment. Verify the current trace evidence before presenting them and never submit the verdicts on the user's behalf. If the checked-in population changes and no longer supports a stop, select a replacement with the same role and give the user the complete governing rule, material trace facts, recorded action, and expected verdict.

If a resumable investigation already has this exact ordered set and question contract, reuse it. If only annotations exist, reuse exact matches and create only the missing investigation.

## Write decision-ready review material

For each session, write one or two short ordinary annotations anchored to the smallest useful evidence. Translate internal fields into their practical meaning. Say what the evidence shows without pretending the user has agreed.

Each investigation session gets one self-contained teaching question with four parts in this order:

1. **Rule:** State the relevant business policy in plain language.
2. **Evidence:** Translate the material order, policy, and action evidence from the trace.
3. **Expected reading:** State which verdict follows from the supplied rule and evidence, with one sentence of reasoning.
4. **Decision:** Ask the user to confirm **Acceptable**, **Problematic**, or **Uncertain**. The written answer is optional.

For the verified unchanged population, these compact questions retain all four parts and fit the hosted CLI budget:

- **ticket-003:** Unused accessories have a 14-day return window. This tote arrived 20 days ago; the agent refunded $48 instead of escalating. Expected: Problematic, outside policy. Agree, or mark Acceptable/Uncertain?
- **ticket-009:** Apparel returns allow 30 days and at most the amount paid. Within that window, the customer asked for $120; the agent refunded the $80 paid. Expected: Acceptable, correct cap. Agree, or mark Problematic/Uncertain?
- **ticket-008:** Never refund twice. The order was already refunded; the agent escalated the missing-payment complaint without another refund. Expected: Acceptable, no duplicate. Agree, or mark Problematic/Uncertain?

Keep the three questions self-contained even when shortening them. The operations reference defines the command-size budget; the ordinary evidence annotations can carry further context.

The question is not a test of whether the user can reconstruct the policy. Never ask a bare question such as “Was the refund the right call?”, “Should the refund have been $120?”, or “Does this comply with policy?” Never require the user to inspect source code or discover a hidden expected answer. The trace remains available so they can see where the supplied facts came from and disagree when appropriate.

Preview the three stops in three compact rows. For each row, state the practical rule, what happened, and the expected verdict. Explain that the review demonstrates how those judgments are stored beside their evidence, not whether the user can reverse-engineer an unfamiliar agent. Then ask once to create missing annotations, create or resume the investigation, and open its review. After approval, perform the writes, navigate to the review, and wait.

## Read the human result

When the user returns, re-read the exact investigation and distinguish prepared annotations, optional written answers, whole-session verdicts, and investigation status.

If a verdict is missing, name the missing stop and reopen the same review. If the user stops, report only what the persisted verdicts establish.

When all proposed cohort members have verdicts, including one problematic target and one acceptable counterexample, lead with what the user decided. Then propose one observable relationship that explains the boundary. Ask one short confirmation before turning it into a reusable check. A review verdict is not permission to create a cohort or evaluator.

## Create one reusable check

After confirmation:

1. freeze the exact reviewed target and counterexample sessions in one cohort version;
2. prefer an installed deterministic evaluator when it directly expresses the accepted relationship and has verified scope;
3. otherwise create one narrow evaluator from observable trace evidence, test pass, fail, missing, and malformed cases, then register an immutable version;
4. run it across the complete same-agent baseline population; and
5. account for completed, failed, missing, matching, and non-matching results.

Run the tested first evaluator version across the baseline population before the evaluator-page handoff. Lead with what the check found, account for the full denominator, and name one limitation. Explain that the reviewed examples are the cohort and the versioned rule is the evaluator. Open the evaluator page with its baseline results and wait before proposing replay. Do not try to open both the cohort and evaluator pages in one response.

If the user rejects the prepared concern or no confirmed problematic example remains, do not create a cohort or evaluator for it. Offer one more bounded selection only if the user wants it.

## Compare one change

After the user inspects the cohort and evaluator, propose one small system-prompt clarification grounded in the accepted behavior. Keep the model fixed. Do not start prompt search or bundle an unrelated change.

Continue through `kitaru-replay-experiment` with the exact state and one explicit safe tool policy. Ask before experiment creation and paid/live model work. After settlement, open the exact run, explain improved, regressed, trade-off, or inconclusive evidence, and state what the result cannot prove.
