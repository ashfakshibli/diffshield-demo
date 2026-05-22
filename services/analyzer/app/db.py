import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = Path(os.environ.get("DIFFSHIELD_DB_PATH", ROOT / "infra" / "diffshield_demo.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = _connect()
    try:
        connection.executescript(
            """
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
        )
        connection.commit()
    finally:
        connection.close()


def insert_repo(name: str, source_type: str, source_ref: str, created_at: str) -> int:
    connection = _connect()
    try:
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
        cursor = connection.execute(
            "INSERT INTO scan_runs (repo_id, status, started_at, summary_json) VALUES (?, ?, ?, ?)",
            (repo_id, status, started_at, json.dumps(summary_json)),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def update_scan(scan_id: int, status: str, completed_at: Optional[str], summary_json: Dict[str, Any]) -> None:
    connection = _connect()
    try:
        connection.execute(
            """
            UPDATE scan_runs
            SET status = ?, completed_at = ?, summary_json = ?
            WHERE id = ?
            """,
            (status, completed_at, json.dumps(summary_json), scan_id),
        )
        connection.commit()
    finally:
        connection.close()


def insert_trace(scan_id: int, stage: str, message: str, payload: Dict[str, Any], created_at: str) -> int:
    connection = _connect()
    try:
        cursor = connection.execute(
            """
            INSERT INTO trace_events (scan_run_id, stage, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_id, stage, message, json.dumps(payload), created_at),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def insert_asset(scan_id: int, asset_type: str, name: str, properties: Dict[str, Any]) -> int:
    connection = _connect()
    try:
        cursor = connection.execute(
            """
            INSERT INTO assets (scan_run_id, asset_type, name, properties_json)
            VALUES (?, ?, ?, ?)
            """,
            (scan_id, asset_type, name, json.dumps(properties)),
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
        cursor = connection.execute(
            """
            INSERT INTO edges (scan_run_id, from_asset_id, relation, to_asset_id, properties_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_id, from_asset_id, relation, to_asset_id, json.dumps(properties)),
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
        cursor = connection.execute(
            """
            INSERT INTO findings
            (scan_run_id, title, severity, confidence, attack_path, evidence_json, remediation, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_id,
                title,
                severity,
                confidence,
                attack_path,
                json.dumps(list(evidence)),
                json.dumps(list(remediation)),
                status,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def fetch_one(query: str, params: tuple[Any, ...]) -> Optional[sqlite3.Row]:
    connection = _connect()
    try:
        row = connection.execute(query, params).fetchone()
        return row
    finally:
        connection.close()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    connection = _connect()
    try:
        rows = connection.execute(query, params).fetchall()
        return rows
    finally:
        connection.close()
