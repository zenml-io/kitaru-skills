# Kitaru evidence and reporting

## Discover capabilities

Prefer native MCP; use the structured CLI for local files, waiting, or operations MCP does not expose. Inspect discovered tool schemas and `kitaru schema` or command help before constructing calls. Use exact IDs. Set `KITARU_ACTIVE_SKILL=kitaru-validate-evaluator` for Kitaru CLI and SDK calls. Use `--output json --machine --non-interactive --no-browser` where supported. Preserve existing authorization; explain any newly proposed remote writes, provider data transfer, or paid execution before requesting missing permission.

This workflow uses released Kitaru investigation and evaluation operations. Check the user's installed capabilities and worker packages; give setup or upgrade guidance when missing. A missing operation is not permission to bypass it with direct REST or invent a local substitute for product state.

| Operation | CLI route to inspect | MCP route to discover |
|---|---|---|
| Read investigation and all linked sessions | `investigation get`, `investigation session list` | `kitaru_review_read`: `get`, `list_sessions` |
| Create fixed review worklist | `investigation create` with repeated `--session` and `--session-question` | `kitaru_review_manage`: `create_investigation` |
| Read exact evaluator/version and scope | `evaluator get`, `evaluator version get` | `kitaru_evaluators_read` |
| Evaluate selected sessions | `session evaluate` with exact `--evaluator` and params, optionally `--wait` | `kitaru_workflow_start`: `evaluation` |
| Recover a run and its results | `job get --tasks`, `job watch`, `evaluation list`, `evaluation get` | `kitaru_activity_read` |

Follow pagination to exhaustion within the selected investigation or job, not across the workspace. MCP creation accepts at most 100 investigation sessions; evaluation starts accept at most 100 session/evaluator pairs. For larger rounds, identify each batch explicitly. Every evaluation batch must belong to one agent. Verify evaluator parent scope matches that agent or has a trusted deliberately global origin; a null scope alone does not establish global intent.

## Human review and label snapshot

Use one criterion per investigation. Repeat its exact wording and exceptions in the review question for each session. Prefer separate development and test investigations for clarity, but check both session IDs and related-case groups across them. Different investigation IDs do not prove disjoint data. Worklists and questions are fixed at creation; later rounds need new investigations, not an append operation.

Use `links.review` returned by structured investigation creation. If absent, reuse the verified `dashboard_url` and the compatibility route `DASHBOARD_URL/agents/AGENT_ID/investigations/INVESTIGATION_ID/review`. Do not put trace text into URLs. If no working review route exists, preserve the investigation and report the broken handoff. Do not build another annotation UI or automate the human's verdicts.

Read the investigation-session verdict, not a free-text annotation or an unrelated whole-session quality judgment:

- `acceptable` becomes `pass` for this criterion.
- `problematic` becomes `fail` for this criterion.
- `uncertain` stays separate.
- Null becomes `unreviewed`.

Notes can explain a label but cannot silently replace it. Multiple question answers are possible and are not independent votes. Session verdicts can be changed or cleared; their response has an update timestamp, but no verdict revision history or reviewer identity. A completed investigation is not locked. If a user asks to correct a verdict, verify the exact investigation and session and preserve the old analysis snapshot before an authorized update.

Before comparison, save the accepted criterion and review values into a local analysis snapshot. This is a declared measurement input, not a frozen Kitaru dataset or alternate source of labels. Store it outside version control in the user's analysis location, with identifiers and minimal metadata rather than trace bodies or credentials. Also retain a compact run note: intended use, eligibility rules, split rationale, acceptance targets, source retrieval time, exact agent/evaluator/package/model identities, returned model identity where available, and whether test material has entered tuning context. The helper schema below holds machine-checkable inputs; the note holds decisions it cannot verify.

On resume, re-read the source labels and configuration and compare them with the saved inputs before presenting an old report as current. Preserve the historical report if anything changed. A timestamp change warrants inspection, even if the verdict is unchanged. The helper's baseline check can detect changed normalized inputs; it does not fetch or authenticate the source.

## Match the selected run

Record the job receipt immediately and recover that job after a timeout before considering a replacement. `session evaluate --wait` provides a terminal receipt with expected session/version task pairs, task results, and errors. A wait timeout does not prove the job failed. Reuse an idempotency key when the installed start operation supports it and a retry belongs to the same logical request.

Join **chosen job → its tasks → evaluation rows → selected session and result name**. Verify evaluator version and full params as well. The terminal task results help inspect outcomes; retrieve persisted evaluations by those task IDs for stable result IDs. A plugin can emit several named results. Select exactly the result implementing this criterion, and reject multiple matching rows rather than choosing the latest. If complete provenance cannot be obtained, stop the comparable-result claim and explain the missing contract.

Normalize outcomes in this order:

1. Failed or canceled task: `error`, keeping its reason in the run note. Do not use a partial result as successful evidence.
2. Completed task without the expected named row: `missing`. Pending work is also `missing` in a clearly provisional report, never a finished test.
3. Provider-specific unavailable sentinel: `unavailable`.
4. Explicit binary `passed` value: `pass` or `fail`.
5. A documented abstention from a configured binary evaluator: `held`.

