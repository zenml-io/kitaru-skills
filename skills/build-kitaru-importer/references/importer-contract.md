# Kitaru importer contract

Use this reference to inspect the installed importer surface, implement the parser callable, choose an installation mode, and cross remote-state boundaries safely.

## Contents

- [Authority and capability fingerprint](#authority-and-capability-fingerprint)
- [Parser contract](#parser-contract)
- [Identity and deduplication](#identity-and-deduplication)
- [Local scaffold and test](#local-scaffold-and-test)
- [Installation modes](#installation-modes)
- [Registration and import](#registration-and-import)
- [Remote partial states](#remote-partial-states)

## Authority and capability fingerprint

Treat the installed Kitaru version and offline schema as authoritative. The current reference design was verified against Kitaru commit `d5c11987625aa144dc73ddf94981b8527549b2d6` on `codex/v2-importer-braintrust-otlp`; it may be newer than the user's installation.

Inspect read-only before emitting exact commands:

```text
kitaru version
kitaru schema importer scaffold
kitaru schema importer test
kitaru schema importer register
kitaru schema importer version register
kitaru schema session import
```

Confirm the installed parser import path in the active Python environment. Record this fingerprint:

| Capability | Evidence to record |
|---|---|
| Parser types | `Parser`, `ParsedSession`, `ParsedNode`, and `ImportFailure` import successfully |
| Scaffold | Exact destination and overwrite behavior, or that manual file creation is required |
| Local test | Entrypoint, payload, params, timeout, and code-execution warning, or the project-native isolated test path |
| Registration | Script/package choice, entrypoint, provider, and version behavior when remote registration is requested |
| Version registration | Whether an existing importer can receive an immutable new version when that remote action is requested |
| Session import | Exact importer and agent versions, payload, params, and wait behavior when a remote import is requested |

Stop only when a capability required by the requested outcome is absent. Parser types are required to author against the installed contract. Missing scaffold or local-test helpers may use explicit file creation and project-native isolated tests when those paths still exercise the installed parser contract. Missing registration or session-import capabilities limit remote actions; they do not prevent completing a locally validated importer. Do not upgrade Kitaru or substitute draft syntax without the user's separate direction.

## Parser contract

The reference parser shape is:

```python
from collections.abc import Iterator
from typing import Any

from kitaru.task.importer import ImportFailure, ParsedSession, Parser


def parse(
    payload: bytes, params: dict[str, Any]
) -> Iterator[ParsedSession | ImportFailure]:
    ...


parser: Parser = parse
```

The worker passes the complete payload as `bytes` and one JSON-compatible parameters object. It advances the iterator one item at a time. A parser exception while creating or advancing the iterator is a task-level parser failure; a yielded `ImportFailure` is one isolated failed item.

### Parsed session fields

| Field | Meaning |
|---|---|
| `external_id` | Stable source identity used with the registered provider for deduplication |
| `status` | Installed `SessionStatus` value |
| `name` | Useful source-derived label or `None` |
| `inputs`, `outputs`, `expected` | JSON-compatible session-level content |
| `error` | Root/session failure, not every failed descendant |
| `started_at`, `ended_at` | Aware timestamps when available |
| `metadata` | Bounded source and fidelity metadata |
| `nodes` | Root `ParsedNode` trees in deterministic order |

### Parsed node fields

Map the installed model rather than copying this list blindly. The reference includes:

- `external_id`, `trace_id`, `node_type`, `name`, and `status`;
- `error`, `started_at`, and `ended_at`;
- `inputs`, `outputs`, `attributes`, and bounded `metadata`;
- `requested_model`, served `model`, model `provider`, `model_params`;
- `tokens`, `cost`, `tool_name`, and `subagent_id`;
- `children`, which Kitaru flattens depth-first with each parent before its children.

Reference node types are `llm_call`, `tool_call`, `subagent_call`, and `span`. Do not infer a semantic type merely from a suggestive name when the provider exposes a stronger field.

The reference parsed tree has one primary parent per node. If the installed contract supports secondary parents only after flattening, keep one evidence-backed primary edge and record unsupported secondary relations in provider metadata rather than inventing a different tree.

## Identity and deduplication

Kitaru deduplicates imported sessions on the registered `provider` plus session `external_id`. Agent, agent version, owner, and content are not part of that key in the reference design.

Construct a namespaced external ID from:

```text
<normalized source instance>:<native session or trace id>
```

The registered provider already supplies the outer namespace. Include account, workspace, project, collector, or tenant information in `source instance` whenever the source can reuse native IDs across those scopes. Require an explicit `source_instance` parameter when the export cannot establish one safely.

Construct node IDs from native trace plus span, run, or event identity. Scope them consistently when the source can reuse IDs across accounts.

Consequences:

- rerunning the same provider and external ID is expected to count as skipped;
- changed content under the same identity is not automatically repaired or replaced;
- importing the same source trace under another logical agent may still collide;
- a source instance fallback such as a filename is weaker and must be reported.

Use a deterministic content digest to detect changed content locally before a remote rerun. See [normalization-patterns.md](normalization-patterns.md).

## Local scaffold and test

Use only commands confirmed by the installed schema. The reference forms are:

```text
kitaru importer scaffold PROVIDER --path path/to/provider_importer.py

kitaru importer test path/to/provider_importer.py \
  --entrypoint parse \
  --payload path/to/redacted-export.json \
  --params '{"source_instance":"workspace"}' \
  --timeout 10
```

Scaffolding writes one file and conflicts when the destination exists unless an explicit force option is used. Inspect the existing file and ask before overwriting it.

Local testing validates the script source, imports the entrypoint in a child process, invokes it when a payload is supplied, and checks yielded types and counts. It captures bounded output and enforces a timeout. It does not prove semantic mapping, join correctness, topology, replay readiness, or safety. It is not a sandbox.

Before installing local dependencies, show the user the exact pinned dependencies, their provenance, and the isolated target environment. Ask for explicit approval to install that exact set. Record `none` when the importer uses only the standard library. The remote worker's dependency installation does not make dependencies available locally.

Before running the local importer test, separately show the exact command, importer path, fixture, parameters, and isolation controls. Ask for explicit approval to execute it. Do not treat dependency-installation approval as approval to run importer code.

Run any untrusted importer or importer newly generated in the current task only in a credential-free isolated environment that prevents access to ambient project and cloud credentials. Stop when suitable isolation is unavailable; do not fall back to the normal project shell. The child process used by Kitaru constrains duration and output, but it is not a security sandbox.

## Installation modes

### Script mode: default

Use one script with one top-level attribute entrypoint. Prefer the standard library. When a dependency is necessary, declare minimal exact versions in PEP 723 inline metadata if the installed worker supports it:

```python
# /// script
# dependencies = ["provider-sdk==1.2.3"]
# ///
```

Review the dependency's provenance. Install the exact version only after the local dependency approval described above. Test untrusted or newly generated code in the required credential-free isolated environment. Inline dependencies are executable supply-chain input to the worker, not harmless metadata.

Choose script mode when the importer is private, small, or used by one project. A local script can be a complete deliverable without being copied into Kitaru's OSS repository.

### Package mode: conditional

Use package mode only when the importer already benefits from a maintained distribution route. The reference registration contract requires:

- one exact PEP 508 `==` version;
- no URL, environment marker, wildcard, range, or editable source;
- an entrypoint in `MODULE:ATTRIBUTE` form;
- a trusted package index reachable with the worker's configured credentials.

Do not promise that a local or private package can install remotely until the actual worker route is verified. Prefer script mode when index authentication is uncertain.

## Registration and import

Registration and trace import are separate remote mutations.

Reference first-version commands:

```text
kitaru importer register NAME \
  --script path/to/provider_importer.py \
  --entrypoint parse \
  --provider PROVIDER

kitaru importer register NAME \
  --package 'distribution==1.2.3' \
  --entrypoint package.module:parse \
  --provider PROVIDER
```

Reference new-version command:

```text
kitaru importer version register IMPORTER \
  --script path/to/provider_importer.py \
  --entrypoint parse
```

Registration creates executable remote state. The first registration may create the importer parent, upload a source blob, and then create the first immutable version. Preserve every returned identifier. If the parent exists after a later step fails, resolve it and use version registration rather than blindly recreating it.

Reference bounded import:

```text
kitaru session import path/to/redacted-export.json \
  --importer IMPORTER@VERSION \
  --agent AGENT@VERSION \
  --params '{"source_instance":"workspace"}' \
  --wait
```

Use exact importer and agent versions. Import uploads the payload, creates a job, and may create persistent sessions. A local timeout ends waiting, not the remote job. Tags may be applied after import and can fail separately; preserve the session and job receipt before attempting follow-on mutations.

Before each action, confirm the active principal, tenant or project, least-privilege permissions, exact source or payload, and expected persistence. Never reuse an earlier approval for the second action.

## Remote partial states

Registration and import are multi-step flows. Possible durable states include:

- importer parent exists without the intended version;
- source blob exists without a completed version;
- payload blob exists without a job;
- job exists and continues after the local waiter times out;
- earlier sessions exist after a later parser item crashes;
- a session exists after node ingestion fails;
- import succeeded but post-import tagging failed.

The reference result counts created, skipped, and failed items and retains at most 20 failure samples. The sample list is not a complete failure ledger when the failed count is larger.

Always re-read current state before retrying. Session creation precedes node ingestion, so an incomplete session can occupy the deduplication key and a whole-payload retry can skip it rather than repair it.
