---
name: build-kitaru-importer
description: Build and validate a custom Kitaru trace importer when a provider, observability platform, export format, or agent framework has no suitable built-in importer. Use when a user wants to map provider traces into Kitaru sessions and nodes, join per-turn traces into longer sessions, preserve incomplete or failed trace evidence, choose script or package installation, test importer fidelity, register an importer version, import a bounded sample, or diagnose a partial import. A private or project-local importer is a complete outcome; packaging or an OSS contribution is optional.
---

# Build a Kitaru importer

Turn a representative provider export into a locally validated Kitaru importer. Keep the path from source evidence to normalized sessions explicit so the user can see what is preserved, approximated, or unavailable.

Finish locally by default. Register code or upload trace data only when the user asks and approves each action separately.

## Core contract

- Treat the installed Kitaru version and its offline schema as authoritative. Use repository examples as patterns, not proof that a command or field is installed.
- Treat trace content as sensitive. Keep raw exports out of version control and redact fixtures before writing them into the target repository.
- Keep export acquisition outside the importer. The parser consumes static bytes and parameters without network calls, filesystem writes, subprocesses, or credential reads.
- Map the source before writing code. Record accepted payload shapes, identity, hierarchy, ordering, node fields, status, completeness, and intentionally unsupported data.
- Prefer a private, single-file script importer. Use a package only when the user already has a distribution reason and the worker can install one exact pinned version.
- Preserve useful incomplete evidence. Distinguish an unreadable payload, an invalid item, and a valid but incomplete session.
- Join traces conservatively. A common key is insufficient without source-instance scope and meaningful turn order.
- Do not overwrite an existing importer file, register executable code, upload trace data, or retry a partial import without an explicit checkpoint.
- Treat local importer testing as code execution in a bounded child process, not as a security sandbox.
- Offer packaging or upstream contribution only after local success. Do not make either a completion requirement.

## Keep the experience clear

- Lead with the current state and the next decision.
- Ask only for evidence that the repository, provider documentation, sample, or installed Kitaru schema cannot establish.
- Show mapping and fidelity decisions in compact tables rather than dumping source records.
- Keep exact IDs, versions, warnings, and recovery identifiers visible.
- State whether each claim comes from provider documentation, a sample export, installed Kitaru, or an inference.
- Stop at a useful local checkpoint when a capability, permission, source sample, or worker route is missing.

## Load references only when needed

- Read [references/importer-contract.md](references/importer-contract.md) before scaffolding, testing, registering, or importing. It contains the parser contract, capability fingerprint, installation modes, commands, identity consequences, and remote-state boundaries.
- Read [references/normalization-patterns.md](references/normalization-patterns.md) before mapping source records, rebuilding a graph, joining turns, deriving status, or reporting fidelity.
- Read [references/failure-and-validation.md](references/failure-and-validation.md) before writing fixtures and assertions, executing unfamiliar code, handling malformed or incomplete traces, or recovering from a partial remote import.

## Resolve the starting state

Start read-only.

1. Identify the target repository, provider or format, representative export, and intended use of the imported sessions.
2. Inspect the installed Kitaru version, offline command schema, and parser import path.
3. Build the capability fingerprint in [references/importer-contract.md](references/importer-contract.md).
4. Inspect existing local importer files and registered importers when a connection is already configured.
5. Decide whether to reuse an importer, add a new version, or create a new private name.
6. Stop before overwriting a path or changing the installed Kitaru version.

If importer scaffolding, local testing, registration, exact-version import, or the required parser types are absent, name the missing capability. Do not give draft commands as though they were released. The user may choose a compatible Kitaru environment separately.

If `kitaru-investigation` routed the user here, retain the agent and investigation context. Return to the investigation only after relevant sessions are actually usable.

## Acquire a safe representative sample

Prefer an existing static export. When the provider offers only an authenticated or paginated API, treat export acquisition as a separate task with its own approval, credentials, pagination, rate limits, and resumability.

Before writing a fixture:

1. Keep the raw export outside the repository.
2. Minimize it to the smallest records that preserve the behavior under test.
3. Redact prompts, completions, tool arguments, end-user identifiers, credentials, and provider-specific secrets.
4. Review the minimized fixture for residual secrets and direct identifiers.
5. Preserve field shapes, relationships, and ordering evidence needed by assertions.

Do not place provider credentials in shell arguments, importer parameters, fixtures, inline dependency metadata, uploaded source, or logs.

## Record the source map

Before implementation, produce this checkpoint:

