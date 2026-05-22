import re
from typing import Any, Dict


SERVICE_PATTERN = re.compile(r"^\s{2}([A-Za-z0-9_-]+):\s*$")
PORT_PATTERN = re.compile(r'^\s*-\s*"?(?P<host>\d+):(?P<container>\d+)"?\s*$')
ENV_PATTERN = re.compile(r"^\s*([A-Z0-9_]+)\s*:\s*(.+)\s*$")


def parse_compose(content: str) -> Dict[str, Any]:
    services: list[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    in_ports = False
    in_environment = False

    for raw_line in content.splitlines():
        service_match = SERVICE_PATTERN.match(raw_line)
        if service_match:
            current = {
                "name": service_match.group(1),
                "ports": [],
                "environment": {},
            }
            services.append(current)
            in_ports = False
            in_environment = False
            continue

        if current is None:
            continue

        stripped = raw_line.strip()
        if stripped == "ports:":
            in_ports = True
            in_environment = False
            continue
        if stripped == "environment:":
            in_environment = True
            in_ports = False
            continue
        if stripped.endswith(":") and stripped not in {"ports:", "environment:"}:
            in_ports = False
            in_environment = False

        if in_ports:
            port_match = PORT_PATTERN.match(stripped)
            if port_match:
                current["ports"].append(
                    {
                        "host": port_match.group("host"),
                        "container": port_match.group("container"),
                    }
                )

        if in_environment:
            env_match = ENV_PATTERN.match(stripped)
            if env_match:
                current["environment"][env_match.group(1)] = env_match.group(2).strip().strip('"')

    return {"services": services}

