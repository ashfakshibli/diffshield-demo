import io
import tarfile
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator, Tuple
from urllib import request
from urllib.parse import urlparse


RepoSource = Tuple[Path, str, str, str]


def _is_url(repo_ref: str) -> bool:
    parsed = urlparse(repo_ref)
    return parsed.scheme in {"http", "https"}


def _parse_github_repo(repo_ref: str) -> tuple[str, str]:
    parsed = urlparse(repo_ref)
    if parsed.netloc != "github.com":
        raise ValueError("Only public GitHub repository URLs are supported in hosted mode")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repository URL: {repo_ref}")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    return owner, repo


def _safe_extract(archive: tarfile.TarFile, target_dir: Path) -> None:
    for member in archive.getmembers():
        destination = (target_dir / member.name).resolve()
        if not str(destination).startswith(str(target_dir.resolve())):
            raise ValueError(f"Unsafe archive entry: {member.name}")
    archive.extractall(path=target_dir)


@contextmanager
def materialize_repo(repo_ref: str) -> Iterator[RepoSource]:
    if not _is_url(repo_ref):
        repo_root = Path(repo_ref)
        if not repo_root.exists():
            raise FileNotFoundError(f"Repo path does not exist: {repo_ref}")
        if not repo_root.is_dir():
            raise NotADirectoryError(f"Repo path is not a directory: {repo_ref}")
        yield repo_root, "local_path", str(repo_root), repo_root.name
        return

    owner, repo = _parse_github_repo(repo_ref)
    tarball_url = f"https://api.github.com/repos/{owner}/{repo}/tarball"
    req = request.Request(
        tarball_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "diffshield-analyzer",
        },
    )

    with TemporaryDirectory(prefix="diffshield-repo-") as tmp_dir:
        with request.urlopen(req, timeout=30) as response:
            archive_bytes = response.read()

        extract_root = Path(tmp_dir)
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            _safe_extract(archive, extract_root)

        extracted_dirs = [path for path in extract_root.iterdir() if path.is_dir()]
        if not extracted_dirs:
            raise RuntimeError(f"Unable to extract repository archive for {repo_ref}")

        yield extracted_dirs[0], "github_url", repo_ref, repo
