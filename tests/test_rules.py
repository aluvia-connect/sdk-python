"""Tests for the rules engine."""

import pytest

from aluvia_sdk.client.rules import match_pattern, should_proxy


class TestMatchPattern:
    """Tests for match_pattern function."""

    def test_universal_wildcard(self) -> None:
        """Test that * matches any hostname."""
        assert match_pattern("example.com", "*")
        assert match_pattern("google.com", "*")
        assert match_pattern("subdomain.example.com", "*")

    def test_exact_match(self) -> None:
        """Test exact hostname matching."""
        assert match_pattern("example.com", "example.com")
        assert not match_pattern("example.com", "google.com")
        assert not match_pattern("sub.example.com", "example.com")

    def test_subdomain_wildcard(self) -> None:
        """Test *.example.com pattern."""
        assert match_pattern("sub.example.com", "*.example.com")
        assert match_pattern("deep.sub.example.com", "*.example.com")
        assert not match_pattern("example.com", "*.example.com")
        assert not match_pattern("exampleXcom", "*.example.com")

    def test_tld_wildcard(self) -> None:
        """Test google.* pattern."""
        assert match_pattern("google.com", "google.*")
        assert match_pattern("google.co.uk", "google.*")
        assert not match_pattern("google", "google.*")
        assert not match_pattern("googlex.com", "google.*")

    def test_case_insensitive(self) -> None:
        """Test that matching is case-insensitive."""
        assert match_pattern("EXAMPLE.COM", "example.com")
        assert match_pattern("example.com", "EXAMPLE.COM")
        assert match_pattern("Sub.Example.Com", "*.example.com")

    def test_empty_inputs(self) -> None:
        """Test empty input handling."""
        assert not match_pattern("", "example.com")
        assert not match_pattern("example.com", "")
        assert not match_pattern("", "")


class TestShouldProxy:
    """Tests for should_proxy function."""

    def test_empty_rules(self) -> None:
        """Test that empty rules mean no proxy."""
        assert not should_proxy("example.com", [])

    def test_universal_proxy(self) -> None:
        """Test that ['*'] proxies everything."""
        assert should_proxy("example.com", ["*"])
        assert should_proxy("google.com", ["*"])

    def test_specific_host(self) -> None:
        """Test specific hostname rules."""
        assert should_proxy("example.com", ["example.com"])
        assert not should_proxy("google.com", ["example.com"])

    def test_negative_rules(self) -> None:
        """Test negative (exclusion) rules."""
        rules = ["*", "-example.com"]
        assert not should_proxy("example.com", rules)
        assert should_proxy("google.com", rules)

    def test_auto_placeholder(self) -> None:
        """Test that AUTO placeholder is ignored."""
        assert should_proxy("example.com", ["AUTO", "example.com"])
        assert not should_proxy("google.com", ["AUTO", "example.com"])
        assert not should_proxy("example.com", ["AUTO"])

    def test_subdomain_rules(self) -> None:
        """Test subdomain wildcard rules."""
        rules = ["*.google.com"]
        assert should_proxy("maps.google.com", rules)
        assert not should_proxy("google.com", rules)

    def test_complex_rules(self) -> None:
        """Test complex rule combinations."""
        rules = ["*", "-api.stripe.com", "-*.internal.com"]
        assert should_proxy("example.com", rules)
        assert not should_proxy("api.stripe.com", rules)
        assert not should_proxy("service.internal.com", rules)
        assert should_proxy("external.com", rules)
