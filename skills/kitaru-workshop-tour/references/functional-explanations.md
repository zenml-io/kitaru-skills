# Functional explanations

Explain the Kitaru flow as it runs. Treat the visible conversation as a concise
product walkthrough, not a log of the coding agent's internal work. Keep setup
compact, but state what each durable operation produced and why that object is
needed next.

Assume the user has not read the sample agent, has not used Kitaru before, and does not know its vocabulary. Explain from the concrete returns example first. Introduce a product term only when the current step makes its purpose visible.

Use only terms that exist in Kitaru's product, CLI, API, or documentation when naming an object. Do not coin a noun for a temporary explanation, group of fields, or stage in the tour, and do not replace an official object with a friendly-sounding alias. Explain an unfamiliar Kitaru term from the concrete example, then use that term consistently. Use ordinary verbs and sentences for everything else. For example, say “Here is what the experiment will do” rather than naming the summary a “run card,” and say “the agent configuration has changed” rather than introducing an “agent fingerprint.”

## Explain durable transitions

Before a durable action, state what will change, why it is needed, what the user can inspect afterward, and whether approval is required. Afterward, state what was created or reused, retain the exact ID in the current task context, and name the next decision.

Do not narrate commands, file reads, reference loading, schema lookup, cache
paths, temporary files, parsing, quoting, retries, or status checks. In
particular, avoid updates such as “I found,” “I loaded,” “I hit a parsing
problem,” or “I am deriving the payload shape.” These statements describe the
coding agent, not Kitaru. Resolve routine work quietly. If recovery becomes a
real blocker, name the intended Kitaru action, the blocker, and the smallest
recovery once.

Do explain installations, server selection, registration, imports, durable
review writes, and evaluator runs because they change the user's environment or
create a Kitaru object. When a command updates or installs something, explain
what capability it provides and why the tour needs it before asking for
approval.

Keep explanations direct. Do not quiz the user or make them repeat information before continuing.

## Give the audience a starting mental model

Before any setup check, distinguish the coding agent from the returns agent in
one or two sentences. The coding agent is the assistant conducting this tour:
it can inspect the template and use Kitaru tools, while the returns agent is
the recorded customer-support system whose past behavior the audience will
inspect. Then state the path in ordinary language: establish the prepared
environment, inspect the recorded population, review five examples, make one
repeatable check from a human-confirmed relationship, and compare one bounded
change.

When the host offers a visible task, todo, or plan interface, keep that same
path there as a short status outline. The outline is for the audience to orient
themselves, not a transcript of agent mechanics. Update it only when a stage
has produced a durable result or the evidence changes the route.

At the opening, conclude with what the first readiness check will establish,
then continue into that read-only check. Use a wait only at consequential
handoffs: after the imported population is opened in the frontend, before
durable review writes, after later frontend visits, and before paid or live
execution. State what the audience has just learned and name the next
meaningful action. Do not announce a "pause" or ask the audience to perform a
ritual acknowledgement.

## Explain the flow in context

### Connect to Kitaru

Explain that a Kitaru server is where agents, recorded runs, annotations, and
review results are stored. This route uses Kitaru Cloud. If the user already has
a healthy cloud server selected, say that the tour will keep using it. If setup
is missing, explain the smallest required login or server-selection change and
why it unlocks the next step.

When CLI or MCP setup is relevant, explain the distinction without turning it into a choice the user must make: the CLI and MCP are two ways for the coding agent to work with the same Kitaru server. A working project-local CLI is enough for the tour; MCP can make later agent interactions more direct.

### Identify the agent and its history

Before registration, explain that Kitaru ties recorded behavior to an exact agent version so later findings can be traced back to the code that produced them. Registration does not run the agent or judge its quality; it gives that code version a durable identity.

Before import, explain that the template includes 30 already-recorded customer-support runs. Importing them gives Kitaru the complete sequence of model messages, tool calls, and tool results, which is what lets the user inspect what actually happened rather than trusting the final reply alone.

After registration or import, state the exact durable result in approachable terms. For example: “Kitaru now knows which version of the returns agent produced these 30 runs, so we can review its behavior without running or paying for the model again.”

After that statement, open the agent sessions page. Explain that each row is a
recorded run with its input, model and tool evidence, final action, and later
review or evaluation results. The audience should inspect the population before
the tour applies any evaluator or chooses a case. Wait for their return.

### Prepare the review

Before the deterministic survey, explain that the coding agent will apply the
same pinned checks to every recorded run before choosing what deserves close
reading. State that these checks read stored evidence and make no model calls.
Show this compact orientation table before running them:

| Evaluator | Plain-language question |
|---|---|
| Session diagnostics | Is the recorded trace complete and structurally trustworthy? |
| Trajectory signals | Did the agent repeat tools, retry a failure, or enter a short cycle? |
| Tool health | Did a tool fail, return no useful result, or contradict its recorded status? |
| Operating guardrail | Did the run stay within the accepted service ceiling? |
| Fast-path target (optional) | Which otherwise valid runs are relatively slow, costly, or tool-heavy? |

