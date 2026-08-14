---
name: kitaru-replay-experiment
description: Run and interpret one safe, bounded Kitaru replay comparison against an accepted cohort and exact evaluators. Use when a user wants to replay a cohort, test or compare a model, prompt, system prompt, parameter, agent version, or tool policy, supervise an experiment run, determine whether one candidate helped, or ask for one bounded change worth testing.
---

# Kitaru replay experiment

Test one candidate condition against known cases and explain whether the available evidence improved, regressed, traded off, or stayed inconclusive. Do not make the deployment decision.

## Core contract

- Start from an accepted behavior, exact cohort version, exact evaluator versions and parameters, and one candidate change. Suggest one bounded candidate only when asked.
- Replay starts a fresh agent task from each historical session's stored top-level inputs after applying the override. It does not restore an arbitrary checkpoint, conversation, process memory, adapter instance state, filesystem, or external world state.
- Resolve adapter support and its construction path before showing an actionable run card. A shared replay schema does not prove that an adapter supports a requested override or tool source.
- Require an explicit tool policy for every tool-using run. Omission resolves to live passthrough on the current server and is unsafe as an implicit default.
- Carry exact IDs, versions, evaluator parameters, run-spec evidence, tool policy, failures, and missing results forward.
- Explain remote writes, model and worker compute, cost uncertainty, and possible live effects before execution. One complete run-card approval covers the experiment create and run start; any live-tool path needs separate approval.
- Prefer native Kitaru MCP operations. Use the structured CLI for built-in waiting or another capability MCP does not expose. Verify installed schemas when they differ from the references.
- Never bypass a missing adapter, evidence, comparison, or product contract with direct REST calls or ad hoc local state.

## Load references only when needed

- Read [references/experiment-contract.md](references/experiment-contract.md) before any Kitaru operation or adapter capability claim.
- Read [references/experiment-method.md](references/experiment-method.md) before choosing the comparison type, interpreting conflicting results, adding repeats, or evaluating a user-defined gate.

## Resolve the starting state

Begin read-only. Reuse exact identifiers from an investigation checkpoint or the user's request, then re-read each object.

Resolve:

1. the accepted behavior and intended use: exploration, known-case regression, or an exact user-defined gate;
2. the exact cohort-version ID and ordered case count;
3. one exact candidate agent-version ID and the current public run spec and capabilities;
4. exact evaluator-version IDs, parameters, and factual evidence about their checks and limitations;
5. one proposed replay override and its expected effect;
6. the adapter and construction path;
7. every tool the candidate may invoke and one explicit policy covering all of them.

Route to `kitaru-investigation` when no behavior or cohort has been accepted. Use its evaluator route when no suitable evaluator exists or when the current evaluator is too weak for the intended claim. Offer a claim downgrade instead of forcing validation ceremony when the user only needs an exploratory result.

If an experiment or run already exists, re-read it and resume supervision or interpretation. Experiment configuration freezes after it has runs, so create a new experiment for a materially changed candidate, evaluator set, override, or tool policy.

## Preflight capability and safety

Reject unsupported adapter conditions before approval or paid execution. Return the exact blocker and smallest supported alternative. Do not let a user approve past an unresolved adapter or construction path.

For tool-using agents:

- Prefer baseline-scoped recorded history when it can answer the hypothesis and the adapter supports it.
- Use `fail` or `error_result` on a history or static miss unless live execution is deliberate.
- Treat `on_miss=passthrough` as live passthrough and gate it separately.
- Warn that cohort-wide or agent-wide history can borrow stale or cross-case state. Matching uses tool name and canonical JSON arguments, then selects the latest match in scope.
- Treat LLM-generated results as a synthetic condition, not restoration of the historical external world.
- Keep tool execution failures separate from agent-quality failures.

Check whether repeated calls with identical arguments can legitimately return different values. Baseline scope is the narrowest history source, not proof that a stored result remains faithful.

## Show one run card

Prefill this compact execution checksum. Do not turn it into an experiment-design questionnaire.

