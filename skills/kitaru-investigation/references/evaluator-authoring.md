# Evaluator authoring

Use this reference only after one observable behavior and exact cohort version have been accepted, or when the user supplies equivalent reviewed evidence directly.

## Confirm the capability card

Present this card before drafting code or a judge prompt:

```text
Capability: <one behavior being measured>
Example request or situation: <condition that requires it>
Initial conditions: <information, permissions, dependencies, and state available>
Required outcome: <independently observable success>
Evidence: <what establishes the outcome without trusting the agent's own account>
```

Reject or revise the capability when the agent could pass without exercising it, required information is absent, success is ambiguous, or the evidence measures only a dependency or infrastructure failure.

## Choose the evaluator mechanism

Prefer deterministic code for structural or rule-based criteria that can be checked objectively. It is cheaper, reproducible, and easier to explain.

Use an LLM judge only when the accepted criterion genuinely requires interpretation. Do not choose a judge merely because writing code is inconvenient.

A change from deterministic code to an LLM judge, or between materially different implementations, creates a new evaluator version with separate validation evidence.

## Draft one narrow binary rubric

Measure one observable criterion. Define `Pass` and `Fail` explicitly and allow materially equivalent successful behavior.

Use two to four reviewed examples with at least one example of each verdict. Explain every example with session or node evidence. Do not claim hidden intent or require the agent to copy a preferred tool sequence or reference wording.

Require structured evaluator output containing:

```json
{
  "reason": "short trace-grounded explanation",
  "verdict": "Pass or Fail"
}
```

Treat missing evidence, timeouts, credential failures, invalid judge output, and evaluator crashes as infrastructure errors rather than automatic negative scores for the agent.

## Confirm the exact rubric

Show:

- evaluator kind and implementation entrypoint;
- exact Pass definition;
- exact Fail definition;
- permitted equivalent behavior;
- required evidence and missing-evidence behavior;
- reviewed examples and their expected verdicts;
- cohort-version ID and accepted-behavior text;
- known limitations.

Present the confirmation compactly when possible:

| Field | Confirmed value |
|---|---|
| Evaluator kind | Deterministic or LLM judge |
| Pass | Exact definition |
| Fail | Exact definition |
| Equivalent behavior | Allowed alternatives |
| Evidence | Required trace or outcome evidence |
| Missing evidence | Infrastructure or unresolved behavior |
| Examples | Exact reviewed session references |
| Cohort | Exact cohort-version ID |

Ask the user to accept, edit, or reject this exact revision. Do not treat earlier agreement with a similar draft as acceptance, and never silently alter a confirmed rubric to improve later results.

## Implement and register

1. Scaffold a local evaluator file when code is required.
2. Implement the narrow criterion without unrelated framework or scoring machinery.
3. Test it locally against the selected reviewed examples.
4. Register a new immutable evaluator version. Use the CLI for local script upload; use MCP only when the implementation already exists as a server blob or exact package pin.
5. Re-read the registered evaluator and version.
6. Return the exact evaluator ID, evaluator-version ID, cohort-version ID, and accepted rubric revision in a checkpoint card.

Do not deploy the evaluator or change the agent automatically.

## Keep validation separately gated

A small blinded check may debug rubric alignment, but it does not establish production performance. Run it only when labels are withheld through a server-enforced boundary or a separate evaluation actor. Do not rely on labels stored beside traces on a filesystem the coding agent can read.

Production-quality LLM-judge validation requires:

1. disjoint training, development, and test session identities;
2. few-shot demonstrations drawn only from training data;
3. prompt iteration only against development results;
4. a frozen evaluator version before a one-time test run;
5. true-positive rate and true-negative rate reported separately;
6. the confusion matrix, raw disagreements, and infrastructure errors;
7. no development or test traces entering the prompt or discovery context.

Treat 30 to 50 Pass and 30 to 50 Fail examples in both development and test as a reliability target from the course method, not an MVP gate or universal law. Question rubric ambiguity and example quality before blaming human labels.

If label isolation is unavailable, stop at the immutable evaluator-version checkpoint and state that validation remains unproven.
