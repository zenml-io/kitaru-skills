# Insight method

Use this reference to choose a level, pick sessions, turn notes into patterns, measure them, and decide what a card may claim.

## Contents

- [Choose a level](#choose-a-level)
- [Estimate the budget](#estimate-the-budget)
- [Count cheaply first](#count-cheaply-first)
- [Pick the sample](#pick-the-sample)
- [Read and take notes](#read-and-take-notes)
- [Group notes into patterns](#group-notes-into-patterns)
- [Deep waves](#deep-waves)
- [Tally and state confidence](#tally-and-state-confidence)
- [Explain with code](#explain-with-code)
- [What a good card says](#what-a-good-card-says)
- [Compare with earlier runs](#compare-with-earlier-runs)

## Choose a level

| Level | What runs | Reads | Can claim |
|---|---|---|---|
| Quick | `kitaru session analyze` with a server analyzer over the pinned scope | No session text by the user's models | What the analyzer's fixed counters found |
| Standard | Cheap counts, then readers over about 40 sessions, then grouping | About 40 sessions | Patterns with examples; a rough rate from the random slice only |
| Deep | Standard, then checker, measurement, and first-failure waves | About 40 plus a fresh random sample of 100 to 200 | Patterns that survived a refutation attempt, with a measured rate and range, and exact first-failure nodes |

Default to Standard. Propose Deep when the user wants numbers they can act on, the scope is large, or Standard found patterns whose rates matter for prioritizing. Propose Quick alone when the user wants a cheap first look or no session text should leave Kitaru.

Scale the Standard sample down for a small scope: `pick_sample.py` picks every session when the scope is no larger than the targeted plus random budget (40 by default), and the tally then reports exact counts. Deep's measurement wave adds nothing in that case; skip it.

## Estimate the budget

Before approval, estimate from the scope's session sizes: about 6,000 condensed tokens per ordinary session is a starting guess. After condensing, use the `estimated_tokens` total that `condense_sessions.py` reports, plus about 1,500 tokens of brief per subagent. Name the reader and measurement model tiers, and say the estimate covers input only.

Report the number of sessions read, the estimated tokens, the subagent count, and what will be written: for example, "Deep: reads 40 sessions in full, then checks 5 patterns against 150 more; about 1.3M input tokens across 30 subagents; writes up to 8 cards."

## Count cheaply first

Over the whole pinned scope, collect what the server can count without reading text:

- status, origin, cost, `llm_call_count`, `tool_call_count`, and duration per session;
- failed tool and model nodes per session through the node `node_type` filter;
- `kitaru_failure_matrix` over the scope, when MCP is available, for where failures first appear by tool or step.

Use these to aim the sample and to give each pattern a countable proxy when one exists. Report them as counts over the full scope; they need no sampling caveat. Uniform counts, including zero tool calls, are not findings by themselves. Check whether the recorded behavior matters for the agent's task. Distinguish observed absence from missing instrumentation: a trace with no recorded tool calls does not prove the agent used no tools when tool activity was not captured.

## Pick the sample

Run `scripts/pick_sample.py` over the saved session list pages:

```bash
python3 scripts/pick_sample.py RUN/scope/*.json --targeted 25 --random 15 --out RUN/sample.json --ids-out RUN/population_ids.txt
```

It records a fresh seed unless `--seed` is given. It draws two parts and records why each session was picked:

- **Targeted picks** aim at likely trouble and extremes: failed sessions, shuffled with the seed so later failures are as likely as early ones, fill up to half, and the rest rotate through the highest and lowest cost, the most tool calls, and the longest and shortest duration. They find patterns fast but overrepresent failure.
- **A random slice**, drawn with a recorded seed from the whole scope, independent of the targeted picks. Only this slice supports a rate.

A session can be both targeted and random; keep both reasons. The default for Standard is 25 targeted and 15 random. Record the seed in `run.json` so the same sample can be redrawn.

## Read and take notes

Give each reader subagent five to eight condensed transcripts and the reader brief from [subagent-briefs.md](subagent-briefs.md). Include the context brief when one exists. Each reader writes one note per session, so the main agent never needs the transcripts.

Without subagents, read the transcripts yourself in batches of five to eight, write the same notes, and clear each batch from working memory before the next. Tell the user that reading was sequential.

## Group notes into patterns

Read all notes, then propose up to eight supported patterns, including none. A pattern is an observable behavior, not a cause:

- **Definition:** one or two sentences a reader could apply to a new session with a yes or no answer.
- **Members:** the session IDs whose notes show it, with node IDs.
- **Counterexample:** a session that looks similar but does not show it, and why.
- **Proxy:** a countable signal over the full scope, if one exists (for example a tool's error count).

Merge notes that describe the same behavior in different words. Keep a pattern that appears once only when its impact is severe, and label it as a single observation. Include one notably good behavior when the notes support it; users act on what works too.

If no useful patterns remain after grouping or checking, report what scope was read and any coverage gaps, then finish without card validation or write calls. A run with no useful patterns is a complete outcome.

For surviving patterns, write `patterns.json` in the format the tally script expects; see [subagent-briefs.md](subagent-briefs.md).

## Deep waves

Run these after grouping. Each wave reads condensed transcripts from disk and writes JSON lines to disk.

1. **Checker wave.** One checker per pattern. It did not write the pattern, so it judges it more fairly. It reads the members and the counterexample, then tries to refute the pattern: members that do not fit, a definition too vague to apply, or a simpler explanation. Narrow or drop patterns it refutes, and record what changed.
2. **Measurement wave.** Draw a fresh random sample of 100 to 200 sessions that were not read yet, from the same saved scope pages: `python3 scripts/pick_sample.py RUN/scope/*.json --targeted 0 --random N --exclude RUN/sample.json --out RUN/measure/sample.json`. The rate then describes the sessions not already read, which keeps the sessions that defined each pattern from confirming it. Export and condense them into `RUN/measure/`. Measurement subagents judge each session against every surviving definition: `yes`, `no`, or `unclear`. When a pattern has an exact proxy, count the proxy over the full scope instead and skip judging it.
3. **First-failure wave.** For each failed or pattern-member session, find the node where things first went wrong and the last node that went right. Use node IDs from the transcript. These become card evidence and can feed `kitaru_failure_matrix` comparisons.

Keep checker and measurement subagents separate from the readers that found the pattern where the host allows it.

## Tally and state confidence

Run `scripts/tally_notes.py`:

```bash
python3 scripts/tally_notes.py --sample RUN/sample.json --patterns RUN/patterns.json --notes RUN/notes --out RUN/tally.json
```

For Deep, add `--measure-sample RUN/measure/sample.json --judgments RUN/measure/judgments`. For each pattern it reports members among targeted picks, members among the random slice, and, for Deep, `yes` judgments over the measurement sample. It computes a 95% Wilson interval only for measurement judgments, where every session was judged against the final definition. It rejects a measurement sample drawn from a different scope.

Phrase confidence from what was measured:

- every session in scope read (`census`): "in 3 of the 10 sessions in scope", with no range, because nothing was sampled;
- exact proxy count: "31 of 400 sessions (8%) had `lookup_order` fail twice in a row";
- Deep measurement: "about 18% of sessions (95% interval 13 to 25%, from 150 random sessions)";
- Standard random slice: "noticed in 4 of 15 randomly picked sessions", a floor rather than a rate, because readers note what they see instead of judging every session against the final definition;
- targeted picks only: "seen in 9 of 25 sessions picked for failures or extremes; not a rate".

Report `unclear` judgments separately; never fold them into `yes` or `no`.

## Explain with code

When the context brief exists, read the code behind the strongest patterns: the prompt section, tool implementation, or routing rule involved. Add at most one likely cause per card, labeled as a hypothesis, with the file path and revision. Do not claim a cause from traces alone.

## What a good card says

A good card lets someone act without opening the run folder:

- a title naming the behavior, not the metric ("Refunds promised before checking the return window");
- what happens, in one concrete example with a session and node;
- how common it is, phrased per the confidence rules above;
- why it matters, in terms of the agent's purpose;
- the likely cause, labeled as a hypothesis, when code supports one;
- what to check first, and what would confirm or refute it.

Prefer a `text` card. Use `categorical` when a split across labels is the finding (failures per tool), and `binned` for a distribution (duration). Put the narrative in `description` either way.

## Compare with earlier runs

When an earlier `kitaru-insights` run covered the same or an overlapping scope, match patterns by definition, not by name. Label each pattern new, recurring, or no longer seen, and say so on the card. A pattern absent from a later Standard sample is not proven fixed; only a measured rate supports that.
