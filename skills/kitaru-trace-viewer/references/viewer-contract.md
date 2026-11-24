# Viewer contract

This is the contract between a viewer file and Kitaru's session viewer page. Verify it against the installed Kitaru when behavior differs: the runtime is `kitaru/mcp/ui/kitaru-viewer.js` and the built-in viewer is `kitaru/mcp/ui/viewers/default.html` inside the installed package.

## The file

- One complete HTML page with inline `<style>` blocks in the head and inline `<script>` blocks anywhere. The page mounts the body's content and runs each script once, in document order, after mounting, keeping its attributes such as `type="module"`. Data blocks such as `<script type="application/json" id="config">` stay in place and do not run.
- No external scripts, stylesheets, fonts, images, or network calls: the content security policy blocks them, and the mount skips `<script src>`. Inline small images as `data:` URLs.
- At most 4 MB. The file name without `.html` is the viewer's name: lowercase letters, digits, `-`, and `_`, starting with a letter or digit. `default` is reserved.
- Do not wait for `DOMContentLoaded`; it has already fired. Render in `kitaru.onSession`.

## The view

`kitaru.onSession(view => …)` runs after mounting and again after every move to another investigation session. Render everything from `view` each time.

| Field | Contents |
| --- | --- |
| `view.session` | The session record: `id`, `name`, `number`, `status`, `inputs`, `outputs`, `error`, `metadata`, the text selectors, counts, cost |
| `view.nodes` | Every node with payloads (up to 2,000, `nodes_truncated` when cut), in recorded order. Each has `id`, `external_id`, `parent_external_id`, `node_type` (`llm_call`, `tool_call`, `subagent_call`, `span`), `name`, `status`, `error`, `inputs`, `outputs`, `reasoning`, the text selectors, `model`, `tool_name`, `tokens`, `started_at`, `ended_at` |
| `view.annotations` | Saved notes on this session, and answers to this investigation |
| `view.investigation` | `null`, or `id`, `name`, `status`, `position`, `sessions` (position, session id, verdict) and `investigation_session` (its `id`, `questions` with `key`, `question`, and `highlights`, and `verdict`) |
| `view.capabilities.can_write` | `false` when the MCP server runs read-only |
| `view.links.session` | The session in the Kitaru UI, when the server reports a dashboard |

## Anchors

A note is saved with a selector: an optional `node_id`, a JSON Pointer `path`, and an optional character `span`.

- Node paths start at the node record, with the keys `inputs`, `outputs`, `error`, `metadata`, `reasoning`, `model_params`, and `attributes`.
- Session paths start at the session record, with the keys `inputs`, `outputs`, `error`, and `metadata`. A selector without `node_id` is on the session.
- These are the paths the Kitaru UI writes, so notes from either side show in both.

Mark what the reviewer can point at. Elements carry the Kitaru UI's attributes: `data-annot-scope="node:<id>"`, `data-annot-kind` (`text`, `field`, or `node`), and `data-annot-path`.

- `kitaru.renderText(el, { text, nodeId, path, ranges, decorate })` fills `el` with `text` exactly as stored, splits it where `ranges` and saved span notes begin and end, and marks it as a text anchor. `decorate(span, ranges)` styles each piece; saved notes get the `kv-note` class. Call it again to repaint.
- `kitaru.mark(el, { nodeId, path, kind: "field" })` marks a field, `kind: "node"` without a path marks a whole node. SVG elements can be marked too.

The rules that keep notes on the right characters:

1. A text anchor's text content must be the stored string at its path, or a leading part of it. Never put line numbers, labels, markdown rendering, inserted spaces, or ellipses inside it. Put gutters and labels in sibling elements; wrap long text with CSS (`white-space: pre-wrap`, `word-break: break-all`, a width in `ch`).
2. A text anchor's path must resolve to a string; a field anchor's path must resolve to any value.
3. Offsets count UTF-16 code units from the start of the anchor's text, the unit of JavaScript string length, so an emoji counts as two. The MCP server compares every saved span with the text the reviewer selected: a mismatch moves the span to where that text appears once, or saves the note on the whole field, and the reviewer sees a warning.

`kitaru.selfCheck()` reports anchors that break these rules; the preview's anchor check calls it.

## Functions

| Function | What it does |
| --- | --- |
| `nodeText(node, part)`, `sessionText(part)` | `{ text, path }` for `input`, `output`, `system`, `reasoning`, or `error`, through the record's text selectors; `null` when absent |
| `pointer(record, path)`, `join(...keys)`, `findNode(id)` | Resolve and build JSON Pointers; find a node by id |
| `selection()`, `target(el)` | The current text selection, or an element's anchor, as `{ selector, quote, element }` |
| `note({ selector, quote, text })` | Save a note; resolves to `{ annotation, warnings }` |
| `answer(questionKey, { text })` | Save or update the answer to a question; it anchors where the question's first highlight points |
| `edit(annotationId, text)`, `setVerdict(verdict)` | Edit a note's text; set `acceptable`, `problematic`, `uncertain`, or `null` |
| `notesFor({ nodeId, path })`, `answerFor(key)`, `quoteOf(annotation)`, `annotationText(annotation)` | Read saved notes back to paint them |
| `onAnnotations(callback)`, `refreshMarks()` | Repaint after a save |
| `goTo(position)`, `reveal(selector)` | Open another investigation session; scroll to and flash an anchor |
| `tellAssistant(text)`, `shareContext(text)` | Send a message to the conversation as the reviewer; give the assistant context without a message |
| `toggleFullscreen()`, `reportSize()`, `hostContext` | Display mode, height, and the host's theme |
| `ui.reviewPanel(el)` | Questions, verdict buttons, saved notes, navigation, and the whole-session note |
| `ui.enableSelectionNotes({ title })`, `ui.compose(target, { title })` | The note button on selection and the note box; `title(selection)` names a selection in the reviewer's terms |
| `ui.noteButton({ nodeId, path, kind }, { label, title })` | A button marked as a field or node anchor that opens the note box for it and shows its note count |
| `ui.toast(text)` | A short status message |

## Styling

Use the page's tokens so the viewer follows the host's light or dark theme: `--kv-card`, `--kv-subtle`, `--kv-ink`, `--kv-ink-2`, `--kv-ink-3`, `--kv-border`, `--kv-brand`, `--kv-brand-soft`, `--kv-good`, `--kv-bad`, `--kv-warn`, `--kv-sans`, `--kv-mono`, and `--kv-radius`. The classes `kv-btn`, `kv-primary`, `kv-link`, `kv-icon`, `kv-input`, `kv-label`, `kv-hint`, and `kv-muted` match the review kit.

## Product rules the viewer cannot change

- One answer per investigation question: `answer` updates an existing answer, and an answer's selector is fixed once saved.
- The viewer edits notes but cannot delete them.
- The first verdict starts a pending investigation, and the last missing verdict completes it, as in the Kitaru UI.
