"""Case search tool for legal case retrieval.

This module provides a LangChain tool for searching legal cases using the Firecrawl service.
"""
import logging
from typing import Optional
from langchain_core.tools import tool
from app.services.firecrawl_service import get_firecrawl_service

logger = logging.getLogger(__name__)


def _extract_summary(result: dict) -> str:
    """Extract summary from search result.

    Args:
        result: A single search result dictionary

    Returns:
        Summary string, up to 500 characters
    """
    if "markdown" in result:
        return result["markdown"][:500]
    return result.get("snippet", "")


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
            - cases: List of case results with title, url, summary, and relevance
            - total_found: Total number of results found
            - error: Error message if search failed (optional)
    """
    # Input validation
    if not query or not isinstance(query, str):
        logger.warning(f"Invalid query provided: {query}")
        return {"cases": [], "total_found": 0, "error": "Query must be a non-empty string"}

    query = query.strip()
    if not query:
        logger.warning("Empty query after stripping whitespace")
        return {"cases": [], "total_found": 0, "error": "Query cannot be empty or whitespace only"}

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
                "total_found": 0,
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
                "summary": _extract_summary(result),
                "relevance": result.get("score", 0)
            }
            cases.append(case)

        total_found = len(results)
        logger.info(f"Found {total_found} cases for query: '{query}', returning {len(cases)}")

        response = {
            "cases": cases,
            "total_found": total_found
        }

        # Include error if present
        if "error" in search_result:
            response["error"] = search_result["error"]

        return response

    except ValueError as e:
        logger.error(f"Value error in case search: {e}", exc_info=True)
        return {"cases": [], "total_found": 0, "error": f"Invalid input: {str(e)}"}

    except Exception as e:
        logger.error(f"Unexpected error searching cases: {e}", exc_info=True)
        return {"cases": [], "total_found": 0, "error": f"Failed to search cases: {str(e)}"}
