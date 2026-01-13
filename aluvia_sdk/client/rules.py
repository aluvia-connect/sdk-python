"""Hostname matching rules engine."""

from typing import Sequence


def match_pattern(hostname: str, pattern: str) -> bool:
    """
    Match a hostname against a pattern.

    Supported patterns:
    - '*' matches any hostname
    - '*.example.com' matches subdomains of example.com (but not example.com itself)
    - 'example.com' exact match
    - 'google.*' matches google.com, google.co.uk, etc.

    Args:
        hostname: The hostname to match
        pattern: The pattern to match against

    Returns:
        True if hostname matches pattern
    """
    # Normalize inputs to lowercase
    normalized_hostname = hostname.strip().lower()
    normalized_pattern = pattern.strip().lower()

    if not normalized_hostname or not normalized_pattern:
        return False

    # Universal wildcard matches everything
    if normalized_pattern == "*":
        return True

    # Exact match
    if normalized_hostname == normalized_pattern:
        return True

    # Prefix wildcard: *.example.com matches subdomains
    if normalized_pattern.startswith("*."):
        suffix = normalized_pattern[1:]  # '.example.com'
        # Must end with the suffix and have something before it
        if normalized_hostname.endswith(suffix):
            prefix = normalized_hostname[: -len(suffix)]
            # Prefix must not be empty
            return len(prefix) > 0
        return False

    # Suffix wildcard: google.* matches google.com, google.co.uk, etc.
    if normalized_pattern.endswith(".*"):
        prefix = normalized_pattern[:-2]  # 'google'
        # Must start with prefix followed by a dot
        if normalized_hostname.startswith(prefix + "."):
            return True
        return False

    return False


def should_proxy(hostname: str, rules: Sequence[str]) -> bool:
    """
    Determine if a hostname should be proxied based on rules.

    Rules semantics:
    - [] (empty) → no proxy (return False)
    - ['*'] → proxy everything
    - ['example.com'] → proxy only example.com
    - ['*.google.com'] → proxy subdomains of google.com
    - ['*', '-example.com'] → proxy everything except example.com
    - ['AUTO', 'example.com'] → AUTO is placeholder (ignored), proxy example.com

    Negative patterns (prefixed with '-') exclude hosts from proxying.
    If '*' is in rules, default is to proxy unless excluded.
    Without '*', only explicitly matched patterns are proxied.

    Args:
        hostname: The hostname to check
        rules: Sequence of rule patterns

    Returns:
        True if the hostname should be proxied
    """
    normalized_hostname = hostname.strip()
    if not normalized_hostname:
        return False

    # Empty rules means no proxy
    if not rules:
        return False

    # Filter and normalize rules
    normalized_rules = [r.strip() for r in rules if isinstance(r, str) and r.strip()]

    # Filter out AUTO placeholder
    effective_rules = [r for r in normalized_rules if r.upper() != "AUTO"]

    # If no effective rules after filtering, no proxy
    if not effective_rules:
        return False

    # Separate positive and negative rules
    positive_rules = [r for r in effective_rules if not r.startswith("-")]
    negative_rules = [r[1:] for r in effective_rules if r.startswith("-") and len(r) > 1]

    # Check negative rules first (exclusions)
    for neg_pattern in negative_rules:
        if match_pattern(normalized_hostname, neg_pattern):
            return False

    # If '*' is in positive rules, proxy everything (unless excluded above)
    if "*" in positive_rules:
        return True

    # Otherwise, check if hostname matches any positive rule
    for pos_pattern in positive_rules:
        if match_pattern(normalized_hostname, pos_pattern):
            return True

    return False
