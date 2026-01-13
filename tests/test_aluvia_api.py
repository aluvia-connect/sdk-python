"""Tests for AluviaApi."""

import pytest

from aluvia_sdk import AluviaApi, MissingApiKeyError


class TestAluviaApi:
    """Tests for AluviaApi class."""

    def test_missing_api_key(self) -> None:
        """Test that missing API key raises error."""
        with pytest.raises(MissingApiKeyError):
            AluviaApi(api_key="")

    def test_whitespace_api_key(self) -> None:
        """Test that whitespace-only API key raises error."""
        with pytest.raises(MissingApiKeyError):
            AluviaApi(api_key="   ")

    def test_valid_initialization(self) -> None:
        """Test that valid API key allows initialization."""
        api = AluviaApi(api_key="test-api-key")
        assert api.api_key == "test-api-key"
        assert api.api_base_url == "https://api.aluvia.io/v1"

    def test_custom_base_url(self) -> None:
        """Test custom base URL."""
        api = AluviaApi(api_key="test-api-key", api_base_url="https://custom.api")
        assert api.api_base_url == "https://custom.api"

    def test_has_account_namespace(self) -> None:
        """Test that account namespace exists."""
        api = AluviaApi(api_key="test-api-key")
        assert hasattr(api, "account")
        assert hasattr(api.account, "get")
        assert hasattr(api.account, "connections")

    def test_has_geos_namespace(self) -> None:
        """Test that geos namespace exists."""
        api = AluviaApi(api_key="test-api-key")
        assert hasattr(api, "geos")
        assert hasattr(api.geos, "list")
