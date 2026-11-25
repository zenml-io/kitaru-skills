# Presenting insights

Use this reference to lay out a structured insight report, pick the right visualization for each finding, follow the chart limits, choose the grid tile highlight, rank findings, and write the chat report. Write for a reader with about 30 minutes who has not seen the run folder. They should find the most important problem first, see the concrete evidence, and be able to check it themselves.

## Contents

- [How a report appears in the dashboard](#how-a-report-appears-in-the-dashboard)
- [Lay out each finding](#lay-out-each-finding)
- [Choose the right chart](#choose-the-right-chart)
- [Hard chart limits](#hard-chart-limits)
- [Charts left out on purpose](#charts-left-out-on-purpose)
- [Pick the grid tile highlight](#pick-the-grid-tile-highlight)
- [Rank and order findings](#rank-and-order-findings)
- [Write the chat report](#write-the-chat-report)
- [Present Quick results](#present-quick-results)

## How a report appears in the dashboard

One `Insight` record is a complete multi-finding report for an agent. The backend contract supports three connected views (check the installed dashboard version for which views are shipped in the user's deployment):

- **Insights grid tile:** Shows `title`, `source_provider`, `coverage.sessions_analyzed`, the finding count, and the single visual selected by `highlight` (`finding_id` + `artifact_index`).
- **Report view:** Shows `title`, `coverage` (analyzed, available, skipped, failed, and caveats), an optional `next_step` banner and button, and the ordered `findings[]` in natural rank order (`findings[0]` is #1), followed by compact `tier: "secondary"` baseline rows.
- **Finding body and sidebar:** Each finding shows `title`, badges (`severity`, `kind`, `change_status`), Markdown `body`, its ordered `artifacts[]` (lead visual, optional step story or comparison, clickable `evidence` rows with counterexample, optional code `hypothesis`), its `action` button, and follow-up `suggested_questions[]`.

Key formatting rules:

- `report.summary` and `finding.summary` are **plain text** (one line, at most 320 characters, no Markdown). `check_report.py` rejects Markdown symbols and line breaks there.
- Put narrative Markdown in `finding.body` or a `text` artifact (`body`, `callout`, or `hypothesis`).
- Use `evidence` artifacts and `contributing_session_ids` for clickable sessions rather than pasting bare UUID lists into prose.
- Compact tiles and full-width report visuals read the same artifact payload. Always include underlying details (`numerator`, `denominator`, `before_detail`, `after_detail`, `session_id`, `node_id`) so hover tooltips stay exact while compact tiles stay uncluttered.
- Keep run internals out of every visible field: no run ID, seed, scope hash, run-folder paths, model IDs, or level names. Those belong in `metadata["kitaru.insights.skill/v1"]`.

## Lay out each finding

Give every primary finding a consistent, scannable shape:

1. **`title`:** Name the behavior in plain words ("Refunds skip the policy check when the order was edited"), not a metric name.
2. **`summary`:** One plain-text sentence (<= 320 chars) stating the claim and its size.
3. **`body`:** Short Markdown explaining what happens, the observed trigger (`first_failure.before`), how often it happens using the confidence phrasing from [insight-method.md](insight-method.md#tally-and-state-confidence), and the countable cost (tokens, USD, seconds, extra calls). Never paste user secrets or personal data.
4. **Lead visual (`artifacts[0]`):** Pick the single chart from [Choose the right chart](#choose-the-right-chart) that best proves the finding (for example `rate`, `step_strip`, `tool_cycle`, `categorical`, `comparison`, `time_series`, `binned`, or `table`).
5. **Supporting flow or comparison (optional):** Add `step_story` for a concrete 3–5 step conversation trace, `session_comparison` for a failing session beside its passing counterexample, `failure_matrix` for last-good × first-wrong transitions, or `session_timeline` for one session's latency waterfall.
6. **Evidence (`evidence` artifact):** Include `presentation: "table"` (with `step_label`, `signal`, `verdict`, and at least one passing counterexample row with `is_counterexample: true` and `counterexample_note`), or `presentation: "compact"` for lighter proof rows.
7. **Code hypothesis (optional):** When code supports a likely cause, add a `text` artifact with `style: "hypothesis"`, `label: "Code hypothesis"`, `file_path`, and `revision`. Omit it when no code supports a cause; do not guess.
8. **`action` and `suggested_questions`:** Set `action` (`label` <= 60 chars, `prompt` briefing `kitaru-investigation`), `check_first`, and 2–3 specific follow-up `suggested_questions`.

Use `tier: "secondary"` findings for compact baseline context that helps interpret the report without competing with primary findings — for example a 3-part `categorical` (`split_bar`) of how sessions ended, or a `binned` (`micro`) histogram of tool calls per session.

## Choose the right chart

Pick the artifact type from the question the finding answers. Every pairing below follows the Kitaru visualization guide:

| Question the finding answers | Use | Do not use |
|---|---|---|
| **How much?** (one number or 1–6 headline counts) | `stat_grid` or `rate` (`share_bar`) | A bar chart with one bar (`categorical` requires >= 2) |
| **How sure?** (a sampled rate with uncertainty) | `rate` (`presentation: "range"`, with `ci_low`, `ci_high`, `basis`) | A bare percentage |
| **Share of one total, 2 parts** | `rate` (`presentation: "share_bar"`, with `numerator`/`denominator`) | `donut` |
| **Share of one total, 3–4 parts** | `categorical` (`presentation: "donut"` or `"split_bar"`) | Pie chart |
| **Share of one total, 5+ parts** | `categorical` (`presentation: "ranked_bars"`) | `donut` or `split_bar` |
| **Which is biggest?** | `categorical` (`presentation: "ranked_bars"`, sorted descending, `"Other"` last) | Vertical columns or `donut` |
| **Subset inside a larger bucket** | `categorical` (`presentation: "focus_bars"`, using `CategoryValue.total`) | Separate charts |
| **Groups against an overall average** | `categorical` (`presentation: "baseline_bars"`, using `baseline_value`) | Unanchored bars |
| **Two groups across categories** | `comparison` (`presentation: "dot_plot"`; or `"side_by_side"` if <= 3 rows) | Grouped bars past 3 categories |
| **How values spread** | `binned` (`"columns"`, `"horizontal"`, or `"micro"`); or `session_dots` when `n <= 100` | Line chart |
| **Two points in time, one item** | `comparison` (`presentation: "side_by_side"`) | Line with 2 points |
| **Two points in time, many items** | `comparison` (`presentation: "slopegraph"`) | Grouped bars |
| **Before and after a fix or replay** | `comparison` (`presentation: "dumbbell"` or `"split_pair"`) | Two separate charts |
| **Status across imports or runs** | `comparison` (`presentation: "import_status"`, setting `row.status`) | Prose list |
| **3+ points in time or versions** | `time_series` (`"line"` or `"highlight_line"`; `"ordered_columns"` for versions; `"stacked_columns"` for <= 3 segments) | Area or stacked-area chart |
| **Inline trend beside a number** | `time_series` (`presentation: "sparkline"`) | A full chart in a row |
| **Where in a run it went wrong** | `step_strip` (`"rows"` or `"small_multiples"` per agent) or `failure_matrix` across causes | `session_timeline` |
| **Which path sessions took** | `categorical` (`presentation: "path_bars"`); `flow_sankey` only for <= 3 stages and <= 8 nodes | Sankey for everything |
| **Repeating tool loop** | `tool_cycle` (`steps`, `repeat_count`, `session_count`) | Prose alone |
| **One session's failing steps** | `step_story` (`tone: "danger"` on the bad step) | Unstructured wall of text |
| **Failing session vs passing counterexample** | `session_comparison` (`label: null` + `status: "missing"` marks a skipped step) | Two prose paragraphs |
| **Where latency went in one session** | `session_timeline` (spans in ms for one session only) | Aggregate failure location |
| **Which sessions prove it** | `evidence` (`"table"` with counterexample or `"compact"`) | Any chart |
| **Exact values across several columns** | `table` (use `percent_bar`, `delta`, `badge`, `session_link` formats) | Several separate charts |

Give every chart a clear `unit` (when applicable) and state what to notice in the finding's `summary` and `body`. A chart with no stated point is a dashboard metric, not an insight; drop it.

## Hard chart limits

Both the Kitaru server and `scripts/check_report.py` enforce these 11 limits. When your data exceeds a limit, apply the fallback rather than truncating silently:

1. **Ranked bars / path bars (`categorical` `ranked_bars` / `path_bars`):** At most 8 rows. Fold the rest into `"Other"`, always last.
2. **Time/version columns (`time_series` `ordered_columns` / `stacked_columns`):** At most 12 buckets (and only for time or versions). Past 12, switch `presentation` to `"line"`.
3. **Donut (`categorical` `donut`):** Strictly 3–4 parts (total shown in center). For 2 parts use `rate` (`share_bar`); for 5+ use `categorical` (`ranked_bars`).
4. **Split bar (`categorical` `split_bar`):** 2–4 segments, and every non-zero segment must be at least 2% of the total. Fold smaller segments into `"Other"`.
5. **Stacked columns (`time_series` `stacked_columns`):** At most 3 segments (and at most 12 buckets). Past 3 segments, switch to `time_series` (`small_multiples`).
6. **Direct-label line (`time_series` `line`):** At least 3 `x_labels`, single shared `unit`, and at most 5 series. Past 5 series, switch to `highlight_line` with exactly one `focus: true` series and the rest gray.
7. **Dot plot / slopegraph (`comparison` `dot_plot` / `slopegraph`):** At most 8 items (keep the top 8 by change). Paired `side_by_side` bars allow at most 3 items.
8. **Failure matrix (`failure_matrix`):** At most 6×6 (`rows` × `cols`). Fold rare steps into `"Other"`.
9. **Sankey (`flow_sankey`):** Strictly 2–3 stages and at most 8 unique nodes total. Past either limit, switch to `categorical` (`path_bars`).
10. **Small multiples (`time_series` / `step_strip` `small_multiples`):** At most 6 panels on one shared scale. Keep the top 6.
11. **Dot strip (`session_dots`):** At most 100 dots. Past 100 sessions, switch to `binned` (2–12 contiguous bins).

## Charts left out on purpose

The schema excludes four chart families on purpose; never try to mimic them:

- **Pie charts** (use `rate` `share_bar`, `split_bar`, or `donut` for 3–4 parts).
- **3D or decorative gradient bars** (use flat `ranked_bars` or `binned` `columns`).
- **Area and stacked-area charts** (use `line`, `stacked_columns` <= 3 segments, or `small_multiples`).
- **Dual-axis line charts** (every `time_series` uses one shared `unit`; split unrelated units into separate artifacts).

## Pick the grid tile highlight

Set `report.highlight` to `{"finding_id": findings[0].id, "artifact_index": 0}` (or the index of that finding's cleanest visual). The Insights grid tile renders best when the highlighted artifact is one of:

- `rate` (`presentation: "range"` or `"share_bar"`) — a single headline percentage or x-of-y count;
- `tool_cycle` — a repeating tool loop (`search -> fetch_page 14x`);
- `step_strip` (1 row) — where runs break along a step bar;
- `stat_grid` (1–4 headline numbers).

Avoid pointing `highlight` at a dense `table`, `failure_matrix`, or long `evidence` block.

## Rank and order findings

Rank primary findings by impact on the agent's purpose once they pass the checks in [insight-lenses.md](insight-lenses.md#choose-which-findings-to-include). Record each primary finding's impact in `metadata["kitaru.insights.skill/v1"]["findings"][finding.id]["impact"]`:

- **Sessions affected:** how many conversations show it, from the count or rate.
- **Cost:** tokens, money, seconds, or extra calls the behavior wastes, when countable. For a loop, count the repeated calls and the tokens of the model calls around them.
- **Harm:** what the user of the agent experiences: a wrong answer, a broken promise, a task left undone. Harm outranks cost when the two disagree.

Put rank 1 first in `findings[]` (`findings[0]`), followed by ranks 2..N in descending order of impact, and place any `tier: "secondary"` baseline findings at the end of `findings[]`.

## Write the chat report

The chat report is what the user reads first, often in a terminal. Keep the order below, and keep everything else in the run folder.

1. **The answer, in three lines:** what was read ("3,228 conversations from the last two weeks; 40 read in full"), the single most important finding, and the next step.
2. **A ranked table**, one row per primary finding: rank, finding (the title), sessions affected, impact (cost or harm), how sure (the confidence label), next step.
3. **One short paragraph per primary finding**, in rank order: the summary sentence, the conversation flow, and one or two session links (`DASHBOARD_URL/sessions/SESSION_ID` when `kitaru info` reported a dashboard URL, or inline session IDs when it did not).
4. **Changes since last time**, when the run compared windows or versions or matched an earlier run: what is new, what recurs, what narrowed, and what resolved.
5. **How this was made**, in at most three lines at the end: the level, how sessions were picked, what could not be checked, and where the report lives in the dashboard.

Show the same table at the approval step before writing, with the draft report title, finding titles, summary sentences, and chosen chart types. Do not paste report JSON, provenance, run IDs, seeds, hashes, or helper output into the chat report; offer the run folder path if the user wants details.

## Present Quick results

Analyzer reports keep their own wording, but present them the same way in chat: a ranked table of the findings the analyzer wrote, with their counts, followed by what the user should look at first. When the user asked about something an analyzer report does not cover, such as loops for one tool, say so and offer Standard, or the tool-health counts from `tool_stats.py`, instead of leaving the gap unmentioned.
