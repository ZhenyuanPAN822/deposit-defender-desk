from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable


AREA_ALIASES = {
    "kitchen": ("kitchen", "sink", "counter", "countertop", "stove", "oven", "fridge", "refrigerator"),
    "bathroom": ("bathroom", "bath", "toilet", "shower", "tub", "vanity"),
    "bedroom": ("bedroom", "room", "closet"),
    "living room": ("living", "lounge", "floor", "wall", "carpet"),
    "common area": ("common", "hall", "foyer", "stairs", "landing"),
}

DEFAULT_RULES = {
    "CA": {"deposit_return_days": 21, "receipt_threshold": 125, "notes": "California rules vary; verify Civil Code section 1950.5."},
    "NY": {"deposit_return_days": 14, "receipt_threshold": 0, "notes": "New York rules vary by tenancy and locality; verify current statute."},
    "TX": {"deposit_return_days": 30, "receipt_threshold": 0, "notes": "Forwarding address may be required before deadline obligations apply."},
    "FL": {"deposit_return_days": 30, "receipt_threshold": 0, "notes": "Landlord notice rules can vary; verify current Florida statute."},
    "PA": {"deposit_return_days": 30, "receipt_threshold": 0, "notes": "Local rules such as Philadelphia practice may add requirements."},
    "GENERIC": {"deposit_return_days": 30, "receipt_threshold": 0, "notes": "Generic placeholder. Verify local law before action."},
}

DEDUCTION_KEYWORDS = {
    "cleaning": ("clean", "deep clean", "trash", "junk", "removal"),
    "wall damage": ("wall", "paint", "drywall", "hole", "scuff"),
    "floor damage": ("floor", "carpet", "scratch", "stain", "dent", "indent"),
    "appliance": ("appliance", "fridge", "oven", "stove", "dishwasher"),
    "missing item": ("missing", "lost", "replace", "remote", "key", "blind"),
}


@dataclass
class EvidenceItem:
    evidence_id: str
    date: str
    area: str
    description: str
    stage: str = "move-out"
    file_path: str = ""
    source: str = "csv"
    confidence: float = 0.8


@dataclass
class Deduction:
    deduction_id: str
    area: str
    description: str
    amount: float
    landlord_evidence: str = ""
    category: str = "uncategorized"
    source: str = "csv"


@dataclass
class CaseInfo:
    state: str = "GENERIC"
    move_out_date: str = ""
    deposit_amount: float = 0.0
    deduction_notice_date: str = ""
    forwarding_address_sent: bool = True


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def find_column(headers: Iterable[str], candidates: Iterable[str]) -> str | None:
    normalized = {normalize_header(header): header for header in headers}
    for candidate in candidates:
        key = normalize_header(candidate)
        if key in normalized:
            return normalized[key]
    return None


def parse_date(value: str) -> date:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d %Y", "%B %d %Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {value!r}")


def parse_amount(value: object) -> float:
    if isinstance(value, (int, float)):
        return abs(float(value))
    cleaned = re.sub(r"[^0-9.\-]", "", str(value or ""))
    if cleaned in ("", "-", "."):
        return 0.0
    return abs(float(cleaned))


def normalize_area(text: str) -> str:
    lower = (text or "").lower()
    for area, aliases in AREA_ALIASES.items():
        if any(alias in lower for alias in aliases):
            return area
    return (lower.strip() or "unknown")[:40]


def categorize_deduction(text: str) -> str:
    lower = text.lower()
    for category, terms in DEDUCTION_KEYWORDS.items():
        if any(term in lower for term in terms):
            return category
    return "uncategorized"


def parse_evidence_csv(csv_text: str) -> tuple[list[EvidenceItem], dict]:
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    if not reader.fieldnames:
        raise ValueError("Evidence CSV has no header row.")
    headers = reader.fieldnames
    id_col = find_column(headers, ("evidence_id", "id", "photo_id", "file"))
    date_col = find_column(headers, ("date", "taken_at", "timestamp", "created_at"))
    area_col = find_column(headers, ("area", "room", "location", "space"))
    desc_col = find_column(headers, ("description", "notes", "condition", "caption"))
    stage_col = find_column(headers, ("stage", "phase", "move_stage"))
    file_col = find_column(headers, ("file_path", "file", "path", "url"))
    missing = []
    if not date_col:
        missing.append("date/timestamp")
    if not area_col:
        missing.append("area/room/location")
    if not desc_col:
        missing.append("description/notes/condition")
    if missing:
        raise ValueError("Missing required evidence fields: " + ", ".join(missing))
    items: list[EvidenceItem] = []
    errors: list[str] = []
    for index, row in enumerate(reader, start=2):
        try:
            area = normalize_area(row.get(area_col, ""))
            items.append(
                EvidenceItem(
                    evidence_id=str(row.get(id_col, "") or f"E{index}").strip(),
                    date=parse_date(str(row.get(date_col, ""))).isoformat(),
                    area=area,
                    description=str(row.get(desc_col, "")).strip(),
                    stage=str(row.get(stage_col, "") or "move-out").strip().lower(),
                    file_path=str(row.get(file_col, "") if file_col else ""),
                    source="csv",
                    confidence=0.86 if file_col else 0.74,
                )
            )
        except Exception as exc:
            errors.append(f"row {index}: {exc}")
    return items, {"evidence_count": len(items), "row_errors": errors[:10]}


