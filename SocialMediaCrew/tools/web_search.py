"""
Web Search Tool using Serper API.

Used for researching trending topics and gathering information.
"""

import os
import logging
import requests
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev"


class SearchResult(BaseModel):
    """A single search result."""
    title: str
    link: str
    snippet: str


class SearchResults(BaseModel):
    """Collection of search results."""
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    error: Optional[str] = None


def get_serper_api_key() -> str:
    """Get the Serper API key."""
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        raise ValueError("SERPER_API_KEY environment variable not set")
    return key


def search_web(query: str, num_results: int = 10) -> SearchResults:
    """
    Search the web using Serper API.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        SearchResults with list of results
    """
    logger.info(f"Searching web for: {query}")

    try:
        api_key = get_serper_api_key()
    except ValueError as e:
        return SearchResults(query=query, error=str(e))

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "q": query,
        "num": num_results
    }

    try:
        response = requests.post(
            f"{SERPER_API_URL}/search",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Search failed: {response.status_code}")
            return SearchResults(
                query=query,
                error=f"Search API error: {response.status_code}"
            )

        data = response.json()
        organic = data.get("organic", [])

        results = [
            SearchResult(
                title=r.get("title", ""),
                link=r.get("link", ""),
                snippet=r.get("snippet", "")
            )
            for r in organic[:num_results]
        ]

        logger.info(f"Found {len(results)} results")
        return SearchResults(query=query, results=results)

    except requests.RequestException as e:
        logger.error(f"Search request failed: {e}")
        return SearchResults(query=query, error=str(e))


def search_trending_topics(topic_area: str) -> SearchResults:
    """
    Search for trending topics in a specific area.

    Args:
        topic_area: The area to search for trends (e.g., "AI", "technology", "marketing")

    Returns:
        SearchResults with trending topics
    """
    query = f"trending {topic_area} topics 2025 viral"
    return search_web(query, num_results=10)


def search_topic_insights(topic: str) -> SearchResults:
    """
    Search for insights and information about a specific topic.

    Args:
        topic: The topic to research

    Returns:
        SearchResults with topic insights
    """
    query = f"{topic} insights statistics facts 2025"
    return search_web(query, num_results=10)


def search_viral_content(topic: str, platform: str = "twitter") -> SearchResults:
    """
    Search for examples of viral content about a topic.

    Args:
        topic: The topic to search for
        platform: Social media platform

    Returns:
        SearchResults with viral content examples
    """
    query = f"viral {platform} posts about {topic} examples"
    return search_web(query, num_results=10)
