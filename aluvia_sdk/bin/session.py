"""
Session command handlers for CLI.
"""
import uuid
from typing import List, Dict, Any, Optional
from .open import handle_open, OpenOptions
from .close import handle_close
from ..session.lock import list_sessions
from .api_helpers import resolve_session, require_api, require_connection_id
from .cli import output


def parse_session_args(args: List[str]) -> Dict[str, Any]:
    """Parse session command arguments."""
    url: Optional[str] = None
    connection_id: Optional[int] = None
    headed = False
    session_name: Optional[str] = None
    auto_unblock = False
    disable_block_detection = False
    run: Optional[str] = None
    
    i = 0
    while i < len(args):
        if args[i] == '--connection-id' and i + 1 < len(args):
            try:
                parsed = int(args[i + 1])
                if parsed < 1:
                    output({"error": f"Invalid --connection-id: '{args[i + 1]}' must be a positive integer."}, 1)
                connection_id = parsed
            except ValueError:
                output({"error": f"Invalid --connection-id: '{args[i + 1]}' must be a positive integer."}, 1)
            i += 2
        elif args[i] == '--browser-session' and i + 1 < len(args):
            session_name = args[i + 1]
            i += 2
        elif args[i] == '--run' and i + 1 < len(args):
            run = args[i + 1]
            i += 2
        elif args[i] == '--headful':
            headed = True
            i += 1
        elif args[i] == '--auto-unblock':
            auto_unblock = True
            i += 1
        elif args[i] == '--disable-block-detection':
            disable_block_detection = True
            i += 1
        elif not url and not args[i].startswith('--'):
            url = args[i]
            i += 1
        else:
            i += 1
    
    return {
        "url": url,
        "connection_id": connection_id,
        "headed": headed,
        "session_name": session_name,
        "auto_unblock": auto_unblock,
        "disable_block_detection": disable_block_detection,
        "run": run,
    }


async def handle_session(args: List[str]) -> None:
    """Handle session commands."""
    if not args:
        output({"error": "Missing session subcommand. Run 'aluvia help' for usage."}, 1)
    
    subcommand = args[0]
    
    if subcommand == "start":
        await handle_session_start(args[1:])
    elif subcommand == "close":
        await handle_session_close(args[1:])
    elif subcommand == "list":
        handle_session_list()
    elif subcommand == "get":
        await handle_session_get(args[1:])
    elif subcommand == "rotate-ip":
        await handle_session_rotate_ip(args[1:])
    elif subcommand == "set-geo":
        await handle_session_set_geo(args[1:])
    elif subcommand == "set-rules":
        await handle_session_set_rules(args[1:])
    else:
        output({"error": f"Unknown session subcommand: '{subcommand}'. Run 'aluvia help' for usage."}, 1)


async def handle_session_start(args: List[str]) -> None:
    """Handle session start command."""
    parsed = parse_session_args(args)
    
    if not parsed["url"]:
        output({"error": "URL is required. Usage: aluvia session start <url> [options]"}, 1)
    
    opts = OpenOptions(
        url=parsed["url"],
        connection_id=parsed.get("connection_id"),
        headless=not parsed.get("headed", False),
        session_name=parsed.get("session_name"),
        auto_unblock=parsed.get("auto_unblock", False),
        disable_block_detection=parsed.get("disable_block_detection", False),
        run=parsed.get("run"),
    )
    
    await handle_open(opts)


async def handle_session_close(args: List[str]) -> None:
    """Handle session close command."""
    session_name: Optional[str] = None
    close_all = False
    
    i = 0
    while i < len(args):
        if args[i] == '--browser-session' and i + 1 < len(args):
            session_name = args[i + 1]
            i += 2
        elif args[i] == '--all':
            close_all = True
            i += 1
        else:
            i += 1
    
    await handle_close(session_name, close_all)


def handle_session_list() -> None:
    """Handle session list command."""
    sessions = list_sessions()
    output({
        "sessions": [{
            "browserSession": s["session"],
            "pid": s["pid"],
            "startUrl": s.get("url"),
            "cdpUrl": s.get("cdpUrl"),
            "connectionId": s.get("connectionId"),
            "blockDetection": s.get("blockDetection", False),
            "autoUnblock": s.get("autoUnblock", False),
        } for s in sessions],
        "count": len(sessions),
    })


