from pathlib import Path
from typing import Any, Dict


AUTH_MARKERS = ["requireAuth", "getServerSession", "assertAdmin", "withAuth", "auth()"]


def route_path_from_file(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")
    marker = "/app/"
    if marker in normalized:
        normalized = normalized.split(marker, 1)[1]
    if normalized.startswith("app/"):
        normalized = normalized[len("app/") :]
    if normalized.endswith("/route.ts"):
        normalized = normalized[: -len("/route.ts")]
    return "/" + normalized.replace("/route", "").replace("/page", "")


def parse_route(file_path: str, content: str) -> Dict[str, Any]:
    route_path = route_path_from_file(file_path)
    methods: list[str] = []
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
        token = f"export async function {method}"
        if token in content or f"export function {method}" in content:
            methods.append(method)

    is_protected = any(marker in content for marker in AUTH_MARKERS)
    is_admin_route = "/admin" in route_path or "admin" in Path(file_path).parts

    return {
        "route_path": route_path,
        "methods": methods,
        "is_protected": is_protected,
        "is_admin_route": is_admin_route,
    }


def parse_middleware(content: str) -> Dict[str, Any]:
    protected_prefixes: list[str] = []
    for line in content.splitlines():
        if 'pathname.startsWith("' in line:
            prefix = line.split('pathname.startsWith("', 1)[1].split('"', 1)[0]
            protected_prefixes.append(prefix)
        if "matcher:" in line:
            protected_prefixes.append("matcher-config-present")
    return {"protected_prefixes": protected_prefixes}

