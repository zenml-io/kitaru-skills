# Presenting insights

Use this reference to lay out each card for the dashboard, choose between text and chart cards, order the cards, and write the report the user reads in chat. Write for a reader with about 30 minutes who has not seen the run folder. They should find the most important problem first, see the conversation where it happened, and be able to check it themselves.

## Contents

- [What the dashboard shows](#what-the-dashboard-shows)
- [Lay out a text card](#lay-out-a-text-card)
- [Choose a chart card](#choose-a-chart-card)
- [Rank and order the cards](#rank-and-order-the-cards)
- [Write the chat report](#write-the-chat-report)
- [Present Quick results](#present-quick-results)

## What the dashboard shows

The agent's Insights tab shows each card as a title, a description, a body, and one button. The body depends on `data.type`.

- `title` is a heading.
- `description` is printed as **plain text** under the title. Markdown is not rendered there, so `**bold**`, backticks, and list markers show as literal symbols.
- A `text` card renders `data.content` as Markdown (GitHub-flavored: headings, lists, tables, links, code). Text cards are shown first, full width, highlighted.
- A `categorical` card draws a small donut chart with a legend listing each label, its value, and its share. The chart has eight colors.
- A `binned` card draws a bar chart, 112 pixels tall, with the count above each bar.
- The button copies `investigation_prompt`, labeled with `cta_label`.
- Nothing else in the metadata is shown. `evidence`, `contributing_session_ids`, `check_first`, and the provenance block are invisible in the dashboard. A session ID becomes clickable only as an explicit Markdown link in a text card's content.
- Cards without an import, which includes every skill card and every `kitaru session analyze` card, are listed newest first, one page of 100.

So the only places a reader can see your evidence are the description sentence and a text card's content. Put the example, the numbers, and the links there.

## Lay out a text card

Use a text card for every finding that has an example conversation. Fill it in this shape:

- **`title`:** the behavior, in plain words: "Agent repeats the same document search until it gives up". Not a metric name.
- **`description`:** one plain-text sentence of at most 240 characters, with no Markdown, stating the claim and its size: "In 41 of 3,228 conversations the agent called search_documents three or more times in a row with the same query, about 12,000 wasted tokens each." `check_cards.py` rejects Markdown symbols and line breaks here.
- **`data.content`:** Markdown of at most 2,500 characters, with these bold labels in this order, each followed by a short paragraph or list:
  - **What happens:** the conversation as three to five steps, from the user's request to where it went wrong: "User asks for the Q3 contract → agent calls `search_documents` with "Q3 contract" → empty result → calls it again with the same query, four more times → tells the user it cannot find the document." Use the reader note's `flow` field. Name tools and the arguments that matter; never paste user text, personal data, or secrets.
  - **How often:** the count or rate with its confidence label from [insight-method.md](insight-method.md#tally-and-state-confidence), then the cost of the behavior where it is countable (tokens, money, seconds, extra calls).
  - **Why:** the likely cause, labeled as a hypothesis, with the file and line when code supports one. Omit this label when nothing supports a cause; do not guess.
  - **Check it yourself:** two or three Markdown links to sessions that show it, each with the node position to look at, and one counterexample: `- [Loop of five searches, step 7](DASHBOARD/sessions/SESSION_ID)`.
  - **Next step:** the one move to make: a fix to try, an investigation of the cited sessions, or an experiment.

Build each link from the dashboard base URL that `kitaru info` reports (`dashboard_url`) plus `/sessions/SESSION_ID`. Pass the same URL to `check_cards.py --dashboard-url`, which then requires every text card to link at least one contributing session. When `kitaru info` reports no dashboard URL, write the session IDs as inline code instead and say in the report that the dashboard was not reachable.

Keep run details out of every visible field: no run ID, seed, scope hash, file paths in the run folder, model IDs, or level names. They belong in the provenance metadata. "How often" already says how sure the number is.

## Choose a chart card

A chart card makes sense when the shape of the numbers is the finding and the reader would otherwise have to read a list of numbers. Its description is the only text it shows, so it cannot carry an example or a link. Pair it with a text card when the finding also needs a conversation to look at.

| The finding is | Use | Example |
|---|---|---|
| How one count splits across a few labels | `categorical` (donut) with at most eight labels; fold the rest into "Other" | Failed tool calls per tool; where repeated calls happen |
| How a quantity is spread across sessions | `binned` (bars) with at most twelve contiguous bins | Tool calls per conversation; seconds per session |
| Several numbers per tool, or two windows side by side | A Markdown table inside a text card | The tool-health table; this week against last week |
| A behavior with an example conversation | A text card in the layout above | Every finding, bright spot, and opportunity |

- Write at most three chart cards per run, so findings with examples stay the core of the page.
- Give every chart a `unit` and a description sentence that says what to notice: "Two tools account for 81% of failed calls; create_ticket alone has 58%." A chart with no stated point is a dashboard metric, not an insight; drop it.
- Prefer a table in a text card over a chart when the reader needs exact numbers or links. `tool_stats.py --table-out` writes the tool-health table in that form.
- Do not chart a split the user already monitors elsewhere unless it changed or the card explains why it happens.

## Rank and order the cards

Rank the cards by impact on the agent's purpose once they pass the checks in [insight-lenses.md](insight-lenses.md#choose-which-cards-to-write). Estimate each card's impact and record it in the provenance `impact` field ([insight-contract.md](insight-contract.md#skill-provenance)):

- **Sessions affected:** how many conversations show it, from the count or rate.
- **Cost:** tokens, money, seconds, or extra calls the behavior wastes, when countable. For a loop, count the repeated calls and the tokens of the model calls around them.
- **Harm:** what the user of the agent experiences: a wrong answer, a broken promise, a task left undone. Harm outranks cost when the two disagree.

Rank 1 is the card the user should read first. Write the batch in reverse rank order, so rank 1 is the last card in `cards.json`. The dashboard lists cards without an import newest first, so the last card written shows at the top. `check_cards.py` rejects any other order.

## Write the chat report

The chat report is what the user reads first, often in a terminal. Keep the order below, and keep everything else in the run folder.

1. **The answer, in three lines:** what was read ("3,228 conversations from the last two weeks; 40 read in full"), the single most important finding, and the next step.
2. **A ranked table**, one row per card: rank, finding (the title), sessions affected, impact (cost or harm), how sure (the confidence label), next step.
3. **One short paragraph per card**, in rank order: the description sentence, the "What happens" steps, and one or two session links.
4. **Changes since last time**, when the run compared windows or versions or matched an earlier run: what is new, what recurs, and what changed clearly.
5. **How this was made**, in at most three lines at the end: the level, how sessions were picked, what could not be checked, and where the cards are in the dashboard.

Show the same table at the approval step before writing, with the draft titles and description sentences. Do not paste card JSON, provenance, run IDs, seeds, hashes, or helper output into the report; offer the run folder path if the user wants details.

## Present Quick results

Analyzer cards keep their own wording, but report them the same way: a ranked table of the cards the analyzer wrote, with their counts, followed by what the user should look at first. When the user asked about something an analyzer card does not cover, such as loops for one tool, say so and offer Standard, or the tool-health counts from `tool_stats.py`, instead of leaving the gap unmentioned.