| Field | Content |
|---|---|
| Question | Expected effect of the candidate |
| Intended use | Exploration, known-case regression, or exact user-defined gate |
| Comparison | Historical observed vs candidate, fresh control vs candidate, or reproduction check |
| Cohort | Exact cohort-version ID and case count |
| Candidate | Exact agent-version ID plus current run-spec and capabilities fingerprints |
| Fresh control | When used, exact version, fingerprints, conditions, IDs, and known differences |
| Starts from | Stored top-level inputs plus exact overrides |
| State restored | Explicit list of what is and is not restored |
| Evaluators | Exact versions and parameters, one primary outcome, and at most two necessary protections |
| Tool source | Full policy, history scope, `on_miss`, synthetic source, and possible live effects |
| Adapter support | Verified adapter, construction path, and supported requested operations |
| Expected work | Session count, likely model and tool work, and cost uncertainty |
| Claim limit | What this comparison can and cannot establish |

Fingerprint the complete public run-spec and capabilities models using canonical serialization. Do not resolve or expose secrets. Immediately before experiment creation and again before starting execution, re-read both models and compare their fingerprints. If either changed, invalidate approval and show the changed condition. An exact agent-version ID identifies a mutable configuration, not an immutable reproducible artifact, and these checks cannot freeze or prove the configuration a worker later resolves. For a user-defined gate or live-effect run, require immutable runtime identity or narrow the use to exploration. Without that identity, report observed violations but return `cannot evaluate` for the gate. For an exploratory run, preserve the approved fingerprints, re-read them after settlement, and return `inconclusive` if observable drift occurred.

Ask for one approval after the complete card is visible. If the policy includes passthrough, ask separately for approval of the named live tools and effects.

## Create and supervise one run

After approval:

1. Create one experiment with the exact agent parent, replay override, explicit tool policy, and evaluator versions and parameters.
2. Re-read it and verify that the server resolved the intended configuration.
3. Recheck the candidate run-spec and capabilities fingerprints.
4. Start one run against the exact cohort version and candidate agent version. Set `evaluate_baselines=true` for comparative claims.
5. Watch the asynchronous run until it completes, fails, is canceled, reaches an agreed stop condition, or the local wait times out.
6. Read the run and all paginated replay jobs needed to account for completed, failed, canceled, and missing cases.
7. Re-read the candidate run spec and capabilities after settlement. Report any observed drift and the residual risk that a transient mutation could not be detected.

Run once by default. Add predeclared matched repetitions only when stochasticity could reverse a consequential or borderline conclusion, and approve the extra work and cost first.

Cancel only when the user asks or an approved stop condition is met. Cancellation preserves evidence. Deletion is destructive and is not cancellation.

## Read exact evidence

For each case, resolve evaluation results tied to the expected evaluator-version ID. Verify evaluator parameters or deterministic configuration hashes where available. Decline a decision-grade parameterized baseline comparison when the parameters of an existing result cannot be established.

Do not use the current UI aggregate as a decision-grade source. Read exact per-session evidence and show raw counts, denominators, failed, canceled, and missing cases beside every rate. Failed, canceled, and missing results remain outside the quality denominator.

Check candidate prompts, evaluator prompts, examples, tool fixtures, history scopes, and related trace families for leakage. Warn for exploration. Require resolution or narrow the claim only when the intended use is consequential.

## Return the result card

Report:

- exact experiment and run IDs, cohort version, candidate version, evaluator versions and parameters, tool policy, and run-spec evidence;
- comparison type and the state that was and was not restored;
- improved, regressed, unchanged, failed, canceled, and missing case counts, plus pending or evaluating counts for nonterminal runs;
- important paired case changes and protection outcomes;
- evaluator limitations, provenance gaps, and known execution differences;
- one conclusion: `improved`, `regressed`, `trade-off`, or `inconclusive`;
- only when the user supplied a fit-for-purpose gate: `meets`, `does not meet`, or `cannot evaluate` that exact gate;
- one next useful action.

Do not say `ship`. The user owns deployment. Kitaru does not currently expose a public winner, release policy, statistical significance, or CI-exit verdict.

If a run stalls, fails, is canceled, or remains partial, return its exact current state, completed, failed, canceled, missing, pending, and evaluating counts, resumable identifiers, and the smallest safe next action. Keep canceled cases outside quality denominators rather than folding them into failed or missing cases. If replay exposes a genuinely new or ambiguous behavior, hand exact session evidence to a bounded follow-up `kitaru-investigation` instead of silently changing the evaluator.

## Suggest one candidate when asked

Prefer, in order:

1. clarify an ambiguous instruction or tool description;
2. add one small non-leaking example or deterministic protection;
3. change one pipeline component or model setting;
4. consider a larger structural or model change after simpler interventions fail.

Do not start an automatic prompt search, cascade, fine-tuning program, or multi-candidate tournament.
