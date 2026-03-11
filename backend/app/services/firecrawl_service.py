"""Firecrawl service for web search and scraping.

This service wraps Firecrawl MCP tools for searching legal cases and court decisions from the web.
"""
import logging
from typing import Dict, Any, Optional, List
from app.config import get_settings

logger = logging.getLogger(__name__)

# Try different import paths for Firecrawl MCP
_FIRECRAWL_AVAILABLE = False
_FIRECRAWL_IMPORT = None

try:
    from mcp__firecrawl__firecrawl_search import firecrawl_search
    _FIRECRAWL_AVAILABLE = True
    _FIRECRAWL_IMPORT = "mcp__firecrawl__firecrawl_search"
except ImportError:
    try:
        from mcp__firecrawl import firecrawl_search
        _FIRECRAWL_AVAILABLE = True
        _FIRECRAWL_IMPORT = "mcp__firecrawl"
    except ImportError:
        logger.warning("Firecrawl MCP not available - case search will be mocked")


class FirecrawlService:
    """Service for Firecrawl API integration.

    This service provides methods to search the web for legal cases using the Firecrawl MCP tool.
    """

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.firecrawl_api_key

    async def search(self, query: str, limit: int = 5, scrape_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform web search using Firecrawl.

        Args:
            query: Search query string
            limit: Maximum number of results to return (default 5)
            scrape_options: Optional scraping configuration

        Returns:
            Dictionary containing:
                - results: List of search results with title, url, and content
                - error: Error message if search failed (optional)
        """
        if not self.api_key:
            logger.warning("FIRECRAWL_API_KEY not configured")
            return {"results": [], "error": "FIRECRAWL_API_KEY not configured. Set FIRECRAWL_API_KEY environment variable."}

        if not _FIRECRAWL_AVAILABLE:
            logger.warning("Firecrawl MCP not available")
            return {"results": [], "error": "Firecrawl MCP tool not available. Install MCP Firecrawl server."}

        try:
            if _FIRECRAWL_IMPORT == "mcp__firecrawl__firecrawl_search":
                from mcp__firecrawl__firecrawl_search import firecrawl_search
            else:
                from mcp__firecrawl import firecrawl_search

            enhanced_query = f"{query} 裁判文书 案例 判决"
            results = await firecrawl_search(query=enhanced_query, limit=limit, scrape_options=scrape_options or {"formats": ["markdown"]})

            result_list = results.get("results", []) if isinstance(results, dict) else []
            logger.info(f"Firecrawl search completed: {len(result_list)} results")
            return results
        except Exception as e:
            logger.error(f"Firecrawl search error: {e}")
            return {"results": [], "error": f"Search failed: {str(e)}"}

    async def is_available(self) -> bool:
        return bool(self.api_key) and _FIRECRAWL_AVAILABLE


_firecrawl_service: Optional[FirecrawlService] = None

def get_firecrawl_service() -> FirecrawlService:
    global _firecrawl_service
    if _firecrawl_service is None:
        _firecrawl_service = FirecrawlService()
    return _firecrawl_service
