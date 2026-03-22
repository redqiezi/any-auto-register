"""浏览器 Profile 管理 - 为持久浏览器身份与钱包绑定预留"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import time


DEFAULT_PROFILE_ROOT = Path("browser_profiles")


@dataclass
class BrowserProfile:
    name: str
    profile_id: Optional[int] = None
    wallet_id: Optional[int] = None
    proxy: str = ""
    browser_type: str = "chromium"
    user_data_dir: str = ""
    fingerprint: dict = field(default_factory=dict)
    extension_paths: list[str] = field(default_factory=list)
    status: str = "ready"
    created_at: int = field(default_factory=lambda: int(time.time()))


def ensure_profile_dir(profile_id: int) -> str:
    root = DEFAULT_PROFILE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"profile_{profile_id}"
    path.mkdir(parents=True, exist_ok=True)
    return str(path.resolve())
