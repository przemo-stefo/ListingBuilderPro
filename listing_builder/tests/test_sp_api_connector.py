# location: /Users/shawn/Projects/ListingBuilderPro/listing_builder/tests/test_sp_api_connector.py
# Purpose: Comprehensive test suite for Amazon SP-API Connector - TDD Red Phase
# NOT for: Implementation code - only tests that must fail first

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from typing import Dict, Any

# These imports will fail initially - that's expected in RED phase
from amazon_sp_api_connector import (
    AmazonSPAPIConnector,
    AuthenticationError,
    RateLimitError,
    APIError,
    InvalidCredentialsError,
    TokenExpiredError
)


class TestAuthentication:
    """Test suite for Amazon SP-API authentication - all tests must fail initially"""

    def test_successful_authentication(self):
        """Test successful IAM authentication flow - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )

        # Act
        result = connector.authenticate()

        # Assert - These will fail until implementation exists
        assert result is not None
        assert result['access_token'] is not None
        assert result['expires_in'] > 0
        assert connector.is_authenticated() is True

    def test_expired_credentials_refresh(self):
        """Test automatic refresh of expired credentials - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )

        # Simulate expired token
        connector._token_expires_at = datetime.utcnow() - timedelta(minutes=1)

        # Act - Should auto-refresh
        result = connector.ensure_authenticated()

        # Assert
        assert connector.is_authenticated() is True
        assert connector._token_expires_at > datetime.utcnow()

    def test_invalid_credentials_handling(self):
        """Test proper error handling for invalid credentials - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="INVALID_KEY",
            secret_key="INVALID_SECRET",
            region="us-east-1"
        )

        # Act & Assert - Should raise specific error
        with pytest.raises(InvalidCredentialsError) as exc_info:
            connector.authenticate()

        assert "Invalid AWS credentials" in str(exc_info.value)
        assert connector.is_authenticated() is False

    def test_signature_generation(self):
        """Test SigV4 signature generation correctness - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )

        request_params = {
            "method": "GET",
            "url": "https://sellingpartnerapi-na.amazon.com/catalog/items",
            "headers": {
                "host": "sellingpartnerapi-na.amazon.com",
                "x-amz-date": "20240120T120000Z"
            },
            "params": {"marketplaceIds": "ATVPDKIKX0DER"}
        }

        # Act
        signature = connector.generate_signature(request_params)

        # Assert
        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest length
        assert signature.isalnum()  # Only alphanumeric characters

    def test_multiple_marketplace_support(self):
        """Test authentication across different marketplaces - MUST FAIL INITIALLY"""
        # Arrange
        marketplaces = {
            "US": "ATVPDKIKX0DER",
            "UK": "A1F83G8C2ARO7P",
            "DE": "A1PA6795UKMFR9"
        }

        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )

        # Act & Assert
        for country, marketplace_id in marketplaces.items():
            result = connector.authenticate(marketplace_id=marketplace_id)
            assert result['marketplace_id'] == marketplace_id
            assert connector.is_authenticated() is True


class TestInventoryFetching:
    """Test suite for inventory data fetching - all tests must fail initially"""

    def test_single_page_inventory(self):
        """Test fetching inventory that fits in one page - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Act
        inventory = connector.get_inventory()

        # Assert
        assert inventory is not None
        assert 'items' in inventory
        assert len(inventory['items']) > 0
        assert inventory['items'][0]['sku'] is not None
        assert inventory['items'][0]['quantity'] >= 0
        assert inventory['next_token'] is None  # No pagination needed

    def test_paginated_inventory(self):
        """Test handling of paginated inventory responses - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Act - Get all pages
        all_items = []
        next_token = None
        page_count = 0

        while page_count < 10:  # Safety limit
            inventory = connector.get_inventory(next_token=next_token)
            all_items.extend(inventory['items'])
            next_token = inventory.get('next_token')
            page_count += 1

            if not next_token:
                break

        # Assert
        assert len(all_items) > 50  # Assuming we have >50 items requiring pagination
        assert page_count > 1  # Multiple pages were fetched

    def test_empty_inventory_handling(self):
        """Test behavior with no inventory items - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Act - Filter by non-existent SKU
        inventory = connector.get_inventory(sku_filter=["NON_EXISTENT_SKU"])

        # Assert
        assert inventory is not None
        assert inventory['items'] == []
        assert inventory['next_token'] is None
        assert inventory['total_count'] == 0

    def test_inventory_data_transformation(self):
        """Test transformation to unified schema - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Act
        raw_inventory = connector.get_inventory(raw=True)
        transformed_inventory = connector.transform_inventory(raw_inventory)

        # Assert unified schema
        for item in transformed_inventory['items']:
            assert 'id' in item  # Unified ID
            assert 'sku' in item
            assert 'title' in item
            assert 'quantity_available' in item
            assert 'quantity_reserved' in item
            assert 'quantity_inbound' in item
            assert 'marketplace' in item
            assert 'last_updated' in item
            assert item['last_updated'].endswith('Z')  # UTC format


