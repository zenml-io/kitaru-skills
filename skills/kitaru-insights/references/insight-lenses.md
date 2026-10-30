# Insight lenses

Use this reference to decide where readers look and which findings become cards. A lens is a place to look, not a finding. Every lens names how it is detected, because that decides what a card may claim.

## Contents

- [How each lens is detected](#how-each-lens-is-detected)
- [Count lenses](#count-lenses)
- [Read lenses](#read-lenses)
- [Lenses from the user's own material](#lenses-from-the-users-own-material)
- [Test lenses](#test-lenses)
- [Choose which cards to write](#choose-which-cards-to-write)

## How each lens is detected

| Detection | Meaning | Who does it | What a card may claim |
|---|---|---|---|
| Count | Arithmetic over recorded fields | The analyzer's resource cards, `scope_counts.py`, or node filters | Exact counts over the whole scope |
| Read | A model reads session text | Reader subagents find it; Jev or measurement subagents measure it | Examples, then a measured rate |
| Own material | The user's eval suite and the agent's own rules | The main agent, from the repository | Coverage gaps and rule compliance |
| Test | A "what if" a trace cannot show | A prepared replay experiment | Only that an experiment is worth running |

## Count lenses

Read these first; they are cheap and exact. Prefer the analyzer's resource cards when the installed analyzer produced them (cost concentration, where time goes, context growth, prompt cache use, trajectory paths). Otherwise compute the session-level ones with `scripts/scope_counts.py` and skip node-level ones rather than fetching every node of every session.

- **Loud failures:** failed sessions and erroring nodes. The dashboard already shows these; a card needs a shared cause or an unexpected concentration to earn its place.
- **Cost concentration:** how much of the spend the costliest sessions account for, and what those sessions have in common.
- **Latency:** where recorded time goes, by tool or model, never summing overlapping parallel calls.
- **Prompt cache:** the share of input served from cache, and calls where the system prompt changes between consecutive model calls. Sources differ on whether `input_tokens` includes cached reads; when `cached_input_tokens` exceeds `input_tokens`, the source counts them separately.
- **Context size:** model input that grows across a session, and single nodes far larger than the agent's other calls.
- **Paths:** each session's sequence of tool names. Common paths show habits the user may not know about; paths only one session took are anomalies worth reading.
- **Statistical outliers:** sessions far outside the scope's own distribution of duration, cost, tool calls, or model calls.

## Read lenses

Give readers this checklist, and judge each item against what the task needs; more work is not automatically better.

- **Silent failures:** the session completed but did the wrong thing, such as acting against a policy it had read. These are usually the most valuable cards.
- **Verification before claiming:** the agent acted or answered before checking the evidence that decides it, or accepted the first result where the task needed more than one source.
- **Groundedness:** replies or outputs that state facts, timelines, or commitments no tool output supplied.
- **Objections and corrections:** the user pushing back, correcting, repeating a request, or interrupting. Some sources record interruptions directly; check node attributes before reading for them.
- **Dissatisfaction:** frustration, complaints, or abandonment language.
- **Incomplete conversations:** the session ends with the user's request unresolved, such as an unanswered agent question. Leaving can also mean success; require evidence before calling it a drop-off.
- **Repetition:** the agent repeating itself, re-asking for information already given, or redoing work, beyond exact repeats a counter already found.
- **Tool use:** wrong tool for the request, tool results the agent ignored, argument format errors, and registered tools never called.
- **Security:** personal data or secrets in replies or tool arguments, and instructions inside a tool output or user input that the agent obeyed. Cite node IDs only; never copy the sensitive text into a card.
- **Demand:** what users actually ask for compared with what the agent was built for, including out-of-scope requests.
- **Bright spots:** what the best sessions did that others did not.

## Lenses from the user's own material

Build these during the context brief when the repository is reachable:

- **Rule compliance.** Extract every rule the agent is given: system prompt lines, policy text, and guards in code. Write them to `RUN/rules.json` (format in [subagent-briefs.md](subagent-briefs.md)). Readers check each rule; Deep measures each one as a yes-or-no question. A rule broken in many sessions is a strong card because the user already agreed it matters.
- **Eval coverage.** Find the user's eval suite (pytest or notebook evals, DeepEval, promptfoo, Ragas, LangSmith or Langfuse eval code, Kitaru evaluators) and list what each eval checks. After grouping, compare: a common failure pattern that no eval checks becomes an eval coverage gap card. Report the eval files read; do not run the user's evals.

## Test lenses

Some questions are "what if" questions: would a stronger model, more context, more reasoning time, or a separately evaluated component have done better? A trace cannot answer them. Write an opportunity card instead:

- the cohort where the opportunity appears, with session IDs;
- the observable symptom (for example the agent hedging, reporting missing information a tool could supply, or a retrieval tool returning empty results before a failure);
- the candidate change and the evaluator that would judge it;
- a hand-off to `kitaru-replay-experiment`, which owns tool policy, approval, and execution.

Flakiness is a test lens too: it means the same input gives different results, and traces usually hold one run per input. Recommend replaying the same inputs several times, or evaluating the component on its own, rather than claiming flakiness from one run each.

## Choose which cards to write

Write at most eight cards. Rank candidates by three questions, and drop any that fails one:

1. **Is the evidence specific?** A session, a node, and a concrete example the user can open.
2. **Is it news?** Prefer what the user would not have guessed: silent failures over loud ones, a broken rule over a generic quality complaint, a cause in the code over a metric. Drop a card that restates an analyzer card or a number the dashboard already shows, unless it adds a cause or a narrower cohort.
3. **Is there a next step?** A fix to try, a review to run in `kitaru-investigation`, or an experiment to set up.

Then order by impact on the agent's purpose. Include at most one bright spot and at most two opportunity cards, so findings stay the core of the run.