Explain that the first three are descriptive signals. They help choose what to
inspect but do not decide whether a refund, replacement, or escalation was
correct. Each resource configuration is a rule and can return pass, fail, or
unresolved. The three descriptive evaluators fit in one 90-pair job. The
operating guardrail runs separately so the human can confirm the exact ceiling
that a later comparison reuses. If the human accepts the optional fast-path
target, it runs in its own job to highlight the relative resource tail; it does
not carry into replay.

After the survey, first show expected, completed, failed, and missing pair
counts. Then show a findings table that makes the results useful without
inventing one aggregate verdict for the descriptive evaluators:

| Evaluator | Completed pairs | Unresolved pairs | Named signals or result |
|---|---:|---:|---|

For session diagnostics, trajectory signals, and tool health, report the named
signals the evaluator actually returned and how many sessions exposed each
one. Do not translate their absence into a synthetic `clean` verdict. Report
the operating guardrail and, when run, the fast-path target separately as pass,
fail, or unresolved using each evaluator's own top-level result. If the target
was declined, say that it was not run. Explain that an operating failure exceeds
the accepted service envelope, while a fast-path failure identifies a relatively
resource-heavy run for inspection and does not make its behavior wrong. If an
output has mixed ceiling details but no top-level result, keep it unresolved and
describe the mixed details rather than choosing a label. Summarize the findings
in ordinary language, then show a small session matrix containing the customer
request, final action, notable signals, available resource results, and reason a
session may deserve inspection. Do not dump every stored evaluation row. Missing
or failed evaluations remain unresolved evidence rather than quietly
disappearing from the population.

Before adding observations and highlights, explain that the coding agent has read the complete traces and will point to evidence worth noticing. An annotation records the observation; a highlight places it beside the exact tool result, message, or field that supports it. These are prepared suggestions, not the user's verdict.

Before creating the investigation, explain that it turns the five selected
runs into one ordered frontend review. The verdict buttons record the required
human decision on each complete session. Written notes are optional and should
record additional reasoning only when the reviewer finds that useful.

After creation, say what was saved and make the division of labor explicit:
the coding agent prepared evidence pointers, Kitaru keeps them attached to the
trace, and the user decides Acceptable, Problematic, or Uncertain for all five
sessions. Do not overstate the meaning of optional notes or later treat them as
careful annotations when the user was simply moving through the review.

### Turn judgment into a reusable check

After the user returns, begin with what their verdicts established. Then explain that a cohort is a frozen set of the exact reviewed examples: the problematic behavior plus an acceptable comparison that marks its boundary. Freezing the membership prevents the meaning of the check from drifting later.

Before evaluator selection or creation, explain that an evaluator is a repeatable rule applied to recorded runs. The tour is turning the relationship the user just confirmed into a narrow check, then running that check across all 30 sessions to see where the same evidence appears. An evaluator version records the exact rule used so the result remains reproducible.

After the run, lead with the result in plain language. Only then connect the result back to the terms: the reviewed examples became the cohort, the reusable rule became the evaluator version, and Kitaru preserved both beside the evidence and human judgments.

Send the user to the cohort and evaluator pages next. Explain what each page preserves and ask them to come back after they have looked. Do not continue into experiment setup until they return.

### Test one bounded improvement

After the user returns, explain the difference between measuring recorded behavior and testing a change. The experiment will start fresh agent tasks from the reviewed cases' stored top-level inputs, apply one small candidate override, and compare the resulting sessions with the recorded evidence using the exact evaluator the user just inspected. It does not restore conversation checkpoints, process memory, files, or the original external world.

Before experiment creation, briefly explain the proposed change, tool behavior, expected model work, cost uncertainty, and what the comparison can establish. Let the replay-experiment skill obtain approval after that explanation. Do not make paid execution feel like an automatic consequence of completing the review.

Make the candidate change inspectable before asking for approval. Show a short
before-and-after prompt or configuration diff containing only the relevant
changed instruction, then show this compact flow in ordinary language:

```text
Recorded ticket -> same agent with the visible override -> fresh replay
                -> behavior evaluator + tool health + operating guardrail
```

Explain that Kitaru stores the candidate separately as an experiment override;
the checked-in agent code and the recorded baseline do not change. If the
normal creation route uses the CLI, show the prepared override fragment or
equivalent configuration before approval. After an approved creation, it may
show the resolved configuration. Do not interrupt the tour to discover a
command solely for display, and never show credentials.

After settlement, lead with the experiment page. Explain how to select the run, where the baseline and candidate evidence appear, and what improved, regressed, stayed unchanged, failed, or remained missing. Ask the user to inspect it and return before the flow completes.

## Keep explanations honest

- Explain what the current action actually proves. Registration identifies code; it does not validate behavior. Import preserves recorded evidence; it does not make the evidence representative.
- Distinguish the coding agent's prepared observations from the user's verdicts
  when that distinction becomes relevant. Optional written notes may be useful
  context, but they are not required labels and their presence does not prove
  that the reviewer understood or endorsed the prepared observation.
- Do not claim prevalence from five reviewed examples. The full 30-session evaluator result can describe this synthetic population only.
- If a step is resumed rather than created, explain that Kitaru already has the durable result and the tour is reusing it. This shows persistence without pretending the work happened again.
- If something fails, preserve the explanation: name the intended concept, the exact blocked action, and the smallest recovery. Do not replace the tour with raw command output.
