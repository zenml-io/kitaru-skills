# Insight report contract

Use this reference to draft, check, and replace a structured insight report. `scripts/check_report.py` enforces every server limit and skill rule on this page. Lay out findings and choose chart types using [presentation.md](presentation.md).

## Contents

- [Report shape](#report-shape)
- [Finding shape](#finding-shape)
- [Artifact types](#artifact-types)
- [Skill provenance](#skill-provenance)
- [Investigation prompt](#investigation-prompt)
- [Runs, retries, and replacement](#runs-retries-and-replacement)
- [Example](#example)

## Report shape

One `kitaru-insights` run produces one structured `InsightInput` report saved to `RUN/report.json`. The server rejects unknown fields.

| Field | Rule |
|---|---|
| `name` | 1 to 255 letters, digits, `-`, or `_`, starting and ending with a letter or digit. Use `kitaru-insights-SCOPE` or `kitaru-insights-YYYYMMDD`. |
| `title` | Required, at most 255 characters. Names the headline finding or run summary (for example "Refunds skip the policy check when the order was edited" or "Three findings, one new since the last run"). |
| `summary` | Optional plain-text sentence of at most 320 characters, with no Markdown or line breaks, for compact list views. |
| `source_provider` | Optional trace source label of at most 80 characters (for example `langfuse`, `langsmith`, `recorded`, or `mixed`). |
| `coverage` | Required by this skill. Object with `sessions_analyzed` (>= 0), optional `sessions_available` (>= `sessions_analyzed`), `skipped` (>= 0), `failed` (>= 0), optional timezone-aware ISO 8601 `started_after` and `started_before`, and up to 10 `caveats`. |
| `highlight` | Optional `{"finding_id": "...", "artifact_index": 0}` picking the finding and artifact shown on the Insights grid tile. Point it at the rank-1 finding's cleanest visual (`rate`, `tool_cycle`, or single-row `step_strip`). |
| `next_step` | Optional top-of-report `InsightAction`: `label` (<= 60 chars), `prompt` (<= 16,000 chars), and optional `summary` (<= 300 chars, shown as the callout text beside the button). |
| `findings` | Ordered array of 1 to 30 `InsightFinding` objects with unique `id` values. Put rank 1 first (`findings[0]`), followed by remaining primary findings in descending impact order, then optional secondary baseline findings. This skill writes at most 8 primary findings per report. |
| `suggested_questions` | Up to 5 report-level follow-up chat pills: `{"label": "...", "prompt": "..."}` (`label` <= 80 chars, optional `prompt` <= 2,000 chars). |
| `metadata` | Object holding `kitaru.insights.skill/v1`. Do not write the legacy `kitaru.insights/v1` key; handoff actions, contributing sessions, `check_first`, and evidence are first-class fields on each finding. |

Never put the run ID, seed, or scope hash in `title`, `summary`, `body`, or any `text` artifact.

## Finding shape

Each entry in `findings[]` is one ranked section of the report.

| Field | Rule |
|---|---|
| `id` | Required, 1 to 120 characters, unique within the report (for example `p1` or `policy-check-skipped`). |
| `title` | Required, at most 255 characters (aim for under 50, at most 55 so the report sidebar never truncates mid-word). Names the behavior in plain words, not a metric name. |
| `summary` | Required for primary findings (optional for secondary). One plain-text sentence of at most 320 characters, with no Markdown or line breaks, stating the claim and its size. |
| `body` | Optional Markdown narrative with the concrete conversation flow, numbers, observed trigger, and cost. |
| `tier` | `primary` (default) for main findings, or `secondary` for compact baseline context rows shown under the main findings (for example session outcomes or tool-call spread). |
| `kind` | `finding` (something going wrong), `bright_spot` (something going well), `opportunity` (a "what if" worth a replay experiment), or `coverage_gap` (a failure pattern no existing eval checks). |
| `severity` | Optional `high`, `medium`, or `low` harm level. |
| `change_status` | Optional `new`, `recurring`, `narrowed`, or `resolved` relative to earlier runs or time windows. |
| `artifacts` | 0 to 12 typed `InsightArtifact` blocks in display order (lead visual first, optional flow or comparison visual, `evidence` artifact, optional `text` `hypothesis`). |
| `contributing_session_ids` | 0 to 1,000 unique session UUIDs supporting this finding. Primary findings require at least 1. |
| `check_first` | Optional, at most 1,000 characters: the first thing a human should verify. |
| `action` | Required for primary findings: `{"label": "...", "prompt": "...", "summary": "..."}` (`label` <= 60 chars, `prompt` <= 16,000 chars, optional `summary` <= 300 chars). |
| `suggested_questions` | Up to 5 finding-scoped chat pills (`label` <= 80 chars, optional `prompt` <= 2,000 chars). |

## Artifact types

Every item in `finding.artifacts[]` is a discriminated object keyed by `type`, with an optional `title` (1–120 characters) used as the block header above the chart or table when a finding stacks multiple artifacts (omit `title` on a single self-explanatory chart). Compact and full-width dashboard views read the exact same payload, so always populate underlying details (`numerator`, `denominator`, `before_detail`, `after_detail`, `session_id`, `node_id`) when you have them.

| `type` | `presentation` / `style` | Required fields and server limits |
|---|---|---|
| `stat_grid` | — | `items[]` (1–6): `label` (<= 60), `value` (finite number or string), optional `unit`, `tone`, `chat_prompt`. |
| `rate` | `range` \| `share_bar` | `rate` (0–1); paired `ci_low <= rate <= ci_high` when sampled; optional `numerator <= denominator`, `label`, `basis`, `tone`, `chat_prompt`. |
| `categorical` | `ranked_bars` \| `focus_bars` \| `baseline_bars` \| `path_bars` \| `split_bar` \| `donut` | `values[]` (>= 2 unique labels, non-negative finite `value`, optional outer `total >= value`, `tone`, `focus`, `chat_prompt`), optional `unit`, `baseline_value`. Limits: `donut` 3–4 parts; `split_bar` <= 4 segments each >= 2% of total; `ranked_bars`/`path_bars`/null <= 8 rows (`"Other"` last). |
| `comparison` | `side_by_side` \| `slopegraph` \| `dumbbell` \| `dot_plot` \| `split_pair` \| `import_status` | `before_label`, `after_label`, `rows[]` (1–12: `label`, `before`, `after`, optional `before_detail`, `after_detail`, `status`, `tone`, `focus`, `chat_prompt`), optional `unit`. Limits: `side_by_side` <= 3 rows; `dot_plot`/`slopegraph` <= 8 rows. |
| `table` | — | `columns[]` (1–10 unique `key`, `label`, `format` in `text`/`mono`/`number`/`percent`/`percent_bar`/`delta`/`badge`/`session_link`), `rows[]` (1–50 dicts). |
| `binned` | `columns` \| `horizontal` \| `micro` | `bins[]` (2–12 ascending contiguous `lower_bound`/`upper_bound`/`count`, optional `focus`; open bounds only at ends), optional `unit`, `median`, `p95`. |
| `session_dots` | — | `points[]` (1–100: `session_id` UUID, `value`, optional `session_label`, `highlight`), optional `unit`, `scale_min < scale_max`. Past 100 switch to `binned`. |
| `time_series` | `line` \| `highlight_line` \| `ordered_columns` \| `stacked_columns` \| `sparkline` \| `small_multiples` | `x_labels[]` (>= 3 points), `series[]` (1–12 matching `x_labels` length, optional `tone`, `focus`), single `unit`, optional `annotations[]` (<= 6). Limits: columns <= 12 `x_labels`; `stacked_columns` <= 3 series; `line`/null <= 5 series; `highlight_line` exactly 1 `focus: true`; `small_multiples` <= 6 series. |
| `step_strip` | `rows` \| `small_multiples` | `total_steps` (2–30), `rows[]` (1–12, <= 6 for `small_multiples`: `label`, optional `session_count`, `last_good_step`, `first_wrong_step` <= `total_steps`, `severity`, `session_ids` <= 50, `chat_prompt`). |
| `failure_matrix` | — | `state_by` (`tool`/`span`/`node`/`step`), `rows[]` (1–6), `cols[]` (1–6), `total_failed`, `cells[]` (`from_state`, `to_state`, `count`, optional `attempts`, `sessions[]` <= 20). |
| `flow_sankey` | — | `stages[]` (2–3 stages, max 8 unique nodes total across stages), `links[]` (>= 1 linking known node IDs). Past 3 stages or 8 nodes switch to `categorical` `path_bars`. |
| `step_story` | — | `steps[]` (1–12: `number` >= 1, `text` <= 400, optional `role`, `tool_name`, `node_id`, `tone`, `note`), optional `session_id`, `session_label`. |
| `tool_cycle` | — | `steps[]` (1–6: `name`, `status` `ok`/`error`), `repeat_count` (>= 2), `session_count` (>= 1), optional `note`. |
| `session_comparison` | — | `left` and `right` sides (`session_id`, `verdict`, `steps[]` 1–15 with `label` or `null`, optional `node_id`, `status` in `present`/`missing`/`highlight_bad`/`highlight_good`). |
| `session_timeline` | — | `session_id`, `total_duration_ms` (>= 1), `spans[]` (1–40: `name`, `start_ms`, `duration_ms`, optional `node_id`, `tone`), optional `session_label`. Single session only. |
| `evidence` | `table` \| `compact` | `total_sessions` (>= 1), `rows[]` (1–25: `session_id`, optional `session_label`, `node_id`, `step_label`, `signal`, `verdict`, `is_counterexample`, `counterexample_note`). Every non-counterexample `session_id` must appear in the finding's `contributing_session_ids`. |
| `text` | `body` \| `callout` \| `hypothesis` | `content` (non-empty Markdown), optional `label` (<= 60), `file_path` (<= 300), `revision` (<= 64). |

Allowed `tone` values across artifacts: `neutral`, `risk`, `danger`, `good`, `warn`. Allowed `verdict` values: `pass`, `fail`, `unclear`.

## Skill provenance

Store how the report was made under `metadata["kitaru.insights.skill/v1"]`:

```json
{
  "schema_version": 2,
  "run_id": "UUID",
  "skill_version": "plugin version, or unknown",
  "level": "deep",
  "created_at": "2026-10-30T12:00:00Z",
  "host": "the coding agent host",
  "models": {"main": "model ID", "subagents": "model ID or null"},
  "scope": {"description": "tag refunds, started after 2026-10-23", "selector": {}, "population_count": 214, "population_sha256": "hex"},
  "sample": {"seed": 1234, "targeted": 25, "random": 15, "measurement_seed": 5678, "measured": 150, "read_sequentially": false},
  "findings": {
    "p1": {
      "pattern": {"definition": "...", "checker_verdict": "holds", "rule_id": "R1"},
      "rate": {"basis": "measurement", "method": "subagents", "numerator": 27, "denominator": 150, "low": 0.127, "high": 0.249, "unclear": 4, "unavailable": 0},
      "agreement": null,
      "impact": {"summary": "about 18% of refund conversations", "sessions": 27, "amount": null, "unit": null}
    }
  },
  "caveats": ["..."]
}
```

- `schema_version` is `2` for structured multi-finding reports.
- `level` is `standard` or `deep`. Quick reports come from the server analyzer and carry its own provenance.
- `population_sha256` is the SHA-256 of the sorted pinned IDs joined by newlines; `pick_sample.py` reports it. Two runs with the same hash covered the same sessions.
- `findings` is keyed by `finding.id` and must include an entry for every primary finding (entries for secondary findings are optional).
- `pattern.checker_verdict` is `holds`, `narrow`, or null. `rule_id` names the `rules.json` rule a finding breaks, or is null.
- `rate.method` is `readers`, `subagents`, `jev`, `mixed`, or null for counts. `unclear` and `unavailable` count judgments kept out of the denominator.
- `agreement` is null, or the tally's agreement table for a Jev question against reader-based membership: `{"both_yes": 3, "judged_only": 1, "readers_only": 0, "both_no": 6}`.
- `rate.basis` is `census` (every session in scope was read), `exact_proxy`, `measurement`, `random_slice`, or `targeted_only`. Leave `low` and `high` null except for `measurement` on a sample; a measurement over every session in scope has no sampling interval. Copy the numbers from `tally.json`.
- `impact` records what the ranking rests on: `summary` (<= 160 chars), `sessions` affected or null, and `amount` with `unit` (`tokens`, `usd`, `seconds`, `sessions`, or `calls`), both null when cost is not countable.
- Record model IDs only when the host reports them; otherwise write null.

## Investigation prompt

Write each finding's `action.prompt` (and the report's `next_step.prompt`) as a briefing for a fresh coding agent with no access to this run:

1. Start with setup: use the `kitaru-investigation` skill, against the named server and agent. For an `opportunity` finding, say that a confirmed cohort then goes to `kitaru-replay-experiment` with the candidate change, and that skill sets the tool policy and asks for approval.
2. State the finding in one sentence, with the rate phrasing from the tally.
3. List three to six session IDs to review first, with node IDs, and the counterexample.
4. Give the hypothesis, if any, and what would confirm or refute it.
5. Suggest a concrete cohort boundary for the review.
6. Say plainly that this is a skill-written lead, not a human verdict.

Do not paste trace text into the prompt. Reference sessions and nodes by ID.

## Runs, retries, and replacement

- Mint one `run_id` (UUID) per run and record it in `run.json`.
- Use `RUN_ID-report-1` as the idempotency key for the write. Reusing the key on a retry returns the original report instead of creating a duplicate.
- Before writing, list the agent's insights and find earlier skill reports whose `population_sha256` matches, or whose scope description overlaps. Tell the user how many earlier reports exist and from which runs.
- Offer to delete an earlier run's report only after the new report is written and verified, so the agent is never left with neither. List the exact insight IDs, and delete only after explicit confirmation.

## Example

```json
{
  "name": "kitaru-insights-refunds-20261030",
  "title": "Refunds skip the policy check when the order was edited",
  "summary": "After an order edit, the agent issued refunds without calling check_refund_policy in 31 of 47 sessions.",
  "source_provider": "langfuse",
  "coverage": {
    "sessions_analyzed": 214,
    "sessions_available": 250,
    "skipped": 33,
    "failed": 3,
    "started_after": "2026-10-12T00:00:00Z",
    "started_before": "2026-10-19T00:00:00Z",
    "caveats": ["Stopped at the 250-trace import limit."]
  },
  "highlight": {"finding_id": "p1", "artifact_index": 0},
  "next_step": {
    "label": "Investigate this insight",
    "summary": "Run check_refund_policy again after every order edit.",
    "prompt": "Use the kitaru-investigation skill against agent meridian-support..."
  },
  "findings": [
    {
      "id": "p1",
      "title": "Refunds skip the policy check when the order was edited",
      "summary": "In 14% of sessions (between 10% and 20%), the agent called issue_refund without calling check_refund_policy after an edit.",
      "body": "After an order edit, the agent called `issue_refund` without `check_refund_policy` in 31 of 47 sessions. Without an edit it never skipped the check (0 of 167).",
      "tier": "primary",
      "kind": "finding",
      "severity": "high",
      "change_status": "narrowed",
      "artifacts": [
        {
          "type": "rate",
          "presentation": "range",
          "rate": 0.145,
          "ci_low": 0.10,
          "ci_high": 0.20,
          "numerator": 31,
          "denominator": 214,
          "label": "of sessions",
          "basis": "150 random sessions judged",
          "tone": "risk"
        },
        {
          "type": "evidence",
          "presentation": "table",
          "total_sessions": 31,
          "rows": [
            {"session_id": "11111111-1111-1111-1111-111111111111", "session_label": "ses_4f2a91", "node_id": "22222222-2222-2222-2222-222222222222", "step_label": "step 7", "signal": "issue_refund", "verdict": "fail"},
            {"session_id": "33333333-3333-3333-3333-333333333333", "session_label": "ses_2e77a8", "node_id": "44444444-4444-4444-4444-444444444444", "step_label": "step 6", "signal": "check_refund_policy", "verdict": "pass", "is_counterexample": true, "counterexample_note": "Counterexample, 1 of 16"}
          ]
        },
        {
          "type": "text",
          "style": "hypothesis",
          "label": "Code hypothesis",
          "content": "`edit_order` resets the cached policy flag in the session state, and the refund prompt does not require re-checking it.",
          "file_path": "src/tools/orders.py",
          "revision": "a1b2c3d"
        }
      ],
      "contributing_session_ids": ["11111111-1111-1111-1111-111111111111"],
      "check_first": "Confirm check_refund_policy was available in the tool schema during edited-order sessions.",
      "action": {
        "label": "Investigate this insight",
        "prompt": "Use the kitaru-investigation skill against agent meridian-support..."
      },
      "suggested_questions": [
        {"label": "Why is the range this wide?"},
        {"label": "Compare with the counterexample"}
      ]
    },
    {
      "id": "outcomes",
      "title": "How sessions ended",
      "tier": "secondary",
      "kind": "finding",
      "artifacts": [
        {
          "type": "categorical",
          "presentation": "split_bar",
          "unit": "sessions",
          "values": [
            {"label": "Resolved", "value": 158, "tone": "good"},
            {"label": "Escalated", "value": 41, "tone": "warn"},
            {"label": "Abandoned", "value": 15, "tone": "neutral"}
          ]
        }
      ]
    }
  ],
  "suggested_questions": [
    {"label": "Which finding has the highest user impact?"}
  ],
  "metadata": {
    "kitaru.insights.skill/v1": {
      "schema_version": 2,
      "run_id": "55555555-5555-5555-5555-555555555555",
      "level": "deep",
      "scope": {"description": "last 7 days", "selector": {}, "population_count": 214, "population_sha256": "0000000000000000000000000000000000000000000000000000000000000000"},
      "sample": {"seed": 1234, "targeted": 25, "random": 15, "measurement_seed": 5678, "measured": 150, "read_sequentially": false},
      "findings": {
        "p1": {
          "pattern": {"definition": "Calls issue_refund without check_refund_policy after an order edit.", "checker_verdict": "holds", "rule_id": "R1"},
          "rate": {"basis": "measurement", "method": "subagents", "numerator": 27, "denominator": 150, "low": 0.127, "high": 0.249, "unclear": 4, "unavailable": 0},
          "agreement": null,
          "impact": {"summary": "31 sessions with unverified refunds", "sessions": 31, "amount": null, "unit": null}
        }
      },
      "caveats": []
    }
  }
}
```

The example's provenance is abbreviated; write every field listed under [Skill provenance](#skill-provenance).
