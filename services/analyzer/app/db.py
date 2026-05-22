import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional in local SQLite mode
    psycopg = None
    dict_row = None


def _default_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "infra").exists():
            return candidate
    return current.parents[1]


ROOT = Path(os.environ.get("DIFFSHIELD_ROOT", _default_root()))
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_PATH = Path(os.environ.get("DIFFSHIELD_DB_PATH", ROOT / "infra" / "diffshield_demo.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    summary_json TEXT NOT NULL,
    FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_run_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties_json TEXT NOT NULL,
    FOREIGN KEY(scan_run_id) REFERENCES scan_runs(id)
);

CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_run_id INTEGER NOT NULL,
    from_asset_id INTEGER NOT NULL,
    relation TEXT NOT NULL,
    to_asset_id INTEGER NOT NULL,
    properties_json TEXT NOT NULL,
    FOREIGN KEY(scan_run_id) REFERENCES scan_runs(id)
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_run_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    attack_path TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    remediation TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY(scan_run_id) REFERENCES scan_runs(id)
);

CREATE TABLE IF NOT EXISTS trace_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_run_id INTEGER NOT NULL,
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(scan_run_id) REFERENCES scan_runs(id)
);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_runs (
    id BIGSERIAL PRIMARY KEY,
    repo_id BIGINT NOT NULL REFERENCES repos(id),
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    summary_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id BIGSERIAL PRIMARY KEY,
    scan_run_id BIGINT NOT NULL REFERENCES scan_runs(id),
    asset_type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    id BIGSERIAL PRIMARY KEY,
    scan_run_id BIGINT NOT NULL REFERENCES scan_runs(id),
    from_asset_id BIGINT NOT NULL,
    relation TEXT NOT NULL,
    to_asset_id BIGINT NOT NULL,
    properties_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS findings (
    id BIGSERIAL PRIMARY KEY,
    scan_run_id BIGINT NOT NULL REFERENCES scan_runs(id),
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    attack_path TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    remediation TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trace_events (
    id BIGSERIAL PRIMARY KEY,
    scan_run_id BIGINT NOT NULL REFERENCES scan_runs(id),
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _using_postgres() -> bool:
    return bool(DATABASE_URL)


def _adapt_query(query: str) -> str:
    return query.replace("?", "%s") if _using_postgres() else query


def _connect():
    if _using_postgres():
        if psycopg is None:
            raise RuntimeError("psycopg is required when DATABASE_URL is set")
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _run_schema(connection, schema: str) -> None:
    statements = [statement.strip() for statement in schema.split(";") if statement.strip()]
    for statement in statements:
        connection.execute(statement)


def _fetch_inserted_id(cursor) -> int:
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Expected inserted row id")
    return int(row["id"])


def init_db() -> None:
    connection = _connect()
    try:
        if _using_postgres():
            _run_schema(connection, POSTGRES_SCHEMA)
        else:
            connection.executescript(SQLITE_SCHEMA)
        connection.commit()
    finally:
        connection.close()


def insert_repo(name: str, source_type: str, source_ref: str, created_at: str) -> int:
    connection = _connect()
    try:
        if _using_postgres():
            cursor = connection.execute(
                """
                INSERT INTO repos (name, source_type, source_ref, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (name, source_type, source_ref, created_at),
            )
            connection.commit()
            return _fetch_inserted_id(cursor)

        cursor = connection.execute(
            "INSERT INTO repos (name, source_type, source_ref, created_at) VALUES (?, ?, ?, ?)",
            (name, source_type, source_ref, created_at),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def insert_scan(repo_id: int, status: str, started_at: str, summary_json: Dict[str, Any]) -> int:
    connection = _connect()
    try:
        encoded_summary = json.dumps(summary_json)
        if _using_postgres():
            cursor = connection.execute(
                """
                INSERT INTO scan_runs (repo_id, status, started_at, summary_json)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (repo_id, status, started_at, encoded_summary),
            )
            connection.commit()
            return _fetch_inserted_id(cursor)

        cursor = connection.execute(
            "INSERT INTO scan_runs (repo_id, status, started_at, summary_json) VALUES (?, ?, ?, ?)",
            (repo_id, status, started_at, encoded_summary),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def update_scan(scan_id: int, status: str, completed_at: Optional[str], summary_json: Dict[str, Any]) -> None:
    connection = _connect()
    try:
        connection.execute(
            _adapt_query(
                """
                UPDATE scan_runs
                SET status = ?, completed_at = ?, summary_json = ?
                WHERE id = ?
                """
            ),
            (status, completed_at, json.dumps(summary_json), scan_id),
        )
        connection.commit()
    finally:
        connection.close()


def insert_trace(scan_id: int, stage: str, message: str, payload: Dict[str, Any], created_at: str) -> int:
    connection = _connect()
    try:
        payload_json = json.dumps(payload)
        if _using_postgres():
            cursor = connection.execute(
                """
                INSERT INTO trace_events (scan_run_id, stage, message, payload_json, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (scan_id, stage, message, payload_json, created_at),
            )
            connection.commit()
            return _fetch_inserted_id(cursor)

        cursor = connection.execute(
            """
            INSERT INTO trace_events (scan_run_id, stage, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_id, stage, message, payload_json, created_at),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def insert_asset(scan_id: int, asset_type: str, name: str, properties: Dict[str, Any]) -> int:
    connection = _connect()
    try:
        properties_json = json.dumps(properties)
        if _using_postgres():
            cursor = connection.execute(
                """
                INSERT INTO assets (scan_run_id, asset_type, name, properties_json)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (scan_id, asset_type, name, properties_json),
            )
            connection.commit()
            return _fetch_inserted_id(cursor)

        cursor = connection.execute(
            """
            INSERT INTO assets (scan_run_id, asset_type, name, properties_json)
            VALUES (?, ?, ?, ?)
            """,
            (scan_id, asset_type, name, properties_json),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def insert_edge(
    scan_id: int,
    from_asset_id: int,
    relation: str,
    to_asset_id: int,
    properties: Dict[str, Any],
) -> int:
    connection = _connect()
    try:
        properties_json = json.dumps(properties)
        if _using_postgres():
            cursor = connection.execute(
                """
                INSERT INTO edges (scan_run_id, from_asset_id, relation, to_asset_id, properties_json)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (scan_id, from_asset_id, relation, to_asset_id, properties_json),
            )
            connection.commit()
            return _fetch_inserted_id(cursor)

        cursor = connection.execute(
            """
            INSERT INTO edges (scan_run_id, from_asset_id, relation, to_asset_id, properties_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_id, from_asset_id, relation, to_asset_id, properties_json),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def insert_finding(
    scan_id: int,
    title: str,
    severity: str,
    confidence: float,
    attack_path: str,
    evidence: Iterable[str],
    remediation: Iterable[str],
    status: str,
) -> int:
    connection = _connect()
    try:
        evidence_json = json.dumps(list(evidence))
        remediation_json = json.dumps(list(remediation))
        if _using_postgres():
            cursor = connection.execute(
                """
                INSERT INTO findings
                (scan_run_id, title, severity, confidence, attack_path, evidence_json, remediation, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (scan_id, title, severity, confidence, attack_path, evidence_json, remediation_json, status),
            )
            connection.commit()
            return _fetch_inserted_id(cursor)

        cursor = connection.execute(
            """
            INSERT INTO findings
            (scan_run_id, title, severity, confidence, attack_path, evidence_json, remediation, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (scan_id, title, severity, confidence, attack_path, evidence_json, remediation_json, status),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def fetch_one(query: str, params: tuple[Any, ...]) -> Optional[Mapping[str, Any]]:
    connection = _connect()
    try:
        row = connection.execute(_adapt_query(query), params).fetchone()
        return row
    finally:
        connection.close()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[Mapping[str, Any]]:
    connection = _connect()
    try:
        rows = connection.execute(_adapt_query(query), params).fetchall()
        return rows
    finally:
        connection.close()