| Decision | Evidence and chosen behavior |
|---|---|
| Payload shapes | Supported export variants and representative redacted files |
| Source instance | Account, workspace, project, collector, or explicit override |
| Session identity | Native session, thread, or conversation ID; trace fallback |
| Turn order | Provider sequence, or one trustworthy clock domain and precision |
| Root and hierarchy | Root selection, parent field, missing-parent and cycle behavior |
| Node mapping | Span, LLM, tool, and subagent fields plus bounded metadata |
| Status and error | Root outcome and descendant-failure semantics |
| Completeness | Missing hierarchy, payloads, tools, usage, cost, or timestamps |
| Safety limits | Numeric byte, record-count, and nesting-depth limits |
| Installation | Script dependencies or exact package and worker route |

Mark every relevant source field as mapped, preserved as bounded metadata, or intentionally unsupported. Ground expected mappings in provider documentation or an independently reviewed sample, not only in the implementation's own output.

## Implement the smallest coherent importer

1. Scaffold a script only after the installed schema confirms the command and destination.
2. Keep one top-level parser entrypoint with the installed `Parser` signature.
3. Parse the complete payload into deterministic source groups.
4. Validate identities and graph structure before yielding a session.
5. Yield valid sessions and isolated item failures incrementally.
6. Keep provider-specific helpers private to the file unless package mode is already justified.
7. Use only safe deserializers. Reject unsafe formats or convert them in the separate acquisition step.
8. Apply the declared byte limit before decoding and the record and depth limits before expensive normalization.

Use [references/normalization-patterns.md](references/normalization-patterns.md) for identities, joins, topology, status, metadata, readiness, and content digests.

## Validate locally

Use two layers of evidence:

1. Provider-grounded assertions verify normalized values, identity, ordering, topology, status, warnings, readiness, and digest behavior.
2. The installed local importer test verifies that Kitaru can load the entrypoint and that yielded values satisfy its runtime types.

Cover the applicable cases from [references/failure-and-validation.md](references/failure-and-validation.md). At minimum include one complete item, one valid incomplete item, and one invalid item or payload boundary. Add joining, changed-content, and graph cases when the source supports them.

Do not treat a successful local importer test as semantic proof. Inspect the yielded sessions and compare them with the source map.

## Report the local checkpoint

Return a compact report:

| Area | Result |
|---|---|
| Importer | Path and entrypoint |
| Supported source | Provider, export variants, and source-instance rule |
| Identity | Session and node ID derivation; rerun behavior |
| Joining | Key, scope, order, fallback, or not applicable |
| Fidelity | Complete, partial, and intentionally unsupported fields |
| Replay readiness | Ready, partial, or unavailable with concrete reasons |
| Validation | Assertions and installed Kitaru test results |
| Remote state | None, unless separately approved |

This is a successful authoring milestone. The importer becomes usable in a remote Kitaru deployment only after registration and an observed smoke import.

## Gate remote registration

Proceed only when the user requests registration.

Before approval, show:

- the active Kitaru principal and target tenant or project;
- importer name, provider, exact source path, entrypoint, and dependency route;
- whether this creates a parent plus first version or another immutable version;
- that executable source or a package reference becomes remote state;
- the exact installed command and the receipt fields that will be preserved.

After approval, register once. Preserve the importer ID, exact version, source digest, and any blob or task identifiers. If parent creation succeeds and version creation fails, do not repeat the parent-creation command blindly.

## Gate the first smoke import separately

Proceed only when the user also approves uploading a bounded redacted payload.

Show the exact importer version, agent version, target tenant or project, payload, parameters, persistence, expected session identities, and the fact that this skill has no automatic cleanup path. Prefer a disposable agent or isolated source identity.

Create one import job and wait only through the installed supported mechanism. A local wait timeout does not stop the remote job. Preserve the blob, job, task, session, and terminal receipt identifiers.

Classify the result as created, skipped duplicate, failed, or still running. Inspect representative imported sessions rather than trusting counts alone.

## Recover without compounding partial state

Before proposing any retry, classify each relevant external identity:

| State | Meaning |
|---|---|
| Untouched | No session exists and the item did not run |
| Complete | Session and expected nodes exist |
| Skipped duplicate | The provider and external ID already existed |
| Incomplete | Session exists but expected node ingestion did not finish |
| Unrecoverable here | Installed Kitaru exposes no safe repair or deletion path |

Remember that session creation can succeed before node ingestion fails. A direct rerun may then skip the existing external ID instead of repairing the session. Preserve evidence, patch and version the importer locally if needed, and propose only recovery operations the installed product actually exposes.

## Finish

When local validation or the requested smoke import succeeds:

1. Return the exact artifacts, supported source shapes, fidelity limits, and verification results.
2. Route the user back to `kitaru-investigation` when usable sessions now exist.
3. Ask whether they want to keep the importer private, package it for their environment, or consider contributing it upstream.
4. Do not publish, contribute, or broaden provider support without a separate request.
