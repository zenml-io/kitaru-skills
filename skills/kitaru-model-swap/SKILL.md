---
name: kitaru-model-swap
description: Help a user choose the right model for their agent from its own recorded traces, comparing quality, cost, speed, and openness. Use when a user asks which model is best for their agent, whether to switch or upgrade models, how an open, local, Ollama, cheaper, faster, or newer model would do, how to cut LLM cost or avoid provider lock-in, or wants to compare models on production traffic before shipping a change. Imports traces, sends each recorded model call to candidate models with the kitaru/model-swap analyzer, renders an HTML report, collects the user's verdicts on the differences, scores quality from those verdicts, and hands finalists to a replay experiment when the agent supports it.
---

# Kitaru model swap

Help the user choose the right model for their agent: better, cheaper, faster,
or open. Kitaru sends each recorded model call, exactly as it was recorded, to
candidate models and compares their answers. It does not re-run the agent, and
it runs on the user's worker with the user's keys. The user's own verdicts on
the differences decide quality; a replay experiment confirms the finalists end
to end.

Recommend; do not decide. Never change the agent's configuration yourself.

## Core contract

- Run every Kitaru CLI command with `KITARU_ACTIVE_SKILL=kitaru-model-swap` set,
  and prefer `--output json --machine --non-interactive --no-browser`.
- Never ask for, read, echo, or store an API key in chat, files, parameters, or
  command lines you show. The user exports the key in their own shell and passes
  it to a Kitaru provider connection by variable reference, or sets it in the
  worker's environment. Candidates only name the variable.
- Always run a dry run first and get explicit approval of the estimated spend
  before a run that calls paid endpoints. Always pass `max_spend_usd` on a paid
  run.
- A wait timeout is not a failure. Never start another paid analysis of the same
  import without first checking whether the earlier job is still running or
  already finished.
- Include the model the agent uses today as the `reference` candidate. It is
  compared and scored like every other candidate, and its agreement with its own
  recording is the noise floor.
- Agreement means "behaves like today's model", not "is right". Never present
  agreement as quality on its own; quality comes from the user's verdicts.
- Report provider failures (timeouts, rate limits, HTTP errors, empty replies,
  tool-call parse errors, refusals, replies truncated by the token limit) as
  setup problems, never as model quality.
- Keep calls with inferred tool schemas out of conclusions; say how many calls
  used them.
- Use Kitaru product terms: agent, session, node, import, analyzer, insight,
  connection, worker, annotation, cohort, evaluator, replay.

## Load references only when needed

- Read [references/model-swap-contract.md](references/model-swap-contract.md)
  before running any Kitaru command in this skill: exact commands, analyzer
  parameters, report fields, and annotation shape.
- Read [references/tool-schemas.md](references/tool-schemas.md) when the
  coverage shows `missing_tool_schema` skips, or before importing traces that
  are known to lack tool definitions.
- Read [references/verdict-quality.md](references/verdict-quality.md) before
  step 5 and whenever you report quality.

## 1. Set up and import

1. Check `kitaru status`. If Kitaru is missing or not logged in, install it
   (`uv add "kitaru[cli,worker]"`) and log in: `kitaru login --local` for a
   local server, or `kitaru login` / `kitaru login SERVER` for a managed or team
   server. Ask which one the user wants when it is not obvious.
2. Make sure a worker that claims analyzer tasks is running
   (`kitaru worker start --claim importer --claim analyzer --concurrency 10`). A
   local Ollama candidate needs the worker on the same machine as Ollama.
3. Find or register the agent, then import a recent, bounded slice of traces:
   the last 7 days from the user's trace provider through its importer and
   connection, or a JSONL export file. Use the matching Kitaru import guide for
   the provider. Route unsupported sources to `kitaru-importer-builder`.
4. Note the `import_id`.

If the user already has an import, reuse it.

## 2. Ask what matters, then choose candidates

Ask one question: what matters most for this agent right now: better answers,
lower cost, faster replies, or not being locked to one provider? Several answers
are fine. Use it to pick candidates and to lead the summary later.

Then ask whether any provenance rules apply, for example no models from labs in
certain countries, or hosting only in a given region. Record each candidate's
`origin` (`lab`, `lab_country`, `host`, `host_region`) as far as the user or the
provider's documentation states it, and pass the rules as `excluded_origins`.
Excluded candidates are still compared but never recommended; say so, and never
guess an origin the user has not confirmed.

