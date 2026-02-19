"""
Session open handler for CLI.
"""
import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from ..session.lock import (
    write_lock, read_lock, remove_lock, is_process_alive, 
    get_log_file_path, generate_session_name, validate_session_name
)
from ..client.aluvia_client import AluviaClient
from ..client.block_detection import BlockDetectionConfig
from .cli import output


@dataclass
class OpenOptions:
    """Options for opening a browser session."""
    url: str
    connection_id: Optional[int] = None
    headless: bool = True
    session_name: Optional[str] = None
    auto_unblock: bool = False
    disable_block_detection: bool = False
    run: Optional[str] = None


async def handle_open(opts: OpenOptions) -> None:
    """
    Handle opening a browser session in a detached daemon process.
    Spawns the daemon and polls until it's ready.
    """
    # Generate session name if not provided
    session = opts.session_name or generate_session_name()
    
    # Validate session name early
    if opts.session_name and not validate_session_name(opts.session_name):
        output({"error": "Invalid session name. Use only letters, numbers, hyphens, and underscores."}, 1)
    
    # Check for existing instance with this session name
    existing = read_lock(session)
    if existing and is_process_alive(existing["pid"]):
        output({
            "error": f"A browser session named '{session}' is already running.",
            "browserSession": session,
            "startUrl": existing.get("url"),
            "cdpUrl": existing.get("cdpUrl"),
            "connectionId": existing.get("connectionId"),
            "pid": existing["pid"],
        }, 1)
    
    # Clean up stale lock if process is dead
    if existing:
        remove_lock(session)
    
    # Require API key
    api_key = os.environ.get("ALUVIA_API_KEY", "").strip()
    if not api_key:
        output({"error": "ALUVIA_API_KEY environment variable is required."}, 1)
    
    # Spawn a detached child process that runs the daemon
    log_file = get_log_file_path(session)
    
    # Use pythonw.exe on Windows to avoid console window
    python_exe = sys.executable
    if os.name == 'nt' and python_exe.lower().endswith('python.exe'):
        pythonw_exe = python_exe[:-10] + 'pythonw.exe'
        if os.path.exists(pythonw_exe):
            python_exe = pythonw_exe
    
    # Build command arguments
    args = [python_exe, "-m", "aluvia_sdk.bin.cli", "--daemon", opts.url, "--browser-session", session]
    if opts.connection_id is not None:
        args.extend(["--connection-id", str(opts.connection_id)])
    if not opts.headless:
        args.append("--headful")
    if opts.auto_unblock:
        args.append("--auto-unblock")
    if opts.disable_block_detection:
        args.append("--disable-block-detection")
    if opts.run:
        args.extend(["--run", opts.run])
    
    # Spawn the daemon process
    try:
        with open(log_file, 'a') as log_fh:
            if os.name == 'nt':  # Windows
                # Windows flags to run daemon silently without visible console
                # CREATE_NEW_PROCESS_GROUP = 0x00000200
                # DETACHED_PROCESS = 0x00000008
                # CREATE_NO_WINDOW = 0x08000000 (prevents console window from appearing)
                process = subprocess.Popen(
                    args,
                    stdout=log_fh,
                    stderr=log_fh,
                    stdin=subprocess.DEVNULL,
                    creationflags=0x08000000 | 0x00000200 | 0x00000008,
                    env={**os.environ, "ALUVIA_API_KEY": api_key},
                )
            else:  # Unix/Linux/Mac
                process = subprocess.Popen(
                    args,
                    stdout=log_fh,
                    stderr=log_fh,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    env={**os.environ, "ALUVIA_API_KEY": api_key},
                )
    except Exception as err:
        output({"browserSession": session, "error": f"Failed to spawn browser process: {str(err)}"}, 1)
    
    # Wait for the daemon to be fully ready (lock file with ready: true)
    attempts = 0
    max_attempts = 240  # 60 seconds max
    
    while attempts < max_attempts:
        await asyncio.sleep(0.25)
        attempts += 1
        
        # Early exit if daemon process died
        if process.pid and not is_process_alive(process.pid):
            remove_lock(session)
            output({
                "browserSession": session,
                "error": "Browser process exited unexpectedly.",
                "logFile": str(log_file),
            }, 1)
        
        lock = read_lock(session)
        if lock and lock.get("ready"):
            output({
                "browserSession": session,
                "pid": lock["pid"],
                "startUrl": lock.get("url"),
                "cdpUrl": lock.get("cdpUrl"),
                "connectionId": lock.get("connectionId"),
                "blockDetection": lock.get("blockDetection", False),
                "autoUnblock": lock.get("autoUnblock", False),
            })
    
    # Timeout reached
    alive = process.pid and is_process_alive(process.pid)
    output({
        "browserSession": session,
        "error": "Browser is still initializing (timeout)." if alive else "Browser process exited unexpectedly.",
        "logFile": str(log_file),
    }, 1)


