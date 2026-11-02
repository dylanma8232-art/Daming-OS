"""Lazy, host-neutral skill discovery for Daming OS.

OpenClaw normally owns skill loading.  This loader gives other agent runtimes the
same capability without requiring an OpenClaw plugin or a framework-specific SDK.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path
    body: str


class SkillLazyLoader:
    """Indexes only skill paths; file contents are read on first request."""

    def __init__(self, directories: Iterable[str]):
        self.directories = [Path(directory) for directory in directories]
        self._paths: Dict[str, Path] = {}
        self._loaded: Dict[str, Skill] = {}
        self._mtimes: Dict[str, float] = {}

    def discover(self) -> List[str]:
        for directory in self.directories:
            if not directory.exists():
                continue
            for path in directory.rglob("SKILL.md"):
                name = path.parent.name
                self._paths.setdefault(name, path)
        return sorted(self._paths)

    def load(self, name: str) -> Optional[Skill]:
        path = self._paths.get(name)
        if path is None:
            self.discover()
            path = self._paths.get(name)
        if path is None:
            return None
        # 项 10：读取时校验文件 mtime，技能被部署替换后免重启热生效，不再永久使用旧缓存。
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return self._loaded.get(name)
        if name in self._loaded and self._mtimes.get(name) == mtime:
            return self._loaded[name]
        text = path.read_text(encoding="utf-8")
        skill = Skill(name=name, path=path, body=text)
        self._loaded[name] = skill
        self._mtimes[name] = mtime
        return skill

    def invalidate(self, name: str) -> None:
        """主动失效某个已加载技能的缓存（部署后调用可立即生效）。"""
        self._loaded.pop(name, None)
        self._mtimes.pop(name, None)

    def eligible(self, name: str, *, required_env: Iterable[str] = (),
                 required_binaries: Iterable[str] = ()) -> Optional[Skill]:
        """Load a skill only when its host prerequisites are present."""
        if any(not os.getenv(key) for key in required_env):
            return None
        if any(shutil.which(binary) is None for binary in required_binaries):
            return None
        return self.load(name)