def parse_deduction_csv(csv_text: str) -> tuple[list[Deduction], dict]:
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    if not reader.fieldnames:
        raise ValueError("Deduction CSV has no header row.")
    headers = reader.fieldnames
    id_col = find_column(headers, ("deduction_id", "id", "line", "item"))
    area_col = find_column(headers, ("area", "room", "location", "space"))
    desc_col = find_column(headers, ("description", "deduction", "reason", "notes", "charge"))
    amount_col = find_column(headers, ("amount", "cost", "charge_amount", "deduction_amount"))
    proof_col = find_column(headers, ("landlord_evidence", "proof", "receipt", "invoice"))
    missing = []
    if not desc_col:
        missing.append("description/deduction/reason")
    if not amount_col:
        missing.append("amount/cost")
    if missing:
        raise ValueError("Missing required deduction fields: " + ", ".join(missing))
    items: list[Deduction] = []
    errors: list[str] = []
    for index, row in enumerate(reader, start=2):
        try:
            description = str(row.get(desc_col, "")).strip()
            area = normalize_area(row.get(area_col, "") or description)
            items.append(
                Deduction(
                    deduction_id=str(row.get(id_col, "") or f"D{index}").strip(),
                    area=area,
                    description=description,
                    amount=parse_amount(row.get(amount_col, "")),
                    landlord_evidence=str(row.get(proof_col, "") if proof_col else ""),
                    category=categorize_deduction(description),
                )
            )
        except Exception as exc:
            errors.append(f"row {index}: {exc}")
    return items, {"deduction_count": len(items), "row_errors": errors[:10]}


def parse_note_text(text: str) -> tuple[list[EvidenceItem], dict]:
    items: list[EvidenceItem] = []
    rejected: list[str] = []
    for index, block in enumerate([b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()], start=1):
        area_match = re.search(r"(?:area|room|location)\s*[:\-]\s*([^\n]+)", block, re.I)
        date_match = re.search(r"(?:date|taken)\s*[:\-]\s*([A-Za-z0-9,/\- ]{6,20})", block, re.I)
        desc_match = re.search(r"(?:description|condition|notes?)\s*[:\-]\s*([^\n]+)", block, re.I)
        if not area_match or not date_match or not desc_match:
            rejected.append(block[:120])
            continue
        try:
            items.append(
                EvidenceItem(
                    evidence_id=f"T{index}",
                    date=parse_date(date_match.group(1)).isoformat(),
                    area=normalize_area(area_match.group(1)),
                    description=desc_match.group(1).strip(),
                    stage="move-out",
                    source="text",
                    confidence=0.62,
                )
            )
        except Exception as exc:
            rejected.append(f"{block[:80]} ({exc})")
    return items, {"evidence_count": len(items), "rejected_blocks": rejected[:10]}


def load_rules(rule_json: str | None = None) -> dict[str, dict]:
    rules = dict(DEFAULT_RULES)
    if rule_json:
        custom = json.loads(rule_json)
        for key, value in custom.items():
            rules[key.upper()] = value
    return rules


def match_evidence(deduction: Deduction, evidence: list[EvidenceItem]) -> dict:
    same_area = [item for item in evidence if item.area == deduction.area]
    move_in = [item for item in same_area if "move-in" in item.stage]
    move_out = [item for item in same_area if "move-out" in item.stage]
    category_terms = DEDUCTION_KEYWORDS.get(deduction.category, ())
    text_matches = [
        item for item in same_area
        if any(term in item.description.lower() for term in category_terms)
    ]
    support_score = min(100, len(same_area) * 15 + len(move_in) * 20 + len(move_out) * 20 + len(text_matches) * 10)
    gaps = []
    if not move_in:
        gaps.append("missing_move_in_evidence")
    if not move_out:
        gaps.append("missing_move_out_evidence")
    if not deduction.landlord_evidence:
        gaps.append("landlord_receipt_or_photo_missing")
    return {
        "same_area_evidence": [asdict(item) for item in same_area],
        "move_in_count": len(move_in),
        "move_out_count": len(move_out),
        "text_match_count": len(text_matches),
        "support_score": support_score,
        "evidence_gaps": gaps,
    }