When the steps are hard or answers vary, suggest `repeats` of 2 or 3 to read
run-to-run noise, and say it multiplies calls and spend.

Suggest a small set, one line each, covering those goals. A candidate is a
setting, not only a model: today's model at a lower `reasoning_effort`, or with
a cleaned-up `system_prompt`, is often the cheapest change that holds quality,
so offer those next to other models. Only use a prompt the user wrote or
approved, and never build one from the recorded failures, which would tune the
prompt to the very calls it is then judged on.

- the model the agent uses today, as the `reference`. Always include it: today's
  model run again is the noise floor, and without it the report cannot tell a
  real difference from run-to-run variation (it says so in its notes);
- today's model at a lower effort level, and with a cleaned-up prompt when the
  user has one, each as its own named candidate;
- one open-weight model on a hosted provider (`"open_weights": true`);
- one local model if Ollama is installed (`ollama list` shows what is available;
  base URL `http://localhost:11434/v1`, price zero, `"open_weights": true`);
- one cheaper tier and, when quality matters, one stronger model from the
  current provider.

Set expectations up front when the agent delivers its final answer as a
free-text tool argument (for example a `final_result` or `reply` tool whose
argument is the message to the user). No two models word an answer identically,
so every candidate, including the reference, will show most of those calls as
`same_tool_different_args`. Agreement says little there: quality rests on the
user's reviewed verdicts and on per-argument agreement for the structured
fields. Estimate the review load before the paid run (roughly the sampled calls
per candidate times the share of such calls) and tell the user that 10 to 20
reviewed disagreements per finalist give an early read.

Before offering a judge or decision candidates, tell the user what leaves the
worker, and let them opt in knowing it: a decision candidate is sent the
rebuilt conversation of each call it answers (including the system prompt and
tool results), the tool names and descriptions, argument names, and enum
values; a judge is sent both answers it compares. Recorded trace content goes
to that decision service (TypeSafe, Cloudflare, or OpenAI), not only to the
candidate providers the user already chose.

When the review load is large, offer a decision-model judge to order it:
TypeSafe Jev (`"judge": {"kind": "jev"}`, key `TYPESAFE_API_KEY`; Jev may
require early access from TypeSafe), Cloudflare Clef on Workers AI (`"kind":
"clef"` with the account's run URL, which contains the account ID, as
`base_url`, and `"api_key_env": "CLOUDFLARE_API_TOKEN"` passed explicitly), or
OpenAI's Decisions API (`"kind": "openai_decisions"`, which usually reuses
`OPENAI_API_KEY`). It rules only on disagreements where a candidate called the
same tool with different arguments or gave different text, never on a different
tool choice, and returns a probability that the two answers are equivalent, so
review can start with the answers most likely to differ. Explain that it is
fast and cheap but can be swayed by text inside a recorded answer, that its key
goes into the same connection as the candidates' keys, and that its ruling only
orders the review; the user's verdicts still decide quality. Decision models
have no bundled price, so a judge needs a `price` when `max_spend_usd` is set;
its spend counts against that cap, and a missing judge key fails the whole
analysis at the start.

For each paid candidate, decision candidate, and the judge, find which
environment variable will hold its key: `TYPESAFE_API_KEY` for Jev and
`OPENAI_API_KEY` for OpenAI Decisions on their default URLs; for Clef, and for
any decision model with a custom `base_url`, the variable named in its
`api_key_env`. Then set up keys with the commands in the contract reference,
which the user runs themselves:

- **No connection yet:** the user exports the key in their own shell
  (`export NAME=...`, or `read -rs NAME && export NAME` to keep it out of
  history), then runs
  `kitaru connection create ... --set-secret NAME="$NAME" --default`, so the
  key never appears literally in the Kitaru command line.
- **A connection lacks a needed key:** the user runs
  `kitaru connection update CONNECTION --set-secret ...` the same way. An update
  replaces the whole secret map, so the user passes every key the connection
  should keep, not only the new one. Adding a key for a judge or a decision
  candidate, such as `TYPESAFE_API_KEY` or `CLOUDFLARE_API_TOKEN`, follows this
  flow.

Confirm the connection lists the expected `secret_keys` without reading values.

Ask about provider settings only when relevant: a model served without a
tool-call parser needs `tool_call_format: "hermes"`; reasoning models may need
`reasoning_effort`; OpenAI's reasoning models (GPT-6 and later) refuse tools
with reasoning on at `/chat/completions`, so give them `"api": "responses"`.

