"""Small GitHub REST client for First-PR Mentor.

All errors are raised as GitHubError with a friendly message the UI can show.
The token is read from GITHUB_TOKEN and is never printed or logged.
"""
import base64
import math
import os
import re
from datetime import datetime, timezone

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API = "https://api.github.com"
TIMEOUT = 15
cache = st.cache_data(ttl=3600, show_spinner=False)


class GitHubError(Exception):
    """Friendly, user-facing GitHub error."""


class NotFoundError(GitHubError):
    pass


class RateLimitError(GitHubError):
    pass


def _headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "first-pr-mentor",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(path, params=None):
    """GET a GitHub API path and return parsed JSON, or raise GitHubError."""
    try:
        resp = requests.get(f"{API}{path}", headers=_headers(), params=params, timeout=TIMEOUT)
    except requests.RequestException:
        raise GitHubError("Couldn't reach GitHub. Check your internet connection and try again.") from None
    if resp.status_code == 404:
        raise NotFoundError("Not found on GitHub. Check the link (private repos need a token with access).")
    if resp.status_code == 401:
        raise GitHubError("GitHub rejected the token. Check GITHUB_TOKEN in your .env file.")
    if resp.status_code in (403, 429):
        if resp.status_code == 429 or resp.headers.get("X-RateLimit-Remaining") == "0" or "rate limit" in resp.text.lower():
            raise RateLimitError("GitHub rate limit reached. Add a GITHUB_TOKEN to .env or wait a few minutes.")
        raise GitHubError("GitHub refused this request (403). Your token may lack access.")
    if not resp.ok:
        raise GitHubError(f"GitHub returned an error ({resp.status_code}). Please try again.")
    return resp.json()


# ---------- Issue + repo info ----------

def parse_issue_url(url):
    """'https://github.com/o/r/issues/12' -> ('o', 'r', 12). Raises ValueError if invalid."""
    match = re.match(r"^https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)", (url or "").strip())
    if not match:
        raise ValueError("That doesn't look like a GitHub issue link. Expected: https://github.com/owner/repo/issues/123")
    return match.group(1), match.group(2), int(match.group(3))


@cache
def get_issue(owner, repo, number):
    data = _get(f"/repos/{owner}/{repo}/issues/{number}")
    if "pull_request" in data:
        raise GitHubError("That link is a pull request, not an issue. Paste an issue link instead.")
    comments = []
    if data.get("comments", 0) > 0:
        raw = _get(f"/repos/{owner}/{repo}/issues/{number}/comments", {"per_page": 3})
        comments = [{"author": (c.get("user") or {}).get("login", "unknown"), "body": (c.get("body") or "")[:600]} for c in raw[:3]]
    return {
        "number": number,
        "title": data.get("title", ""),
        "body": data.get("body") or "",
        "labels": [label["name"] for label in data.get("labels", [])],
        "html_url": data.get("html_url", ""),
        "comments": comments,
    }


@cache
def get_repo_info(owner, repo):
    data = _get(f"/repos/{owner}/{repo}")
    return {
        "description": data.get("description") or "",
        "language": data.get("language") or "",
        "default_branch": data.get("default_branch", "main"),
        "stars": data.get("stargazers_count", 0),
        "archived": bool(data.get("archived")),
    }


# ---------- Repo context ----------

SKIP_DIRS = {"node_modules", ".git", "vendor", "dist", "build", "__pycache__", ".venv", "venv", "target"}
SKIP_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock", "Gemfile.lock"}
SKIP_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp", ".lock",
    ".exe", ".dll", ".so", ".bin", ".zip", ".gz", ".tar", ".jar", ".pdf",
    ".woff", ".woff2", ".ttf", ".mp4", ".mp3", ".pyc", ".class", ".o", ".min.js",
}


@cache
def get_file_tree(owner, repo, branch):
    """Return a list of file paths (no folders), skipping junk and binaries."""
    data = _get(f"/repos/{owner}/{repo}/git/trees/{branch}", {"recursive": "1"})
    paths = []
    for node in data.get("tree", []):
        if node.get("type") != "blob":
            continue
        path = node["path"]
        parts = path.split("/")
        if any(p in SKIP_DIRS for p in parts[:-1]):
            continue
        if parts[-1] in SKIP_NAMES or any(path.lower().endswith(ext) for ext in SKIP_EXT):
            continue
        paths.append(path)
    return paths


@cache
def get_file_content(owner, repo, path):
    """Decoded text of a file, truncated to 6000 characters."""
    data = _get(f"/repos/{owner}/{repo}/contents/{path}")
    if isinstance(data, list) or data.get("type") != "file":
        raise GitHubError(f"{path} is not a file.")
    if not data.get("content"):
        raise GitHubError(f"{path} is too large to read through the API.")
    text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return text[:6000]


@cache
def get_contributing(owner, repo):
    """Text of CONTRIBUTING.md (tries 3 locations) or None."""
    for path in ("CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md"):
        try:
            return get_file_content(owner, repo, path)
        except NotFoundError:
            continue
    return None


# ---------- Finding relevant files ----------

