"""
API helper functions for CLI commands.
"""
import os
from typing import Dict, Any, Optional, Tuple
from ..api.aluvia_api import AluviaApi
from ..session.lock import read_lock, list_sessions, is_process_alive, remove_lock, to_lock_data, LockData
from .cli import output


def require_api() -> AluviaApi:
    """
    Create an AluviaApi instance from ALUVIA_API_KEY env var.
    Calls output() and exits if the key is missing.
    """
    api_key = os.environ.get("ALUVIA_API_KEY", "").strip()
    if not api_key:
        output({"error": "ALUVIA_API_KEY environment variable is required."}, 1)
    return AluviaApi(api_key=api_key)


def resolve_session(session_name: Optional[str] = None) -> Tuple[str, LockData]:
    """
    Resolve a session by name or auto-select when only one is running.
    Calls output() and exits on error (no sessions, ambiguous sessions, stale lock).
    
    Returns:
        Tuple of (session_name, lock_data)
    """
    if session_name:
        lock = read_lock(session_name)
        if not lock:
            output({"error": f"No session found with name '{session_name}'."}, 1)
        if not is_process_alive(lock["pid"]):
            remove_lock(session_name)
            output({"error": f"Session '{session_name}' is no longer running (stale lock cleaned up)."}, 1)
        return session_name, lock
    
    sessions = list_sessions()
    if len(sessions) == 0:
        output({"error": "No running browser sessions found."}, 1)
    if len(sessions) > 1:
        output({
            "error": "Multiple sessions running. Specify --browser-session <name>.",
            "browserSessions": [s["session"] for s in sessions],
        }, 1)
    
    s = sessions[0]
    return s["session"], to_lock_data(s)


def require_connection_id(lock: LockData, session: str) -> int:
    """
    Require a connection ID from lock data.
    Calls output() and exits if connectionId is missing.
    """
    connection_id = lock.get("connectionId")
    if connection_id is None:
        output({
            "error": f"Session '{session}' has no connection ID. It may have been started without API access."
        }, 1)
    return connection_id