Pick a judge that is neither a candidate nor today's model: a model may favor
answers like its own, and the report notes it when a chat judge runs a
candidate's model or the recorded one.

## 3. Estimate, approve, run

1. Run the analyzer with `"dry_run": true`, render the report, and show the
   user: calls per candidate, estimated spend per candidate and in total, and
   coverage (replayable versus skipped calls). The estimate covers LLM
   candidates and decision candidates (each decision candidate's is at
   `decision_candidates[].estimate`, with `calls` and `spend_usd`) but not the
   judge; when a judge is set, say so and add its likely cost from the `price`
   in the parameters you passed, because the report does not carry it.
2. If coverage shows `missing_tool_schema`, follow
   [references/tool-schemas.md](references/tool-schemas.md) before going on.
3. Check each candidate's `price` in the dry-run report. A candidate with
   `price: null` (shown as "unknown price" in the rendered report) blocks a
   capped run: the analyzer refuses `max_spend_usd` until every candidate,
   every decision candidate, and the judge if one is set, has a known price.
   Ask the user for that model's input and output price per million tokens and
   set an explicit `price` on the candidate, or drop it. Decision models have
   no bundled price, so every decision candidate and a decision judge need an
   explicit `price` in the parameters whenever `max_spend_usd` is set; check
   the judge's `price` in the parameters, not the report. When a candidate sets
   `provider_settings.max_tokens`, each call reserves its full `max_tokens`
   output against the cap, and the analyzer refuses to start if one call's
   reservation alone exceeds `max_spend_usd`.
4. Ask for approval of the spend and a cap. Decision candidates run first,
   before the LLM candidates, and share the same `max_spend_usd` and
   `time_budget_seconds`; the LLM candidates get what is left. A judge's spend
   and time count against the same limits. With a judge or decision
   candidates, leave headroom in `max_spend_usd` and `time_budget_seconds`, or
   the last LLM candidates may not run (the report shows each candidate's
   `calls_not_run`). Run again without `dry_run`, with `max_spend_usd`, an
   `--idempotency-key`, and `--wait --timeout 900`.
5. If the wait times out, the analysis keeps running on the worker. Take the
   `job_id` from the timeout error, follow it with `kitaru job watch JOB_ID` or
   check it with `kitaru job get JOB_ID`, and consider another run only after
   the job has settled. Repeating the same command with the same idempotency key
   returns the original job instead of starting a new one.
6. If the run stopped early (`max_spend` or `time_budget`), say so and offer to
   rerun with a smaller `max_calls` or a higher cap.

## 4. Show the comparison

Render
`kitaru insight report --import-id IMPORT_ID --out model-swap-report.html` and
give the user the path.

Read the checks on the checker before trusting the numbers, and say what they
show: replies cut off by the token limit (`truncated`), timeouts, and provider
errors are failures, not disagreements, and a high count means fixing
`max_tokens` or the provider setup, not the model; `judge_check` shows how often
the judge changed its ruling when only the order of the answers changed, and
the notes flag an unstable judge. Open a handful of raw disagreements yourself
and show them to the user: a wrong grader or a contradictory recorded answer
explains a surprising number more often than the model does.

Then lead with the report's **Best for** rows, ordered by
what the user said matters. When the report names no **Cheapest** or
**Fastest** candidate, say why in its words: no candidate behaves like today's
model often enough, or today's model varies too much from run to run for step
agreement to vouch for an equivalent. Do not pick one yourself from the rates;
point to the **Worth a full replay** row instead. Then summarize each candidate
in plain words:

- how often it picks the same tool or gives the same answer as today's model,
  read against today's model's own noise floor, and per-argument agreement on
  structured fields; quote each rate with its 95% interval
  (`agreement_interval`, `tool_choice_interval`), and do not rank candidates
  on gaps that fall inside the intervals, since with a few dozen calls a gap of
  a few points is usually noise;
- cost per call and per month, and why (price, tokens, reasoning tokens,
  retries);
- median and tail latency;
- whether it is open-weight;
- failures by category and what to change in provider settings;
- with a judge, its `judged_equivalent`, `judged_different`, and
  `judged_unsure` counts and any `judge_failures`, reported as setup problems.

Say plainly that these are similarities to today's model, and that the next step
decides which answers are right.

