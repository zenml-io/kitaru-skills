# TypeScript adapters

Use this reference after the project route identifies a TypeScript agent
entrypoint. Treat the TypeScript SDK and adapter foundation as conditional until
the installed package proves that they are available.

## Contents

- [Establish the installed package surface](#establish-the-installed-package-surface)
- [Use the draft references carefully](#use-the-draft-references-carefully)
- [Choose the supported implementation path](#choose-the-supported-implementation-path)
- [Preserve the framework type surface](#preserve-the-framework-type-surface)
- [Use the adapter primitives when available](#use-the-adapter-primitives-when-available)
- [Map framework events](#map-framework-events)
- [Control replay and side effects](#control-replay-and-side-effects)
- [Bound TypeScript payloads](#bound-typescript-payloads)
- [Test the TypeScript adapter](#test-the-typescript-adapter)

## Establish the installed package surface

Inspect the package manager, lockfile, Node version, module system, TypeScript
configuration, framework version, `@zenml-io/kitaru` version, and exact exports
resolved by the user's project.

Feature-detect the public client before the adapter subpath. A sufficient client
for the current lifecycle normally needs public methods equivalent to:

```text
createSession
updateSession
upsertSessionNodes
getReplay                 when replay is requested
lookupToolResult          when history replay is requested
```

Verify the installed signatures and request types. Do not write direct REST
calls when a method is absent.

Then test whether the project can resolve `@zenml-io/kitaru/adapter` and inspect
its actual exports. Current draft exports include `RunRecorder`, per-run state,
normalized step helpers, replay parsing and resolution, and tool-policy helpers.
Use only the exports present in the installed or explicitly approved local
package.

If neither a sufficient public client nor the adapter subpath is available,
propose the exact published dependency that supplies it and ask before changing
the project. Stop when none exists.

## Use the draft references carefully

The current TypeScript reference is Kitaru draft PR #679:

```text
branch: feat/ts-support
commit: 8022098b61546326e1e00609cca221bfaba92624
core: packages/core/
Mastra adapter: packages/mastra/
Vercel AI adapter: packages/vercel-ai/
```

Refresh the branch and commit before relying on it. At this revision:

- `@zenml-io/kitaru` is `0.1.0-experimental.0` and declares ESM plus a narrow
  Node 22 engine range;
- the core package exports a public client and an `./adapter` subpath;
- `@zenml-io/kitaru-mastra` targets Mastra 1.51.x and wraps non-streaming
  `Agent.generate()`;
- `@zenml-io/kitaru-vercel-ai` targets AI SDK 7.x and wraps non-streaming
  `generateText`;
- the packages are draft, experimental references, not unconditional evidence
  that npm users can install them.

Do not copy package source into the user's project. Do not add an unpublished
workspace dependency without approval. When the user wants to test the draft,
offer an exact locally built tarball or workspace-link path and ask before using
it.

## Choose the supported implementation path

Use this order:

1. Use an existing published framework adapter when it supports the installed
   framework and requested modes.
2. Use the installed `@zenml-io/kitaru/adapter` primitives with the installed
   public client.
3. If the adapter subpath is absent but the installed public client exposes the
   complete session and replay methods, implement the shared lifecycle locally
   against that client.
4. If the only usable package is a user-built draft tarball or workspace link,
   continue only after explicit approval and report the dependency as
   experimental.
5. Otherwise stop. Do not handwrite HTTP requests or generated API types.

Keep the local implementation small. Do not recreate the whole adapter
foundation merely because one helper is absent.

## Preserve the framework type surface

Use a wrapper factory or class that preserves the framework's public call site.
Retain:

- generic model and tool-set parameters;
- input and option types;
- overloads when the framework exposes them;
- exact promised result type;
- configured hooks and callbacks;
- `AbortSignal` behavior;
- ESM import paths and the project's module-resolution rules.

Compile a type-only usage test that assigns the wrapped callable where the
original callable was accepted and checks important inferred result fields.
Runtime tests cannot detect an adapter that degrades a generic API to `unknown`
or `any`.

Compose callbacks in an explicit order. Record the framework event first when a
later user callback failure must not erase evidence. Preserve the user's
callback and its error behavior. Document any order that differs from the
framework default.

## Use the adapter primitives when available

At the inspected draft revision, `RunRecorder` demonstrates this lifecycle:

1. `create(...)` creates an in-progress session and isolated `RunState`.
2. `initialize()` upserts the in-progress root at index `0`.
3. framework callbacks normalize model and tool steps and enqueue ordered node
   upserts;
4. `complete(result)` waits for queued steps, replaces the root as completed,
   and updates the session;
5. `fail(error)` stores the first failure and best-effort writes failed policy
   outcomes, root state, and session state.

Use the installed implementation rather than duplicating it. Verify whether it
closes or owns any client resource; the draft TypeScript client uses `fetch` and
does not mirror Python client ownership.

When implementing against the public client without these primitives, reproduce
the shared lifecycle invariants from `adapter-method.md`, not the private class
layout. Keep one run-state instance per invocation, serialize node writes,
allocate indexes once, and preserve the first failure.

The current client retries node upsert only for a small set of transient server
statuses. Preserve the same node indexes and payload on a retry. Do not retry
model or tool execution as part of recording recovery.

## Map framework events

Prove each callback against the installed framework types and runtime.

For model steps, normalize:

- bounded request input;
- requested and effective model identifiers;
- allowlisted model settings;
- bounded output and public error;
- usage, cost, provider, and external ID when exposed;
- public tool calls and their stable call IDs.

For tools, wrap only public local tool execution paths. Preserve tool schemas,
validation, context, abort signals, return types, and public failures.

Use the draft adapters as contrasting lessons:

### Mastra lessons

- wrap `generate()` only when that is the application's actual entrypoint;
- preserve method binding to the original agent;
- compose configured and caller-provided hooks instead of replacing them;
- treat the narrow peer range as version evidence, not broad compatibility;
- do not infer streaming support from non-streaming generate callbacks.

### Vercel AI lessons

- preserve the typed `generateText` signature rather than returning a generic
  promise;
- wrap local tools before execution so replay policy can prevent side effects;
- disable model retries during controlled replay when a retry could repeat tool
  planning or produce duplicate effects, and report that behavior change;
- store callback recording failures and throw the first failure after generation
  rather than allowing later successful work to hide them;
- compose stop conditions and user callbacks deliberately;
- use ordered execution tickets or an equivalent mechanism when concurrent tool
  starts could let a later side effect run after an earlier policy failure.

Provider-executed, dynamic, approval-gated, and hidden tools remain unsupported
unless their public hooks expose a pre-execution decision and terminal result.

## Control replay and side effects

Resolve replay identity and overrides through the installed SDK. Do not assume
the Python environment contract. At the draft revision, the TypeScript SDK
parses `KITARU_REPLAY_ID`, optional task input, and replay overrides through its
own helpers; verify current precedence and supported fields.

Before generation:

1. run the baseline-admissibility check;
2. apply only bounded, allowlisted prompt, system-prompt, model, and model-setting
   overrides;
3. resolve replacement models through an explicit allowlist and resolver;
4. classify every observable tool by effect;
5. establish the exact miss policy and execution order.

For history replay, the same public-API limitation applies as in Python: a
`found/result` lookup does not prove unique cardinality. Require a complete
preflight that proves unique baseline keys or an installed API that exposes
ambiguity. Otherwise mark history replay unsupported.

When several tool calls can run concurrently, ensure that a failure in an
earlier replay decision prevents later write-capable calls from starting.
Cancellation must reject pending turns and clear any ticket or ledger state.
Do not leave unresolved promises after the framework returns.

Do not support pre-supplied approval responses, provider-native execution, or
dynamic tool shapes unless the installed framework exposes enough public state
to validate and reproduce them safely.

## Bound TypeScript payloads

Do not use broad object cloning as the capture policy. Project the exact fields
needed from framework options, messages, results, and tools.

Enforce limits for:

- object depth;
- object keys and array items;
- individual string length;
- total serialized JSON size;
- model-setting names and numeric ranges;
- replay override keys and sizes.

Reject cycles, non-finite numbers, dangerous prototype keys, functions, symbols,
and unsupported objects. Decide deliberately whether oversized strings are
rejected or visibly truncated.

Always redact or omit authorization, cookies, API keys, passwords, access and
refresh tokens, client secrets, credential objects, raw requests, URLs when they
may carry credentials, provider options, runtime context, file contents, and
other project-specific sensitive paths. Apply the same rules to errors and test
diagnostics.

## Test the TypeScript adapter

Use the project's package manager and test runner. Use a fake Kitaru client,
deterministic fake model, inert local tools, and no provider credentials by
default.

Run:

- the focused unit tests;
- the project's TypeScript typecheck;
- the package or application build when it can expose ESM/export mistakes;
- an import smoke test through the project's real module system.

Cover at least:

- missing adapter subpath with a sufficient public client;
- missing or unapproved Kitaru dependency;
- approved local artifact, clearly reported as experimental;
- native signature, overload, generic, and return-type preservation;
- callback composition and callback failure;
- session creation, initialization, normal completion, and partial failure;
- first-failure preservation;
- stable node indexes across transient upsert retry;
- concurrent invocations and concurrent local tools;
- earlier policy failure blocking later side effects;
- passthrough side effect followed by recording failure;
- static and history hits, misses, ambiguity, and incomplete baseline refusal;
- bounded projection and sentinel credentials;
- unsupported provider, dynamic, hidden, and approval-gated tools;
- explicit non-streaming scope unless a separate public stream lifecycle is
  implemented and tested;
- abort and cleanup of pending execution state.

Inspect the fake client's final session and node tree. Typecheck the user's real
call site, not only an isolated wrapper fixture.
