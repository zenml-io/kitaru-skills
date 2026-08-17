# Kitaru tour operations

Use this reference before reading or mutating Kitaru state. Inspect the installed CLI schema and discovered MCP tool schemas first; they are authoritative when they differ from this reference.

## Choose a transport

Prefer native Kitaru MCP for bounded reads and writes it exposes in `standard` or `destructive` mode. CLI-only use remains supported. Use the structured CLI for local trace files, built-in waiting, local evaluator code, or investigation creation when it can return the product-owned frontend link.

For agent-facing CLI calls, use `--output json --machine --non-interactive --no-browser` when the installed command exposes those flags. Preserve structured results and exact IDs. Do not use direct REST calls to bypass a missing CLI or MCP operation.

## Prepare CLI and MCP

After the template checkout is verified, inspect the project prerequisites, the active environment, and discovered native Kitaru MCP tools.

- Follow the verified template README's frozen environment command when the project environment is missing. Explain that this installs the project-local Kitaru CLI and ask before changing the environment. Use the README's `uv run kitaru ...` form afterward.
- Treat MCP as preferred, not required. If suitable MCP tools are already configured, use them for bounded operations. If they are absent, say once that the guided tour can continue through the project-local CLI and proceed.
- When the user asks to install MCP, or the CLI cannot complete the next operation, follow the official host-specific Kitaru MCP setup. Explain and ask before installing packages or changing host configuration. Preserve the current checkpoint because the coding-agent host may need a restart before it discovers the new server.
- Do not install or reconfigure MCP solely to replace a working CLI during the short tour. Offer MCP setup after the AHA when it would improve the user's ongoing Kitaru workflow.

## Operation map

| Need | Structured CLI | Native MCP |
|---|---|---|
| Check selected workspace and worker | `kitaru status`; diagnose with `kitaru doctor` | Use available bounded registry and activity reads |
| Resolve agent/version | `kitaru agent get`; `kitaru agent version get` | `kitaru_registry_read` |
| Read sessions and complete nodes | `kitaru session list`; `kitaru session get`; `kitaru session nodes --include-payloads` | `kitaru_activity_read` session and children |
| Run descriptive evaluators | `kitaru session evaluate ... --wait`; inspect with `kitaru evaluation list` | `kitaru_workflow_start` and bounded activity reads |
| Create ordinary annotation | `kitaru annotation create --session SESSION --value JSON [--selector JSON]` | `kitaru_review_manage`, `create_annotation` |
| List annotations | `kitaru annotation list` with a session filter | `kitaru_review_read`, `list` annotations |
| Create fixed investigation | `kitaru investigation create` with repeated session, question, and highlight options | `kitaru_review_manage`, `create_investigation` |
| Read investigation and worklist | `kitaru investigation get`; `kitaru investigation session list` | `kitaru_review_read` |
| Create cohort/version | `kitaru cohort create`; `kitaru cohort version create` | `kitaru_cohorts_manage` |
| Check and register evaluators | `kitaru evaluator list`; `scaffold`; `test`; `register` | Registry reads; writes require the appropriate evaluator tool and existing script blob |
| Evaluate baseline sessions | `kitaru session evaluate ... --wait` | `kitaru_workflow_start`, evaluation |

Inspect exact argument names before constructing commands. Prefer exact IDs and versions over display names.

If both `kitaru status` and `kitaru doctor` fail before returning a structured selected-workspace result, do not inspect credential files or guess at server state. Verify the installed CLI version, explain that Kitaru's current local state is unreadable, and return to the canonical template README's current local-workspace selection command as the recovery path. Treat that command as a state-changing setup action covered by the tour's combined approval. Re-run `status` afterward before registration or import.

## Keep prepared notes separate from verdicts

Create tour observations as ordinary annotations using a session ID, optional selector, and string value. They remain visible on the session independently of the investigation.

Do not create an investigation-answer annotation for the reviewer. An investigation answer carries an investigation-session ID and question key, starts a pending investigation, and appears as the answer to that question. The guided tour leaves that optional field to the human and relies on the separately stored whole-session verdict.

Current annotations record an owning account but no typed human, agent, or suggestion provenance. Keep the durable `Agent observation:` prefix. Explain its meaning once in chat and move on.

Before retrying annotation creation, list existing manual annotations for the session and compare selector plus value. General write idempotency is not guaranteed.

## Create and open the review

Every investigation session needs one non-empty question list. Supply one question with one primary highlight for each selected session. Use the question's highlight selector to place the prompt beside its key evidence.

Resolve the review URL in this order:

1. Use `links.review` unchanged from structured investigation creation.
2. Otherwise use the exact verified `dashboard_url`, agent ID, and investigation ID with the documented compatibility route:

```text
DASHBOARD_URL/agents/AGENT_ID/investigations/INVESTIGATION_ID/review
```

Strip one trailing slash from `dashboard_url`. Do not rewrite its path or add trace contents, questions, or judgments to the URL.

If neither route works, preserve the investigation and report its exact ID, the failed or missing URL, and one retry or bug-report action. Do not recreate the prepared frontend tour in chat.

## Resume and evaluate

After frontend review, re-read investigation questions, ordinary annotations, optional answers, and verdicts. Treat verdict coverage as the tour completion signal. Do not infer a missing verdict from a written answer.

Resume an investigation's verdicts only when the current conversation already carries its exact investigation ID or the user explicitly identifies that investigation as their review. A matching tutorial name is not proof that the current reviewer supplied its judgments. Reuse its sessions and exact-match prepared annotations, but create a fresh investigation when reviewer identity is ambiguous.

Before cohort creation, show the exact proposed membership once and obtain confirmation together with the accepted behavior. Prefer an installed configured evaluator when it expresses that behavior. Otherwise keep custom code local until it passes the installed evaluator test command, then register one immutable version.

Evaluation jobs require a live worker. Wait through the supported mechanism once, inspect the terminal job and every resulting evaluation, and keep missing or failed evaluations out of the quality numerator while retaining them in the population accounting.

Whenever a create or evaluation response includes a product-owned frontend link, return that link beside the result. Do not invent a compatibility URL for cohorts, evaluators, or evaluations unless the installed product documentation defines one.
