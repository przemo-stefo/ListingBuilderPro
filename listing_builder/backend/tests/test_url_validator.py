# backend/tests/test_url_validator.py
# Purpose: SSRF protection tests — domain allowlist, private IP rejection
# NOT for: Business logic tests

import pytest
from unittest.mock import patch
from utils.url_validator import (
    validate_marketplace_url,
    validate_webhook_url,
    _reject_private_host,
)


class TestValidateMarketplaceUrl:

    def test_valid_amazon_url(self):
        url = "https://www.amazon.de/dp/B08TEST123"
        assert validate_marketplace_url(url, "amazon") == url

    def test_valid_allegro_url(self):
        url = "https://allegro.pl/oferta/test-123"
        assert validate_marketplace_url(url, "allegro") == url

    def test_valid_ebay_url(self):
        url = "https://www.ebay.de/itm/123456"
        assert validate_marketplace_url(url, "ebay") == url

    def test_valid_kaufland_url(self):
        url = "https://www.kaufland.de/product/123"
        assert validate_marketplace_url(url, "kaufland") == url

    def test_wrong_marketplace_domain_rejected(self):
        with pytest.raises(ValueError, match="not a valid amazon"):
            validate_marketplace_url("https://allegro.pl/test", "amazon")

    def test_unknown_domain_rejected(self):
        with pytest.raises(ValueError, match="not a recognized"):
            validate_marketplace_url("https://evil.com/test")

    def test_empty_url_rejected(self):
        with pytest.raises(ValueError, match="URL is required"):
            validate_marketplace_url("")

    def test_invalid_scheme_rejected(self):
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            validate_marketplace_url("ftp://amazon.de/test", "amazon")

    def test_no_hostname_rejected(self):
        with pytest.raises(ValueError, match="no hostname"):
            validate_marketplace_url("https://", "amazon")


class TestRejectPrivateHost:

    def test_localhost_rejected(self):
        with pytest.raises(ValueError, match="Internal/private"):
            _reject_private_host("localhost")

    def test_127_0_0_1_rejected(self):
        with pytest.raises(ValueError, match="Internal/private"):
            _reject_private_host("127.0.0.1")

    def test_ipv6_loopback_rejected(self):
        with pytest.raises(ValueError, match="Internal/private"):
            _reject_private_host("::1")

    @patch("utils.url_validator.socket.getaddrinfo")
    def test_private_ip_resolution_rejected(self, mock_dns):
        mock_dns.return_value = [
            (2, 1, 0, "", ("192.168.1.1", 0))
        ]
        with pytest.raises(ValueError, match="private/internal IP"):
            _reject_private_host("internal.corp")

    @patch("utils.url_validator.socket.getaddrinfo")
    def test_dns_failure_rejected(self, mock_dns):
        import socket
        mock_dns.side_effect = socket.gaierror("DNS failed")
        with pytest.raises(ValueError, match="Cannot resolve"):
            _reject_private_host("nonexistent.invalid")


class TestValidateWebhookUrl:

    def test_valid_https_url(self):
        url = "https://hooks.example.com/webhook"
        with patch("utils.url_validator._reject_private_host"):
            assert validate_webhook_url(url) == url

    def test_http_rejected(self):
        with pytest.raises(ValueError, match="must use HTTPS"):
            validate_webhook_url("http://hooks.example.com/webhook")

    def test_empty_url_rejected(self):
        with pytest.raises(ValueError, match="required"):
            validate_webhook_url("")
