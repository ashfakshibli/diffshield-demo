import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app import db
from app.pipeline.run_scan import execute_scan


ROOT = Path(__file__).resolve().parents[3]
DEMO_TARGET_REPO = os.environ.get(
    "DEMO_TARGET_REPO",
    "https://github.com/ashfakshibli/diffshield-vuln-demo",
)
HOST = os.environ.get("ANALYZER_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT") or os.environ.get("ANALYZER_PORT", "8001"))


def json_response(handler: BaseHTTPRequestHandler, status: int, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


class AnalyzerHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return json_response(self, 200, {"ok": True, "demo_target_repo": DEMO_TARGET_REPO})

        if path.startswith("/scan/"):
            parts = [part for part in path.strip("/").split("/") if part]
            if len(parts) < 2:
                return json_response(self, 404, {"error": "Not found"})

            scan_id = parts[1]
            if not scan_id.isdigit():
                return json_response(self, 400, {"error": "Invalid scan id"})

            if len(parts) == 2:
                row = db.fetch_one(
                    """
                    SELECT
                        scan_runs.id,
                        repos.name AS repo_name,
                        repos.source_ref AS repo_path,
                        scan_runs.status,
                        scan_runs.started_at,
                        scan_runs.completed_at,
                        scan_runs.summary_json,
                        (SELECT COUNT(*) FROM assets WHERE assets.scan_run_id = scan_runs.id) AS asset_count,
                        (SELECT COUNT(*) FROM edges WHERE edges.scan_run_id = scan_runs.id) AS edge_count,
                        (SELECT COUNT(*) FROM findings WHERE findings.scan_run_id = scan_runs.id) AS finding_count,
                        (SELECT COUNT(*) FROM trace_events WHERE trace_events.scan_run_id = scan_runs.id) AS trace_count
                    FROM scan_runs
                    JOIN repos ON repos.id = scan_runs.repo_id
                    WHERE scan_runs.id = ?
                    """,
                    (int(scan_id),),
                )
                if row is None:
                    return json_response(self, 404, {"error": "Scan not found"})
                return json_response(
                    self,
                    200,
                    {
                        "id": row["id"],
                        "repo_name": row["repo_name"],
                        "repo_path": row["repo_path"],
                        "status": row["status"],
                        "started_at": row["started_at"],
                        "completed_at": row["completed_at"],
                        "counts": {
                            "assets": row["asset_count"],
                            "edges": row["edge_count"],
                            "findings": row["finding_count"],
                            "traces": row["trace_count"],
                        },
                        "summary_json": json.loads(row["summary_json"]),
                    },
                )

            suffix = parts[2]
            if suffix == "findings":
                rows = db.fetch_all(
                    """
                    SELECT id, title, severity, confidence, attack_path, evidence_json, remediation, status
                    FROM findings
                    WHERE scan_run_id = ?
                    ORDER BY
                      CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                      END,
                      confidence DESC
                    """,
                    (int(scan_id),),
                )
                return json_response(
                    self,
                    200,
                    [
                        {
                            "id": row["id"],
                            "title": row["title"],
                            "severity": row["severity"],
                            "confidence": row["confidence"],
                            "attack_path": row["attack_path"],
                            "evidence_json": json.loads(row["evidence_json"]),
                            "remediation": json.loads(row["remediation"]),
                            "status": row["status"],
                        }
                        for row in rows
                    ],
                )

            if suffix == "world-model":
                assets = db.fetch_all(
                    "SELECT id, asset_type, name, properties_json FROM assets WHERE scan_run_id = ? ORDER BY id",
                    (int(scan_id),),
                )
                edges = db.fetch_all(
                    "SELECT id, from_asset_id, relation, to_asset_id, properties_json FROM edges WHERE scan_run_id = ? ORDER BY id",
                    (int(scan_id),),
                )
                return json_response(
                    self,
                    200,
                    {
                        "assets": [
                            {
                                "id": row["id"],
                                "asset_type": row["asset_type"],
                                "name": row["name"],
                                "properties_json": json.loads(row["properties_json"]),
                            }
                            for row in assets
                        ],
                        "edges": [
                            {
                                "id": row["id"],
                                "from_asset_id": row["from_asset_id"],
                                "relation": row["relation"],
                                "to_asset_id": row["to_asset_id"],
                                "properties_json": json.loads(row["properties_json"]),
                            }
                            for row in edges
                        ],
                    },
                )

            if suffix == "traces":
                rows = db.fetch_all(
                    "SELECT id, stage, message, payload_json, created_at FROM trace_events WHERE scan_run_id = ? ORDER BY id",
                    (int(scan_id),),
                )
                return json_response(
                    self,
                    200,
                    [
                        {
                            "id": row["id"],
                            "stage": row["stage"],
                            "message": row["message"],
                            "payload_json": json.loads(row["payload_json"]),
                            "created_at": row["created_at"],
                        }
                        for row in rows
                    ],
                )

        json_response(self, 404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/scan":
            return json_response(self, 404, {"error": "Not found"})

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        payload = json.loads(raw.decode("utf-8") or "{}")
        repo_path = DEMO_TARGET_REPO if payload.get("useSample") else payload.get("repoPath")
        notes = payload.get("notes", "")

        if not repo_path:
            return json_response(
                self,
                400,
                {"error": "repoPath is required when useSample is false; it may be a local path or a public GitHub repo URL"},
            )

        try:
            result = execute_scan(repo_path, notes)
            return json_response(self, 200, result)
        except Exception as error:
            return json_response(self, 500, {"error": str(error)})


def main():
    db.init_db()
    server = ThreadingHTTPServer((HOST, PORT), AnalyzerHandler)
    print(f"DiffShield analyzer running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
