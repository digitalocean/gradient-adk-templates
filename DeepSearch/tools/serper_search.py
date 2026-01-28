import os
import httpx
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class SearchResult(BaseModel):
    """A single search result."""
    title: str = Field(description="Title of the search result")
    link: str = Field(description="URL of the search result")
    snippet: str = Field(description="Snippet/description of the search result")


class SearchResults(BaseModel):
    """Collection of search results."""
    results: List[SearchResult] = Field(description="List of search results")
    query: str = Field(description="The search query used")


def serper_search(query: str, num_results: int = 10) -> SearchResults:
    """
    Perform a web search using Serper API.

    Args:
        query: The search query
        num_results: Number of results to return (default 10)

    Returns:
        SearchResults object containing the search results
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY environment variable is not set")

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": num_results
    }

    response = httpx.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("organic", []):
        results.append(SearchResult(
            title=item.get("title", ""),
            link=item.get("link", ""),
            snippet=item.get("snippet", "")
        ))

    return SearchResults(results=results, query=query)


@tool
def web_search(query: str) -> str:
    """
    Perform a web search to find information on a topic.
    Use this tool when you need to find current information from the internet.

    Args:
        query: The search query to find information about

    Returns:
        A formatted string containing search results with titles, URLs, and snippets
    """
    try:
        search_results = serper_search(query, num_results=10)

        if not search_results.results:
            return f"No results found for: {query}"

        formatted = f"Search results for: {query}\n\n"
        for i, result in enumerate(search_results.results, 1):
            formatted += f"{i}. {result.title}\n"
            formatted += f"   URL: {result.link}\n"
            formatted += f"   {result.snippet}\n\n"

        return formatted
    except Exception as e:
        return f"Search error: {str(e)}"
