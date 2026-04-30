from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deposit_defender_desk.analyzer import CaseInfo, analyze_case, load_sample, parse_note_text, save_outputs


def main() -> None:
    evidence, deductions = load_sample(ROOT / "samples")
    if len(evidence) < 8 or len(deductions) < 5:
        raise SystemExit("sample evidence/deduction corpus is too small")
    text_evidence, metadata = parse_note_text((ROOT / "examples" / "evidence_notes.txt").read_text(encoding="utf-8"))
    if metadata["evidence_count"] < 3:
        raise SystemExit("note parser did not extract expected evidence")
    report = analyze_case(
        CaseInfo(state="CA", move_out_date="2026-03-31", deposit_amount=1800, deduction_notice_date="2026-04-28"),
        deductions,
        evidence + text_evidence,
    )
    if report["summary"]["deduction_count"] != 5:
        raise SystemExit("analysis did not include deductions")
    paths = save_outputs(report, ROOT / "outputs")
    for path in paths.values():
        if not Path(path).exists():
            raise SystemExit(f"missing output: {path}")
    print("Smoke test passed: evidence import, deduction triage, deadline check, and report export work.")


if __name__ == "__main__":
    main()

