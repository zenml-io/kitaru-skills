# Guided tour method

Use this method to create a small prepared lesson from the canonical returns-agent traces. Optimize for a concrete insight, not for a representative audit.

## Select three teaching moments

Survey all ten imported sessions through existing deterministic evaluation records and session metadata, then read every node and full payload for each candidate. This selection pass is read-only. Do not start new evaluation jobs merely to choose the tour. Select:

1. **Consequential problem:** a complete trace where recorded policy, tool, or outcome evidence supports a concrete concern.
2. **Evidence-reading lesson:** a trace where summaries alone are insufficient, such as a difference between a claimed action and a tool result, a missing lookup, or an operational signal that changes the interpretation.
3. **Acceptable counterexample:** a nearby case showing behavior that should not be swept into the same problem.

Include a random component in the initial survey so selection is not limited to the first obvious failures. The final three are curated for teaching and do not support prevalence claims.

Do not use ticket identifiers, fixture implementation, test-only expected outcomes, or a prewritten candidate as an answer key. Public agent instructions, recorded inputs, model and tool activity, tool results, and visible synthetic policy outputs are valid tutorial evidence.

## Write prepared observations

For each session, write one or two concise ordinary annotations. Anchor each note to the smallest useful node, JSON field, or text span. Use the complete session only when no narrower selector carries the meaning.

Start every durable note with `Agent observation:`. State what the evidence shows and why it matters without pretending the user has already agreed. Prefer:

> Agent observation: The policy result requires approval above $200, while the highlighted tool result records an accepted $280 refund.

Avoid:

> Agent observation: This is definitely a bad session and proves the agent is unsafe.

Before creating a note, list the session's existing manual annotations and reuse an exact matching selector and observation. Do not append duplicates after a dropped response or resumed tour.

## Prepare the investigation

Keep one session-specific question per session. The current review still presents a written answer field, but the guided tour asks the human only for the whole-session verdict. Phrase the question as an invitation to inspect the prepared evidence:

- “Given the approval limit and recorded refund action, how would you judge this complete session?”
- “Does the final customer reply accurately reflect the tool result shown here?”
- “Does this nearby case look acceptable, problematic, or uncertain when compared with the prepared observation?”

Attach one primary highlight to each question. Use the selector of the most important prepared annotation and a short context description. Additional evidence remains visible through the ordinary annotations. This keeps the question anchored predictably in the current frontend.

Order the sessions problem, subtle lesson, counterexample. Give the investigation a valid machine name such as `guided-returns-tour`, adding a short letter-or-digit suffix when a distinct investigation is required. Do not put spaces or a display title in the name. Put the readable title and the fact that a coding agent prepared observations while the reviewer supplies whole-session verdicts in the description. Preserve the exact investigation ID for resumption.

## Preview without ceremony

Before the combined write approval, show three compact rows:

| Stop | What the user will inspect | Why it is useful |
|---|---|---|
| 1 | The consequential action and its governing evidence | Shows why complete tool traces matter. |
| 2 | The subtle inconsistency or missing evidence | Shows why a final answer alone can mislead. |
| 3 | A nearby acceptable case | Shows that a useful check needs boundaries. |

Adapt the descriptions to the actual selected traces. Do not show internal IDs, sampling methodology, raw JSON, or a long research plan in the conversational lead.

## Read the human verdicts

After the user selects Done, re-read the investigation and distinguish:

- prepared manual annotations;
- optional written answers;
- whole-session verdicts; and
- investigation status.

The complete tour succeeds when the user has judged the three sessions. Written answers are optional. If one verdict is missing, explain which teaching stop remains and offer the same frontend link. If the user wants to stop, lead with what the persisted verdicts already establish and keep any unreviewed prepared observation clearly separate from human judgment.

Lead with the user's choices and the evidence beside them. A verdict does not automatically endorse every prepared annotation. Propose a repeatable behavior only after the user has judged every session that would enter its cohort, including at least one problematic target and one acceptable counterexample.

## Turn one finding into a check

After the user accepts the behavior and every proposed cohort member has a human verdict:

1. Include exact problematic examples plus at least one acceptable counterexample in an immutable cohort version.
2. Check the installed evaluator catalog first. Use a configured deterministic evaluator when it directly expresses the accepted behavior.
3. Otherwise scaffold one narrow evaluator from observable recorded evidence. Do not map ticket or session identifiers to answers or import the template's test-only oracle.
4. Test the evaluator locally, register an immutable version, and run it across the complete `returns-baseline` population.
5. Compare its results with the three human verdicts. Fix an evident evaluator bug; otherwise report disagreement rather than changing the human judgment to make the check pass.

If no human-confirmed problematic example remains, or the user rejects the proposed behavior, stop before cohort and evaluator creation. Treat that correction as a useful result and offer one more bounded prepared review only if the user wants it.

## Land the AHA

Use this order:

1. State the user's finding.
2. State what Kitaru preserved that made the finding inspectable.
3. State what the reusable check found across all ten sessions.
4. Name one limitation, such as the synthetic population or missing external outcome evidence.
5. Explain “cohort” and “evaluator version” only after the result is clear.

Lead with direct frontend links for every created object or result whose
structured response supplies one. The user should not have to search the UI for
the investigation, cohort, evaluator, or evaluation run that the tour just
described.

Do not continue automatically into paid replay. Offer it as the next chapter.
