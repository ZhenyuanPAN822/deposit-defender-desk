# Deposit Defender Desk

English | [中文](README.zh-CN.md)

## Hero Section

Deposit Defender Desk is a local-first evidence desk for renters preparing a security deposit dispute packet.

- Match landlord deductions against move-in and move-out evidence.
- Calculate deposit return deadline estimates from editable state rules.
- Generate evidence gaps, action priorities, and a draft documentation request outline.

Screenshot/GIF to be added before launch.

Quick demo:

```bash
python server.py
```

Open `http://127.0.0.1:8790`, click **Load sample**, then **Run analysis**.

## Problem

Security deposit disputes usually come down to documentation. Renters may have photos, videos, cleaning receipts, walkthrough forms, texts, and a landlord deduction list, but the evidence is scattered across camera rolls, email, PDFs, and memory. When the deadline is close, the hard part is matching each deduction to the right proof and seeing which evidence gaps still need work.

## Why Existing Approaches Are Not Enough

Generic folders store photos but do not connect them to deduction line items. Spreadsheets require the renter to manually calculate deadlines and evidence strength. Legal articles explain the rules, but they do not assemble a local evidence packet. AI chat alone can overclaim or miss the user's actual proof.

Deposit Defender Desk focuses on the operational layer: organize evidence, map deductions to proof, identify gaps, and create a concise packet outline.

## What This Project Does

`evidence CSV / evidence notes / deduction CSV -> evidence matching -> deadline and gap analysis -> dispute packet outline -> Markdown/JSON report`

## Key Features

- Flexible evidence CSV import for dated move-in and move-out photos, videos, walkthrough forms, and receipts.
- Landlord deduction CSV import with amount, area, description, and provided proof.
- Pasted evidence note parser for quick manual documentation.
- Editable state rule JSON for deposit return deadlines and receipt thresholds.
- Evidence matching by room/area and deduction category.
- Evidence gap detection for missing move-in proof, move-out proof, landlord receipts, and high-dollar charges.
- Draft documentation request / dispute outline.
- Markdown and JSON export.

## Why this is useful

This turns a messy security-deposit folder into a structured dispute packet: which deductions have matching evidence, which ones are missing proof, whether the notice appears late under configured rules, and what documents to gather before responding.

## Demo / Screenshots

Screenshot/GIF to be added before launch.

The bundled sample includes move-in evidence, move-out evidence, a signed walkthrough, cleaning receipt, disputed countertop/wall/cleaning/common-area charges, missing landlord proof, and a late notice scenario.

## Quick Start

```bash
cd products/product-022/repo
python server.py
```

Then open:

```text
http://127.0.0.1:8790
```

No account, API key, landlord portal, email connection, or internet access is required.

## Example Input / Output

Evidence CSV:

```csv
evidence_id,date,area,description,stage,file_path
E001,2025-04-01,kitchen,"Move-in photo shows existing chip near sink edge",move-in,photos/kitchen.jpg
E002,2026-03-31,kitchen,"Move-out photo shows sink edge unchanged",move-out,photos/kitchen_out.jpg
```

Deduction CSV:

```csv
deduction_id,area,description,amount,landlord_evidence
D001,kitchen,"Countertop chip repair near sink",450,""
```

Output files:

```text
outputs/deposit-defender-report.md
outputs/deposit-defender-report.json
```

## Use Cases

- Prepare a response to itemized deposit deductions.
- Check whether each deduction has matching move-in/move-out evidence.
- Identify missing receipts, photos, or walkthrough forms.
- Build a concise documentation request before escalating.
- Keep a local record without uploading rental evidence to a cloud service.

## How It Works

The analyzer normalizes evidence and deductions by room/area, categorizes deduction text, compares each deduction with matching move-in and move-out evidence, flags missing evidence, applies a configurable state deadline rule, and creates a triage score. The score is a workflow priority, not a legal prediction.

## Project Structure

```text
deposit_defender_desk/analyzer.py  Evidence parser, deduction matcher, deadline analysis, exports
server.py                          Local HTTP server
web/                               Browser UI
samples/                           Evidence and deduction fixtures
examples/                          Pasted evidence notes
tests/                             Unit tests
scripts/smoke_test.py              User-perspective smoke test
```

## Roadmap

- Photo metadata import helper.
- PDF itemized deduction parser.
- State rule packs maintained as separate editable JSON files.
- Exhibit numbering and printable packet export.
- Calendar reminder export for deposit deadlines.

## Limitations

Deposit Defender Desk is not legal advice and does not predict court outcomes. State and local rules change and must be verified. The app does not upload photos, read image contents, contact landlords, file claims, or connect to email/cloud storage. Evidence matching is based on text, areas, dates, and local rule configuration.

## License

MIT

## Language

中文版本: [README.zh-CN.md](README.zh-CN.md)

