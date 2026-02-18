"""
Session lock file management for CLI.
"""

import os
import json
import tempfile
import signal
import random
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, TypedDict

LOCK_DIR = Path(tempfile.gettempdir()) / "aluvia-sdk"

ADJECTIVES = [
    "swift",
    "bold",
    "calm",
    "keen",
    "warm",
    "bright",
    "silent",
    "rapid",
    "steady",
    "clever",
    "vivid",
    "agile",
    "noble",
    "lucid",
    "crisp",
    "gentle",
    "fierce",
    "nimble",
    "sturdy",
    "witty",
]

NOUNS = [
    "falcon",
    "tiger",
    "river",
    "maple",
    "coral",
    "cedar",
    "orbit",
    "prism",
    "flint",
    "spark",
    "ridge",
    "ember",
    "crane",
    "grove",
    "stone",
    "brook",
    "drift",
    "crest",
    "sage",
    "lynx",
]


class LockDetection(TypedDict, total=False):
    """Lock detection data structure."""

    hostname: str
    lastUrl: str
    blockStatus: str
    score: float
    signals: List[str]
    pass_: str  # 'pass' is a reserved keyword, use 'pass_'
    persistentBlock: bool
    timestamp: int


class LockData(TypedDict, total=False):
    """Lock data structure."""

    pid: int
    session: Optional[str]
    connectionId: Optional[int]
    cdpUrl: Optional[str]
    proxyUrl: Optional[str]
    url: Optional[str]
    ready: Optional[bool]
    blockDetection: Optional[bool]
    autoUnblock: Optional[bool]
    lastDetection: Optional[LockDetection]


class SessionInfo(TypedDict, total=False):
    """Session info structure."""

    session: str
    pid: int
    connectionId: Optional[int]
    cdpUrl: Optional[str]
    proxyUrl: Optional[str]
    url: Optional[str]
    ready: Optional[bool]
    blockDetection: Optional[bool]
    autoUnblock: Optional[bool]
    lastDetection: Optional[LockDetection]


def _lock_file_name(session_name: Optional[str] = None) -> str:
    """Get the lock file name for a session."""
    return f"cli-{session_name or 'default'}.lock"


def _log_file_name(session_name: Optional[str] = None) -> str:
    """Get the log file name for a session."""
    return f"cli-{session_name or 'default'}.log"


def write_lock(data: LockData, session_name: Optional[str] = None) -> None:
    """Write lock data to file."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    file_path = LOCK_DIR / _lock_file_name(session_name)
    tmp_path = file_path.with_suffix(".lock.tmp")

    try:
        tmp_path.write_text(json.dumps(data), encoding="utf-8")
        tmp_path.replace(file_path)  # atomic overwrite, cross-platform
    finally:
        # Clean up temp file if it still exists
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def read_lock(session_name: Optional[str] = None) -> Optional[LockData]:
    """Read lock data from file."""
    try:
        file_path = LOCK_DIR / _lock_file_name(session_name)
        raw = file_path.read_text(encoding="utf-8").strip()
        parsed = json.loads(raw)
        if isinstance(parsed.get("pid"), int):
            return parsed
        return None
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def remove_lock(session_name: Optional[str] = None) -> None:
    """Remove lock file."""
    try:
        file_path = LOCK_DIR / _lock_file_name(session_name)
        file_path.unlink()
    except (FileNotFoundError, OSError):
        pass


def is_process_alive(pid: int) -> bool:
    """Check if a process is alive."""
    try:
        # On Unix, signal 0 doesn't send signal but checks if process exists
        # On Windows, os.kill may not work the same, so we use different approach
        if os.name == "nt":  # Windows
            import ctypes

            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:  # Unix/Linux/Mac
            os.kill(pid, 0)
            return True
    except (OSError, AttributeError, Exception):
        return False


def get_log_file_path(session_name: Optional[str] = None) -> Path:
    """Get the log file path for a session."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    return LOCK_DIR / _log_file_name(session_name)


def validate_session_name(name: str) -> bool:
    """Validate session name format."""
    import re

    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def generate_session_name() -> str:
    """Generate a unique session name."""
    max_attempts = 10
    for attempt in range(max_attempts):
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        name = f"{adj}-{noun}" if attempt == 0 else f"{adj}-{noun}-{attempt}"
        file_path = LOCK_DIR / _lock_file_name(name)

        if not file_path.exists():
            return name

        # Lock file exists — check if the process is still alive
        lock = read_lock(name)
        if not lock or not is_process_alive(lock["pid"]):
            # Stale lock, we can reuse this name
            remove_lock(name)
            return name

    # Fallback: use timestamp
    return f"session-{int(time.time() * 1000)}"


def to_lock_data(info: SessionInfo) -> LockData:
    """Convert SessionInfo to LockData (removes session key)."""
    lock_data = dict(info)
    lock_data.pop("session", None)
    return lock_data


def list_sessions() -> List[SessionInfo]:
    """List all active sessions."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    sessions: List[SessionInfo] = []

    try:
        for file_path in LOCK_DIR.iterdir():
            if file_path.suffix != ".lock" or not file_path.name.startswith("cli-"):
                continue

            # Extract session name from filename
            name_parts = file_path.stem.split("-", 1)
            if len(name_parts) < 2:
                continue
            session_name = name_parts[1]

            lock = read_lock(session_name)
            if not lock:
                # Corrupt lock file, clean up
                remove_lock(session_name)
                continue

            if not is_process_alive(lock["pid"]):
                # Stale lock, clean up
                remove_lock(session_name)
                continue

            sessions.append(
                {
                    "session": session_name,
                    "pid": lock["pid"],
                    "connectionId": lock.get("connectionId"),
                    "cdpUrl": lock.get("cdpUrl"),
                    "proxyUrl": lock.get("proxyUrl"),
                    "url": lock.get("url"),
                    "ready": lock.get("ready"),
                    "blockDetection": lock.get("blockDetection"),
                    "autoUnblock": lock.get("autoUnblock"),
                    "lastDetection": lock.get("lastDetection"),
                }
            )
    except OSError:
        pass

    return sessions
