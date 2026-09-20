"""Behavioral tests for the offline validation report."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/kitaru-validate-evaluator/scripts/summarize_validation.py"
)
spec = importlib.util.spec_from_file_location("validation_report", SCRIPT)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def snapshot(outcomes: list[str], label: str = "fail") -> dict:
    rows = []
    for i, outcome in enumerate(outcomes):
        rows.append(
            {
                "session_id": f"s{i}",
                "group_id": f"g{i}",
                "split": "development",
                "investigation_id": "investigation",
                "investigation_session_id": f"link{i}",
                "human_label": label,
                "label_updated_at": "2026-09-20T12:00:00Z",
                "exclusion_reason": None,
                "evaluation": {
                    "job_id": "job",
                    "task_id": f"task{i}",
                    "evaluator_version_id": "version",
                    "result_name": "criterion",
                    "params": {},
                    "outcome": outcome,
                    "result_id": None
                    if outcome in ("error", "missing")
                    else f"result{i}",
                },
            }
        )
    return {
        "schema_version": 1,
        "criterion": {"id": "criterion", "revision": "1", "text": "One narrow rule"},
        "evaluator": {
            "version_id": "version",
            "result_name": "criterion",
            "params": {},
        },
        "selected_session_ids": [row["session_id"] for row in rows],
        "records": rows,
    }


class ReportTests(unittest.TestCase):
    def test_twelve_failure_example(self) -> None:
        result = report.summarize(
            snapshot(["fail"] * 8 + ["pass"] * 2 + ["held", "error"])
        )
        split = result["splits"]["development"]
        self.assertEqual(split["selected"], 12)
        self.assertEqual(
            split["outcomes_by_human_label"]["fail"],
            {
                "pass": 2,
                "fail": 8,
                "held": 1,
                "unavailable": 0,
                "error": 1,
                "missing": 0,
            },
        )
        metrics = split["metrics_by_human_label"]["fail"]
        self.assertEqual(
            metrics["decided_agreement"],
            {"numerator": 8, "denominator": 10, "rate": 0.8},
        )
        self.assertEqual(metrics["all_labeled_correct_decisions"]["denominator"], 12)
        self.assertAlmostEqual(metrics["coverage"]["rate"], 10 / 12)

    def test_no_decisions_or_empty_class_is_not_zero_accuracy(self) -> None:
        result = report.summarize(snapshot(["held", "unavailable", "missing"], "pass"))[
            "splits"
        ]["development"]
        self.assertIsNone(
            result["metrics_by_human_label"]["pass"]["decided_agreement"]["rate"]
        )
        self.assertIsNone(result["metrics_by_human_label"]["fail"]["coverage"]["rate"])
        self.assertEqual(
            result["metrics_by_human_label"]["pass"]["coverage"]["rate"], 0
        )
        self.assertEqual(report.summarize(snapshot([]))["selected"], 0)

    def test_separate_accounting_exclusion_takes_precedence(self) -> None:
        data = snapshot(["pass"] * 4)
        data["records"][0]["human_label"] = "uncertain"
        data["records"][0]["exclusion_reason"] = "Evidence unavailable"
        data["records"][1]["human_label"] = "uncertain"
        data["records"][2]["human_label"] = "unreviewed"
        for row in data["records"][:3]:
            row["evaluation"] = None
        before = copy.deepcopy(data)
        result = report.summarize(data)["splits"]["development"]
        self.assertEqual(
            result["separate"],
            {"excluded": ["s0"], "uncertain": ["s1"], "unreviewed": ["s2"]},
        )
        self.assertEqual(sum(result["outcomes_by_human_label"]["fail"].values()), 1)
        self.assertEqual(data, before)

    def test_rejects_ambiguous_or_incomplete_identity(self) -> None:
        mutations = [
            lambda d: d["selected_session_ids"].append("missing"),
            lambda d: d["selected_session_ids"].append("s0"),
            lambda d: d["records"].append(copy.deepcopy(d["records"][0])),
            lambda d: d["records"][1]["evaluation"].update(task_id="task0"),
            lambda d: d["records"][1]["evaluation"].update(result_id="result0"),
            lambda d: d["records"][0]["evaluation"].update(params={"threshold": 0.9}),
            lambda d: d["records"][0]["evaluation"].update(
                evaluator_version_id="different"
            ),
            lambda d: d["records"][0]["evaluation"].update(result_name="different"),
            lambda d: d["records"][0].update(evaluation=None),
            lambda d: d.update(schema_version=True),
            lambda d: d["records"][0]["evaluation"].update(outcome="error"),
            lambda d: d["records"][0]["evaluation"].update(result_id=None),
            lambda d: d["evaluator"]["params"].update(value=float("nan")),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                data = snapshot(["pass", "fail"])
                mutate(data)
                with self.assertRaises(ValueError):
                    report.summarize(data)

    def test_explicit_batches_and_shared_investigation_are_allowed(self) -> None:
        data = snapshot(["pass", "fail"])
        data["records"][1]["evaluation"]["job_id"] = "second-batch"
        self.assertEqual(report.summarize(data)["selected"], 2)
        data["records"][1]["split"] = "test"
        self.assertEqual(report.summarize(data)["splits"]["test"]["selected"], 1)

    def test_related_groups_cannot_cross_splits(self) -> None:
        data = snapshot(["pass", "fail"])
        data["records"][1].update(
            split="test", investigation_id="test-investigation", group_id="g0"
        )
        with self.assertRaisesRegex(ValueError, "group_id crosses splits"):
            report.validate(data)

    def test_drift_detects_labels_config_and_provenance_not_order(self) -> None:
        old = snapshot(["pass", "fail"])
        new = copy.deepcopy(old)
        new["records"].reverse()
        new["selected_session_ids"].reverse()
        self.assertEqual(report.compare_snapshots(new, old), [])
        new["records"][0]["human_label"] = "pass"
        new["records"][0]["evaluation"]["result_id"] = "rerun-result"
        self.assertEqual(
            report.compare_snapshots(new, old),
            ["records.s1.evaluation", "records.s1.human_label"],
        )
        new = copy.deepcopy(old)
        new["criterion"]["revision"] = "2"
        new["evaluator"]["params"] = {"threshold": 0.9}
        for row in new["records"]:
            row["evaluation"]["params"] = {"threshold": 0.9}
        changes = report.compare_snapshots(new, old)
        self.assertIn("criterion", changes)
        self.assertIn("evaluator", changes)

    def test_cli_report_drift_and_malformed_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            baseline = Path(directory) / "baseline.json"
            data = snapshot(["pass"])
            path.write_text(json.dumps(data))
            baseline.write_text(json.dumps(data))
            run = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["selected"], 1)
            data["records"][0]["human_label"] = "pass"
            path.write_text(json.dumps(data))
            run = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--baseline", str(baseline)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)["status"], "changed")
            self.assertNotIn("splits", json.loads(run.stdout))
            for invalid in (
                '{"schema_version":1,"schema_version":1}',
                '{"value":NaN}',
                "[]",
                "{",
            ):
                path.write_text(invalid)
                run = subprocess.run(
                    [sys.executable, str(SCRIPT), str(path)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, "")
                self.assertEqual(json.loads(run.stderr)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