async def handle_session_get(args: List[str]) -> None:
    """Handle session get command."""
    session_name: Optional[str] = None
    
    i = 0
    while i < len(args):
        if args[i] == '--browser-session' and i + 1 < len(args):
            session_name = args[i + 1]
            i += 2
        else:
            i += 1
    
    session, lock = resolve_session(session_name)
    conn_id = lock.get("connectionId")
    
    base: Dict[str, Any] = {
        "browserSession": session,
        "pid": lock["pid"],
        "startUrl": lock.get("url"),
        "cdpUrl": lock.get("cdpUrl"),
        "connectionId": conn_id,
        "blockDetection": lock.get("blockDetection", False),
        "autoUnblock": lock.get("autoUnblock", False),
        "lastDetection": lock.get("lastDetection"),
    }
    
    # If we have a connection ID, enrich with full connection object from API
    if conn_id is not None:
        try:
            api = require_api()
            conn = await api.account.connections.get(conn_id)
            if conn:
                base["connection"] = conn
        except Exception:
            # API enrichment is best-effort; base lock data is still returned
            pass
    
    output(base)


async def handle_session_rotate_ip(args: List[str]) -> None:
    """Handle session rotate-ip command."""
    session_name: Optional[str] = None
    
    i = 0
    while i < len(args):
        if args[i] == '--browser-session' and i + 1 < len(args):
            session_name = args[i + 1]
            i += 2
        else:
            i += 1
    
    session, lock = resolve_session(session_name)
    conn_id = require_connection_id(lock, session)
    api = require_api()
    
    new_session_id = str(uuid.uuid4()).replace('-', '')
    await api.account.connections.patch(conn_id, {"session_id": new_session_id})
    
    output({
        "browserSession": session,
        "connectionId": conn_id,
        "sessionId": new_session_id,
    })


async def handle_session_set_geo(args: List[str]) -> None:
    """Handle session set-geo command."""
    session_name: Optional[str] = None
    geo: Optional[str] = None
    clear = False
    
    i = 0
    while i < len(args):
        if args[i] == '--browser-session' and i + 1 < len(args):
            session_name = args[i + 1]
            i += 2
        elif args[i] == '--clear':
            clear = True
            i += 1
        elif not geo and not args[i].startswith('--'):
            geo = args[i]
            i += 1
        else:
            i += 1
    
    if not geo and not clear:
        output({"error": "Geo code is required. Usage: aluvia session set-geo <geo> [--browser-session <name>]"}, 1)
    
    if geo and not geo.strip():
        output({"error": "Geo code cannot be empty. Provide a valid geo code or use --clear."}, 1)
    
    session, lock = resolve_session(session_name)
    conn_id = require_connection_id(lock, session)
    api = require_api()
    
    target_geo = None if clear else geo.strip()
    await api.account.connections.patch(conn_id, {"target_geo": target_geo})
    
    output({
        "browserSession": session,
        "connectionId": conn_id,
        "targetGeo": target_geo,
    })


async def handle_session_set_rules(args: List[str]) -> None:
    """Handle session set-rules command."""
    session_name: Optional[str] = None
    remove_rules: Optional[str] = None
    append_rules: Optional[str] = None
    
    i = 0
    while i < len(args):
        if args[i] == '--browser-session' and i + 1 < len(args):
            session_name = args[i + 1]
            i += 2
        elif args[i] == '--remove' and i + 1 < len(args):
            remove_rules = args[i + 1]
            i += 2
        elif not append_rules and not args[i].startswith('--'):
            append_rules = args[i]
            i += 1
        else:
            i += 1
    
    if not append_rules and not remove_rules:
        output({"error": "Rules are required. Usage: aluvia session set-rules <rules> [--browser-session <name>]"}, 1)
    
    if append_rules and remove_rules:
        output({"error": "Cannot both append and remove rules. Use either <rules> or --remove <rules>, not both."}, 1)
    
    session, lock = resolve_session(session_name)
    conn_id = require_connection_id(lock, session)
    api = require_api()
    
    # Fetch current rules
    conn = await api.account.connections.get(conn_id)
    current_rules: List[str] = conn.get("rules", []) if conn else []
    
    new_rules: List[str]
    
    if remove_rules:
        # Remove mode: filter out specified rules
        to_remove = {r.strip() for r in remove_rules.split(',') if r.strip()}
        new_rules = [r for r in current_rules if r not in to_remove]
    else:
        # Append mode: add new rules to existing (deduplicate)
        to_add = [r.strip() for r in append_rules.split(',') if r.strip()]
        existing = set(current_rules)
        new_rules = current_rules + [r for r in to_add if r not in existing]
    
    await api.account.connections.patch(conn_id, {"rules": new_rules})
    
    output({
        "browserSession": session,
        "connectionId": conn_id,
        "rules": new_rules,
        "count": len(new_rules),
    })
