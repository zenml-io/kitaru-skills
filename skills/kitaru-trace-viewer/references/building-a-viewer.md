# Building a viewer

## Study the sessions

Read two or three sessions whole: a typical one, a failed or surprising one, and one the user considers good. For each, note:

- the node names and their order, and which node holds the agent's final answer;
- the record path of each piece of material the reviewer judges, for example `/inputs/sequence` on the session or `/outputs/schedule` on the `finalize_plan` node;
- the text the reviewer will want to select, and whether it is stored as one string;
- which tool outputs the reviewer compares the agent's answer against.

Design for the shape these sessions share. When a session lacks a node the viewer needs, render a short message that names what is missing and suggests the `default` viewer, rather than failing.

## Design for the reviewer

- Lead with the picture the reviewer already uses: a map, a timeline, a table, a document. Put the agent's answer and the evidence it rests on side by side, so a mismatch is visible without reading JSON.
- Make the things the reviewer points at selectable or clickable. Text the reviewer may quote becomes a text anchor; structured items (a feature, an assignment, a row) become field anchors, with a "Note on this …" button in a detail panel.
- Show saved notes where they belong: `kv-note` marks in text, a badge or ✎ on fields, the notes list in the review panel.
- Keep the review panel (`kitaru.ui.reviewPanel`) unless the user wants a different layout. It carries the questions, verdicts, and navigation the investigation needs.
- Offer **Full screen** for dense pictures, and keep the layout usable in a narrow frame.

## Keep it clean

Aim for a viewer that is stylish and exact for its domain and quiet everywhere else. Check a draft against these rules before showing it:

- **One picture carries the domain.** The map, chart, or document is the largest thing on the page; everything else supports it.
- **Space, not boxes.** Separate sections with spacing or a hairline, not bordered cards. Keep page padding around 14-16 px and section gaps around 20 px.
- **One header line.** The session's name, then a short muted line of the two or three facts that matter. No paragraph of metadata.
- **Few words.** Small sentence-case labels, no instructions on the page, one line per check with its reason in a tooltip, and details only for what the reviewer selected.
- **Labels only where they fit.** Leave small shapes unlabeled and name them on hover, rather than stacking rows of labels.
- **Color means something.** Use color for types, statuses, and broken rules, from the page's tokens so light and dark themes both work. Use `kitaru.ui.noteButton` and the review kit's classes so controls match.

## Add domain checks

A check is a rule the reviewer would apply by hand, computed in the page: a gene on a different strand than its evidence, a job during maintenance, a total that does not add up, a claim in the agent's text that its own output contradicts. Show each check as a hint with its reason, link it to what it is about, and underline contradicted claims in the agent's text with `renderText` ranges.

- Compute checks from the session's own data, never from outside knowledge the page cannot show.
- Keep a check's wording factual ("10 min between jobs; cleaning needs 45"). The reviewer decides whether it matters.
- Never save a check result as an annotation.

## Avoid the common mistakes

| Mistake | What goes wrong | Do instead |
| --- | --- | --- |
| Rendering markdown or adding line numbers inside a text anchor | Notes land on characters the reviewer never selected | Render the stored string verbatim; put numbers in a sibling gutter |
| Building elements with `innerHTML` from payload text | A crafted trace runs code in the page | Use `textContent` or `kitaru.renderText` |
| Loading a library from a CDN | The page's policy blocks it and the viewer breaks | Inline what you need; draw with SVG and CSS |
| Rendering once at load | Moving to the next session shows stale content | Render everything in `onSession` |
| Storing review state in the page | It is lost on the next open and never reaches Kitaru | Save through `note`, `answer`, and `setVerdict` |
| Anchoring a field to a path that does not resolve | Saving fails | Build paths from the record with `kitaru.join` and check them with the anchor check |

## Test before handing over

Run the anchor check (see the operations reference) against at least one session per shape the viewer handles, and fix every reported problem. Then open the preview yourself or ask the user to: select text, save a note, answer a question, set a verdict, move to the next session, and confirm the notes appear in the review panel and in the picture.
