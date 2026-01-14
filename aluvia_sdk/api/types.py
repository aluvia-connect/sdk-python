"""Type definitions for the API layer."""

from typing import Any, List, Literal, Optional, TypedDict, Union


class SuccessEnvelope(TypedDict):
    """Success response envelope."""

    success: Literal[True]
    data: Any


class ErrorDetail(TypedDict, total=False):
    """Error detail structure."""

    code: str
    message: str
    details: Any


class ErrorEnvelope(TypedDict):
    """Error response envelope."""

    success: Literal[False]
    error: ErrorDetail


class Account(TypedDict, total=False):
    """Account information."""

    balance_gb: float
    # Additional fields as per API


class AccountUsage(TypedDict, total=False):
    """Account usage information."""

    pass  # Additional fields as per API


class AccountPayment(TypedDict, total=False):
    """Account payment information."""

    pass  # Additional fields as per API


class AccountConnection(TypedDict, total=False):
    """Account connection configuration."""

    id: Union[str, int]
    connection_id: Union[str, int]
    proxy_username: str
    proxy_password: str
    rules: List[str]
    session_id: Optional[str]
    target_geo: Optional[str]


class AccountConnectionDeleteResult(TypedDict):
    """Result of deleting a connection."""

    connection_id: str
    deleted: bool


class Geo(TypedDict, total=False):
    """Geographic targeting option."""

    code: str
    name: str
    # Additional fields as per API
