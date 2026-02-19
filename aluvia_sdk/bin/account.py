"""
Account command handlers for CLI.
"""
from typing import List, Optional
from .api_helpers import require_api
from .cli import output


async def handle_account(args: List[str]) -> None:
    """Handle account commands."""
    subcommand = args[0] if args else None
    
    if not subcommand:
        api = require_api()
        account = await api.account.get()
        output({"account": account})
    
    if subcommand == "usage":
        start: Optional[str] = None
        end: Optional[str] = None
        
        i = 1
        while i < len(args):
            if args[i] == "--start" and i + 1 < len(args):
                start = args[i + 1]
                i += 2
            elif args[i] == "--end" and i + 1 < len(args):
                end = args[i + 1]
                i += 2
            else:
                i += 1
        
        api = require_api()
        usage = await api.account.usage(start=start, end=end)
        output({"usage": usage})
    
    output({"error": f"Unknown account subcommand: '{subcommand}'."}, 1)