class TestBuyBoxMonitoring:
    """Test suite for Buy Box status monitoring - all tests must fail initially"""

    def test_buy_box_winner_detection(self):
        """Test detection of Buy Box ownership - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        asins = ["B08N5WRWNB", "B07XQR8JL7", "B09MT3HFM9"]

        # Act
        buy_box_status = connector.get_buy_box_status(asins)

        # Assert
        assert len(buy_box_status) == len(asins)
        for asin in asins:
            assert asin in buy_box_status
            status = buy_box_status[asin]
            assert 'is_winner' in status
            assert 'competitor_price' in status
            assert 'our_price' in status
            assert isinstance(status['is_winner'], bool)

    def test_buy_box_percentage_calculation(self):
        """Test Buy Box win percentage calculation - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Act
        stats = connector.get_buy_box_statistics(
            asin="B08N5WRWNB",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )

        # Assert
        assert 'win_percentage' in stats
        assert 0 <= stats['win_percentage'] <= 100
        assert 'total_time_hours' in stats
        assert 'winning_time_hours' in stats
        assert stats['winning_time_hours'] <= stats['total_time_hours']

    def test_no_buy_box_eligibility(self):
        """Test products without Buy Box eligibility - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Act - Product in restricted category
        status = connector.get_buy_box_status(["RESTRICTED_ASIN_123"])

        # Assert
        assert status["RESTRICTED_ASIN_123"]['is_eligible'] is False
        assert status["RESTRICTED_ASIN_123"]['reason'] == "Category not eligible"
        assert status["RESTRICTED_ASIN_123"]['is_winner'] is None


class TestRateLimiting:
    """Test suite for rate limiting and throttling - all tests must fail initially"""

    def test_respect_rate_limits(self):
        """Test that connector respects API rate limits - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            rate_limit_per_second=2  # 2 requests per second max
        )
        connector.authenticate()

        # Act - Try to make 5 rapid requests
        request_times = []
        for i in range(5):
            start = datetime.utcnow()
            connector.get_inventory(limit=1)
            request_times.append(datetime.utcnow() - start)

        # Assert - Should have delays between requests
        total_time = sum([t.total_seconds() for t in request_times])
        assert total_time >= 2.0  # Should take at least 2 seconds for 5 requests at 2/sec

    def test_exponential_backoff(self):
        """Test exponential backoff on 429 responses - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Track retry delays
        retry_delays = []

        def mock_request_with_429(*args, **kwargs):
            retry_delays.append(connector._current_backoff_seconds)
            if len(retry_delays) < 3:
                raise RateLimitError("Too Many Requests", retry_after=1)
            return {"items": []}

        # Act
        with patch.object(connector, '_make_request', mock_request_with_429):
            result = connector.get_inventory()

        # Assert - Backoff should increase exponentially
        assert len(retry_delays) >= 2
        assert retry_delays[1] > retry_delays[0]  # Exponential increase
        assert retry_delays[1] >= retry_delays[0] * 2  # At least double
        assert result is not None  # Eventually succeeded

    def test_request_queuing(self):
        """Test request queuing when approaching limits - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            queue_requests=True,
            rate_limit_per_second=2
        )
        connector.authenticate()

        # Act - Submit 10 requests
        requests = []
        for i in range(10):
            req = connector.get_inventory_async(limit=1)  # Non-blocking
            requests.append(req)

        # Wait for all to complete
        results = connector.wait_for_all(requests)

        # Assert
        assert len(results) == 10
        assert all(r is not None for r in results)
        assert connector.get_queue_size() == 0  # Queue should be empty

    def test_quota_tracking(self):
        """Test accurate quota usage tracking - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            daily_quota=1000
        )
        connector.authenticate()

        # Act - Make several requests
        for i in range(5):
            connector.get_inventory(limit=10)

        # Assert
        quota_status = connector.get_quota_status()
        assert quota_status['used'] == 5
        assert quota_status['remaining'] == 995
        assert quota_status['reset_time'] is not None
        assert quota_status['percentage_used'] == 0.5


class TestCaching:
    """Test suite for response caching - all tests must fail initially"""

    def test_cache_hit(self):
        """Test returning cached data when available - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            cache_ttl=300  # 5 minutes
        )
        connector.authenticate()

        # Act - First request (cache miss)
        result1 = connector.get_inventory(limit=10)
        cache_stats1 = connector.get_cache_stats()

        # Second request (should be cache hit)
        result2 = connector.get_inventory(limit=10)
        cache_stats2 = connector.get_cache_stats()

        # Assert
        assert result1 == result2  # Same data returned
        assert cache_stats1['hits'] == 0
        assert cache_stats1['misses'] == 1
        assert cache_stats2['hits'] == 1
        assert cache_stats2['misses'] == 1

    def test_cache_expiration(self):
        """Test cache TTL expiration - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            cache_ttl=1  # 1 second TTL for testing
        )
        connector.authenticate()

        # Act
        result1 = connector.get_inventory(limit=10)

        # Wait for cache to expire
        import time
        time.sleep(1.5)

        result2 = connector.get_inventory(limit=10)
        cache_stats = connector.get_cache_stats()

        # Assert
        assert cache_stats['hits'] == 0  # No hits because cache expired
        assert cache_stats['misses'] == 2  # Both requests were misses

    def test_cache_invalidation(self):
        """Test manual cache invalidation - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            cache_ttl=300
        )
        connector.authenticate()

        # Act
        result1 = connector.get_inventory(limit=10)
        connector.invalidate_cache()  # Manual invalidation
        result2 = connector.get_inventory(limit=10)
        cache_stats = connector.get_cache_stats()

        # Assert
        assert cache_stats['hits'] == 0  # No hits after invalidation
        assert cache_stats['misses'] == 2  # Both were misses
        assert cache_stats['invalidations'] == 1


