# Full-replay method

Use this method before the prompt audit or finalist comparison. A screen rebuilds
individual model calls; a full replay starts a fresh agent task from a session's stored
top-level inputs. It does not restore arbitrary conversation checkpoints, process
memory, or external state.

## Prepare the handoff

Read [kitaru-replay-experiment](../../kitaru-replay-experiment/SKILL.md), its
[experiment contract](../../kitaru-replay-experiment/references/experiment-contract.md),
and its [comparison
method](../../kitaru-replay-experiment/references/experiment-method.md) before planning
or operating full replays. This skill selects the question, candidates, and comparison
conditions; the replay skill verifies capabilities, obtains execution approval, creates
and supervises each bounded experiment, and interprets its results. If it is
unavailable, offer to install it and preserve the handoff; do not guess the missing
execution contract.

Prepare these details before asking to run:

1. The user-accepted session-level outcome criterion and intended claim. A preference
   between two individual model calls is evidence to discuss, not automatically a
   definition of task success.
2. The exact agent-version ID, public run spec, installed adapter and construction path,
   and evidence that each requested override and tool policy is supported.
3. Exact cohort-version IDs, session membership, independent case counts, and any
   disjoint tuning/held-out split. Run start takes a cohort-version ID, not just the
   cohort's name or parent ID.
4. At least one exact evaluator-version ID, its parameters and verified agent scope, and
   evidence that it grades the accepted outcome. If none fits, use the investigation
   skill's evaluator route before execution.
5. A complete override for each experiment, including the approved prompt and supported
   model settings, plus the translated model string for each finalist. Verify the replay
   worker's provider dependencies and configuration using the [provider
   contract](model-swap-contract.md#provider-and-replay-compatibility).
6. An explicit tool policy covering every tool. Omission currently permits live
   passthrough. Resolve policy choices using the replay skill: verified isolated local
   fixtures can allow changed arguments; recorded history matches prior calls and does
   not restore external state. Use a deliberate failure or error result for
   history/static misses unless live execution is intended. External live effects
   require separate approval.
7. Expected model, evaluator, and worker work and cost, including control runs and any
   predeclared repetitions; existing experiment/run IDs to resume rather than duplicate.

Use the replay skill's current schemas and commands for creation and execution. It
requires approval before either remote write. Preserve the user's existing approval for
the same scope, and obtain additional approval only when the work or effects exceed it.

## Match the control to the question

| Question | Fresh control | Candidate |
|---|---|---|
| Does the prompt rewrite help? | Today's model with the original prompt and current model settings | Today's model with the rewritten prompt and the same model settings |
| Which model works with the approved prompt? | Today's model with the approved prompt | Each finalist with that same approved prompt |

Hold the cohort, evaluator versions and parameters, tool policy, runtime conditions, and
non-target settings fixed. Declare an effort or other setting change as part of the
candidate rather than silently changing it with the prompt. Verify that
provider-specific settings are supported; identical setting names do not prove identical
behavior across providers.

For example, after accepting prompt `P1` in place of `P0`, the full-replay control is
today's model with `system_prompt=P1`; each finalist also receives `system_prompt=P1`
plus its translated `model`. A no-override run of today's `P0` setup would mix prompt
effects with model effects. Use no override only when the unchanged configuration really
is the intended control. If the approved prompt cannot be applied faithfully, narrow the
comparison instead of claiming to isolate the model change.

Keep the analyzer screen's `reference` distinct: it must retain the recorded prompt
because it measures agreement with recorded calls and cannot accept a `system_prompt`
replacement. Today's model with the audited prompt is a separate screen candidate. Its
role does not replace the prompt-matched full-replay control.

Record the exact control and candidate experiment/run IDs. Pair their fresh results by
source session and the same evaluator version and parameters. The historical baseline
linked by an experiment is not automatically the fresh prompt-matched control. Describe
a control-to-candidate calculation as analysis of those exact results, not a built-in
Kitaru winner or significance verdict.

## Choose the right grading rule

Prefer deterministic outcome checks when independently verifiable evidence exists.
Distinguish two uses:

- **Known-case grading:** a fixed cohort may have independently reviewed expected labels
  or answers. Pin the answer key to those exact cases and evaluator version, keep it
  available only to grading, and describe the result as performance on those known
  cases. An identifier may locate a reviewed target; it is not evidence that the answer
  is correct.
- **Reusable behavior evaluation:** derive the check from inputs, structured outputs,
  and recorded tool outcomes. For example, check that a claimed refund corresponds to an
  accepted refund action and that the final structured action agrees with it. This does
  not prove that the refund was the right business decision. Avoid an ID-to-answer table
  when claiming to evaluate a general behavior.

The returns tutorial teaches the second use, so its prohibition on ticket-ID answer
tables still applies there. Keep expected answers and held-out cases out of candidate
prompts, prompt-optimization examples, agent-accessible tool fixtures, and judge
calibration used to develop the evaluator. Have the human review ambiguous targets
rather than treating recorded outputs or agent suggestions as truth.

## Small cohorts and repetitions

Count independent sessions, not model calls. Ten sessions split into five tuning and
five held-out cases leave each case worth 20 percentage points on its side. That can
expose obvious failures but cannot establish broad quality or equivalence. Related
sessions from the same conversation or trace family may provide less independent
evidence; keep related cases on the same side of the split.

Freeze the split before tuning. Use tuning cases to select the rewrite or settings, then
assess the selected change on untouched held-out cases. Once those cases influence
another choice, treat them as tuning data and obtain fresh held-out cases for a new
confirmation. If a useful split is not available, collect more independent sessions or
run a bounded known-case exploration without claiming held-out confirmation. There is no
universal minimum that makes every comparison reliable.

Analyzer `repeats` resends each reconstructed call and does not rerun the agent. For
full replays, run once by default. When stochastic variation could change a borderline
or consequential conclusion, predeclare matched repetitions of the fresh control and
candidates on the same cohort and evaluator/tool conditions. Include all repetitions in
the approved cost and work, and supervise each run through the replay skill. Repeating
five cases three times still tests five independent cases, not fifteen.

Report raw paired improved, regressed, and unchanged counts, independent case counts,
per-type results, and each repetition's variability. Keep failed, canceled, truncated,
and missing results outside quality denominators and report them separately. Use
uncertainty estimates only when their method fits the sampling and repeated-case
structure; do not treat repeats as independent samples or manufacture significance for a
tiny curated cohort. If observed variation or missing evidence can reverse the
conclusion, report `inconclusive` and explain whether more independent cases or more
matched repetitions would address the uncertainty, without promising an exact resolving
sample size.
