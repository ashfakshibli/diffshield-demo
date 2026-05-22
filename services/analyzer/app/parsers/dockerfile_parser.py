from typing import Any, Dict


def parse_dockerfile(content: str) -> Dict[str, Any]:
    user = None
    exposes: list[str] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        upper = line.upper()
        if upper.startswith("USER "):
            user = line.split(None, 1)[1].strip()
        if upper.startswith("EXPOSE "):
            exposes.extend(part.strip() for part in line.split(None, 1)[1].split())

    return {
        "user": user,
        "runs_as_root": user in (None, "", "root", "0"),
        "exposed_ports": exposes,
    }