class TestDataTransformation:
    """Test suite for data transformation to unified schema - all tests must fail initially"""

    def test_transform_inventory_to_unified_schema(self):
        """Test inventory data transformation - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )

        raw_amazon_data = {
            "inventorySummaries": [{
                "asin": "B08N5WRWNB",
                "fnSku": "SKU-TEST-001",
                "sellerSku": "MY-SKU-001",
                "condition": "NewItem",
                "inventoryDetails": {
                    "fulfillableQuantity": 150,
                    "reservedQuantity": {
                        "totalReservedQuantity": 5
                    }
                }
            }]
        }

        # Act
        unified_data = connector.transform_to_unified_schema(
            raw_amazon_data,
            source="amazon",
            data_type="inventory"
        )

        # Assert unified schema structure
        assert 'metadata' in unified_data
        assert unified_data['metadata']['source'] == 'amazon'
        assert unified_data['metadata']['timestamp'] is not None

        assert 'data' in unified_data
        assert len(unified_data['data']) == 1

        item = unified_data['data'][0]
        assert item['id'] == 'amazon_MY-SKU-001'  # Prefixed ID
        assert item['sku'] == 'MY-SKU-001'
        assert item['external_id'] == 'B08N5WRWNB'  # ASIN
        assert item['quantity']['available'] == 150
        assert item['quantity']['reserved'] == 5
        assert item['quantity']['total'] == 155

    def test_handle_missing_fields_gracefully(self):
        """Test handling of missing/null fields - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )

        incomplete_data = {
            "inventorySummaries": [{
                "sellerSku": "MY-SKU-002",
                # Missing: asin, fnSku, inventoryDetails
            }]
        }

        # Act
        unified_data = connector.transform_to_unified_schema(
            incomplete_data,
            source="amazon",
            data_type="inventory"
        )

        # Assert - Should handle missing fields with defaults
        item = unified_data['data'][0]
        assert item['sku'] == 'MY-SKU-002'
        assert item['external_id'] is None  # Missing ASIN
        assert item['quantity']['available'] == 0  # Default value
        assert item['quantity']['reserved'] == 0  # Default value


class TestErrorHandling:
    """Test suite for error handling scenarios - all tests must fail initially"""

    def test_network_timeout_handling(self):
        """Test handling of network timeouts - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            request_timeout=1,  # 1 second timeout
            max_retries=3
        )
        connector.authenticate()

        # Act - Should retry on timeout
        with patch('requests.get', side_effect=TimeoutError("Connection timeout")):
            with pytest.raises(APIError) as exc_info:
                connector.get_inventory()

        # Assert
        assert "timeout" in str(exc_info.value).lower()
        assert connector.get_retry_count() == 3  # Tried max retries

    def test_malformed_json_response(self):
        """Test handling of malformed JSON responses - MUST FAIL INITIALLY"""
        # Arrange
        connector = AmazonSPAPIConnector(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1"
        )
        connector.authenticate()

        # Act
        with patch('requests.get') as mock_get:
            mock_get.return_value.text = "Not valid JSON{{"
            mock_get.return_value.status_code = 200

            result = connector.get_inventory(use_cache_on_error=True)

        # Assert
        assert result is not None  # Should return cached or empty result
        assert connector.get_last_error() is not None
        assert "JSON" in connector.get_last_error()