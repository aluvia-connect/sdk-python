"""Aluvia SDK for Python - local smart proxy for automation workloads and AI agents."""

from aluvia_sdk.api.aluvia_api import AluviaApi
from aluvia_sdk.client.aluvia_client import AluviaClient
from aluvia_sdk.client.block_detection import (
    BlockDetection,
    BlockDetectionConfig,
    BlockDetectionResult,
    DetectionSignal,
)
from aluvia_sdk.connect import connect
from aluvia_sdk.errors import (
    ApiError,
    ConnectError,
    InvalidApiKeyError,
    MissingApiKeyError,
    ProxyStartError,
)

__version__ = "1.0.0"

__all__ = [
    "AluviaClient",
    "AluviaApi",
    "connect",
    "BlockDetection",
    "BlockDetectionConfig",
    "BlockDetectionResult",
    "DetectionSignal",
    "MissingApiKeyError",
    "InvalidApiKeyError",
    "ApiError",
    "ProxyStartError",
    "ConnectError",
]
