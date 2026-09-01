# Hosted tour operations

Use the installed Kitaru CLI schema and any native Kitaru MCP tool schemas as the authority. This reference records the command forms already verified for the bundled template. Do not rediscover them with help commands, source reads, speculative probe writes, or ad hoc Python scripts.

The hosted runtime contract is fixed: use `kitaru`, `/app/.venv/bin/python`, and `jq`. Never run `uv` or install packages. The project lock belongs to the public example and may not match the hosted server; the shared `/app/.venv` is the tour runtime.

## Keep the first read bounded

`prepareOnboardingRunner` already establishes the runner, selected cloud workspace, template directory, and worker. Do not repeat those checks unless its result reports a blocker.

Use the status returned by `prepareOnboardingRunner`; rerun it only when that result is missing, failed, or stale. Do not run separate version, adapter-import, provider-import, credential, or worker probes. Then make one targeted Kitaru state read:

1. Resolve the `returns-resolver` parent and exact version whose entrypoint and source identity match the bundled template.
2. Read only relevant active or completed imports and the sessions they produced.
3. Confirm that usable sessions belong to the resolved version and retain full trace payloads.

Do not list all workspace resources as a substitute for this targeted read. Do not run discovery loops that try several speculative commands. If a verified form fails because the installed version rejects it, inspect that command's installed help once. If the correction is not clear from that one help result, stop and report the exact command and error rather than creating probe objects.

## Choose the transport

Prefer a native Kitaru MCP tool when the hosted agent exposes a suitable bounded operation. Otherwise use the CLI through `runOnboardingCommand`. Do not use direct REST calls or raw database access.

For CLI calls, request structured JSON and non-interactive behavior only when the installed command exposes those flags. Keep each command bounded and return only the fields needed for the next decision.

| Need | CLI family | Native MCP family |
|---|---|---|
| Selected server and worker | `kitaru status` | bounded registry/activity read |
| Agent and version | `kitaru agent get`; `kitaru agent version get` | `kitaru_registry_read` |
| Sessions and nodes | `kitaru session list`; `kitaru session get`; `kitaru session nodes SESSION_ID --include-payloads` | `kitaru_activity_read` |
| Annotations and investigation | `kitaru annotation`; `kitaru investigation` | `kitaru_review_read`; `kitaru_review_manage` |
| Cohort and evaluator | `kitaru cohort`; `kitaru evaluator`; `kitaru session evaluate` | cohort, registry, and workflow tools |
| Experiment | `kitaru experiment`; `kitaru experiment run` | experiment and workflow tools |

Use exact IDs once resolved. Never retry a write until a read proves it did not land.

## Use the bundled-template forms

Run these from `/opt/kitaru/examples/python/pydantic_ai_ticket_resolver`. The runner supplies the active Kitaru connection. Use `kitaru`. Replace the identity placeholders with the resolved route; keep the template runtime arguments unchanged:

- `PARENT_NAME` is `returns-resolver` only when absent or source-matched. After a collision, use the user-approved distinct demo name throughout registration and all later operations.
- `AGENT_ID` is that parent's returned UUID. Use it for parent-scoped reads, investigations, and navigation.
- `AGENT_VERSION_REF` is the source-matched version's exact `PARENT_NAME@INTEGER` reference. Retain its returned UUID too; do not assume version 1 or use a version UUID where the CLI requires this reference.

```text
kitaru status
kitaru agent get PARENT_NAME
kitaru session list --agent AGENT_ID --tag returns-baseline --origin imported --size 20 -o json
```

Kitaru 0.23.0 does not expose `--include-payloads` on `session list`. After the user returns from the required sessions-page handoff, select the three candidate session IDs from the retained bounded JSON listing, then request payloads only for their nodes:

```text
kitaru session nodes SESSION_ID --include-payloads -o json
```

For an absent template agent, the one approved setup write is the documented registration followed by this import:

```text
kitaru agent register PARENT_NAME --command "/app/.venv/bin/python -m returns_agent.agent" --description "Resolve one synthetic returns or delivery request, execute one mock action, and draft the customer reply." --display-version baseline-v1 --working-dir . --timeout-seconds 180 --tool lookup_order --tool get_return_policy --tool check_shipping --tool issue_refund --tool create_replacement --tool escalate_to_human -o json

kitaru session import traces/langfuse-traces.jsonl --importer kitaru/langfuse@latest --agent AGENT_VERSION_REF --tag returns-baseline --params '{"source_instance":"kitaru-quickstart-example"}' --media-type application/x-ndjson --wait
```

Read the registration receipt before constructing the import command. After the import receipt reports ten created sessions and no failures, do exactly one filtered session listing. The `--agent` filter is parent-scoped: keep only sessions belonging to the retained agent-version UUID and matching import provenance. Do not inspect any nodes or fixtures in this turn. Navigate to the sessions page and end the turn. Apply the same boundary when the first durable-state read establishes a reusable population. Only after the user returns may you select candidates from the retained session metadata and read full nodes and payloads for the three chosen sessions; do not repeat the population listing.

For ordinary agent observations, `--value` and `--selector` are JSON values. JSON-encode the text and selector rather than hand-escaping an inline shell command:

```text
kitaru annotation create --session SESSION_ID --selector '{"node_id":"NODE_ID"}' --value '"Agent observation: Concise, trace-grounded evidence."'
```

Create one real investigation with a machine-safe name. Each question belongs to its exact session UUID and each highlight is JSON:

