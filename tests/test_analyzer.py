import unittest
from pathlib import Path

from deposit_defender_desk.analyzer import (
    CaseInfo,
    analyze_case,
    load_sample,
    parse_deduction_csv,
    parse_evidence_csv,
    parse_note_text,
)


class DepositDefenderTests(unittest.TestCase):
    def test_evidence_csv_mapping(self):
        csv_text = "timestamp,room,notes,file\n2026-03-31,Kitchen,Clean sink,photo.jpg\n"
        evidence, metadata = parse_evidence_csv(csv_text)
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].area, "kitchen")
        self.assertEqual(metadata["evidence_count"], 1)

    def test_missing_evidence_fields(self):
        with self.assertRaisesRegex(ValueError, "Missing required evidence fields"):
            parse_evidence_csv("date,notes\n2026-03-31,Clean\n")

    def test_deduction_csv_mapping(self):
        csv_text = "item,location,charge,cost,receipt\n1,Living room,Wall repaint,300,\n"
        deductions, metadata = parse_deduction_csv(csv_text)
        self.assertEqual(len(deductions), 1)
        self.assertEqual(deductions[0].category, "wall damage")
        self.assertEqual(metadata["deduction_count"], 1)

    def test_note_text_parser(self):
        text = Path(__file__).resolve().parents[1] / "examples" / "evidence_notes.txt"
        evidence, metadata = parse_note_text(text.read_text(encoding="utf-8"))
        self.assertEqual(len(evidence), 3)
        self.assertEqual(len(metadata["rejected_blocks"]), 1)

    def test_analysis_matches_evidence_and_flags_gaps(self):
        evidence, deductions = load_sample(Path(__file__).resolve().parents[1] / "samples")
        report = analyze_case(CaseInfo(state="CA", move_out_date="2026-03-31", deposit_amount=1800, deduction_notice_date="2026-04-28"), deductions, evidence)
        self.assertEqual(report["summary"]["deduction_count"], 5)
        self.assertTrue(report["summary"]["notice_late"])
        self.assertGreaterEqual(report["summary"]["high_strength_findings"], 1)
        self.assertTrue(report["findings"][0]["evidence_checklist"])

    def test_custom_rule_changes_deadline(self):
        evidence, deductions = load_sample(Path(__file__).resolve().parents[1] / "samples")
        report = analyze_case(
            CaseInfo(state="ZZ", move_out_date="2026-03-31", deposit_amount=1800),
            deductions,
            evidence,
            rule_json='{"ZZ":{"deposit_return_days":10,"receipt_threshold":100,"notes":"custom"}}',
        )
        self.assertEqual(report["summary"]["deposit_return_deadline"], "2026-04-10")

    def test_markdown_export_shape(self):
        evidence, deductions = load_sample(Path(__file__).resolve().parents[1] / "samples")
        report = analyze_case(CaseInfo(state="GENERIC", move_out_date="2026-03-31", deposit_amount=1800), deductions, evidence)
        self.assertIn("draft_dispute_outline", report)


if __name__ == "__main__":
    unittest.main()

