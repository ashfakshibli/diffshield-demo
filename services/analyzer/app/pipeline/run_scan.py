from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app import db
from app.parsers.compose_parser import parse_compose
from app.parsers.dockerfile_parser import parse_dockerfile
from app.parsers.env_parser import parse_env
from app.parsers.route_parser import parse_middleware, parse_route
from app.pipeline.ingest import ingest_repo
from app.pipeline.rules import build_candidates
from app.pipeline.trace import trace
from app.pipeline.validate import validate_candidates
from app.pipeline.world_model import build_world_model


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_scan(repo_path: str, notes: str) -> Dict[str, Any]:
    repo_name = Path(repo_path).name
    started_at = now_iso()
    repo_id = db.insert_repo(repo_name, "local_path", repo_path, started_at)
    scan_id = db.insert_scan(repo_id, "running", started_at, {"candidate_paths": 0, "validated_with": "pending", "scanned_files": []})

    trace(scan_id, "ingest", "Starting repo ingest", {"repo_path": repo_path})
    files = ingest_repo(repo_path)
    trace(scan_id, "ingest", "Collected target files", {"files": list(files.keys())})

    parsed: Dict[str, Any] = {"routes": []}
    if "Dockerfile" in files:
        parsed["dockerfile"] = parse_dockerfile(files["Dockerfile"])
        trace(scan_id, "parse", "Parsed Dockerfile", parsed["dockerfile"])
    if "docker-compose.yml" in files:
        parsed["compose"] = parse_compose(files["docker-compose.yml"])
        trace(scan_id, "parse", "Parsed docker-compose", parsed["compose"])
    if ".env.example" in files:
        parsed["env"] = parse_env(files[".env.example"])
        trace(scan_id, "parse", "Parsed env file", {"variables": len(parsed["env"]["variables"])})
    if "middleware.ts" in files:
        parsed["middleware"] = parse_middleware(files["middleware.ts"])
        trace(scan_id, "parse", "Parsed middleware", parsed["middleware"])

    for file_path, content in files.items():
        if file_path.startswith("app/api/") and file_path.endswith("route.ts"):
            route = parse_route(file_path, content)
            parsed["routes"].append(route)
    trace(scan_id, "parse", "Parsed route files", {"routes": parsed["routes"]})

    assets, edges = build_world_model(parsed)
    trace(scan_id, "model", "Built world model", {"assets": len(assets), "edges": len(edges)})

    inserted_assets: list[int] = []
    for asset in assets:
        inserted_assets.append(db.insert_asset(scan_id, asset["asset_type"], asset["name"], asset["properties"]))

    for edge in edges:
        db.insert_edge(
            scan_id,
            inserted_assets[edge["from_index"]],
            edge["relation"],
            inserted_assets[edge["to_index"]],
            edge["properties"],
        )

    candidates = build_candidates(parsed)
    trace(scan_id, "rules", "Generated candidate findings", {"count": len(candidates), "rule_ids": [candidate["rule_id"] for candidate in candidates]})

    validated = validate_candidates(candidates, notes)
    trace(scan_id, "validate", "Validated findings", {"count": len(validated["findings"]), "validated_with": validated["validated_with"]})

    for finding in validated["findings"]:
        db.insert_finding(
            scan_id,
            finding["title"],
            finding["severity"],
            float(finding["confidence"]),
            finding["attack_path"],
            finding["evidence"],
            finding["remediation"],
            "open",
        )

    completed_at = now_iso()
    summary = {
        "candidate_paths": len(candidates),
        "validated_with": validated["validated_with"],
        "scanned_files": list(files.keys()),
    }
    db.update_scan(scan_id, "completed", completed_at, summary)
    trace(scan_id, "persist", "Persisted scan results", summary)

    return {"scan_id": scan_id, "repo_path": repo_path}

