# Verdict-backed quality

Agreement with today's model says where candidates behave alike, not which
answer is right. The user's verdicts on the disagreements turn agreement into a
quality score. Compute it yourself from the report and the annotations; nothing
in Kitaru computes it for you.

## Inputs

- The report:
  `kitaru insight list --filter '{"field":"import_id","op":"eq","value":"IMPORT_ID"}' --name model-swap-summary`,
  newest item whose report has `dry_run: false`. Note its `id` (the run
  identity) and read `metadata["kitaru.model_swap/v1"]`. Per candidate, take
  `model`, `answered`, and `agreement` (counts per category). From the run,
  take the `disagreements` list with `candidate`, `session_id`, `node_id`, and
  `schema_source`.
- The verdicts: for each session in `disagreements`,
  `kitaru annotation list --filter '{"field":"session_id","op":"eq","value":"SESSION_ID"}' --size 1000`.
  Keep annotations whose value has `model_swap.run` equal to the run's insight
  `id`, and match each to a disagreement by `model_swap.candidate`,
  `model_swap.model`, and `selector.node_id`. Ignore verdicts from other runs or
  for another model. When a node has several matching verdicts, use the newest.

Drop every disagreement whose `schema_source` is `inferred`. The report already
leaves those calls out of `answered` and `agreement`, so they stay out of the
score on both sides.

## Counts per candidate

Work out these numbers for each candidate, the `reference` included:

- **A, agreeing calls:** `agreement.same_tool_same_args + agreement.same_text`.
- **M, disagreements:** `answered - A`. Take M from the counts, not from the
  length of the `disagreements` list, because that list is truncated at
  `max_disagreements` and also carries inferred-schema calls.
- **R, reviewed disagreements:** the candidate's non-inferred disagreements with
  a matching verdict other than `unsure`.
- **Unreviewed:** M minus every reviewed disagreement, `unsure` included. Report
  the count; leave these calls out of the score.

## Head-to-head score

Score each candidate head to head against the recording on the same calls: the
candidate's agreeing calls plus its reviewed disagreements. Both sides get the
same denominator, A + R.

- **Agreeing calls** count as right for both the candidate and today's model.
  They credit both sides equally, so only reviewed disagreements separate the
  two. Treating them as right assumes today's model was right on them; say this
  assumption out loud. When the user has also judged a sample of agreeing calls,
  use that sample instead.
- **Reviewed disagreements** count by verdict:

| Verdict | Candidate | Today's model |
|---|---|---|
| `candidate_correct` | right | wrong |
| `recorded_correct` | wrong | right |
| `both_acceptable` | right | right |
| `both_wrong` | wrong | wrong |
| `unsure` | left out | left out |

```text
candidate quality             = (A + reviewed right for the candidate) / (A + R)
today's model, same calls     = (A + reviewed right for today's model) / (A + R)
```

Report both numbers for each candidate. Today's model has a different
head-to-head number against each candidate, because each candidate disagrees on
different calls; never combine them into one score for today's model.

The `reference` candidate is scored exactly like any other candidate: its
disagreements with its own recording are run-to-run variation, reviewed the same
way. Use its score as the noise floor for the others.

Never use `judge_equivalent` as a verdict or to fill in unreviewed
disagreements.

## How to show it

One line per candidate: candidate quality and today's model on the same calls,
as percentages, then "from R reviewed of M disagreements". Mark scores resting
on fewer than 10 reviewed disagreements as early. Never round an early score
into a recommendation without saying it is early. When fewer than half of a
candidate's disagreements are reviewed, offer to review more before recommending
it.
