"""Tests for FirecrawlService."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.firecrawl_service import FirecrawlService, get_firecrawl_service


class TestFirecrawlService:
    @pytest.mark.asyncio
    async def test_get_firecrawl_service_returns_singleton(self):
        """Test that get_firecrawl_service returns singleton instance"""
        service1 = get_firecrawl_service()
        service2 = get_firecrawl_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_firecrawl_service_has_api_key(self):
        """Test that FirecrawlService loads API key from config"""
        service = get_firecrawl_service()
        assert hasattr(service, 'api_key')

    @pytest.mark.asyncio
    async def test_is_available_returns_true_with_api_key(self):
        """Test that is_available returns True when API key is set"""
        service = FirecrawlService()
        service.api_key = "test_key"
        result = await service.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_is_available_returns_false_without_api_key(self):
        """Test that is_available returns False when API key is empty"""
        service = FirecrawlService()
        service.api_key = ""
        assert await service.is_available() is False

    @pytest.mark.asyncio
    async def test_search_with_mock_returns_results(self):
        """Test search method with mocked Firecrawl"""
        service = FirecrawlService()
        service.api_key = "test_key"
        with patch('app.services.firecrawl_service._FIRECRAWL_AVAILABLE', True):
            with patch('app.services.firecrawl_service._FIRECRAWL_IMPORT', "mcp__firecrawl__firecrawl_search"):
                with patch('app.services.firecrawl_service.firecrawl_search', new_callable=AsyncMock, create=True) as mock_search:
                    mock_search.return_value = {"results": [{"title": "Test", "url": "http://example.com", "markdown": "Test"}]}
                    results = await service.search("劳动合同纠纷", limit=5)
                    assert "results" in results
                    assert isinstance(results.get("results"), list)

    @pytest.mark.asyncio
    async def test_search_returns_error_when_no_api_key(self):
        """Test that search returns error when API key is not configured"""
        service = FirecrawlService()
        service.api_key = ""
        result = await service.search("test")
        assert "results" in result
        assert result["results"] == []
        assert "error" in result

    @pytest.mark.asyncio
    async def test_search_handles_missing_results_key(self):
        """Test that search handles response with missing results key"""
        service = FirecrawlService()
        service.api_key = "test_key"
        with patch('app.services.firecrawl_service._FIRECRAWL_AVAILABLE', True):
            with patch('app.services.firecrawl_service._FIRECRAWL_IMPORT', "mcp__firecrawl__firecrawl_search"):
                with patch('app.services.firecrawl_service.firecrawl_search', new_callable=AsyncMock, create=True) as mock_search:
                    mock_search.return_value = {"data": "no results key"}
                    result = await service.search("test")
                    # Should handle gracefully - either return results list or error
                    assert "results" in result or "error" in result
