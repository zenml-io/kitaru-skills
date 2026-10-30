"""Behavioral tests for the offline kitaru-insights helpers."""

import contextlib
import importlib.util
import io
import json
import shlex
import tempfile
import unittest
import uuid
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/kitaru-insights/scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pick_sample = load("pick_sample")
condense = load("condense_sessions")
tally = load("tally_notes")
cards = load("check_cards")


def session(i: int, status: str = "completed", cost: float = 0.01, tools: int = 2, agent: str = "agent") -> dict:
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
            self.assertIn(f"[{node_id}]", text)
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
        self.assertEqual(document["patterns"][0]["rate"], {"basis": "census", "numerator": 2, "denominator": 12, "low": None, "high": None})

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


def card(**overrides) -> dict:
    sid = str(uuid.uuid4())
    base = {
        "name": "kitaru-insights-p1",
        "title": "Refunds promised before checking the return window",
        "description": "Example.",
        "data": {"type": "text", "content": "Body."},
        "metadata": {
            "kitaru.insights/v1": {"investigation_prompt": "Use the kitaru-investigation skill.", "cta_label": "Investigate early refunds", "contributing_session_ids": [sid], "evidence": [{"session_id": sid, "node_id": None, "signal": "refund before policy"}]},
            "kitaru.insights.skill/v1": {"schema_version": 1, "run_id": str(uuid.uuid4()), "level": "standard", "scope": {"population_count": 10, "population_sha256": "a" * 64}, "sample": {}, "pattern": {}, "rate": {"basis": "measurement", "low": 0.1, "high": 0.5}},
        },
    }
    base.update(overrides)
    return base


class CheckCardsTest(unittest.TestCase):
    def test_valid_card_passes_and_command_round_trips(self):
        batch = [card()]
        self.assertEqual(cards.check_cards(batch), [])
        argv = shlex.split(cards.build_command(batch, "my agent", "run-batch-1"))
        self.assertEqual(json.loads(argv[argv.index("--insight") + 1]), batch[0])
        self.assertEqual(argv[argv.index("--agent") + 1], "my agent")

    def test_rejects_contract_violations(self):
        bad = card(name="-bad", extra=1)
        bad["metadata"]["kitaru.insights/v1"]["cta_label"] = "x" * 41
        bad["metadata"]["kitaru.insights/v1"]["eyebrow"] = "analyzer-only"
        bad["metadata"]["kitaru.insights.skill/v1"]["rate"] = {"basis": "targeted_only", "low": 0.1}
        errors = "\n".join(cards.check_cards([bad]))
        for fragment in ("name must", "unknown field extra", "cta_label", "eyebrow", "must not carry an interval"):
            self.assertIn(fragment, errors)

    def test_rejects_stray_evidence_extra_keys_and_infinite_values(self):
        stray = card()
        stray["metadata"]["kitaru.insights/v1"]["evidence"][0]["session_id"] = str(uuid.uuid4())
        self.assertTrue(any("not in contributing_session_ids" in e for e in cards.check_cards([stray])))
        values = card(data={"type": "categorical", "values": [{"label": "a", "value": float("inf"), "note": "x"}]})
        errors = "\n".join(cards.check_cards([values]))
        self.assertIn("only label and value", errors)
        self.assertIn("non-negative numbers", errors)
        bounds = card(data={"type": "binned", "bins": [{"lower_bound": "0", "upper_bound": 1, "count": 1}]})
        self.assertTrue(any("finite numbers" in e for e in cards.check_cards([bounds])))
        noticed = card()
        noticed["metadata"]["kitaru.insights.skill/v1"]["rate"] = {"basis": "random_slice", "low": 0.1, "high": 0.4}
        self.assertTrue(any("must not carry an interval" in e for e in cards.check_cards([noticed])))

    def test_rejects_bad_bins_and_too_many_cards(self):
        bins = card(data={"type": "binned", "bins": [{"lower_bound": 0, "upper_bound": 5, "count": 1}, {"lower_bound": 6, "upper_bound": None, "count": 2}]})
        self.assertTrue(any("does not start" in e for e in cards.check_cards([bins])))
        many = [card(name=f"kitaru-insights-p{i}") for i in range(9)]
        self.assertTrue(any("at most 8" in e for e in cards.check_cards(many)))

    def test_rejects_mixed_runs_and_duplicate_names(self):
        errors = cards.check_cards([card(), card()])
        self.assertIn("cards: names must be unique within a run", errors)
        self.assertIn("cards: every card in one batch must share one run_id", errors)


if __name__ == "__main__":
    unittest.main()
