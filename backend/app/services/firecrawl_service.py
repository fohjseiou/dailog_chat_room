"""Firecrawl service for web search and scraping.

This service wraps Firecrawl for searching legal cases and court decisions from the web.
"""
import logging
from typing import Dict, Any, Optional
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

# Try to import Firecrawl SDK
_FIRECRAWL_AVAILABLE = False

try:
    from firecrawl import FirecrawlApp
    _FIRECRAWL_AVAILABLE = True
    logger.info("Firecrawl SDK loaded successfully")
except ImportError:
    logger.warning("Firecrawl SDK not available - install with: pip install firecrawl-py")


class FirecrawlService:
    """Service for Firecrawl API integration.

    This service provides methods to search the web for legal cases using Firecrawl.
    """

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.firecrawl_api_key
        self._app = None

    def _get_app(self) -> Optional["FirecrawlApp"]:
        """Get or create FirecrawlApp instance."""
        if not _FIRECRAWL_AVAILABLE or not self.api_key:
            return None
        if self._app is None:
            try:
                self._app = FirecrawlApp(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize FirecrawlApp: {e}")
                return None
        return self._app

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
            logger.warning("Firecrawl SDK not available")
            return {"results": [], "error": "Firecrawl SDK not available. Install with: pip install firecrawl-py"}

        app = self._get_app()
        if not app:
            return {"results": [], "error": "Failed to initialize Firecrawl app"}

        try:
            # Enhance query for Chinese legal context
            enhanced_query = f"{query} 裁判文书 案例 判决"

            # Use Firecrawl search
            search_params = {
                "query": enhanced_query,
                "pageOptions": {
                    "fetchPageContent": True,
                    "includeHtml": False,
                    "includeRawHtml": False,
                }
            }

            logger.info(f"Searching Firecrawl with query: '{enhanced_query}'")
            search_result = app.search(**search_params)

            # Process results
            results = []
            if isinstance(search_result, dict):
                # Extract data from response
                data = search_result.get("data", [])
                for item in data[:limit]:
                    if isinstance(item, dict):
                        result = {
                            "title": item.get("title", "Untitled"),
                            "url": item.get("url", ""),
                            "markdown": item.get("markdown", item.get("description", "")),
                            "score": 0.8  # Default relevance score
                        }
                        results.append(result)

            logger.info(f"Firecrawl search completed: {len(results)} results")
            return {"results": results}

        except Exception as e:
            logger.error(f"Firecrawl search error: {e}", exc_info=True)
            return {"results": [], "error": f"Search failed: {str(e)}"}

    async def is_available(self) -> bool:
        """Check if Firecrawl service is available."""
        return bool(self.api_key) and _FIRECRAWL_AVAILABLE and self._get_app() is not None


_firecrawl_service: Optional[FirecrawlService] = None

def get_firecrawl_service() -> FirecrawlService:
    global _firecrawl_service
    if _firecrawl_service is None:
        _firecrawl_service = FirecrawlService()
    return _firecrawl_service
