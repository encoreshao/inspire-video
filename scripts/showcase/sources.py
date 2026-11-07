"""Classify an ingest source: website, GitHub repo, GitLab repo (any host) or local folder."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


class SourceError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    kind: str       # "website" | "github" | "gitlab" | "local"
    url: str        # normalised URL, or the absolute folder path for "local"
    host: str       # "" for local
    repo_path: str  # "owner/repo" (GitLab: "group/sub/repo"); "" for website and local


SSH = re.compile(r"^git@([A-Za-z0-9.-]+):(\S+?)(?:\.git)?/?$")
GITHUB_HOSTS = ("github.com", "www.github.com")


def _gitlab_hosts(extra) -> set[str]:
    env = os.environ.get("INSPIRE_GITLAB_HOSTS", "")
    hosts = {h.strip().lower() for h in env.split(",") if h.strip()}
    return hosts | {h.strip().lower() for h in extra}


def _is_gitlab(host: str, hosts: set[str]) -> bool:
    return host in hosts or host == "gitlab.com" or host.startswith("gitlab.")


def _repo_source(kind: str, host: str, path: str) -> Source:
    segs = [s for s in path.split("/") if s]
    if kind == "gitlab" and "-" in segs:
        segs = segs[:segs.index("-")]          # GitLab puts pages after "/-/"
    if kind == "github":
        segs = segs[:2]
    if segs and segs[-1].endswith(".git"):
        segs[-1] = segs[-1][:-4]
    if len(segs) < 2:
        raise SourceError(f"{host}{path} is not a repository (expected owner/name)")
    repo_path = "/".join(segs)
    return Source(kind, f"https://{host}/{repo_path}", host, repo_path)


def classify_source(arg: str, gitlab_hosts=()) -> Source:
    arg = (arg or "").strip()
    if not arg:
        raise SourceError("no source given")
    hosts = _gitlab_hosts(gitlab_hosts)
    m = SSH.match(arg)
    if m:
        host = m.group(1).lower()
        if host in GITHUB_HOSTS:
            return _repo_source("github", "github.com", m.group(2))
        if _is_gitlab(host, hosts):
            return _repo_source("gitlab", host, m.group(2))
        raise SourceError(f"cannot tell what {host} hosts; use an https URL")
    if "://" in arg:
        parts = urlsplit(arg)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise SourceError(f"only http(s) URLs are supported, got {arg!r}")
        host = parts.hostname.lower()
        if host in GITHUB_HOSTS:
            return _repo_source("github", "github.com", parts.path)
        if _is_gitlab(host, hosts):
            return _repo_source("gitlab", host, parts.path)
        try:
            port = parts.port
        except ValueError:
            raise SourceError(f"invalid port in {arg!r}") from None
        shown = f"[{host}]" if ":" in host else host      # never keep user:password@ from the URL
        url = f"{parts.scheme}://{shown}{f':{port}' if port else ''}{parts.path or '/'}"
        if parts.query:
            url += f"?{parts.query}"
        return Source("website", url, host, "")
    folder = Path(arg).expanduser()
    if folder.is_dir():
        return Source("local", str(folder.resolve()), "", "")
    raise SourceError(f"{arg!r} is neither an existing folder nor a URL")
