# Explain the next decision visually

Use one small view to answer the user's current question. Start with examples and counts; reveal percentages and formal names only when they help. All examples below are synthetic and must be identified as such. Replace them with verified records for real reporting.

Prefer host-native tables or diagrams. Local HTML is optional, not a new review interface. Keep sensitive excerpts minimal and local; never send traces to a rendering service. Preserve text equivalents, visible labels, and a reading order that works without color, hover, or a wide screen. For narrow displays, stack comparisons vertically. Any optional controls need keyboard access and visible focus. A host without rich rendering can complete the whole workflow with prose and tables.

## Criterion card: does this match your intent?

Synthetic example:

| Field | Meaning |
|---|---|
| Criterion | Does the reply promise a refund duration unsupported by the available policy/tool evidence? |
| Failure | Reply promises two days; the recorded policy provides no duration. |
| Counterexample | Reply accurately quotes the policy's five-day duration. |
| Exception | A reply making no timing promise does not violate this criterion. |
| Required evidence | Final reply and the relevant policy/tool results. |
| Missing evidence | Unresolved eligibility, not a failure label. |

Ask whether this boundary matches the user's meaning. Do not label illustrative examples as observed traces. Keep exact numeric comparisons in code when appropriate.

## Disagreement: what explains this case?

Synthetic example:

| Evidence | Value |
|---|---|
| Recorded policy | No processing-time guarantee is recorded. |
| Final reply | “Your refund will arrive tomorrow.” |
| Human criterion verdict | Fail |
| Evaluator verdict | Pass |

In a real report, link to the original session and show only the relevant evidence beside the two verdicts. Ask whether the judge missed the promise, the rubric allows it, the human label needs correction, or evidence is incomplete. Explain your own analysis as analysis. Do not attribute a rationale to a provider that returned only a probability or threshold statement.

If there are no disagreements, show one real agreement instead and explain the limits of the reviewed sample. If execution failed, show the error and recovery choice, not a fabricated comparison.

## Outcome summary: what happened to every case?

Synthetic example with 20 selected, eligible, human-labeled cases:

| Human criterion label | Evaluator pass | Evaluator fail | Held | Unavailable/error | Total |
|---|---:|---:|---:|---:|---:|
| Pass | 6 | 1 | 1 | 0 | 8 |
| Fail | 2 | 8 | 1 | 1 | 12 |

Lead with: “Of the 12 failures you identified, the evaluator caught 8, missed 2, left 1 undecided, and could not evaluate 1. Let's inspect a missed problem first.”

Then explain the denominators: it caught 8 of the 10 failures it decided; it produced a correct fail decision for 8 of all 12 human failures. The held case needs a review decision and the error needs recovery. The two false passes remain mistakes even though they received decisions.

For human passes, it accepted 6 of 7 decided cases; 6 of all 8 received a correct pass decision. Show zero excluded, uncertain, and unreviewed cases for this synthetic example. Real reports must include their actual counts and reasons rather than dropping them. Use the deterministic helper for real arithmetic.

A stacked count chart may accompany the table, but use words as well as colors. Do not replace the table with one overall accuracy score. An all-held class has zero decided coverage and “not measured” decided agreement, not 100% agreement.

## Split diagram: what can teach the evaluator?

Synthetic family assignment: related sessions A1 and A2 both belong to examples; B1 and B2 both belong to development; C1 and C2 both belong to test. Different investigation IDs alone do not establish separation.

```text
Examples A1/A2 ------> Instructions
Development B1/B2 --> Inspect errors --> Revise configuration
Test C1/C2 ---------> Frozen configuration --> Final report
                                               |
                                  Revision informed by test?
                                               |
                               Retire C1/C2 from untouched test
```

Explain that a human may label C1/C2 using the frozen rubric. Their contents and outcomes must not guide tuning if they are to remain test evidence. If the user only needs today's exploratory comparison, stop before asking them to build these groups.

## Development comparison: did the change help?

Synthetic example on the same 12 human failures:

| Configuration | Caught | Missed | Held | Error | Decided |
|---|---:|---:|---:|---:|---:|
| A | 8 | 2 | 1 | 1 | 10/12 |
| B | 8 | 0 | 3 | 1 | 8/12 |

B has fewer false passes but sends more cases for review; it has not caught additional failures. Also compare human-pass outcomes before judging the trade-off. A higher decided-only percentage does not by itself make B better for the intended use.

Only offer a threshold control when the evaluator exposes a compatible score and decision policy. Label recomputed counts as simulation. For TypeSafe Noul, apply its actual polarity and symmetric undecided band, not a generic single threshold. Verify the selected configuration before final testing. Keep tuning controls out of final-test views.

## Optional metric names

Introduce these after the user understands the counts:

- **False pass:** evaluator passes a human failure; the problem is missed.
- **False fail:** evaluator fails a human pass; acceptable behavior is rejected.
- **Decided coverage:** pass plus fail outputs divided by eligible human-labeled cases, separately for each class.
- **Decided-only pass recall:** correct passes divided by human passes receiving a decision.
- **Decided-only failure recall:** correct fails divided by human failures receiving a decision.

With PASS defined as positive, the last two are TPR and TNR conditional on receiving a decision. State that qualification every time those names could be mistaken for all-cases rates. Do not compare conditional recall with an all-cases acceptance target. Keep unconditional correct-decision fractions separately labeled and all zero-denominator quantities “not measured.” No formula is required to choose the next useful action.
