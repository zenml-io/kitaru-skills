---
name: kitaru-validate-evaluator
description: Guide a human through checking one evaluator against criterion-specific Kitaru investigation verdicts, inspecting disagreements, improving on development cases, and assessing a frozen configuration on held-out cases. Use when a user asks whether an evaluator agrees with their judgment, wants to validate an existing judge, or continues from evaluator authoring. Supports TypeSafe and other evaluators without deploying a gate or changing the review UI.
---

# Validate one evaluator

Help the user decide what the evidence supports for their intended use. Teach through one concrete comparison at a time. The human defines acceptable behavior; the agent organizes evidence and measures agreement.

## Read the relevant reference

- Read [method.md](references/method.md) before defining labels, choosing splits, tuning, or interpreting a result.
- Read [kitaru-contracts.md](references/kitaru-contracts.md) before discovering operations, opening review, exporting records, running evaluations, or resuming jobs. It defines identity, provider semantics, and the local reporting contract.
- Read [visual-guidance.md](references/visual-guidance.md) when presenting a criterion, disagreement, split, or result. Ordinary prose and tables are a complete fallback.

Use [scripts/summarize_validation.py](scripts/summarize_validation.py) for count reports, following the input contract in `kitaru-contracts.md`. The helper reads local analysis records; it does not obtain labels, contact Kitaru, or run the evaluator.

## Start from the user's current evidence

Resolve the criterion, intended use, evaluator/version and selected result name, session population, existing investigation, and any saved analysis or job IDs. Infer these from a supplied handoff where possible. Ask only for a missing decision that changes the next action; do not make the user repeat setup or permission.

Re-read saved review and execution state before creating replacements. Prefer discovered MCP operations and use supported CLI operations where needed. Set `KITARU_ACTIVE_SKILL=kitaru-validate-evaluator` on Kitaru CLI commands and SDK scripts. Explain the content transfer, remote writes, and paid execution before obtaining any still-missing authorization. Keep credentials and raw traces out of committed files.

Preserve the chosen provider. TypeSafe/Jev is optional; use its released integration when selected and verify the installed contract. Another evaluator can enter this workflow directly. No sibling skill is required.

## Guide the next decision

1. **What should this check catch?** Inspect a real failure and valid counterexample. Confirm one criterion, its required evidence, exceptions, intended use, and the costlier mistake.
2. **Let's label a few cases.** Create or resume a criterion-specific investigation through existing Kitaru review. Explain that its session verdict judges only this criterion: `acceptable` is pass, `problematic` is fail, and `uncertain` is unresolved. Leave unreviewed cases unreviewed. Do not infer labels from free text or reuse broad quality verdicts without criterion-specific human confirmation.
3. **Here is where you disagree.** Run or retrieve the exact selected evaluation and compare it with saved human verdicts. Inspect one disagreement first. If none exists, show one agreement and the sample's limits; do not invent a disagreement. A small exploratory report is a useful stopping point.
4. **Can we improve it without teaching to the test?** Separate examples, development, and test cases before tuning. Make revisions using development evidence only. Keep related cases together and preserve the original reports.
5. **Let's check new cases once.** Freeze the configuration and acceptance criteria, obtain test labels under the frozen rubric, run the untouched test cases, and report counts and limitations. Human labeling alone does not contaminate a reserved test set. Using its contents or outcomes to revise the evaluator does.

One knowledgeable reviewer can supply the reference labels. Never change their label merely because the evaluator disagrees. Ask for a human decision when the rubric or reference label genuinely needs revision. Keep test examples and labels out of tuning context where possible, and disclose when isolation is procedural rather than enforced.

## Preserve accounting and a resumable checkpoint

Distinguish pass, fail, held, unavailable/error, missing evidence, uncertain human labels, and unreviewed cases. A provider error is not an agent failure; a held result is not a third human target label. Do not interpret an unset `passed` field without the evaluator's result contract. Stop an agreement claim if the required evidence, label meaning, or exact result identity is unresolved.

Keep a local, uncommitted analysis snapshot in an authorized location using the contracts reference. Kitaru verdicts remain mutable; the snapshot preserves what this report measured, not a product-enforced freeze. On resume, compare current labels, source timestamps, criterion, and configuration. Preserve an old report and create a new analysis revision when its inputs changed.

Finish with the criterion and intended use, exact investigation/cohort and evaluator/job/result identities, configuration, split membership, human-label coverage, count report, exclusions, isolation limits, and snapshot path. Name the next useful action and the claims the evidence cannot support. Do not turn agreement into probability calibration, production prevalence, deployment, or a new CI gate.

If the user wants to compare a changed agent, an available `kitaru-replay-experiment` skill can receive this checkpoint. That is an optional next task, with its own execution and tool-policy scope.
