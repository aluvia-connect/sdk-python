"""
Geos command handler for CLI.
"""
from .api_helpers import require_api
from .cli import output


async def handle_geos() -> None:
    """Handle geos command."""
    api = require_api()
    geos = await api.geos.list()
    output({"geos": geos, "count": len(geos)})
