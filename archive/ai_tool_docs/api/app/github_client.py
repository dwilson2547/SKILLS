"""GitHub API client using only stdlib (urllib) — no extra dependencies."""
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
_BINARY_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "bmp", "webp", "ico", "tiff", "tif",
    "pdf", "zip", "gz", "tar", "rar", "7z", "exe", "dll", "so", "dylib",
    "woff", "woff2", "ttf", "eot", "otf", "mp3", "mp4", "wav", "avi",
    "mov", "mkv", "flac", "ogg", "webm", "db", "sqlite", "class", "jar",
}


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    h: dict = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def _get_json(url: str) -> object:
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"GitHub API error {exc.code} for {url}: {exc.read().decode()}"
        ) from exc


def get_repo_info(owner: str, repo: str) -> dict:
    """Return the repository metadata dict (includes default_branch)."""
    url = f"{API_BASE}/repos/{owner}/{repo}"
    data = _get_json(url)
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected repo info response for {owner}/{repo}")
    return data


def is_wiki_repo(repo: str) -> bool:
    return repo.endswith(".wiki")


def is_text_file(file_path: str) -> bool:
    dot = file_path.rfind(".")
    if dot == -1:
        return True
    return file_path[dot + 1:].lower() not in _BINARY_EXTENSIONS


def get_latest_commit_sha(owner: str, repo: str, branch: str) -> str:
    url = (
        f"{API_BASE}/repos/{owner}/{repo}/commits"
        f"?sha={urllib.parse.quote(branch, safe='')}&per_page=1"
    )
    data = _get_json(url)
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"No commits found for {owner}/{repo}@{branch}")
    return data[0]["sha"]


def get_repo_tree(owner: str, repo: str, commit_sha: str) -> list[dict]:
    """Return the recursive file tree for a commit."""
    url = f"{API_BASE}/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1"
    data = _get_json(url)
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected tree response for {owner}/{repo}")
    items: list[dict] = data.get("tree", [])
    if data.get("truncated"):
        logger.warning(
            "Tree for %s/%s was truncated by GitHub — some files may be missing",
            owner, repo,
        )
    return items


def download_file(owner: str, repo: str, file_path: str, branch: str) -> str:
    encoded = "/".join(
        urllib.parse.quote(part, safe="") for part in file_path.split("/")
    )
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{encoded}"
    token = os.environ.get("GITHUB_TOKEN", "")
    headers: dict = {}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Failed to download {file_path} from {owner}/{repo}: HTTP {exc.code}"
        ) from exc
