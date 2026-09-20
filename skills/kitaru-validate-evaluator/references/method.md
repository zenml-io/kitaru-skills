# Human-guided validation method

## 1. Make the decision concrete

Start with what the user wants the evaluator to help decide: finding cases for review, checking a known regression, or supporting a consequential decision. These uses need different evidence. Ask which mistake hurts more: overlooking a real problem or rejecting acceptable behavior.

Inspect a human-identified failure and a valid counterexample. Draft a short criterion with pass, fail, exceptions, required evidence, and missing-evidence treatment. Confirm changes to meaning, not a criterion already accepted. Prefer code for exact comparisons, counting, and structural rules. Keep a semantic judge for interpretation.

For example, unsupported refund timing is narrower than all invented refund promises. A reply claiming that a refund has completed is a different check. Do not silently narrow the user's request to fit an example. A missing recorded tool result cannot establish that a promise was unsupported; mark the evidence gap separately unless other sufficient evidence is available.

Use one criterion per investigation. Its verdict labels that criterion across the whole session, not general helpfulness. A prior overall-quality verdict needs human confirmation or relabeling before use here. Keep annotations as explanatory evidence; do not convert their prose into a binary label yourself.

## 2. Collect human reference labels

Use the existing investigation review flow described in `kitaru-contracts.md`. Explain the verdict mapping before review. Keep one required observation question short; its answer supports understanding but does not replace the session verdict. Reuse a compatible investigation and its progress. Separate investigations for development and test may help, but different investigation IDs do not prove their sessions or related families are disjoint.

One knowledgeable person can define correctness. If decision authority is shared, arrange independent judgments using available review workflows before reconciliation. A mutable shared session verdict is not a record of independent votes. Resolve disagreement by clarifying the rule, adding a boundary example, or separating mixed criteria. Preserve the human's decision and record the rubric revision; do not manufacture consensus.

Where possible, have people label before seeing evaluator predictions. State any limits to isolation honestly. When review cannot be opened or required payloads are unavailable, preserve the existing IDs and name the blocker. Do not build a replacement annotation interface or fill verdicts on the user's behalf.

## 3. Get an exploratory result

Use a small set with relevant human passes and failures when available. Do not require a universal sample size before a first useful comparison. If one class is absent, report it as unmeasured and seek examples of that class before making a claim about it.

Retrieve or run the selected evaluator configuration and result name. Normalize and count results through the contracts reference and reporting helper. Start with one concrete disagreement and the minimum relevant evidence. Ask whether it reflects an evaluator mistake, rubric ambiguity, a reference-label mistake, or missing evidence. Any reference-label change needs human judgment; any change of criterion requires reviewing affected labels.

If all cases agree, say exactly how many and which kinds of cases were checked. Stable repeated answers and agreement on a small familiar set do not establish performance on new cases. Offer the exploratory checkpoint without forcing further validation.

## 4. Separate learning from assessment

For stronger evidence, group related conversations, duplicate exports, and replay variants before assigning cases:

- **Examples/training:** demonstrations that may appear in evaluator instructions. Optional for zero-shot evaluators.
- **Development:** cases used to diagnose errors and revise wording, model, observation window, evidence selection, parser, or thresholds. Assign already-explored pilot cases here or to examples.
- **Test:** reserved cases used to assess a frozen configuration. Keep their contents and labels out of tuning context where possible.

Record membership and related-group identity, not only aggregate counts. Do not copy a development case into prompt examples while continuing to count it as independent development evidence. Acquire a separate representative training example or explicitly reassign the case and its related group.

Human reviewers may inspect reserved test cases solely to label them under the frozen rubric. That necessary inspection does not itself contaminate the test. Cases used to develop the rubric, choose examples, tune settings, or diagnose evaluator behavior are no longer untouched. When the host cannot isolate test content from the tuning agent, disclose the procedural boundary rather than claiming enforced blinding.

Before viewing test outcomes, agree on acceptance criteria for the stated use, both error directions, acceptable undecided workload, and evidence needed from each class. Use context-specific targets and counts, not a universal 90% rule. A tiny or narrow sample can remain inconclusive even if it meets a numerical target.

## 5. Improve on development cases

Change one meaningful part of the evaluator at a time when that makes the comparison interpretable. Re-run comparable development cases and report missed problems, unnecessary rejections, held results, and failed executions. Preserve configuration identities and compare the same eligible cases; disclose membership changes.

Inspect mistakes before assuming that changing a threshold will fix them. The criterion may combine several ideas, required context may be missing, or the model may not distinguish the cases. Use only a decision policy the selected evaluator supports. Confidence-like scores are not automatically calibrated probabilities of correctness.

For TypeSafe Noul, raw scores are `p(yes)`; a question asking whether a failure occurred normally has reverse pass polarity. Its symmetric pass/held/fail rule is not a single cutoff. Follow the installed result contract in `kitaru-contracts.md`; do not convert a high raw score into a pass by default. Report any threshold exploration as development work, and verify the chosen configuration before final assessment.

## 6. Assess once and explain the result

Freeze the complete evaluator configuration, criterion, evidence policy, split membership, accepted label snapshot, and acceptance criteria. Use the exact job/task/results for the test run. A completed investigation does not lock its verdicts; detect label changes before combining fresh results with a saved report.

Show all selected-session accounting. Among human passes and failures, separately report evaluator pass, fail, held, and unavailable/error. List unresolved labels, unreviewed sessions, and evidence exclusions nearby with reasons. Exclude operational outcomes from decided-only quality denominators while keeping them visible in coverage and full-cohort accounting. With a zero denominator, report “not measured.”

Explain both mistakes in ordinary terms before naming metrics. Keep decided-only class agreement separate from the fraction of all eligible human-labeled cases receiving a correct decision. Never present either as the application's production success rate. A curated regression set cannot establish production prevalence.

If a person or second model reviews held cases, evaluate that route separately before making claims about the combined workflow. Agreement with reference labels does not establish probability calibration. Do not add prevalence corrections or confidence-interval machinery to this workflow.

When test findings inform revisions, retire that test from future untouched-test claims and obtain fresh test evidence before a new final assessment. Preserve the old result. Changes to labels, criterion, data source, evidence view, evaluator, model, or parameters require reassessing validity; they do not silently inherit the old result.

End with what the evidence supports for the agreed use, what remains unmeasured, and one next action. Do not deploy, change a gate, or award a readiness badge. A factual agreement report can be useful even when the conclusion is that more evidence is needed.

## Further reading

[Hamel Husain and Shreya Shankar's public validation workflow](https://github.com/ai-evals-course/evals-skills/blob/main/skills/validate-evaluator/SKILL.md) develops the disagreement-review and held-out-test method. This skill applies it to Kitaru investigation verdicts, adding explicit accounting for undecided results and execution failures. Its numerical examples are not universal acceptance targets.
