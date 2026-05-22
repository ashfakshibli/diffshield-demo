from datetime import datetime, timezone
from typing import Any, Dict

from app.db import insert_trace


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def trace(scan_id: int, stage: str, message: str, payload: Dict[str, Any]) -> None:
    insert_trace(scan_id, stage, message, payload, now_iso())

