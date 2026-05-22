from typing import Any, Dict, List


def build_candidates(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    docker = parsed.get("dockerfile") or {}
    if docker.get("runs_as_root"):
        findings.append(
            {
                "rule_id": "container-runs-as-root",
                "title": "Application container runs as root",
                "severity": "high",
                "attack_path": "Compromised application code executes inside a root container, increasing post-exploitation impact and lateral movement options.",
                "evidence": [
                    "Dockerfile is missing a non-root USER instruction or explicitly uses root.",
                    f"Observed Dockerfile user value: {docker.get('user')!r}",
                ],
                "remediation": [
                    "Create a dedicated non-root runtime user.",
                    "Set USER before the final CMD/ENTRYPOINT stage.",
                ],
                "confidence": 0.89,
            }
        )

    for service in parsed.get("compose", {}).get("services", []):
        for port in service.get("ports", []):
            host_port = str(port.get("host"))
            if host_port in {"5050", "8080", "3001"}:
                findings.append(
                    {
                        "rule_id": "public-internal-port",
                        "title": f"Internal service port is published on the host ({host_port})",
                        "severity": "high" if service["name"] == "admin" else "medium",
                        "attack_path": f"An external actor reaches the {service['name']} service over a host-published port, bypassing the assumption that the service is internal-only.",
                        "evidence": [
                            f"docker-compose exposes host port {host_port} to container port {port.get('container')}.",
                            f"Service name: {service['name']}",
                        ],
                        "remediation": [
                            "Remove host publication for internal-only services.",
                            "If exposure is required, place the service behind authenticated ingress.",
                        ],
                        "confidence": 0.86,
                    }
                )

    for variable in parsed.get("env", {}).get("variables", []):
        if variable["is_secret_like"]:
            findings.append(
                {
                    "rule_id": "secret-pattern-in-env",
                    "title": f"Secret-like configuration appears in env file ({variable['key']})",
                    "severity": "medium",
                    "attack_path": "Committed environment examples can normalize unsafe handling of sensitive values, leak real patterns, or encourage insecure secret distribution across environments.",
                    "evidence": [
                        f"Variable {variable['key']} appears in .env.example.",
                        "Key name matches a secret-like token pattern.",
                    ],
                    "remediation": [
                        "Replace literal example secrets with neutral placeholders and document secret manager usage.",
                        "Keep secret naming but remove realistic values and rotate any reused credentials.",
                    ],
                    "confidence": 0.72,
                }
            )
        if variable["is_debug_flag"]:
            findings.append(
                {
                    "rule_id": "debug-mode-enabled",
                    "title": "Debug mode is enabled in shared configuration",
                    "severity": "low",
                    "attack_path": "Debug-enabled builds often expose verbose errors, diagnostic endpoints, or behavior that expands the attack surface in shared environments.",
                    "evidence": [
                        "DEBUG=true is present in .env.example.",
                    ],
                    "remediation": [
                        "Default DEBUG to false in shared examples.",
                        "Gate debugging features behind environment-specific controls.",
                    ],
                    "confidence": 0.66,
                }
            )

    protected_prefixes = parsed.get("middleware", {}).get("protected_prefixes", [])
    for route in parsed.get("routes", []):
        if route.get("is_admin_route") and not route.get("is_protected"):
            findings.append(
                {
                    "rule_id": "admin-route-without-auth",
                    "title": "Admin API route appears reachable without route-level auth",
                    "severity": "critical",
                    "attack_path": f"An attacker reaches {route['route_path']} directly, invokes privileged admin behavior, and chains that access into data exposure or destructive actions.",
                    "evidence": [
                        f"Route file maps to {route['route_path']}.",
                        "No route-local auth marker was detected.",
                        f"Middleware protected prefixes: {protected_prefixes or ['none detected']}",
                    ],
                    "remediation": [
                        "Require an explicit auth and admin authorization check inside the route handler.",
                        "Extend middleware coverage to /api/admin/* only if that matches your security model.",
                    ],
                    "confidence": 0.93,
                }
            )

    if any(variable["key"].upper().startswith("DATABASE_") for variable in parsed.get("env", {}).get("variables", [])):
        findings.append(
            {
                "rule_id": "broad-db-access-path",
                "title": "Application service has a direct broad path to the database",
                "severity": "medium",
                "attack_path": "A compromise in the web tier can pivot directly into the database using shared credentials and a flat service relationship.",
                "evidence": [
                    "Database credentials are distributed through environment variables.",
                    "Application code and compose config imply direct web-to-postgres connectivity.",
                ],
                "remediation": [
                    "Reduce database privileges to the minimum required role.",
                    "Separate admin-only database actions from the main web runtime path.",
                ],
                "confidence": 0.77,
            }
        )

    return findings

