"""Tests for AluviaClient."""

import pytest

from aluvia_sdk import AluviaClient, MissingApiKeyError


class TestAluviaClient:
    """Tests for AluviaClient class."""

    def test_missing_api_key(self) -> None:
        """Test that missing API key raises error."""
        with pytest.raises(MissingApiKeyError):
            AluviaClient(api_key="")

    def test_whitespace_api_key(self) -> None:
        """Test that whitespace-only API key raises error."""
        with pytest.raises(MissingApiKeyError):
            AluviaClient(api_key="   ")

    def test_valid_initialization(self) -> None:
        """Test that valid API key allows initialization."""
        client = AluviaClient(api_key="test-api-key", log_level="silent")
        assert client.api_key == "test-api-key"

    def test_default_options(self) -> None:
        """Test that default options are set correctly."""
        client = AluviaClient(api_key="test-api-key")
        assert client.api_base_url == "https://api.aluvia.io/v1"
        assert client.poll_interval_ms == 5000
        assert client.gateway_protocol == "http"
        assert client.gateway_port == 8080
        assert client.local_proxy is True
        assert client.strict is True

    def test_https_gateway_default_port(self) -> None:
        """Test that HTTPS gateway defaults to port 8443."""
        client = AluviaClient(api_key="test-api-key", gateway_protocol="https")
        assert client.gateway_port == 8443

    def test_custom_options(self) -> None:
        """Test that custom options are respected."""
        client = AluviaClient(
            api_key="test-api-key",
            api_base_url="https://custom.api",
            poll_interval_ms=10000,
            gateway_port=9090,
            local_proxy=False,
        )
        assert client.api_base_url == "https://custom.api"
        assert client.poll_interval_ms == 10000
        assert client.gateway_port == 9090
        assert client.local_proxy is False

    def test_has_api_wrapper(self) -> None:
        """Test that client has API wrapper."""
        client = AluviaClient(api_key="test-api-key")
        assert hasattr(client, "api")
        assert hasattr(client.api, "account")
        assert hasattr(client.api, "geos")