An unset `passed` value is not sufficient evidence of abstention: descriptive scores and unconfigured verdict policies can also leave it null. Establish a valid binary decision rule before normalizing those outputs. Never manufacture that rule from final-test results. Eligibility exclusions require a recorded reason independent of judge agreement. Missing evidence may justify exclusion under the accepted policy; a provider error or inconvenient disagreement does not.

## TypeSafe judge

Use the released `kitaru-typesafe-evaluator` package, entrypoint `kitaru_typesafe_evaluator.judge:judge`. It is optional and must be installed on the selected worker and registered with the matching connection schema. Inspect the installed evaluator catalog and schema before configuring it. Follow the version-matched [judge evaluations guide](https://docs.zenml.io/kitaru/guides/judge-evaluations) for setup. Inspect and reuse a compatible existing TypeSafe connection. If a new one is needed, create it without changing the provider default and select it for this run with `--evaluator-connection EVALUATOR@VERSION=CONNECTION`. Change a workspace-wide default only with explicit authorization for that broader effect. Supply keys through a connection or worker environment, never params or snapshots. Configure connections before creating the job because connection selection is snapshotted then.

Pin the package, evaluator version, requested model, full params, and actual returned model identity. Select one named question per validation report. For Noul, put the boundary, exceptions, and any prompt examples in `instructions`; Kitaru's Noul params reject `criteria`. Retain only the necessary state fields. `outcome` includes `request`, `tool_calls`, and `final_answer`; `full` also includes `system_prompt` and `model_messages`. Top-level `include` selection does not redact retained content or guarantee that the recording has enough evidence.

Noul's raw score is always `p(yes)`. With `pass_when: "no"`, a low raw score supports passing. Prefer the stored `passed` result over recomputing it. For development-only threshold exploration, convert to good-answer probability `g = p(yes)` for `"yes"`, or `g = 1 - p(yes)` for `"no"`. At `decisive_at = d`, pass when `g >= d`, fail when `g <= 1 - d`, and hold between them. The default `d = 0.8` is not task validation. This policy is symmetric; do not present an arbitrary single threshold as equivalent. A missing `pass_when` is descriptive, not a held binary judgment.

Oversize input returns `value: "unavailable"`; invalid credentials and API failures can fail the task. Check these before interpreting unset `passed`. Missing tool evidence does not automatically cause a hold. The explanation contains model identity and a threshold statement, not generated reasoning. A `choice` confidence is distribution concentration, not measured correctness; `score` produces an ordinal position rather than a pass/fail judgment. Use Noul for the binary workflow unless a different explicit decision contract is established.

## Reporting helper input

Run the bundled standard-library helper with the user's Python interpreter (or `uv run --no-project python` if uv is their tool):

```bash
python /absolute/path/to/kitaru-validate-evaluator/scripts/summarize_validation.py snapshot.json
python /absolute/path/to/kitaru-validate-evaluator/scripts/summarize_validation.py refreshed.json --baseline snapshot.json
```

Resolve the helper path from this installed skill directory. It reads JSON and emits JSON to stdout, without contacting Kitaru or writing source state. Capture its exit code and output. On drift it reports changed paths and exits 2 without new counts; investigate the changes and create a deliberate analysis revision rather than dropping the baseline to bypass the check.

The input is a normalized export, not the raw Kitaru response. Use these exact top-level fields:

- `schema_version`: integer `1`.
- `criterion`: object containing nonempty `id`, `revision`, and `text` strings.
- `evaluator`: object containing `version_id`, `result_name`, and the complete `params` object.
- `selected_session_ids`: every selected session ID, once.
- `records`: exactly one record for each selected ID, including unresolved and excluded cases.

Each record contains `session_id`, `group_id` (shared by related cases), `split` (`examples`, `development`, or `test`), `investigation_id`, `investigation_session_id`, `human_label` (`pass`, `fail`, `uncertain`, or `unreviewed`), `label_updated_at`, `exclusion_reason` (null or a nonempty reason), and `evaluation`.

An evaluation contains `job_id`, `task_id`, `evaluator_version_id`, `result_name`, full `params`, `outcome` (`pass`, `fail`, `held`, `unavailable`, `error`, or `missing`), and `result_id`. Result IDs are required for pass/fail/held/unavailable, and null for error/missing. These IDs describe the selected source run, not identifiers the agent invents to satisfy validation. Null evaluation is permitted only for excluded or unresolved human labels. If an eligible case has no identifiable task, preserve it in the source worklist and resolve the run's missing task provenance before making this report.

The helper rejects duplicate or missing selected IDs, overlapping related groups across splits, and mismatched evaluator configuration. It validates the normalized records, not the accuracy of their extraction or whether all source pages were fetched. Reconcile the selected count with Kitaru before running it.

Excluded records take precedence in the summary, followed by uncertain/unreviewed labels; all remaining records enter their human pass/fail row. Thus every selected case appears once in cohort accounting. The source records retain labels and reasons for inspection. See [visual-guidance.md](visual-guidance.md) for presenting the output without dumping JSON.