async def handle_open_daemon(opts: OpenOptions) -> None:
    """
    Daemon entry point — runs in the detached child process.
    Starts the proxy + browser, writes lock, and stays alive.
    """
    print("[daemon] Starting daemon...", flush=True)
    
    api_key = os.environ.get("ALUVIA_API_KEY", "").strip()
    if not api_key:
        print("[daemon] ERROR: ALUVIA_API_KEY not set", flush=True)
        sys.exit(1)
    
    session_name = opts.session_name
    block_detection_enabled = not opts.disable_block_detection
    
    print(f"[daemon] Session name: {session_name}, URL: {opts.url}", flush=True)
    
    # Create callback for block detection updates
    async def update_lock_with_detection(result, page):
        """Callback to update lock file with detection results"""
        lock = read_lock(session_name)
        if not lock:
            return
        last_detection = {
            "hostname": result.hostname,
            "lastUrl": result.url,
            "blockStatus": result.block_status,
            "score": result.score,
            "signals": [{"name": s.name, "weight": s.weight, "details": s.details} for s in result.signals],
            "pass": result.pass_type,
            "persistentBlock": result.persistent_block,
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
        }
        write_lock({**lock, "lastDetection": last_detection}, session_name)
    
    # Configure block detection
    block_detection_config = None
    if block_detection_enabled:
        block_detection_config = BlockDetectionConfig(
            enabled=True,
            auto_unblock=opts.auto_unblock,
            on_detection=update_lock_with_detection,
        )
    else:
        block_detection_config = BlockDetectionConfig(enabled=False)
    
    # Create client and start
    playwright_options = {"headless": opts.headless}
    
    client_config = {
        "api_key": api_key,
        "start_playwright": True,
        "playwright_options": playwright_options,
        "block_detection": block_detection_config,
    }
    if opts.connection_id is not None:
        client_config["connection_id"] = opts.connection_id
    
    try:
        client = AluviaClient(**client_config)
        
        # Write early lock so parent knows daemon is alive
        write_lock({
            "pid": os.getpid(),
            "session": session_name,
            "url": opts.url,
            "blockDetection": block_detection_enabled,
            "autoUnblock": block_detection_enabled and opts.auto_unblock,
        }, session_name)
        
        connection = await client.start()
        
        if opts.auto_unblock:
            print("[daemon] Auto-unblock enabled", flush=True)
        print(f"[daemon] Browser initialized — proxy: {connection.url}", flush=True)
        
        # Get CDP URL from connection object
        cdp_url = getattr(connection, 'cdp_url', "")
        if cdp_url:
            print(f"[daemon] CDP URL: {cdp_url}", flush=True)
        else:
            print("[daemon] Warning: CDP URL not available", flush=True)
        
        if opts.connection_id is not None:
            print(f"[daemon] Connection ID: {opts.connection_id}", flush=True)
        if session_name:
            print(f"[daemon] Session: {session_name}", flush=True)
        print(f"[daemon] Opening {opts.url}", flush=True)
        
        # Get browser context (create new one from browser)
        browser_context = None
        if connection.browser:
            contexts = connection.browser.contexts
            if contexts:
                browser_context = contexts[0]
            else:
                browser_context = await connection.browser.new_context()
        
        if not browser_context:
            print("[daemon] ERROR: No browser context available", flush=True)
            remove_lock(session_name)
            sys.exit(1)
        
        page = await browser_context.new_page()
        await page.goto(opts.url, wait_until="domcontentloaded")
        
        # Gather session info
        page_title = await page.title()
        
        # Get CDP URL from connection object (set by AluviaClient)
        cdp_url = getattr(connection, 'cdp_url', "")
        
        # Get connection ID
        conn_id = opts.connection_id
        if not conn_id:
            # Try to get it from config_manager
            if hasattr(client, "config_manager") and hasattr(client.config_manager, "connection_id"):
                conn_id = client.config_manager.connection_id
            elif hasattr(client, "connection_id"):
                conn_id = client.connection_id
        
        # Write lock file with full session metadata (marks session as ready)
        existing_lock = read_lock(session_name)
        write_lock({
            "pid": os.getpid(),
            "session": session_name,
            "connectionId": conn_id,
            "cdpUrl": cdp_url,
            "proxyUrl": connection.url,
            "url": opts.url,
            "ready": True,
            "blockDetection": block_detection_enabled,
            "autoUnblock": block_detection_enabled and opts.auto_unblock,
            "lastDetection": existing_lock.get("lastDetection") if existing_lock else None,
        }, session_name)
        
        print(f"[daemon] Session ready — session: {session_name or 'default'}, url: {opts.url}, cdpUrl: {cdp_url}, connectionId: {conn_id or 'unknown'}, pid: {os.getpid()}", flush=True)
        if page_title:
            print(f"[daemon] Page title: {page_title}", flush=True)
        
        # If --run was provided, execute the script and then shut down
        if opts.run:
            script_path = Path(opts.run).resolve()
            if not script_path.exists():
                print(f"[daemon] Script not found: {script_path}")
                remove_lock(session_name)
                await connection.close()
                sys.exit(1)
            
            print(f"[daemon] Running script: {script_path}")
            
            # Execute the script (basic implementation - can be enhanced)
            exit_code = 0
            try:
                # Load and execute the script with injected variables
                import runpy
                script_globals = {
                    "page": page,
                    "browser": connection.browser,
                    "context": connection.browser_context,
                }
                runpy.run_path(str(script_path), init_globals=script_globals)
            except Exception as err:
                print(f"[daemon] Script error: {err}")
                import traceback
                traceback.print_exc()
                exit_code = 1
            
            print("[daemon] Script finished.")
            remove_lock(session_name)
            await connection.close()
            sys.exit(exit_code)
        
        # Keep daemon alive until interrupted
        print("[daemon] Daemon running. Press Ctrl+C to stop.")
        
        # Graceful shutdown handler
        stopping = False
        
        async def shutdown():
            nonlocal stopping
            if stopping:
                return
            stopping = True
            print("[daemon] Shutting down...")
            try:
                await connection.close()
            except Exception:
                pass
            remove_lock(session_name)
            print("[daemon] Stopped.")
            sys.exit(0)
        
        # Setup signal handlers
        import signal
        loop = asyncio.get_event_loop()
        
        if os.name != 'nt':  # Unix/Linux/Mac only
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        
        # Wait indefinitely
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            await shutdown()
    
    except Exception as err:
        print(f"[daemon] ERROR: {err}")
        import traceback
        traceback.print_exc()
        remove_lock(session_name)
        sys.exit(1)