Then report the decision-model fit, which every report includes at no extra
cost: how many sampled calls, and what share of recorded cost, are
**decision** calls (the model only chose a tool and enum or boolean values),
**partial** calls (the tool choice is a decision, but free-form values or text
need an LLM), or **generative**, with the main reasons. Calls whose tool
schemas were inferred count as generative, because an inferred schema is not
trusted for decisions. When decision calls or a large partial share exist,
offer to try a decision model on them as a `decision_candidates` entry (Jev,
Clef, or OpenAI Decisions; same `kind`, `base_url`, `model`, `api_key_env`,
and `price` fields as a decision judge, plus a `name`), after telling the user
what it is sent (see step 2), with the same key setup, dry-run, price, and
approval steps as any paid run. A run may hold only decision candidates, with
`candidates` empty. Report its tool-choice agreement, how often all its
decisions matched, per-argument agreement, failures, and `calls_not_run`. For
savings, compare its `decision_call_cost_usd` with
`recorded_decision_call_cost_usd`: both cover only the calls whose shape is
**decision**, which a decision model could take over entirely. Do not set its
`cost_per_call_usd` against the recorded model's full cost per call; that
figure covers only the decision parts of every asked call, and a partial call
still needs an LLM for the rest. Explain that moving a partial call means
changing the agent to decide with the decision model and generate the rest
with an LLM.

## 5. Judge the differences

Review happens here in chat because the Kitaru dashboard has no view that
compares a candidate's answer with the recorded one. Each verdict is still
stored in Kitaru as an annotation on the session node, so it outlives this
conversation.

Walk through the disagreements in small batches of three to five, grouped by
what the recorded model did, starting with the candidates the user is most
interested in. When a judge ran, the report orders each group by its ruling:
different, then unsure or not judged, then equivalent, within each group. The
judge does not choose which disagreements the report keeps. Follow that order,
and suggest before the first batch that the likely equivalent ones be reviewed
last. Skip them only if the user explicitly agrees; skipped disagreements stay
unreviewed, are reported as unreviewed, and never count as equivalent or as a
verdict. Skip disagreements whose `schema_source` is `inferred`. For each, show
both answers in one or two lines and ask: "Today's model did X; this candidate
did Y. Which is right?" Offer: recorded correct, candidate correct, both
acceptable, both wrong, unsure.

Store only the user's exact choice, with the command in the contract reference,
including the run's insight `id` and the candidate's `model`. Never store your
own opinion as a verdict. Never turn a disagreement's `judge_equivalent` into a
verdict or a preselected answer, and never skip a disagreement on the judge's
ruling without the user's explicit agreement; show its `judge_probability` at
most as a hint the user is free to ignore.

Stop when the user wants to; then compute and show the verdict-backed quality
per candidate following
[references/verdict-quality.md](references/verdict-quality.md), including how
many disagreements were reviewed. A candidate that differs from today's model
can score higher than it.

## 6. Prove the finalists

Start from the report's **Worth a full replay** row: every candidate except
clear failures, plus the cheapest. Step agreement often ranks a cheap model that
keeps outcomes low, so do not cut the list to the top few by agreement rate.
With the user, remove only candidates the goals from step 2 rule out (price,
provenance, openness, latency) or that the verdicts show getting important
calls wrong, and keep the cheapest candidate the user would accept even if it
ranks low. A full replay of a few dozen sessions usually costs a few dollars
per candidate, so replaying more finalists is cheaper than missing the right
one; give the user that estimate before they trim further. Only a full replay
graded on outcomes shows which finalist keeps them.

Before handing off, settle what a full replay can show:

- **Headroom.** Ask for, or read from the baseline evaluation, how often today's
  model already passes. At 95% or more there is little quality left to gain:
  frame the run as "same quality, lower cost or latency", and ask whether a
  finalist holds quality, not whether it beats today's model.
- **Noise.** Run today's model as its own arm: a second experiment on the same
  cohort, tool policy and evaluators with no override, which replays the agent
  unchanged and measures how much outcomes vary when nothing changes. Count
  that arm in the cost estimate. A difference smaller
  than that, or whose 95% interval includes zero, is no evidence: never
  recommend switching for quality on it, and when the user is iterating, say
  how many more sessions would resolve it.
- **Hard cases.** Recorded traffic skews easy, because users try what they
  expect to work. Build the cohort from a random sample of sessions plus
  sessions people found hard: complaints, escalations, human overrides, and
  reopened cases. Ask the user for their session ids or for the tag or
  annotation that marks them; do not pick them from the step comparison, since
  sessions where candidates disagreed would tilt the cohort toward them. Report
  results for the random sample and the hard cases separately.
