from typing import Any, Dict


def parse_env(content: str) -> Dict[str, Any]:
    variables: list[Dict[str, Any]] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        variables.append(
            {
                "key": key,
                "value": value,
                "is_secret_like": any(token in key.upper() for token in ["SECRET", "TOKEN", "PASSWORD", "KEY"]),
                "is_debug_flag": key.upper() == "DEBUG" and value.lower() in {"true", "1", "yes"},
            }
        )

    return {"variables": variables}

