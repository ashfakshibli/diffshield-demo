import json
import os
from urllib import error, request
from typing import Any, Dict, List


def _fallback_validate(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "validated_with": "deterministic-fallback",
        "findings": candidates,
    }


def validate_candidates(candidates: List[Dict[str, Any]], notes: str) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return _fallback_validate(candidates)

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

    prompt = {
        "task": "Validate repo threat-model findings for a compact security analysis workflow.",
        "notes": notes,
        "instructions": [
            "Do not invent new findings.",
            "For each candidate, keep the title but improve severity, confidence, evidence wording, and remediation clarity if needed.",
            "Return strict JSON only.",
        ],
        "candidates": candidates,
    }

    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are a security systems validator. Return only JSON."
            },
            {
                "role": "user",
                "content": json.dumps(prompt)
            }
        ],
    }

    req = request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            raw = json.loads(response.read().decode("utf-8"))
            content = raw["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "validated_with": model,
                "findings": parsed.get("validated_findings", candidates),
            }
    except (error.URLError, KeyError, ValueError, json.JSONDecodeError):
        return _fallback_validate(candidates)