- **Held-out sessions.** When the user changes prompts or settings between
  rounds, create two cohorts from disjoint sessions before the first round, a
  tuning cohort and a held-out cohort, and keep a change only when the held-out cohort improves too
  (or holds, when the goal is cost). A gain only on the tuning cohort is
  overfitting.
- **The evaluator.** Prefer a programmatic check (exact label, schema, tests)
  when the outcome allows it. An LLM evaluator should not be a finalist's
  model or today's model, should score each replayed session on its own
  without being told which arm produced it, and should score checkable
  yes-or-no claims rather than a 1 to 5 scale. Run it
  twice on a few sessions and report whether any verdict changed before
  trusting it. Keep replays that timed out, errored, or were cut off out of the
  quality denominator and report them apart.

Check whether the agent can replay with a model override: run
`kitaru agent version get AGENT@VERSION`. Replay is possible only when the
version's `run_spec` is not null and `run_spec.runtime_capabilities.overrides`
is true. Whether the sessions were imported or recorded live does not decide
this; the agent version does.

- **Replay possible:** translate each finalist into the model string the agent's
  framework accepts, because the replay `model` override goes to the agent's
  framework, not to the analyzer. For Pydantic AI that is a `provider:model`
  string such as `openai:gpt-5-mini`, `openrouter:qwen/qwen3-32b`, or
  `ollama:qwen3:8b`; other frameworks name models their own way. Confirm the
  worker that runs the agent has that provider's credentials and, for local or
  self-hosted models, its base URL. Report a finalist the framework cannot
  address as not replayable instead of forcing it. Then create the cohort
  described above (`kitaru cohort create NAME --agent AGENT --session SESSION
  ...`) and hand off to the `kitaru-replay-experiment` skill with the cohort
  version, one experiment per finalist with its translated model string as the
  override plus the no-override experiment for today's model, and the user's
  verdicts as the accepted behavior for choosing or authoring an evaluator. That skill owns the
  tool policy, approval, and interpretation.
- **Replay not possible** (no run spec, or `overrides` is false, as for
  importer-backed adapters that record a provider trace after the run): say that
  a full replay is not available for this agent version, so the step-level
  comparison and verdicts are the evidence. Explain that recording the agent
  through a Kitaru adapter that supports overrides would make end-to-end replay
  possible, and offer `kitaru-adapter-builder` when the user wants that.

## 7. Recommend

End with a recommendation, not a decision, framed by the user's goals:

- which calls or tools a decision model could take over, from the decision-model
  fit and any decision candidate results, and what the agent change would be;
  state any savings as `decision_call_cost_usd` against
  `recorded_decision_call_cost_usd` on fully decision-shaped calls, and say
  that partial calls keep an LLM for their free-form parts;
- the best candidate for each goal they named, with the evidence: verdict-backed
  quality and how many verdicts back it, cost per month, latency, openness,
  origin, and replay results when available; never recommend an excluded
  candidate. Present **Best for** picks as candidates to confirm, not a single
  winner: in calibration against full-run task success on five agents, step
  agreement kept the best model near the top but often ranked the cheapest
  model that held quality low, and a single "cheapest within 10 points" pick
  could still lose task success. Confirm the finalists with a full replay
  before switching;
- the report's **Best mix** when it moves some steps: which steps (named by
  what a router sees before the call, such as "first turn" or "after
  lookup_order") go to which candidate and which stay on today's model, with
  the combined cost and the agent change needed to route by step. Say which
  steps stayed put for too few calls (`too_few_calls`, below `min_mix_calls`),
  because today's model does not match its own recording there
  (`noisy_reference`), or because the pick did not hold on held-out sessions
  (`held_out: failed`); flag picks with too few held-out calls to confirm
  (`held_out: too_few`); and say that today's cost comes from the reference's
  replay when there is one (`today_source`). A mix is a shortlist too: replay it
  before routing traffic;
- that costs per session and month assume the recorded number of steps: point
  to tokens per call, and say a full replay is needed to know cost per task for
  a model that may take more turns or retries;
- calls or tools where today's model should stay, and why;
- what still needs a check: few reviewed disagreements, many failures, inferred
  schemas, reasoning-heavy steps, an unstable judge or evaluator;
- when a finalist's difference from today's model is within noise, say so in
  those words: for a quality goal the recommendation is not to switch; for a
  cost goal it is that the cheaper finalist held quality on this many sessions,
  with the interval.

Give the configuration change needed to switch, as the base URL and model name
the agent would use, and do not apply it. Suggest rerunning the comparison on
new traces when models or traffic change.