```text
kitaru investigation create returns-baseline-review --agent AGENT_ID --session SESSION_ID --session-question 'SESSION_ID:acceptability=Direct question grounded in this session.' --session-highlights 'SESSION_ID:acceptability=[{"selector":{"node_id":"NODE_ID"},"description":"What this evidence shows."}]' -o json
```

Repeat the three session options for each of the other selected sessions in the same create command. For this CLI path, keep each teaching question within 220 characters and use one highlight per question with a description within 60 characters. Use the compact questions in the tour-method reference after confirming their facts. Put additional explanation in the separately approved ordinary annotations, not in the command. Omit the optional investigation description.

Keep the complete command within `runOnboardingCommand`'s 2,000-character bound, including actual IDs, JSON, spaces, and shell quoting. Shorten wording if necessary without dropping the rule, material evidence, expected verdict, or invitation to disagree. Do not split the investigation into three objects, write temporary payload scripts, or retry an oversized command unchanged. Retain the returned investigation ID and use its product-owned review link when present.

Before a cohort or evaluator write, read the exact investigation and verify complete verdict coverage. The user’s verdicts establish the behavior; optional written answers do not substitute for verdicts.

For a custom evaluator, use the installed result contract. Every return must contain a stable `name` and either `score` or `value`; `details` is not a valid field. Write the complete source once with `writeOnboardingEvaluator`. Never inline evaluator source in `runOnboardingCommand`, use a shell heredoc, or append it in chunks. This avoids the command tool's deliberate 2,000-character input bound.

```python
from kitaru.task.evaluator import EvaluationResult

return EvaluationResult(
    name="accepted_behavior",
    score=passed,
    passed=passed,
    explanation="Short explanation grounded in recorded trace evidence.",
)
```

Test the final local evaluator once with `kitaru evaluator test .kitaru-onboarding/evaluators/evaluator.py --entrypoint evaluate` before creating its first remote version. Test its actual reviewed pass, fail, missing, and malformed-evidence behavior locally, not only the load-and-signature command. Only after all four pass, create one cohort from the confirmed reviewed session IDs and register exactly one evaluator version. Do not create a provisional version and do not use `kitaru evaluator version register` to repair the first version: Kitaru 0.23.0 has a known `idempotency_key` bug on that path. Run that exact version once over the same resolved agent's imported `returns-baseline` population, account for completed, failed, and missing results, then navigate to the evaluator page and wait for the user to inspect the results.

## Identify matching durable state

A matching template route requires more than the parent name:

- the exact agent version points to the bundled template entrypoint and source identity;
- import provenance points to the checked-in trace file or the known import job;
- sessions belong to that exact version and have complete trace payloads.

A same-name parent without this proof is a collision, not a match.

For downstream recovery, follow relationships outward from the exact session set. A unique investigation with the same ordered sessions and prepared questions can be offered for resumption. A unique cohort version containing the human-reviewed members and evaluator version scoped to the same agent can be resumed. When uniqueness or ownership is unclear, ask rather than choosing by recency or name.

## Keep observations separate from verdicts

Create prepared observations as ordinary annotations. Start each value with `Agent observation:` and anchor it to the smallest useful node or payload field. Before creation, list that session's annotations and reuse an exact selector-plus-value match.

Do not create an investigation answer for the reviewer. The user supplies the whole-session verdict in the frontend; a written answer remains optional.

## Open product pages

Prefer links returned by Kitaru. Otherwise use the verified dashboard URL with exact IDs and these compatibility routes:

```text
DASHBOARD_URL/agents/AGENT_ID/sessions
DASHBOARD_URL/agents/AGENT_ID/investigations/INVESTIGATION_ID/review
DASHBOARD_URL/agents/AGENT_ID/cohorts/COHORT_ID/sessions
DASHBOARD_URL/evaluators/EVALUATOR_ID
DASHBOARD_URL/experiments/EXPERIMENT_ID?run=RUN_NUMBER
```

Pass the workspace-relative suffix to `navigateKitaruUi`; do not expose the dashboard host or construct a different workspace URL in chat.

Use product navigation only at these checkpoints: imported or reused sessions, investigation review, evaluator with baseline results, and completed experiment run. One navigation call is one handoff, followed by a wait for the user to return. The sessions-page navigation must end its turn: navigation is applied after the assistant turn finishes, and selecting evidence, reading payloads, preparing review material, or navigating again before the user returns would skip the recorded-population lesson.

## Replay boundary

Hand the exact accepted behavior, cohort version, evaluator version, parent and candidate agent-version IDs, prompt override, and explicit tool policy to `kitaru-replay-experiment`.

The hosted template uses deterministic local tools against a fresh in-memory store. Let the replay skill verify adapter support and the appropriate policy. It owns the concise run preview, approval, creation, execution, and result interpretation.

Pass these resolved reference forms to the replay skill so it does not rediscover them:

- agent versions use `PARENT@INTEGER`, for example `returns-resolver@1`, never an agent-version UUID;
- cohort and evaluator inputs use the exact immutable version identifiers returned when they were created;
- retain the experiment ID returned by creation and reuse it for start and polling;
- poll the run no more often than once after 45 seconds and once after another 60 seconds.

Before asking for paid replay approval, prove the run specification uses `/app/.venv/bin/python -m returns_agent.agent`. The runner readiness result already proves that interpreter imports the adapter. If an older resumed version uses plain `python` or `uv run`, create a corrected immutable agent version as part of the approved replay setup and use its `PARENT@INTEGER` reference. Never start a replay after a runtime probe has failed.
