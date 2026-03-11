"""Case search tool for legal case retrieval.

This module provides a LangChain tool for searching legal cases using the Firecrawl service.
"""
import logging
from typing import Optional
from langchain_core.tools import tool
from app.services.firecrawl_service import get_firecrawl_service

logger = logging.getLogger(__name__)


@tool
async def search_cases(query: str, limit: Optional[int] = 5) -> dict:
    """Search for legal cases and court decisions.

    This tool searches for legal cases, court decisions, and judgments related to the query.
    It uses web search to find relevant legal documents and case law.

    Args:
        query: The search query describing the legal topic or case type (e.g., "劳动合同纠纷", "合同违约")
        limit: Maximum number of cases to return (default: 5, max: 10)

    Returns:
        A dictionary containing:
            - cases: List of case results with title, url, and summary
            - error: Error message if search failed (optional)
    """
    # Input validation
    if not query or not isinstance(query, str):
        logger.warning(f"Invalid query provided: {query}")
        return {"cases": [], "error": "Query must be a non-empty string"}

    query = query.strip()
    if not query:
        logger.warning("Empty query after stripping whitespace")
        return {"cases": [], "error": "Query cannot be empty or whitespace only"}

    # Limit validation
    if limit is not None:
        try:
            limit = int(limit)
            if limit < 1:
                limit = 1
            elif limit > 10:
                logger.info(f"Limit {limit} exceeds maximum, using 10")
                limit = 10
        except (ValueError, TypeError):
            logger.warning(f"Invalid limit provided: {limit}, using default 5")
            limit = 5
    else:
        limit = 5

    logger.info(f"Searching for cases with query: '{query}', limit: {limit}")

    try:
        firecrawl_service = get_firecrawl_service()

        # Check if service is available
        if not await firecrawl_service.is_available():
            logger.warning("Firecrawl service not available")
            return {
                "cases": [],
                "error": "Case search service is not available. Please configure FIRECRAWL_API_KEY."
            }

        # Perform search
        search_result = await firecrawl_service.search(
            query=query,
            limit=limit,
            scrape_options={"formats": ["markdown"]}
        )

        # Extract and format results
        results = search_result.get("results", [])
        cases = []

        for result in results[:limit]:
            case = {
                "title": result.get("title", "Untitled"),
                "url": result.get("url", ""),
                "summary": result.get("markdown", "")[:500] if "markdown" in result else result.get("snippet", "")
            }
            cases.append(case)

        logger.info(f"Found {len(cases)} cases for query: '{query}'")

        response = {"cases": cases}

        # Include error if present
        if "error" in search_result:
            response["error"] = search_result["error"]

        return response

    except Exception as e:
        logger.error(f"Error searching cases: {e}", exc_info=True)
        return {"cases": [], "error": f"Failed to search cases: {str(e)}"}
