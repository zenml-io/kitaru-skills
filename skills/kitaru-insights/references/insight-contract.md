# Insight card contract

Use this reference to draft, check, and replace cards. `scripts/check_cards.py` enforces every limit on this page.

## Contents

- [Card shape](#card-shape)
- [Shared card context](#shared-card-context)
- [Skill provenance](#skill-provenance)
- [Investigation prompt](#investigation-prompt)
- [Runs, retries, and replacement](#runs-retries-and-replacement)
- [Example](#example)

## Card shape

Each card is one `InsightInput` object. The server rejects unknown top-level fields.

| Field | Rule |
|---|---|
| `name` | Letters, digits, `-`, and `_`; starts and ends with a letter or digit; at most 255 characters. Use `kitaru-insights-PATTERN_ID`. |
| `title` | Non-empty, at most 255 characters. Names the behavior. |
| `description` | Markdown narrative: example, rate phrasing, why it matters, hypothesis, what to check first. |
| `data` | `{"type": "text", "content": "..."}`, `{"type": "categorical", "unit": "...", "values": [{"label": "...", "value": 3}]}` with unique labels and non-negative values, or `{"type": "binned", "unit": "...", "bins": [{"lower_bound": 0, "upper_bound": 10, "count": 4}]}` with ascending, contiguous bins. Only the first bin may have a null lower bound and only the last a null upper bound. |
| `metadata` | Object holding the two keys below. |

Write at most eight cards per run. The dashboard shows a limited page of cards without an import, so a smaller set stays visible longer. Keep names unique within the run.

## Shared card context

Store reader-facing context under `metadata["kitaru.insights/v1"]`, using the same field names and limits as Kitaru's analyzers so the dashboard and other agents read skill cards the same way. Include only these fields:

| Field | Rule |
|---|---|
| `investigation_prompt` | Required. At most 16,000 characters. The dashboard copies it from the card's button. |
| `cta_label` | Required. At most 40 characters, naming the move: "Investigate refund promises". |
| `contributing_session_ids` | Required. 1 to 1,000 session UUIDs that showed the pattern. |
| `evidence` | Up to 20 `{"session_id", "node_id", "signal"}` locators. `node_id` is the node's `id` UUID or null; `signal` is at most 80 characters. |
| `check_first` | Optional, at most 1,000 characters: the first thing a reviewer should verify. |

Do not copy analyzer-only fields such as `eyebrow`, `position`, `coverage`, or `generation`. Their absence tells readers the card did not come from an analyzer.

## Skill provenance

Store how the card was made under `metadata["kitaru.insights.skill/v1"]`:

```json
{
  "schema_version": 1,
  "run_id": "UUID",
  "skill_version": "plugin version, or unknown",
  "level": "standard",
  "created_at": "2026-10-30T12:00:00Z",
  "host": "the coding agent host",
  "models": {"main": "model ID", "subagents": "model ID or null"},
  "scope": {"description": "tag refunds, started after 2026-10-23", "selector": {}, "population_count": 400, "population_sha256": "hex"},
  "sample": {"seed": 1234, "targeted": 25, "random": 15, "measurement_seed": null, "measured": 0, "read_sequentially": false},
  "pattern": {"id": "p1", "kind": "finding", "definition": "...", "status": "new", "checker_verdict": null, "rule_id": null},
  "rate": {"basis": "measurement", "method": "subagents", "numerator": 27, "denominator": 150, "low": 0.127, "high": 0.249, "unclear": 4, "unavailable": 0},
  "agreement": null,
  "hypothesis": {"text": "...", "path": "src/tools/orders.py", "revision": "git SHA"},
  "caveats": ["..."]
}
```

- `level` is `standard` or `deep`. Quick cards come from the analyzer and carry its own provenance.
- `population_sha256` is the SHA-256 of the sorted pinned IDs joined by newlines; `pick_sample.py` reports it. Two runs with the same hash covered the same sessions.
- `pattern.kind` is `finding` (something going wrong), `bright_spot` (something going well), `opportunity` (a "what if" worth an experiment), or `coverage_gap` (a failure pattern no existing eval checks). `rule_id` names the `rules.json` rule a finding breaks, or is null.
- `pattern.status` is `new`, `recurring`, or null when no earlier run exists. `checker_verdict` is `holds`, `narrow`, or null.
- `rate.method` is `readers` (noticed while reading), `subagents` (judged by measurement subagents), `jev`, or `mixed` for how the numerator was found, or null for counts. `unclear` and `unavailable` count judgments kept out of the denominator.
- `agreement` is null, or the tally's agreement table for a Jev question against reader-based membership: `{"both_yes": 3, "jev_only": 1, "readers_only": 0, "both_no": 6}`.
- `rate.basis` is `census` (every session in scope was read), `exact_proxy`, `measurement`, `random_slice`, or `targeted_only`. Leave `low` and `high` null except for `measurement` on a sample; a measurement over every session in scope has no sampling interval. Copy the numbers from `tally.json`.
- `hypothesis` is null when no code supports one.
- Record model IDs only when the host reports them; otherwise write null.

## Investigation prompt

Write the prompt as a briefing for a fresh coding agent with no access to this run:

1. Start with setup: use the `kitaru-investigation` skill, against the named server and agent. For an `opportunity` card, say that a confirmed cohort then goes to `kitaru-replay-experiment` with the candidate change, and that skill sets the tool policy and asks for approval.
2. State the finding in one sentence, with the rate phrasing from the tally.
3. List three to six session IDs to review first, with node IDs, and the counterexample.
4. Give the hypothesis, if any, and what would confirm or refute it.
5. Suggest a concrete cohort boundary for the review.
6. Say plainly that this is a skill-written lead, not a human verdict.

Do not paste trace text into the prompt. Reference sessions and nodes by ID.

## Runs, retries, and replacement

- Mint one `run_id` (UUID) per run and record it in `run.json`. Every card in the run carries it.
- Use `RUN_ID-batch-N` as the idempotency key for each write. Reusing the key on a retry returns the original result instead of writing again.
- Before writing, list the agent's cards and find earlier skill runs whose `population_sha256` matches, or whose scope description overlaps. Tell the user how many earlier cards exist and from which runs.
- Offer to delete an earlier run's cards only after the new cards are written and checked, so the agent is never left with neither. List the exact card IDs, and delete only after explicit confirmation.

## Example

```json
{
  "name": "kitaru-insights-p1",
  "title": "Refunds promised before checking the return window",
  "description": "In about 18% of sessions (95% interval 13 to 25%, from 150 random sessions) the agent told the customer a refund was approved before calling `check_return_policy`. ...",
  "data": {"type": "text", "content": "..."},
  "metadata": {
    "kitaru.insights/v1": {
      "investigation_prompt": "Use the kitaru-investigation skill ...",
      "cta_label": "Investigate early refund promises",
      "contributing_session_ids": ["UUID"],
      "evidence": [{"session_id": "UUID", "node_id": "UUID", "signal": "refund promised before policy check"}],
      "check_first": "Confirm the policy tool was available in these sessions."
    },
    "kitaru.insights.skill/v1": {"schema_version": 1, "run_id": "UUID", "level": "standard"}
  }
}
```

The example's provenance is abbreviated; write every field listed under [Skill provenance](#skill-provenance).
