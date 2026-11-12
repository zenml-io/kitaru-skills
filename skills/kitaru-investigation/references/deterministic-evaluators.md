# Installed evaluator selection

Use the installed Kitaru evaluator catalog as the authority. Re-read it before selection because available evaluators and versions can change.

## Start with descriptive evidence

First resolve the cohort's exact agent ID, then list the installed evaluators and exact versions through the current registry operation. Keep evaluators scoped to that agent and verified global evaluators. A null `agent_id` is necessary but not sufficient evidence of deliberate global scope because deleting a scoped evaluator's agent also clears that field. Accept a null-scoped parent only when a trusted creation record or known default-catalog identity establishes that it was deliberately global, or after revalidating its criterion, implementation, and intended reuse for the cohort's agent. If portability cannot be established, exclude it and create a new agent-scoped parent. Do not try an evaluator scoped to another agent or a name from this reference until the server returns an eligible match. Then run only the descriptive evaluators relevant to the accepted behavior on a small selected set. Current default installations may expose version-1 bundles such as:

| Evaluator | Useful evidence |
|---|---|
| `kitaru/session-diagnostics@1` | Session and payload completeness signals |
| `kitaru/trajectory-signals@1` | Loops, retries, and trajectory shape |
| `kitaru/tool-health@1` | Tool calls, errors, and tool-use signals |
| `kitaru/timing-profile@1` | Timing and latency evidence |
| `kitaru/llm-call-signals@1` | Model-call and token-related signals |

Default installations also register three basic evaluators: `kitaru/cost@1` (total recorded session cost), `kitaru/latency@1` (session wall-clock duration), and `kitaru/tool-call-patterns@1` (repeated calls to the same tool).

These results describe recorded behavior. A retry, slow span, tool error, or missing payload is not automatically an agent-quality failure.

## Prefer an installed configured rule

Check whether an evaluator returned by the installed catalog directly expresses the accepted criterion. Current default installations may expose configured rules such as:

| Evaluator | Use when the accepted criterion concerns |
|---|---|
| `kitaru/output-contract@1` | Required or forbidden output shape or content |
| `kitaru/resource-budget@1` | Cost, token, call, or latency limits |
| `kitaru/tool-policy@1` | Required or forbidden tools, per-tool call limits, or numeric limits on recorded tool inputs or outputs |
| `kitaru/model-policy@1` | Required or forbidden model use |
| `kitaru/workflow-conformance@1` | Contractual workflow steps or ordering |

Configured rules fail on a recorded violation and pass only for a terminal session whose required evidence is complete. Insufficient evidence leaves `passed` unset: report that HOLD separately, never as a pass, and keep it out of pass rates.

Check `numeric_rules` on `tool-policy` (Kitaru 0.27.4 or later) before writing custom code for a numeric limit such as a refund ceiling. Each named rule selects an exact `tool_name`, a `source` of `inputs` or `outputs`, an RFC 6901 `path`, an `operator` (`lt`, `lte`, `gt`, or `gte`), and a fixed decimal `limit`. An optional `when` compares a Boolean at another pointer on the same call, for example `{"source":"outputs","path":"/accepted","equals":true}`. Every matching call is checked, and each rule emits a result named `numeric_rule.NAME`. A missing pointer, unreadable value, unavailable output, or no matching call produces HOLD. A rule does not sum calls, compare fields across calls, convert units, or take its limit from another tool; use custom code for those criteria. Verify the installed version's params schema before relying on these fields.

Pin the exact evaluator version and parameters. Evaluator-produced rows preserve both, and replay `if_missing` reuse requires the session, version, and parameters to match. The builtin deterministic evaluator scale contract does not emit input or configuration SHA result rows. Reuse relevant cost, timing, resource, model, and tool-policy results as replay protections instead of recreating them.

Interpret each builtin float result according to its named metric. Coverage metrics count available observations; finding and policy metrics count detected problems; resource budgets report observed use against the configured ceiling. The score is a literal per-session numerator with `min_score=0` and `max_score` as the honest opportunity total when one exists. Higher is better for coverage, while lower is better for failures, violations, and other findings; `passed` remains a separate verdict. Do not invent a maximum for an unbounded count, and keep genuinely multidimensional evidence as a string or categorical value instead of forcing it into one score. Session-specific maxima may differ, in which case a run aggregate keeps its raw-score statistics but returns a null aggregate `max_score`.

For an interpretive criterion, check for a suitable registered [TypeSafe judge](typesafe-evaluator.md) before proposing custom code. It is an optional provider-backed package, not a default evaluator or a deterministic rule. Verify its scope, package version, params contract, credentials, and permission to send the required evidence before using it.

Do not force a deterministic configured evaluator to stand in for an interpretive outcome. Exact tool order is appropriate when the order is contractual, not merely because one successful trace used it.

## Return a compact checkpoint

For an installed match, run it and return:

- accepted behavior and exact cohort-version ID;
- exact evaluator and evaluator-version IDs plus the evaluator parent's agent scope and, for a null scope, the evidence that established deliberate global portability;
- exact parameters;
- descriptive evidence used to choose it;
- missing evidence and infrastructure failures;
- intended use and claim limit.

Do not require custom authoring or reviewed Pass and Fail examples when an explicit deterministic rule already expresses the accepted meaning. Continue to custom authoring only when no installed evaluator fits.