STOPWORDS = {
    "this", "that", "with", "from", "have", "should", "would", "could", "there", "their", "about",
    "which", "when", "what", "where", "while", "will", "been", "being", "does", "doing", "done",
    "into", "than", "then", "them", "they", "your", "some", "such", "only", "also", "just", "like",
    "more", "most", "much", "must", "need", "needs", "want", "wants", "issue", "please", "thanks",
    "thank", "make", "makes", "currently", "instead", "after", "before", "because", "other", "these",
    "those", "here", "very", "able", "using", "used", "uses", "add", "fix", "bug", "feature", "request",
}
SOURCE_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".cs",
    ".rb", ".php", ".kt", ".swift", ".html", ".css", ".vue", ".scala",
}
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|(^|/)test_|_test\.|\.test\.|\.spec\.")


def extract_keywords(text):
    """Lowercase words > 3 chars (minus stopwords) plus code identifiers like snake_case/camelCase."""
    keywords = set()
    for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text or ""):
        low = word.lower()
        is_identifier = "_" in word or re.search(r"[a-z][A-Z]", word) is not None
        if low in STOPWORDS or not (len(low) > 3 or is_identifier):
            continue
        keywords.add(low)
        if is_identifier:  # also match the parts, e.g. parse_config -> parse, config
            for part in re.split(r"_|(?<=[a-z])(?=[A-Z])", word):
                if len(part) > 3 and part.lower() not in STOPWORDS:
                    keywords.add(part.lower())
    return keywords


def find_relevant_files(file_tree, issue_title, issue_body, top_n=5):
    """Score file paths by keyword matches. Prefer source files; downweight tests/docs unless mentioned."""
    text = f"{issue_title} {issue_body}".lower()
    title_kw = extract_keywords(issue_title)
    body_kw = extract_keywords((issue_body or "")[:3000]) - title_kw
    mentions_tests = "test" in text
    mentions_docs = any(w in text for w in ("doc", "readme", "typo"))

    scored = []
    for path in file_tree:
        low = path.lower()
        name = low.rsplit("/", 1)[-1]
        score = 0.0
        for kw, weight in [(k, 2) for k in title_kw] + [(k, 1) for k in body_kw]:
            if kw in name:
                score += weight * 2
            elif kw in low:
                score += weight
        if score == 0:
            continue
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
        if ext in SOURCE_EXT:
            score *= 1.5
        if TEST_RE.search(low) and not mentions_tests:
            score *= 0.4
        if (ext in {".md", ".rst", ".txt"} or low.startswith("docs/")) and not mentions_docs:
            score *= 0.4
        scored.append((score, path))
    scored.sort(key=lambda s: (-s[0], len(s[1])))
    return [path for _, path in scored[:top_n]]


# ---------- Skill-matched issue search ----------

KNOWN_LANGS = {"python", "javascript", "typescript", "java", "c++", "go", "rust", "html", "css", "c", "c#", "ruby", "php", "kotlin", "swift"}
BASE_QUERY = 'label:"good first issue" state:open is:issue no:assignee'


def _query_for(skill):
    """One search per skill. 'react' and unknown skills are keyword searches; html/css uses html."""
    if skill == "html/css":
        skill = "html"
    if skill == "react":
        return f"{BASE_QUERY} language:javascript react"
    if skill in KNOWN_LANGS:
        return f'{BASE_QUERY} language:"{skill}"'
    return f"{BASE_QUERY} {skill}"


def _days_since(iso_time):
    then = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - then).days


@cache
def search_good_first_issues(skills, max_results=15):
    """Search, merge, dedupe, filter stale/archived, rank. `skills` is a tuple of strings."""
    skills = [s.strip().lower() for s in skills if s.strip()][:6]
    if not skills:
        return []

    found = {}  # issue url -> {"item": ..., "matches": set of skills}
    for skill in skills:
        data = _get("/search/issues", {"q": _query_for(skill), "sort": "updated", "order": "desc", "per_page": 30})
        for item in data.get("items", []):
            entry = found.setdefault(item["html_url"], {"item": item, "matches": set()})
            entry["matches"].add(skill)

    # Drop issues with no activity for ~6 months, keep the freshest 25 to save API calls
    fresh = [e for e in found.values() if _days_since(e["item"]["updated_at"]) <= 182]
    fresh.sort(key=lambda e: e["item"]["updated_at"], reverse=True)

    results = []
    for entry in fresh[:25]:
        item = entry["item"]
        owner, repo = item["repository_url"].split("/")[-2:]
        try:
            info = get_repo_info(owner, repo)
        except RateLimitError:
            if results:
                break
            raise
        except GitHubError:
            continue
        if info["archived"]:
            continue

        age = _days_since(item["updated_at"])
        body_len = len(item.get("body") or "")
        # Score out of 100: skill match 40, recent 20, stars 15 (moderate), few comments 15, short body 10
        skill_pts = 40 * min(1, len(entry["matches"]) / max(1, min(len(skills), 2)))
        score = (
            skill_pts
            + 20 * max(0, 1 - age / 182)
            + 15 * min(1, math.log10(info["stars"] + 1) / 4)
            + 15 * max(0, 1 - item.get("comments", 0) / 10)
            + 10 * max(0, 1 - body_len / 1500)
        )
        results.append({
            "title": item["title"],
            "url": item["html_url"],
            "repo": f"{owner}/{repo}",
            "language": info["language"],
            "stars": info["stars"],
            "comments": item.get("comments", 0),
            "age_days": age,
            "score": round(score),
        })
    results.sort(key=lambda r: -r["score"])
    return results[:max_results]
