#!/usr/bin/env python3
"""Platform registry: publishing limits per platform and the render profile each platform uses.

The data lives in config/platforms.yaml. Used by scripts/publish_meta.py and scripts/render.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "config/platforms.yaml"
DEFAULT_PROFILE = "vertical-9x16"
LANGS = ("zh", "en")


class RegistryError(ValueError):
    """The registry file is invalid, or an id is not in it."""


@dataclass(frozen=True)
class Profile:
    id: str
    width: int
    height: int
    safe_x: int
    safe_top: int
    safe_bottom: int
    title_top: int
    compact: bool = False
    supported: bool = True
    fallback: str | None = None

    def props(self) -> dict:
        """The camelCase dict the Remotion compositions receive as their `profile` prop."""
        return {"id": self.id, "width": self.width, "height": self.height, "safeX": self.safe_x,
                "safeTop": self.safe_top, "safeBottom": self.safe_bottom, "titleTop": self.title_top,
                "compact": self.compact}


@dataclass(frozen=True)
class Platform:
    id: str
    name: str
    lang: str
    profile: str
    duration_min: int
    duration_max: int
    title_field: str
    title_min: int
    title_max: int
    description_max: int
    hashtags_max: int
    verified: bool
    file_stem: str
    title_punct: str | None = None   # when set, a title may hold only letters, digits, CJK and these marks


class Registry:
    def __init__(self, profiles: dict[str, Profile], platforms: dict[str, Platform]):
        self.profiles = profiles
        self.platforms = platforms

    def platform(self, platform_id: str) -> Platform:
        if platform_id not in self.platforms:
            raise RegistryError(f"unknown platform '{platform_id}'; known: {', '.join(self.platforms)}")
        return self.platforms[platform_id]

    def profile(self, profile_id: str) -> Profile:
        if profile_id not in self.profiles:
            raise RegistryError(f"unknown profile '{profile_id}'; known: {', '.join(self.profiles)}")
        return self.profiles[profile_id]

    def resolve(self, profile_id: str) -> tuple[Profile, str | None]:
        """The profile to render for `profile_id`: itself, or its fallback (with a warning) when not supported yet."""
        profile = self.profile(profile_id)
        if profile.supported:
            return profile, None
        fallback = self.profile(profile.fallback)
        return fallback, f"profile {profile.id} is not supported yet; rendering {fallback.id} instead"


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects a repeated mapping key instead of keeping the last one."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=True)
            if isinstance(key, (str, int, float, bool)) or key is None:
                if key in seen:
                    raise RegistryError(f"duplicate key '{key}' at line {key_node.start_mark.line + 1}; "
                                        "each id must be unique (rename the copied block)")
                seen.add(key)
        return super().construct_mapping(node, deep)


def _need(block, keys, where: str) -> None:
    if not isinstance(block, dict):
        raise RegistryError(f"{where} must be a mapping")
    for key in keys:
        if key not in block:
            raise RegistryError(f"{where} is missing '{key}'")


def load(path=None) -> Registry:
    raw = yaml.load(Path(path or DEFAULT_PATH).read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    _need(raw, ("profiles", "platforms"), "registry")

    profiles: dict[str, Profile] = {}
    for pid, b in raw["profiles"].items():
        where = f"profile {pid}"
        _need(b, ("width", "height", "safe", "title_top"), where)
        _need(b["safe"], ("x", "top", "bottom"), f"{where}.safe")
        profiles[pid] = Profile(pid, b["width"], b["height"], b["safe"]["x"], b["safe"]["top"], b["safe"]["bottom"],
                                b["title_top"], bool(b.get("compact", False)), bool(b.get("supported", True)),
                                b.get("fallback"))
    if DEFAULT_PROFILE not in profiles or not profiles[DEFAULT_PROFILE].supported:
        raise RegistryError(f"the registry must define a supported '{DEFAULT_PROFILE}' profile")
    for p in profiles.values():
        if p.supported:
            continue
        if not p.fallback:
            raise RegistryError(f"profile {p.id} is unsupported and needs a 'fallback' profile")
        if p.fallback not in profiles:
            raise RegistryError(f"profile {p.id} falls back to unknown profile '{p.fallback}'")
        if not profiles[p.fallback].supported:
            raise RegistryError(f"profile {p.id}: fallback '{p.fallback}' is not supported either")

    platforms: dict[str, Platform] = {}
    for pid, b in raw["platforms"].items():
        where = f"platform {pid}"
        _need(b, ("name", "lang", "profile", "duration", "title_field", "title", "description_max", "hashtags_max"), where)
        if b["lang"] not in LANGS:
            raise RegistryError(f"{where}: lang must be one of {', '.join(LANGS)}")
        if b["profile"] not in profiles:
            raise RegistryError(f"{where}: unknown profile '{b['profile']}'")
        _need(b["duration"], ("min", "max"), f"{where}.duration")
        _need(b["title"], ("max",), f"{where}.title")
        platforms[pid] = Platform(pid, b["name"], b["lang"], b["profile"], b["duration"]["min"], b["duration"]["max"],
                                  b["title_field"], b["title"].get("min", 1), b["title"]["max"], b["description_max"],
                                  b["hashtags_max"], bool(b.get("verified", False)), b.get("file_stem", pid), b["title"].get("punct"))
    stems: dict[str, str] = {}
    for pf in platforms.values():
        if pf.file_stem in stems:
            raise RegistryError(f"platforms {stems[pf.file_stem]} and {pf.id} share file_stem '{pf.file_stem}'; "
                                "their publish files would overwrite each other")
        stems[pf.file_stem] = pf.id
    return Registry(profiles, platforms)


def video_name(slug: str, profile_id: str) -> str:
    return f"{slug}.mp4" if profile_id == DEFAULT_PROFILE else f"{slug}-{profile_id}.mp4"


def cover_name(profile_id: str) -> str:
    return "cover.png" if profile_id == DEFAULT_PROFILE else f"cover-{profile_id}.png"


def plan_renders(reg: Registry, platform_ids=(), profile_id: str | None = None) -> tuple[list[Profile], list[str]]:
    """The distinct profiles to render (first-use order) and a warning for each fallback taken."""
    wanted = [profile_id] if profile_id else [reg.platform(p).profile for p in platform_ids] or [DEFAULT_PROFILE]
    profiles: list[Profile] = []
    warnings: list[str] = []
    for wanted_id in wanted:
        profile, warning = reg.resolve(wanted_id)
        if warning and warning not in warnings:
            warnings.append(warning)
        if profile not in profiles:
            profiles.append(profile)
    return profiles, warnings


def check_duration(reg: Registry, platform_ids, seconds: float) -> list[str]:
    errors = []
    for pid in platform_ids:
        p = reg.platform(pid)
        if not p.duration_min <= seconds <= p.duration_max:
            errors.append(f"{p.id}: clip is {seconds:.1f}s; {p.name} allows {p.duration_min}-{p.duration_max} s")
    return errors
