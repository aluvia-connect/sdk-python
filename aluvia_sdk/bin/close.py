"""
Session close handler for CLI.
"""
import os
import signal
import asyncio
from typing import Optional, List
from ..session.lock import remove_lock, is_process_alive, list_sessions, to_lock_data, LockData
from .cli import output


async def handle_close(session_name: Optional[str] = None, close_all: bool = False) -> None:
    """
    Handle closing browser sessions.
    
    Args:
        session_name: Name of session to close (None for auto-select)
        close_all: Whether to close all sessions
    """
    if close_all:
        sessions = list_sessions()
        if len(sessions) == 0:
            output({"error": "No running browser sessions found.", "closed": [], "count": 0}, 1)
        
        # Send SIGTERM to all sessions
        for s in sessions:
            try:
                if os.name == 'nt':  # Windows
                    os.kill(s["pid"], signal.SIGTERM)
                else:
                    os.kill(s["pid"], signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
        
        # Wait up to 10 seconds for all processes to exit
        max_wait = 40
        alive = {s["pid"] for s in sessions}
        for _ in range(max_wait):
            if not alive:
                break
            await asyncio.sleep(0.25)
            for pid in list(alive):
                if not is_process_alive(pid):
                    alive.remove(pid)
        
        # Force-kill any survivors
        for pid in alive:
            try:
                if os.name == 'nt':  # Windows
                    os.kill(pid, signal.SIGTERM)  # Windows doesn't have SIGKILL
                else:
                    os.kill(pid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
        
        # Now remove all locks
        closed: List[str] = []
        for s in sessions:
            remove_lock(s["session"])
            closed.append(s["session"])
        
        output({"message": "All browser sessions closed.", "closed": closed, "count": len(closed)})
    
    # If no session name specified, figure out what to close
    if not session_name:
        sessions = list_sessions()
        if len(sessions) == 0:
            output({"error": "No running browser sessions found."}, 1)
        if len(sessions) > 1:
            output({
                "error": "Multiple sessions running. Specify --browser-session <name> or --all.",
                "browserSessions": [s["session"] for s in sessions],
            }, 1)
        # Single session — use its data directly
        session = sessions[0]
        session_name = session["session"]
        await close_session(session_name, to_lock_data(session))
        return
    
    # Session name provided — need to verify it's alive
    sessions = list_sessions()
    match = next((s for s in sessions if s["session"] == session_name), None)
    
    if not match:
        output({"browserSession": session_name, "error": "No running browser session found."}, 1)
    
    await close_session(session_name, to_lock_data(match))


async def close_session(session_name: str, lock: LockData) -> None:
    """Close a single session."""
    if not is_process_alive(lock["pid"]):
        remove_lock(session_name)
        output({
            "browserSession": session_name,
            "message": "Browser process was not running. Lock file cleaned up.",
        })
    
    try:
        if os.name == 'nt':  # Windows
            os.kill(lock["pid"], signal.SIGTERM)
        else:
            os.kill(lock["pid"], signal.SIGTERM)
    except (OSError, ProcessLookupError) as err:
        output({"browserSession": session_name, "error": f"Failed to stop process: {str(err)}"}, 1)
    
    # Wait for the process to exit (up to 10 seconds)
    max_wait = 40
    for _ in range(max_wait):
        await asyncio.sleep(0.25)
        if not is_process_alive(lock["pid"]):
            remove_lock(session_name)
            output({
                "browserSession": session_name,
                "message": "Browser session closed successfully.",
            })
    
    # If still alive after timeout, force kill
    if is_process_alive(lock["pid"]):
        try:
            if os.name == 'nt':  # Windows
                os.kill(lock["pid"], signal.SIGTERM)
            else:
                os.kill(lock["pid"], signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
        
        await asyncio.sleep(0.5)
        remove_lock(session_name)
        
        if is_process_alive(lock["pid"]):
            output({
                "browserSession": session_name,
                "error": "Failed to stop browser process (timeout).",
            }, 1)
    
    remove_lock(session_name)
    output({
        "browserSession": session_name,
        "message": "Browser session closed (forced).",
    })
