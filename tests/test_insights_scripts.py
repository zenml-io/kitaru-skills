"""Behavioral tests for the offline kitaru-insights helpers."""

import contextlib
import importlib.util
import io
import json
import shlex
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/kitaru-insights/scripts"
# The helpers import their shared page loader the way `python3 scripts/NAME.py` resolves it.
sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pick_sample = load("pick_sample")
condense = load("condense_sessions")
tally = load("tally_notes")
reports = load("check_report")
scope_counts = load("scope_counts")
to_judgments = load("evaluations_to_judgments")
tool_stats = load("tool_stats")


def session(i: int, status: str = "completed", cost: float | str = 0.01, tools: int = 2, agent: str = "agent") -> dict:
    return {
        "id": f"s{i:03d}",
        "agent_id": agent,
        "status": status,
        "cost": cost,
        "tool_call_count": tools,
        "started_at": "2026-10-30T10:00:00+00:00",
        "ended_at": f"2026-10-30T10:{i % 60:02d}:00+00:00",
    }


class PickSampleTest(unittest.TestCase):
    def test_random_slice_is_seeded_and_independent_of_targeted_picks(self):
        items = [session(i, status="failed" if i < 10 else "completed", cost=i / 100) for i in range(100)]
        first = pick_sample.build(items, targeted=10, random_count=15, seed=7, include_in_progress=False)
        again = pick_sample.build(items, targeted=10, random_count=15, seed=7, include_in_progress=False)
        self.assertEqual(first, again)
        random_ids = [p["session_id"] for p in first["picks"] if p["random"]]
        self.assertEqual(len(random_ids), 15)
        targeted = [p for p in first["picks"] if any(r != "random" for r in p["reasons"])]
        self.assertEqual(len(targeted), 10)
        failed = [p for p in targeted if "failed" in p["reasons"]]
        self.assertEqual(len(failed), 5, "failed picks are capped at half the targeted budget")

    def test_small_scope_reads_every_session(self):
        sample = pick_sample.build([session(i) for i in range(30)], targeted=25, random_count=15, seed=3, include_in_progress=False)
        self.assertEqual(len(sample["picks"]), 30)
        self.assertTrue(all(p["reasons"] == ["all_in_scope"] for p in sample["picks"]))

    def test_failed_picks_are_not_just_the_oldest(self):
        items = [session(i, status="failed") for i in range(100)]
        picked = {p["session_id"] for p in pick_sample.build(items, targeted=10, random_count=0, seed=5, include_in_progress=False)["picks"] if "failed" in p["reasons"]}
        self.assertNotEqual(picked, {f"s{i:03d}" for i in range(5)})

    def test_exclude_keeps_measurement_draw_fresh(self):
        items = [session(i) for i in range(50)]
        read = {f"s{i:03d}" for i in range(20)}
        sample = pick_sample.build(items, targeted=0, random_count=30, seed=8, include_in_progress=False, exclude=read)
        drawn = {p["session_id"] for p in sample["picks"]}
        self.assertEqual(len(drawn), 30)
        self.assertFalse(drawn & read)
        self.assertEqual(sample["population_count"], 50)

    def test_scope_is_pinned_and_hashed(self):
        items = [session(i) for i in range(5)] + [session(9, status="in_progress")]
        sample = pick_sample.build(items, targeted=2, random_count=2, seed=1, include_in_progress=False)
        self.assertEqual(sample["population_ids"], [f"s{i:03d}" for i in range(5)])
        self.assertEqual(len(sample["population_sha256"]), 64)

    def test_rejects_scopes_spanning_agents(self):
        with self.assertRaisesRegex(ValueError, "2 agents"):
            pick_sample.build([session(1), session(2, agent="other")], 1, 1, 1, False)

    def test_reads_cli_envelopes_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.json"
            page.write_text(json.dumps({"ok": True, "items": [session(1), session(1), session(2)]}))
            self.assertEqual(len(pick_sample.load_items([page])), 2)
            mcp = Path(tmp) / "mcp.json"
            mcp.write_text(json.dumps({"schema_version": "1", "ok": True, "data": {"items": [session(3)]}}))
            self.assertEqual(len(pick_sample.load_items([mcp])), 1)
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"ok": True}))
            with self.assertRaisesRegex(ValueError, "items array"):
                pick_sample.load_items([bad])

    def test_picks_out_lists_only_the_picked_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            page, picks = Path(tmp) / "page.json", Path(tmp) / "picked.txt"
            page.write_text(json.dumps({"items": [session(i) for i in range(50)]}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(pick_sample.main([str(page), "--targeted", "2", "--random", "3", "--seed", "7", "--out", str(Path(tmp) / "sample.json"), "--picks-out", str(picks)]), 0)
            sample = json.loads((Path(tmp) / "sample.json").read_text())
            self.assertEqual(picks.read_text().split(), [p["session_id"] for p in sample["picks"]])


class CondenseTest(unittest.TestCase):
    def test_transcript_uses_selectors_and_keeps_node_ids(self):
        node_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as tmp:
            export, out = Path(tmp) / "export", Path(tmp) / "out"
            export.mkdir()
            (export / "s1.session.json").write_text(json.dumps({"item": {"id": "s1", "status": "failed", "inputs": {"messages": [{"content": "Where is order #48213?"}]}, "input_text_selector": "/messages/0/content"}}))
            (export / "s1.nodes.json").write_text(json.dumps({"items": [{"id": node_id, "external_id": "a", "node_type": "tool_call", "name": "lookup_order", "tool_name": "lookup_order", "status": "failed", "error": "404", "inputs": {"order_id": "#48213"}, "outputs": None}]}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(condense.main([str(export), str(out)]), 0)
            text = (out / "s1.md").read_text()
            self.assertIn("Where is order #48213?", text)
            self.assertIn(f"- [0] node {node_id}: tool_call", text)
            self.assertIn("zero-based", text)
            self.assertIn("error: 404", text)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertGreater(manifest["estimated_tokens"], 0)

    def test_reads_mcp_envelopes_and_rejects_wrong_session_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp)
            (export / "s2.session.json").write_text(json.dumps({"schema_version": "1", "ok": True, "data": {"id": "s2", "status": "completed"}}))
            (export / "s2.nodes.json").write_text(json.dumps({"schema_version": "1", "ok": True, "data": {"items": [{"id": "n1", "node_type": "span", "name": "run", "status": "completed"}]}}))
            loaded = condense.load_export(export)
            self.assertEqual(loaded["s2"]["session"]["status"], "completed")
            self.assertEqual(len(loaded["s2"]["pages"][0][1]), 1)
            (export / "s3.session.json").write_text(json.dumps({"ok": True}))
            with self.assertRaisesRegex(ValueError, "id s3"):
                condense.load_export(export)

    def test_reads_session_read_json_and_keeps_zero_based_positions(self):
        session_id, node_id = str(uuid.uuid4()), str(uuid.uuid4())
        transcript = {
            "session_id": session_id, "status": "completed", "origin": "imported", "cost": "0.0123", "node_count": 5, "request": "Refund order 7?",
            "steps": [
                {"index": 3, "node_id": node_id, "node_type": "tool_call", "name": "check_policy", "status": "completed", "input": '{"order":7}', "output": "window closed… [+812 chars]"},
                {"index": 4, "node_id": str(uuid.uuid4()), "node_type": "llm_call", "name": "reply", "model": "m", "status": "completed", "system_prompt": "New rules.", "output": "(same as [3])"},
            ],
            "final_output": "Refund approved.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            export, out = Path(tmp) / "export", Path(tmp) / "out"
            export.mkdir()
            (export / "picked.read.json").write_text(json.dumps({"schema_version": "1", "ok": True, "items": [transcript]}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(condense.main([str(export), str(out)]), 0)
            text = (out / f"{session_id}.md").read_text()
            self.assertIn(f"- [3] node {node_id}: tool_call check_policy status=completed", text)
            self.assertIn("  result: window closed… [+812 chars]", text)
            self.assertIn("  system prompt changed: New rules.", text)
            self.assertIn("cost: 0.0123", text)
            self.assertIn("## Nodes (2 shown of 5)", text)
            entry = json.loads((out / "manifest.json").read_text())["sessions"][0]
            self.assertEqual((entry["node_count"], entry["clipped_fields"], entry["has_nodes"]), (5, 1, True))

    def test_reads_mcp_session_read_and_rejects_double_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp)
            (export / "mcp.read.json").write_text(json.dumps({"schema_version": "1", "ok": True, "data": {"transcripts": [{"session_id": "s4", "steps": []}]}}))
            self.assertIn("transcript", condense.load_export(export)["s4"])
            (export / "s4.session.json").write_text(json.dumps({"item": {"id": "s4"}}))
            with self.assertRaisesRegex(ValueError, "exported twice"):
                condense.load_export(export)
            (export / "s4.session.json").unlink()
            (export / "bad.read.json").write_text(json.dumps({"items": [{"id": "s5"}]}))
            with self.assertRaisesRegex(ValueError, "session read transcripts"):
                condense.load_export(export)

    def test_clip_keeps_head_and_tail(self):
        text, cut = condense.clip("a" * 100 + "END", 30)
        self.assertTrue(cut)
        self.assertTrue(text.endswith("END"))

    def test_pointer_handles_escapes_and_misses(self):
        doc = {"a/b": [{"~x": "hit"}]}
        self.assertEqual(condense.resolve_pointer(doc, "/a~1b/0/~0x"), "hit")
        self.assertIsNone(condense.resolve_pointer(doc, "/a~1b/5"))
        self.assertIsNone(condense.resolve_pointer(doc, "missing"))


class TallyTest(unittest.TestCase):
    sample = {
        "population_count": 100,
        "population_sha256": "0" * 64,
        "picks": [{"session_id": "t1", "reasons": ["failed"], "random": False}, {"session_id": "t2", "reasons": ["failed"], "random": False}]
        + [{"session_id": f"r{i}", "reasons": ["random"], "random": True} for i in range(10)],
    }

    def test_rate_comes_only_from_the_random_slice(self):
        patterns = {"patterns": [{"id": "p1", "members": ["t1", "t2", "r0"]}]}
        result = tally.tally(self.sample, patterns, None, None, None)["patterns"][0]
        self.assertEqual(result["targeted"]["hits"], 2)
        self.assertEqual(result["rate"]["basis"], "random_slice")
        self.assertEqual((result["rate"]["numerator"], result["rate"]["denominator"]), (1, 10))
        self.assertIsNone(result["rate"]["low"], "noticed counts carry no sampling interval")

    def test_reading_the_whole_scope_is_an_exact_count(self):
        ids = [p["session_id"] for p in self.sample["picks"]]
        census = {**self.sample, "population_count": len(ids), "population_ids": ids}
        document = tally.tally(census, {"patterns": [{"id": "p1", "members": ["t1", "r0"]}]}, None, None, None)
        self.assertTrue(document["census"])
        self.assertEqual(document["patterns"][0]["rate"], {"basis": "census", "method": "readers", "numerator": 2, "denominator": 12, "low": None, "high": None})

    def test_targeted_only_has_no_interval(self):
        sample = {**self.sample, "picks": self.sample["picks"][:2]}
        result = tally.tally(sample, {"patterns": [{"id": "p1", "members": ["t1"]}]}, None, None, None)["patterns"][0]
        self.assertEqual(result["rate"]["basis"], "targeted_only")
        self.assertIsNone(result["rate"]["low"])

    def test_measurement_excludes_unclear_and_reports_missing(self):
        measure = {"seed": 9, "population_sha256": "0" * 64, "picks": [{"session_id": f"m{i}", "reasons": ["random"], "random": True} for i in range(4)]}
        judgments = [
            {"session_id": "m0", "pattern_id": "p1", "verdict": "yes", "node_id": "n"},
            {"session_id": "m1", "pattern_id": "p1", "verdict": "no"},
            {"session_id": "m2", "pattern_id": "p1", "verdict": "unclear"},
        ]
        result = tally.tally(self.sample, {"patterns": [{"id": "p1", "members": ["t1"]}]}, None, measure, judgments)["patterns"][0]
        self.assertEqual((result["rate"]["numerator"], result["rate"]["denominator"]), (1, 2))
        self.assertEqual(result["measurement"]["unclear"], 1)
        self.assertEqual(result["measurement"]["missing"], ["m3"])

    def test_rejects_members_that_were_not_read(self):
        with self.assertRaisesRegex(ValueError, "not read"):
            tally.tally(self.sample, {"patterns": [{"id": "p1", "members": ["elsewhere"]}]}, None, None, None)

    def test_rejects_yes_without_node(self):
        measure = {"seed": 1, "population_sha256": "0" * 64, "picks": [{"session_id": "m0", "reasons": ["random"], "random": True}]}
        with self.assertRaisesRegex(ValueError, "no node_id"):
            tally.tally(self.sample, {"patterns": [{"id": "p1", "members": []}]}, None, measure, [{"session_id": "m0", "pattern_id": "p1", "verdict": "yes"}])

    def test_rejects_measurement_from_another_scope_or_empty(self):
        measure = {"seed": 1, "population_sha256": "f" * 64, "picks": [{"session_id": "m0", "reasons": ["random"], "random": True}]}
        with self.assertRaisesRegex(ValueError, "different scope"):
            tally.tally(self.sample, {"patterns": []}, None, measure, [{"session_id": "m0", "pattern_id": "p1", "verdict": "no"}])
        with self.assertRaisesRegex(ValueError, "no judgments"):
            tally.tally(self.sample, {"patterns": []}, None, {**measure, "population_sha256": "0" * 64}, [])
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "notes.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "no .jsonl"):
                tally.read_lines(Path(tmp))

    def test_whole_scope_jev_measurement_has_no_interval_and_reports_agreement(self):
        ids = [p["session_id"] for p in self.sample["picks"]]
        scope = {**self.sample, "population_count": len(ids), "population_ids": ids}
        measure = {"seed": 2, "population_sha256": "0" * 64, "picks": [{"session_id": s, "reasons": ["all_in_scope"], "random": False} for s in ids]}
        judgments = [{"session_id": s, "pattern_id": "p1", "verdict": "yes" if s in {"t1", "r0", "r1"} else "no", "evaluation_id": f"e-{s}"} for s in ids]
        judgments[-1]["verdict"] = "unavailable"
        versions = {s: ("v1" if s.startswith("t") else "v2") for s in ids}
        result = tally.tally(scope, {"patterns": [{"id": "p1", "members": ["t1", "t2"]}]}, None, measure, judgments, versions)["patterns"][0]
        self.assertEqual(result["rate"]["basis"], "measurement", "judged measurement outranks a census of reader notes")
        self.assertEqual(result["rate"]["method"], "jev")
        self.assertIsNone(result["rate"]["low"])
        self.assertEqual(result["rate"]["unavailable"], 1)
        self.assertEqual(result["agreement"], {"both_yes": 1, "judged_only": 2, "readers_only": 1, "both_no": 7})
        self.assertEqual(result["by_version"]["v1"]["yes"], 1)

    def test_note_coverage(self):
        notes = [{"session_id": "t1"}, {"session_id": "t1"}, {"session_id": "zz"}]
        coverage = tally.tally(self.sample, {"patterns": []}, notes, None, None)["notes"]
        self.assertIn("t2", coverage["missing"])
        self.assertEqual(coverage["duplicated"], ["t1"])
        self.assertEqual(coverage["unexpected"], ["zz"])

    def test_wilson_bounds(self):
        low, high = tally.wilson(18, 100)
        self.assertAlmostEqual(low, 0.1171, places=3)
        self.assertAlmostEqual(high, 0.2668, places=3)


def make_finding(fid: str = "p1", sid: str | None = None, **overrides) -> dict:
    sid = sid or str(uuid.uuid4())
    base = {
        "id": fid,
        "title": "Refunds skip the policy check when the order was edited",
        "summary": "In 14% of sessions the agent issued a refund without checking the return policy.",
        "body": "After an order edit, the agent called `issue_refund` without `check_refund_policy`.",
        "tier": "primary",
        "kind": "finding",
        "severity": "high",
        "change_status": "narrowed",
        "artifacts": [
            {
                "type": "rate",
                "presentation": "range",
                "rate": 0.145,
                "ci_low": 0.10,
                "ci_high": 0.20,
                "numerator": 31,
                "denominator": 214,
                "label": "of sessions",
                "basis": "150 random sessions judged",
                "tone": "risk",
            },
            {
                "type": "evidence",
                "presentation": "table",
                "total_sessions": 31,
                "rows": [
                    {"session_id": sid, "step_label": "step 7", "signal": "issue_refund", "verdict": "fail"},
                    {
                        "session_id": str(uuid.uuid4()),
                        "step_label": "step 6",
                        "signal": "check_refund_policy",
                        "verdict": "pass",
                        "is_counterexample": True,
                        "counterexample_note": "Checked policy after edit",
                    },
                ],
            },
        ],
        "contributing_session_ids": [sid],
        "check_first": "Confirm check_refund_policy was available in the tool schema.",
        "action": {"label": "Investigate this insight", "prompt": "Use the kitaru-investigation skill."},
        "suggested_questions": [{"label": "Why is the range this wide?"}],
    }
    base.update(overrides)
    return base


def make_report(**overrides) -> dict:
    finding = make_finding()
    base = {
        "name": "kitaru-insights-refunds",
        "title": "Refunds skip the policy check when the order was edited",
        "summary": "After an order edit, 31 of 47 sessions skipped check_refund_policy.",
        "source_provider": "langfuse",
        "coverage": {
            "sessions_analyzed": 214,
            "sessions_available": 250,
            "skipped": 33,
            "failed": 3,
            "started_after": "2026-10-12T00:00:00Z",
            "started_before": "2026-10-19T00:00:00Z",
            "caveats": ["Stopped at the 250-trace limit."],
        },
        "highlight": {"finding_id": "p1", "artifact_index": 0},
        "next_step": {
            "label": "Investigate this insight",
            "summary": "Run check_refund_policy again after every order edit.",
            "prompt": "Use the kitaru-investigation skill.",
        },
        "findings": [finding],
        "suggested_questions": [{"label": "Which finding has the highest impact?"}],
        "metadata": {
            "kitaru.insights.skill/v1": {
                "schema_version": 2,
                "run_id": str(uuid.uuid4()),
                "level": "deep",
                "scope": {"population_count": 214, "population_sha256": "a" * 64},
                "sample": {"seed": 7, "targeted": 25, "random": 15},
                "findings": {
                    "p1": {
                        "pattern": {"definition": "Skips policy check after edit.", "checker_verdict": "holds", "rule_id": None},
                        "rate": {"basis": "measurement", "method": "subagents", "numerator": 27, "denominator": 150, "low": 0.127, "high": 0.249},
                        "agreement": None,
                        "impact": {"summary": "31 sessions with unverified refunds", "sessions": 31, "amount": 492000, "unit": "tokens"},
                    }
                },
                "caveats": [],
            }
        },
    }
    base.update(overrides)
    return base


class CheckReportTest(unittest.TestCase):
    def test_valid_report_passes_and_command_round_trips(self):
        report = make_report()
        self.assertEqual(reports.check_payload(report), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "my report.json"
            path.write_text(json.dumps(report))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(reports.main([str(path), "--emit-command", "my agent", "--idempotency-key", "run-report-1"]), 0)
            argv = shlex.split(out.getvalue())
            self.assertEqual(json.loads(Path(argv[argv.index("--insight-file") + 1]).read_text()), report)
            self.assertEqual(argv[argv.index("--agent") + 1], "my agent")
            self.assertEqual(argv[argv.index("--idempotency-key") + 1], "run-report-1")

    def test_rejects_non_finite_json_in_report_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(make_report()).replace('"low": 0.127', '"low": NaN'))
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(reports.main([str(path)]), 1)
            self.assertIn("NaN", err.getvalue())

    def test_rejects_top_level_and_legacy_metadata_violations(self):
        bad = make_report(name="-bad", extra=1)
        bad["coverage"]["sessions_analyzed"] = 300
        bad["coverage"]["started_after"] = "2026-10-12T00:00:00"
        bad["highlight"] = {"finding_id": "missing", "artifact_index": 0}
        bad["metadata"]["kitaru.insights/v1"] = {"cta_label": "legacy"}
        bad["metadata"]["kitaru.insights.skill/v1"]["findings"]["p1"]["rate"] = {"basis": "targeted_only", "low": 0.1}
        errors = "\n".join(reports.check_report(bad))
        for fragment in (
            "report.name",
            "unknown field extra",
            "cannot exceed sessions_available",
            "timezone-aware",
            "does not match any finding",
            "legacy card key",
            "must not carry an interval",
        ):
            self.assertIn(fragment, errors)

    def test_rejects_stray_non_counterexample_evidence_but_allows_counterexample(self):
        report = make_report()
        # Counterexample in make_report already uses a fresh UUID outside contributing_session_ids.
        self.assertEqual(reports.check_report(report), [])
        # Changing the non-counterexample row to an unknown session must fail.
        report["findings"][0]["artifacts"][1]["rows"][0]["session_id"] = str(uuid.uuid4())
        self.assertTrue(any("not in contributing_session_ids" in e for e in reports.check_report(report)))

    def test_plain_text_summaries_and_no_run_id_leaks(self):
        for bad in ("Calls `search` twice.", "**Bold** claim.", "Line one.\nLine two.", "- list", "See [x](https://x)", "x" * 321):
            r = make_report(summary=bad)
            self.assertTrue(any("report.summary" in e for e in reports.check_report(r)), bad)
        leaky = make_report()
        run_id = leaky["metadata"]["kitaru.insights.skill/v1"]["run_id"]
        leaky["findings"][0]["body"] = f"Generated by {run_id}."
        self.assertTrue(any("contains the run_id" in e for e in reports.check_report(leaky)))

    def test_primary_finding_cap_and_duplicate_finding_ids(self):
        many_findings = [make_finding(fid=f"p{i}") for i in range(9)]
        report = make_report(findings=many_findings)
        for i in range(9):
            report["metadata"]["kitaru.insights.skill/v1"]["findings"][f"p{i}"] = report["metadata"]["kitaru.insights.skill/v1"]["findings"]["p1"]
        self.assertTrue(any("at most 8" in e for e in reports.check_report(report)))
        dup = make_report(findings=[make_finding("p1"), make_finding("p1")])
        self.assertTrue(any("duplicate finding id" in e for e in reports.check_report(dup)))

    def test_artifact_title_validation(self):
        self.assertEqual(reports.check_artifact({"type": "rate", "title": "Skip rate", "rate": 0.14}), [])
        self.assertTrue(any(".title" in e for e in reports.check_artifact({"type": "rate", "title": "", "rate": 0.14})))
        self.assertTrue(any(".title" in e for e in reports.check_artifact({"type": "rate", "title": "x" * 121, "rate": 0.14})))

    def test_all_17_artifact_types_pass_validation(self):
        sid, sid2, nid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        all_17 = [
            {"type": "stat_grid", "title": "Run overview", "items": [{"label": "New", "value": 3, "tone": "warn"}]},
            {"type": "rate", "presentation": "share_bar", "rate": 0.24, "numerator": 29, "denominator": 120},
            {"type": "categorical", "presentation": "ranked_bars", "unit": "sessions", "values": [{"label": "Policy", "value": 24}, {"label": "Other", "value": 5}]},
            {"type": "comparison", "presentation": "dumbbell", "before_label": "v1", "after_label": "v2", "unit": "%", "rows": [{"label": "Refund fail", "before": 14, "after": 2, "before_detail": "31/214", "after_detail": "4/214"}]},
            {"type": "table", "columns": [{"key": "tool", "label": "Tool", "format": "mono"}, {"key": "rate", "label": "Fail", "format": "percent_bar"}], "rows": [{"tool": "search", "rate": 0.12}]},
            {"type": "binned", "presentation": "columns", "unit": "calls", "median": 6, "p95": 18, "bins": [{"lower_bound": 0, "upper_bound": 10, "count": 142}, {"lower_bound": 10, "upper_bound": None, "count": 72}]},
            {"type": "session_dots", "unit": "s", "scale_min": 0, "scale_max": 60, "points": [{"session_id": sid, "value": 12.5, "highlight": True}]},
            {"type": "time_series", "presentation": "line", "x_labels": ["W1", "W2", "W3"], "unit": "%", "series": [{"label": "Fail rate", "values": [12, 14, 9]}], "annotations": [{"x_index": 2, "label": "v2"}]},
            {"type": "step_strip", "presentation": "rows", "total_steps": 10, "rows": [{"label": "Policy skipped", "session_count": 24, "last_good_step": 6, "first_wrong_step": 7, "severity": "high", "session_ids": [sid]}]},
            {"type": "failure_matrix", "state_by": "tool", "rows": ["edit_order"], "cols": ["issue_refund"], "total_failed": 31, "cells": [{"from_state": "edit_order", "to_state": "issue_refund", "count": 31, "sessions": [{"session_id": sid, "node_id": nid}]}]},
            {"type": "flow_sankey", "stages": [{"label": "Start", "nodes": [{"id": "s", "label": "Edit", "count": 47}]}, {"label": "End", "nodes": [{"id": "ok", "label": "Checked", "count": 16, "tone": "good"}, {"id": "bad", "label": "Skipped", "count": 31, "tone": "danger"}]}], "links": [{"source": "s", "target": "ok", "count": 16}, {"source": "s", "target": "bad", "count": 31}]},
            {"type": "step_story", "session_id": sid, "steps": [{"number": 1, "text": "User edits order", "role": "user"}, {"number": 7, "text": "Calls issue_refund without policy check", "role": "tool", "tool_name": "issue_refund", "node_id": nid, "tone": "danger"}]},
            {"type": "tool_cycle", "steps": [{"name": "search", "status": "ok"}, {"name": "fetch_page", "status": "error"}], "repeat_count": 14, "session_count": 23},
            {"type": "session_comparison", "left": {"session_id": sid, "verdict": "fail", "steps": [{"label": "edit_order"}, {"label": None, "status": "missing"}, {"label": "issue_refund", "status": "highlight_bad"}]}, "right": {"session_id": sid2, "verdict": "pass", "steps": [{"label": "edit_order"}, {"label": "check_refund_policy", "status": "highlight_good"}, {"label": "issue_refund"}]}},
            {"type": "session_timeline", "session_id": sid, "total_duration_ms": 4200, "spans": [{"name": "lookup_order", "start_ms": 0, "duration_ms": 800}, {"name": "issue_refund", "start_ms": 800, "duration_ms": 3400, "tone": "danger"}]},
            {"type": "evidence", "presentation": "compact", "total_sessions": 31, "rows": [{"session_id": sid, "verdict": "fail"}]},
            {"type": "text", "style": "hypothesis", "label": "Code hypothesis", "content": "State flag cleared.", "file_path": "src/orders.py", "revision": "abc1234"},
        ]
        for artifact in all_17:
            self.assertEqual(reports.check_artifact(artifact), [], f"failed for {artifact['type']}")

    def test_enforces_zuris_11_chart_limits(self):
        cases = [
            ({"type": "categorical", "presentation": "ranked_bars", "values": [{"label": f"c{i}", "value": i + 1} for i in range(9)]}, "at most 8"),
            ({"type": "categorical", "presentation": "donut", "values": [{"label": "a", "value": 1}, {"label": "b", "value": 1}]}, "3 to 4"),
            ({"type": "categorical", "presentation": "split_bar", "values": [{"label": "a", "value": 99}, {"label": "b", "value": 1}]}, "at least 2%"),
            ({"type": "comparison", "presentation": "side_by_side", "before_label": "a", "after_label": "b", "rows": [{"label": f"r{i}", "before": 1, "after": 2} for i in range(4)]}, "at most 3"),
            ({"type": "comparison", "presentation": "dot_plot", "before_label": "a", "after_label": "b", "rows": [{"label": f"r{i}", "before": 1, "after": 2} for i in range(9)]}, "at most 8"),
            ({"type": "binned", "bins": [{"lower_bound": 0, "upper_bound": 5, "count": 1}, {"lower_bound": 6, "upper_bound": None, "count": 2}]}, "previous bin's upper_bound"),
            ({"type": "session_dots", "points": [{"session_id": str(uuid.uuid4()), "value": i} for i in range(101)]}, "1 to 100"),
            ({"type": "time_series", "presentation": "ordered_columns", "x_labels": [f"v{i}" for i in range(13)], "series": [{"label": "s", "values": list(range(13))}]}, "at most 12"),
            ({"type": "time_series", "presentation": "stacked_columns", "x_labels": ["a", "b", "c"], "series": [{"label": f"s{i}", "values": [1, 2, 3]} for i in range(4)]}, "at most 3"),
            ({"type": "time_series", "presentation": "line", "x_labels": ["a", "b", "c"], "series": [{"label": f"s{i}", "values": [1, 2, 3]} for i in range(6)]}, "at most 5"),
            ({"type": "time_series", "presentation": "highlight_line", "x_labels": ["a", "b", "c"], "series": [{"label": "a", "values": [1, 2, 3]}, {"label": "b", "values": [2, 3, 4]}]}, "exactly one series"),
            ({"type": "time_series", "presentation": "small_multiples", "x_labels": ["a", "b", "c"], "series": [{"label": f"s{i}", "values": [1, 2, 3]} for i in range(7)]}, "at most 6"),
            ({"type": "step_strip", "presentation": "small_multiples", "total_steps": 10, "rows": [{"label": f"a{i}"} for i in range(7)]}, "at most 6"),
            ({"type": "failure_matrix", "rows": [f"r{i}" for i in range(7)], "cols": ["c0"], "total_failed": 1, "cells": []}, "1 to 6"),
            ({"type": "flow_sankey", "stages": [{"nodes": [{"id": f"n{i}", "label": f"n{i}", "count": 1} for i in range(5)]}, {"nodes": [{"id": f"m{i}", "label": f"m{i}", "count": 1} for i in range(4)]}], "links": [{"source": "n0", "target": "m0", "count": 1}]}, "at most 8 nodes"),
        ]
        for artifact, expected in cases:
            errors = "\n".join(reports.check_artifact(artifact))
            self.assertIn(expected, errors, f"expected {expected!r} for {artifact}")

    def test_batch_rejects_duplicate_names_and_mixed_runs(self):
        errors = reports.check_payload([make_report(), make_report()])
        self.assertIn("payload: report names must be unique within a batch", errors)
        self.assertIn("payload: every report in one batch must share one run_id", errors)

    def test_warns_on_long_finding_titles_and_repeated_rate_leads(self):
        report = make_report()
        f0 = report["findings"][0]
        f0["title"] = "A" * 60
        f1 = {**f0, "id": "p2", "title": "Short title two"}
        f2 = {**f0, "id": "p3", "title": "Short title three"}
        report["findings"] = [f0, f1, f2]
        warnings = "\n".join(reports.collect_warnings(report))
        self.assertIn("findings[0].title: 60 chars", warnings)
        self.assertIn("3 primary findings lead with a rate chart", warnings)
        clean = make_report()
        clean["findings"][0]["title"] = "Short sidebar-friendly title"
        self.assertEqual(reports.collect_warnings(clean), [])


class ScopeCountsTest(unittest.TestCase):
    def test_cost_concentration_needs_enough_sessions(self):
        few = scope_counts.build([session(i, cost=1.0) for i in range(5)])
        self.assertIsNone(few["scope"]["cost"]["top_share"])
        items = [session(i, cost=10.0 if i < 2 else 1.0) for i in range(20)]
        self.assertEqual(scope_counts.build(items)["scope"]["cost"]["top_share"], round(20 / 38, 4))

    def test_cost_reads_decimal_strings(self):
        # Kitaru serializes Decimal cost as a JSON string.
        items = [session(i, cost="10.00" if i < 2 else "1.00") for i in range(20)]
        self.assertEqual(scope_counts.build(items)["scope"]["cost"]["top_share"], round(20 / 38, 4))

    def test_cache_writes_keep_unknown_counts_out_of_the_total(self):
        items = [
            {**session(1), "tokens": {"input_tokens": 10, "cache_write_input_tokens": 300}},
            {**session(2), "tokens": {"input_tokens": 10, "cache_write_input_tokens": None}},
            session(3),
        ]
        writes = scope_counts.build(items)["scope"]["cache_writes"]
        self.assertEqual(writes, {"sessions_reporting": 1, "sessions_unknown": 2, "cache_write_input_tokens": 300})
        self.assertIsNone(scope_counts.build([session(4)])["scope"]["cache_writes"]["cache_write_input_tokens"])

    def test_cache_share_follows_the_convention_the_data_shows(self):
        exclusive = [{**session(1), "tokens": {"input_tokens": 100, "cached_input_tokens": 300}}]
        cache = scope_counts.build(exclusive)["scope"]["cache"]
        self.assertEqual((cache["convention"], cache["share"]), ("exclusive", 0.75))
        unknown = [{**session(1), "tokens": {"input_tokens": 400, "cached_input_tokens": 100}}]
        cache = scope_counts.build(unknown)["scope"]["cache"]
        self.assertEqual((cache["convention"], cache["share_if_inclusive"], cache["share_if_exclusive"]), ("unknown", 0.25, 0.2))

    def test_cache_share_skips_sessions_with_unknown_input_tokens(self):
        # Kitaru reports a token total as null when any call in the session lacks it.
        items = [
            {**session(1), "tokens": {"input_tokens": None, "cached_input_tokens": 50}},
            {**session(2), "tokens": {"input_tokens": 1000, "cached_input_tokens": 400}},
        ]
        cache = scope_counts.build(items)["scope"]["cache"]
        self.assertEqual((cache["sessions_reporting"], cache["convention"], cache["share_if_inclusive"]), (1, "unknown", 0.4))

    def test_counts_per_agent_version(self):
        items = [{**session(i, status="failed" if i == 0 else "completed"), "agent_version_id": "v1" if i < 3 else "v2"} for i in range(5)]
        by_version = scope_counts.build(items)["by_version"]
        self.assertEqual(by_version["v1"]["status"], {"completed": 2, "failed": 1})
        self.assertEqual(by_version["v2"]["sessions"], 2)


    def test_compares_windows_and_flags_only_clear_changes(self):
        def week(day: int, i: int, failed: bool, tools: int) -> dict:
            return {**session(i, status="failed" if failed else "completed", tools=tools), "started_at": f"2026-11-{day:02d}T10:00:00+00:00", "ended_at": f"2026-11-{day:02d}T10:05:00+00:00"}

        items = [week(3, i, i < 1, 2) for i in range(40)] + [week(10, 100 + i, i < 16, 6) for i in range(40)]
        windows = pick_sample.parse_windows(["last=2026-11-01T00:00:00Z/2026-11-08T00:00:00Z", "this=2026-11-08T00:00:00Z/2026-11-15T00:00:00Z"])
        document = scope_counts.build(items, windows)
        self.assertEqual((document["by_window"]["last"]["sessions"], document["by_window"]["this"]["sessions"]), (40, 40))
        changes = {c["metric"]: c for c in document["window_changes"]}
        self.assertTrue(changes["failed_share"]["notable"])
        self.assertEqual((changes["tool_calls_p50"]["ratio"], changes["tool_calls_p50"]["notable"]), (3.0, True))
        self.assertFalse(changes["duration_seconds_p50"]["notable"])
        small = scope_counts.build(items[:5] + items[40:45], windows)["window_changes"]
        self.assertTrue(all(not c["comparable"] and not c["notable"] for c in small))

    def test_rejects_bad_windows(self):
        for spec in ("nameless", "a=2026-11-08T00:00:00/2026-11-09T00:00:00Z", "a=2026-11-09T00:00:00Z/2026-11-08T00:00:00Z"):
            with self.assertRaises(ValueError):
                pick_sample.parse_window(spec)
        with self.assertRaisesRegex(ValueError, "unique"):
            pick_sample.parse_windows(["a=2026-11-01T00:00:00Z/2026-11-02T00:00:00Z"] * 2)


class EvaluationsToJudgmentsTest(unittest.TestCase):
    def row(self, session_id: str, name: str, score, value=None) -> dict:
        return {"id": f"{session_id}-{name}", "session_id": session_id, "name": name, "score": score, "value": value, "explanation": "jev"}

    def test_maps_probabilities_and_unavailable_rows(self):
        rows = [self.row("s1", "insights.p1", 0.93), self.row("s2", "insights.p1", 0.1), self.row("s3", "insights.p1", 0.5), self.row("s4", "insights.p1", None, "unavailable"), self.row("s1", "other", 0.9)]
        judged = {j["session_id"]: j["verdict"] for j in to_judgments.convert(rows, "insights.", 0.8)}
        self.assertEqual(judged, {"s1": "yes", "s2": "no", "s3": "unclear", "s4": "unavailable"})

    def test_rejects_duplicate_runs_and_empty_results(self):
        with self.assertRaisesRegex(ValueError, "two insights.p1 rows"):
            to_judgments.convert([self.row("s1", "insights.p1", 0.9), {**self.row("s1", "insights.p1", 0.2), "id": "other"}], "insights.", 0.8)
        with self.assertRaisesRegex(ValueError, "no evaluation rows"):
            to_judgments.convert([self.row("s1", "other", 0.9)], "insights.", 0.8)


class ToolStatsTest(unittest.TestCase):
    def step(self, index: int, name: str, status: str = "completed", node_input: str | None = "{}", node_type: str = "tool_call") -> dict:
        return {"index": index, "node_id": str(uuid.UUID(int=index + 1)), "node_type": node_type, "name": name, "status": status, "input": node_input, "duration_seconds": 1.0 + index}

    def transcript(self, session_id: str, steps: list[dict], started: str = "2026-11-10T10:00:00Z") -> dict:
        return {"session_id": session_id, "status": "completed", "started_at": started, "steps": steps, "node_count": len(steps)}

    def test_counts_failures_retries_repeats_loops_and_cycles(self):
        long_query = '{"query": "' + "q" * 80 + '"}'
        loop = [self.step(0, "chat", node_type="llm_call", node_input="hi"), self.step(1, "search", node_input=long_query), self.step(2, "search", node_input="(same as [1])"), self.step(3, "search", status="failed", node_input='{"query": "other"}'), self.step(4, "search", node_input='{"query": "other"}')]
        cycle = [self.step(i, "plan" if i % 2 == 0 else "act") for i in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            export, out, table = Path(tmp) / "export", Path(tmp) / "tools.json", Path(tmp) / "tools.md"
            export.mkdir()
            (export / "picked.read.json").write_text(json.dumps({"items": [self.transcript("s1", loop), self.transcript("s2", cycle, "2026-11-03T10:00:00Z")]}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tool_stats.main([str(export), "--out", str(out), "--table-out", str(table), "--window", "last=2026-11-01T00:00:00Z/2026-11-08T00:00:00Z", "--window", "this=2026-11-08T00:00:00Z/2026-11-15T00:00:00Z"]), 0)
            document = json.loads(out.read_text())
            search = next(r for r in document["scope"]["tools"] if r["tool"] == "search")
            self.assertEqual((search["calls"], search["failed"], search["retries_after_failure"], search["identical_repeats"], search["loop_sessions"], search["longest_run"]), (4, 1, 1, 2, 1, 4))
            self.assertEqual(search["examples"]["loop"], [{"session_id": "s1", "node_id": str(uuid.UUID(int=2))}])
            self.assertEqual(document["scope"]["cycles"][0]["cycle"], "plan → act")
            self.assertEqual((document["by_window"]["last"]["tool_calls"], document["by_window"]["this"]["tool_calls"]), (6, 4))
            self.assertIn("| `search` | 4 | 1 | 1 (25.0%) | 1 | 2 | 1 |", table.read_text())

    def test_reads_raw_node_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp)
            (export / "s1.session.json").write_text(json.dumps({"item": {"id": "s1", "started_at": "2026-11-10T10:00:00Z"}}))
            nodes = [{"id": f"n{i}", "node_type": "tool_call", "tool_name": "lookup", "status": "failed" if i == 0 else "completed", "inputs": {"id": 1}, "started_at": "2026-11-10T10:00:00Z", "ended_at": "2026-11-10T10:00:02Z"} for i in range(2)]
            (export / "s1.nodes.json").write_text(json.dumps({"items": nodes}))
            sid, started, calls = tool_stats.tool_calls(condense.load_export(export)["s1"])
            stats = tool_stats.count([(sid, calls)], 3, 3)["tools"][0]
            self.assertEqual((stats["calls"], stats["retries_after_failure"], stats["identical_repeats"], stats["seconds"]["p50"]), (2, 1, 1, 2.0))


if __name__ == "__main__":
    unittest.main()
