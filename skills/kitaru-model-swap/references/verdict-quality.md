# Verdict-backed quality

Agreement with today's model says where candidates behave alike, not which answer is right. The user's verdicts on the disagreements turn agreement into a quality score. Compute it yourself from the report and the annotations; nothing in Kitaru computes it for you.

## Inputs

- The report: `kitaru insight list --filter '{"field":"import_id","op":"eq","value":"IMPORT_ID"}' --name model-swap-summary`, newest item, `metadata["kitaru.model_swap/v1"]`. Per candidate, `answered` and `agreement` (counts per category); the run-level `disagreements` list with `candidate`, `session_id`, and `node_id`.
- The verdicts: `kitaru annotation list --session SESSION_ID` for each session in `disagreements`. Keep annotations whose value has `model_swap.candidate` and `model_swap.verdict`, and match them to disagreements by candidate and `selector.node_id`. When a node has several verdicts for the same candidate, use the newest.

## Per candidate

- **Agreeing calls**: `same_tool_same_args` plus `same_text` counts. Treat them as right only if today's model was right on those calls; say this assumption out loud. When the user has also judged a sample of agreeing calls, use that sample instead.
- **Reviewed disagreements**: verdict `candidate_correct` or `both_acceptable` counts as right; `recorded_correct` or `both_wrong` counts as wrong; `unsure` is left out.
- **Unreviewed disagreements**: left out of the score and reported as a count.

Quality = (agreeing calls + reviewed disagreements judged right) / (agreeing calls + reviewed disagreements, excluding unsure).

For today's model, use the same verdicts from its side: on each reviewed disagreement, `recorded_correct` or `both_acceptable` counts as right for today's model, and `candidate_correct` or `both_wrong` as wrong.

## How to show it

One line per candidate: quality as a percentage, then "from N reviewed of M disagreements". Mark scores resting on fewer than 10 reviewed disagreements as early. Never round an early score into a recommendation without saying it is early. When fewer than half of a candidate's disagreements are reviewed, offer to review more before recommending it.
