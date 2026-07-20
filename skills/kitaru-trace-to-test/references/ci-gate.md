# CI regression gate

Read this file only after a candidate experiment has produced useful evidence.
The gate is the last rung, not a substitute for boundary validation.

## Gate eligibility

A case is eligible only when:

- import produced an exact immutable execution ID;
- a PydanticAI message-history boundary validated with blocked fallback;
- evidence is `recorded_path_comparable`;
- the objective and every expected protection appear in the experiment;
- the bounded rerun is PASS;
- repeating the same idempotency request returns the same stored attempt.

A root-input replay, divergent tool path, blocked recorded response, missing
protection, HOLD, or FAIL is not gate-ready.

## Recurring authorization

Treat a live CI gate as standing authorization for future persistent
registrations and paid replay requests. Before enabling it, show:

| Authorization fact | Required value |
|---|---|
| Triggers | pull request, push, schedule, or manual |
| Frequency | expected runs per day, week, or month |
| Registration | one immutable AgentVersion per candidate commit |
| Credentials | provider and CI secret scope |
| Spend | maximum per run and estimated recurring total |
| Retries | job retry behavior and idempotency key reuse |
| Control | who can disable or change the required job |

Obtain explicit standing authorization for that configuration. Without it, keep
the live test behind `KITARU_RUN_REPLAY_GATE=1` and leave the CI job disabled or
manual.

## Exact experiment pattern

Use the exact experiment ID. Register the current candidate with a
commit-derived immutable label. Derive the idempotency key from the candidate
label and the frozen experiment identity.

Adapt this shape to the project rather than copying names:

```python
import hashlib
import os

import pytest

from kitaru import RegressionLimits

from my_agent.evals import candidate_agent, quality_objective


EXPERIMENT_ID = "<exact-experiment-id>"
PROVIDER_CREDENTIAL = "<PROVIDER_API_KEY>"
PROVIDER_MARKER = "<repository-provider-marker>"

pytestmark = [pytest.mark.live_llm, getattr(pytest.mark, PROVIDER_MARKER)]


def test_incident_regression_gate() -> None:
    if os.environ.get("KITARU_RUN_REPLAY_GATE") != "1":
        pytest.skip("set KITARU_RUN_REPLAY_GATE=1 to authorize paid replay")
    if not os.environ.get(PROVIDER_CREDENTIAL):
        pytest.skip(f"{PROVIDER_CREDENTIAL} is not configured")
    candidate_ref = os.environ.get("GITHUB_SHA") or os.environ[
        "KITARU_CANDIDATE_LABEL"
    ]
    candidate_label = f"ci-{candidate_ref[:12]}"
    experiment_key = hashlib.sha256(EXPERIMENT_ID.encode()).hexdigest()[:12]
    candidate_agent.register(
        label=candidate_label,
        entrypoint="my_agent.evals:candidate_agent",
    )

    result = candidate_agent.replay(
        experiment=EXPERIMENT_ID,
        idempotency_key=f"incident-gate-{candidate_label}-{experiment_key}",
        repeats=1,
        scorers=[quality_objective],
        limits=RegressionLimits(
            max_trials=1,
            max_cost_usd=<approved-cost>,
            max_incurred_tokens=<approved-tokens>,
            max_duration_seconds=<approved-seconds>,
        ),
    )
    result.assert_pass()
```

Replace the provider credential and marker placeholders with the repository's
actual values. Keep the opt-in guard even after standing authorization; enable
it deliberately in the authorized CI job environment.

In CI, `GITHUB_SHA` supplies the immutable candidate identity. For local
execution, require an explicit `KITARU_CANDIDATE_LABEL` derived from a commit
and dirty-tree state. Do not silently reuse a generic `local` label.

Show the exact proposed path and diff before creating or changing a test file.

## Cost implications

Explain the concrete sequence:

1. The test registers the current commit as a candidate version.
2. Replay calls the candidate model from the frozen boundary.
3. Exact recorded tool matches return stored responses.
4. Unmatched tool calls are blocked and recorded.
5. The objective and protections inspect the resulting child execution.
6. The user is billed for live model requests made by the replay.
7. A repeated CI attempt with the same key returns stored evidence instead of
   making another replay trial.

`max_trials=1` limits replay trials, not provider calls within a trial. A
single agent trial may include several model turns and output retries.

Use the cheapest comparable shape on pull requests. Put larger repeat counts or
wider suites in an explicitly scheduled job when the repository's cost policy
permits it.

## Recommended tests

### Deterministic tests

- the objective convicts a known bad execution and accepts a known good one;
- each protection convicts its forbidden behavior;
- each protection accepts a safe behavior;
- exact recorded tool name and arguments serve the recorded response;
- changed arguments are blocked;
- the blocked path never invokes the live tool callable;
- malformed or incomplete boundaries are rejected;
- root-input replay remains HOLD rather than being called comparable;
- the same idempotency request returns the same experiment.

### Live provider gate

Keep the provider test:

- under the repository's live-test location;
- marked with the repository's provider and live-spend markers;
- disabled unless `KITARU_RUN_REPLAY_GATE=1`;
- skipped cleanly when credentials are absent;
- limited to one trial on pull requests;
- configured with a short bounded prompt and explicit operational limits.

Do not place paid provider calls in deterministic test jobs.

## Validation before claiming CI READY

| Check | Required evidence |
|---|---|
| Imports | test module imports without unintended provider calls |
| Frozen identity | exact experiment ID appears in the test |
| Candidate identity | commit-derived immutable label |
| Retry safety | deterministic idempotency key |
| Spend | one trial and explicit cost, token, and duration limits |
| Verdict | `assert_pass()` |
| Local checks | deterministic tests pass |
| CI authorization | recurring triggers, credentials, registration, spend, and retries are approved |
| Opt-in | `KITARU_RUN_REPLAY_GATE=1` is set only in the authorized job |
| CI wiring | containing job exists and credential behavior is documented |
| Merge protection | required-job configuration is verified or explicitly outstanding |

A passing local test does not itself block merges. Report CI READY only for the
test artifact. Report merge-gate activation separately.

## Failure behavior

A CI failure should print or preserve:

- verdict and reason codes;
- failed objective or protection;
- comparability;
- recorded response hits and misses;
- blocked calls and path divergences;
- actual cost, tokens, and duration;
- exact experiment and child execution IDs.

Do not automatically rerun a failed paid gate with a new idempotency key.
