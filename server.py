from __future__ import annotations

import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from deposit_defender_desk.analyzer import (
    CaseInfo,
    Deduction,
    EvidenceItem,
    analyze_case,
    load_sample,
    parse_deduction_csv,
    parse_evidence_csv,
    parse_note_text,
    save_outputs,
)


ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
SAMPLES = ROOT / "samples"
OUTPUTS = ROOT / "outputs"
PORT = 8790


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self.serve_file(WEB / "index.html", "text/html")
        if parsed.path == "/app.js":
            return self.serve_file(WEB / "app.js", "application/javascript")
        if parsed.path == "/styles.css":
            return self.serve_file(WEB / "styles.css", "text/css")
        if parsed.path == "/api/sample":
            evidence, deductions = load_sample(SAMPLES)
            return self.json_response({"evidence": [asdict(x) for x in evidence], "deductions": [asdict(x) for x in deductions]})
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body or "{}")
            if parsed.path == "/api/parse-evidence":
                evidence, metadata = parse_evidence_csv(payload.get("csv", ""))
                return self.json_response({"evidence": [asdict(x) for x in evidence], "metadata": metadata})
            if parsed.path == "/api/parse-deductions":
                deductions, metadata = parse_deduction_csv(payload.get("csv", ""))
                return self.json_response({"deductions": [asdict(x) for x in deductions], "metadata": metadata})
            if parsed.path == "/api/parse-notes":
                evidence, metadata = parse_note_text(payload.get("text", ""))
                return self.json_response({"evidence": [asdict(x) for x in evidence], "metadata": metadata})
            if parsed.path == "/api/analyze":
                evidence = [EvidenceItem(**item) for item in payload.get("evidence", [])]
                deductions = [Deduction(**item) for item in payload.get("deductions", [])]
                case = CaseInfo(**payload.get("case", {}))
                report = analyze_case(case, deductions, evidence, rule_json=payload.get("rule_json"))
                report["saved_outputs"] = save_outputs(report, OUTPUTS)
                return self.json_response(report)
        except Exception as exc:
            return self.json_response({"error": str(exc)}, status=400)
        self.send_error(404)

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def json_response(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Deposit Defender Desk running at http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

