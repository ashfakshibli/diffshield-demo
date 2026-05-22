from pathlib import Path
from typing import Dict


TARGET_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
    "middleware.ts",
    "app/api/admin/users/route.ts",
    "app/api/health/route.ts",
    "lib/db.ts",
]


def ingest_repo(repo_path: str) -> Dict[str, str]:
    root = Path(repo_path)
    if not root.exists():
        raise FileNotFoundError(f"Repo path does not exist: {repo_path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repo path is not a directory: {repo_path}")

    collected: Dict[str, str] = {}
    for relative_path in TARGET_FILES:
        file_path = root / relative_path
        if file_path.exists() and file_path.is_file():
            collected[relative_path] = file_path.read_text(encoding="utf-8")
    return collected