def analyze_case(case: CaseInfo, deductions: list[Deduction], evidence: list[EvidenceItem], rule_json: str | None = None) -> dict:
    rules = load_rules(rule_json)
    state_key = (case.state or "GENERIC").upper()
    rule = rules.get(state_key, rules["GENERIC"])
    move_out = parse_date(case.move_out_date)
    return_deadline = move_out + timedelta(days=int(rule.get("deposit_return_days", 30)))
    notice_date = parse_date(case.deduction_notice_date) if case.deduction_notice_date else None
    days_until_deadline = (return_deadline - date.today()).days
    notice_late = bool(notice_date and notice_date > return_deadline)

    findings = []
    for deduction in deductions:
        match = match_evidence(deduction, evidence)
        amount_risk = "high" if deduction.amount >= 500 else "medium" if deduction.amount >= 150 else "low"
        dispute_strength = min(100, match["support_score"] + (20 if notice_late else 0) + (15 if not deduction.landlord_evidence else 0))
        if "missing_move_out_evidence" in match["evidence_gaps"]:
            dispute_strength -= 15
        if "missing_move_in_evidence" in match["evidence_gaps"]:
            dispute_strength -= 10
        findings.append(
            {
                **asdict(deduction),
                "amount_risk": amount_risk,
                "dispute_strength": max(0, dispute_strength),
                "matched_evidence": match,
                "recommended_action": recommended_action(dispute_strength, match["evidence_gaps"], notice_late),
                "evidence_checklist": evidence_checklist(deduction, match["evidence_gaps"]),
            }
        )

    findings = sorted(findings, key=lambda row: (row["dispute_strength"], row["amount"]), reverse=True)
    summary = {
        "state": state_key,
        "deposit_amount": case.deposit_amount,
        "total_deductions": round(sum(item.amount for item in deductions), 2),
        "deduction_count": len(deductions),
        "evidence_count": len(evidence),
        "deposit_return_deadline": return_deadline.isoformat(),
        "days_until_deadline_from_today": days_until_deadline,
        "notice_late": notice_late,
        "forwarding_address_sent": case.forwarding_address_sent,
        "high_strength_findings": sum(1 for row in findings if row["dispute_strength"] >= 60),
    }
    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "case": asdict(case),
        "summary": summary,
        "rule_used": rule,
        "findings": findings,
        "draft_dispute_outline": draft_outline(case, summary, findings),
        "method_notes": [
            "This is an evidence organization tool, not legal advice.",
            "State rules are configurable local reference data and must be verified.",
            "Dispute strength is a workflow triage score, not a prediction of legal outcome.",
        ],
    }


def recommended_action(score: int, gaps: list[str], notice_late: bool) -> str:
    if notice_late and score >= 50:
        return "raise_deadline_and_evidence_issue_first"
    if score >= 70:
        return "include_in_primary_dispute_packet"
    if gaps:
        return "fill_evidence_gap_before_dispute"
    if score >= 40:
        return "ask_for_itemized_proof_or_receipt"
    return "monitor_or_deprioritize"


def evidence_checklist(deduction: Deduction, gaps: list[str]) -> list[str]:
    checklist = ["lease or move-in checklist", "move-out photos or video", "landlord itemized statement", "payment/deposit proof"]
    if "missing_move_in_evidence" in gaps:
        checklist.append("find move-in photos or signed condition checklist")
    if "missing_move_out_evidence" in gaps:
        checklist.append("find move-out photos/video for this area")
    if "landlord_receipt_or_photo_missing" in gaps:
        checklist.append("request invoice, receipt, photo, or specific description from landlord")
    if deduction.amount >= 125:
        checklist.append("verify whether local rules require receipts or good-faith estimates for this amount")
    return checklist


def draft_outline(case: CaseInfo, summary: dict, findings: list[dict]) -> str:
    lines = [
        "Subject: Security deposit deduction documentation request",
        "",
        f"I am writing about the security deposit for my tenancy ending {case.move_out_date}.",
        f"My records show a deposit amount of ${case.deposit_amount:.2f} and deductions totaling ${summary['total_deductions']:.2f}.",
        f"Please review the attached evidence index and the deposit return deadline estimate of {summary['deposit_return_deadline']}.",
        "",
        "Disputed / needs-documentation items:",
    ]
    for row in findings[:8]:
        lines.append(f"- {row['description']} (${row['amount']:.2f}): {row['recommended_action']}; evidence score {row['dispute_strength']}.")
    lines.extend(["", "This letter is a documentation request and dispute packet outline, not legal advice."])
    return "\n".join(lines)


def markdown_report(report: dict) -> str:
    lines = ["# Deposit Defender Desk Report", "", f"Generated: {report['generated_at']}", "", "## Summary", ""]
    for key, value in report["summary"].items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    lines.extend(["", "## Findings", ""])
    for row in report["findings"]:
        lines.append(f"- **{row['description']}** (${row['amount']:.2f}): {row['recommended_action']} (score {row['dispute_strength']})")
        lines.append(f"  - Gaps: {', '.join(row['matched_evidence']['evidence_gaps']) or 'none'}")
        lines.append(f"  - Checklist: {', '.join(row['evidence_checklist'])}")
    lines.extend(["", "## Draft Outline", "", "```text", report["draft_dispute_outline"], "```", "", "## Method Notes", ""])
    for note in report["method_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def save_outputs(report: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "deposit-defender-report.json"
    md_path = output_dir / "deposit-defender-report.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def load_sample(root: Path) -> tuple[list[EvidenceItem], list[Deduction]]:
    evidence, _ = parse_evidence_csv((root / "sample_evidence.csv").read_text(encoding="utf-8"))
    deductions, _ = parse_deduction_csv((root / "sample_deductions.csv").read_text(encoding="utf-8"))
    return evidence, deductions

