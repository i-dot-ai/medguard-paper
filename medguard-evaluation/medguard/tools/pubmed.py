import os
import warnings
from datetime import datetime
from typing import Any, Dict, List

import dotenv
import httpx
import xmltodict
from inspect_ai.tool import tool
from tenacity import retry, stop_after_attempt, wait_exponential

from medguard.tools.models import JournalList


class PubMedSearcher:
    def __init__(self):
        dotenv.load_dotenv()
        self.NCBI_API_KEY = os.environ.get("NCBI_API_KEY")
        if not self.NCBI_API_KEY:
            warnings.warn("No NCBI API key loaded. Use of this tool may be throttled.")

        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def make_request(
        self, client: httpx.AsyncClient, url: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return xmltodict.parse(response.text)

    async def search_pubmed(
        self, query: str, max_results: int = 10, min_year: int = None
    ) -> JournalList:
        """Searches the PubMed API based on a free text query

        Args:
            query (str): Free text search query
            max_results (int): Maximum number of results to return
            min_year (int): Minimum publication year to consider

        Returns:
            JournalList: A list of articles matching the search query, including abstracts and metadata
        """
        if min_year is None:
            min_year = datetime.now().year - 5  # Default to 5 years ago

        search_params = {
            "db": "pubmed",
            "term": f"({query}) AND ({min_year}:3000[pdat])",
            "api_key": self.NCBI_API_KEY,
            "retmax": max_results * 2,  # Fetch more results to allow for filtering
            "sort": "relevance",
        }

        async with httpx.AsyncClient() as client:
            search_result = await self.make_request(client, self.search_url, search_params)
            id_list = search_result["eSearchResult"]["IdList"]["Id"]

            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "api_key": self.NCBI_API_KEY,
                "rettype": "abstract",
            }

            fetch_result = await self.make_request(client, self.fetch_url, fetch_params)

        articles = fetch_result["PubmedArticleSet"]["PubmedArticle"]
        processed_articles = self.process_articles(articles)

        # Sort by publication date (most recent first)
        processed_articles.sort(key=lambda x: x["publication_date"], reverse=True)

        output = JournalList(
            query=query,
            articles=processed_articles[:max_results],
            abstracts=[article["abstract"] for article in processed_articles[:max_results]],
        )

        return output

    def process_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed_articles = []
        for article in articles:
            try:
                medline_citation = article["MedlineCitation"]
                article_data = medline_citation["Article"]

                abstract = article_data.get("Abstract", {}).get("AbstractText", [""])
                if isinstance(abstract, dict):
                    abstract = abstract["#text"]
                if isinstance(abstract, list):
                    abstract = abstract[0]

                processed_article = {
                    "pmid": medline_citation["PMID"]["#text"],
                    "title": article_data["ArticleTitle"],
                    "abstract": abstract,
                    "journal": article_data["Journal"]["Title"],
                    "publication_date": article_data["Journal"]["JournalIssue"]["PubDate"].get(
                        "Year", "Unknown"
                    ),
                    "authors": [
                        author["LastName"]
                        for author in article_data.get("AuthorList", {}).get("Author", [])
                        if isinstance(author, dict)
                    ],
                }
                processed_articles.append(processed_article)
            except KeyError as e:
                warnings.warn(f"Error processing article: {e}")
        return processed_articles


@tool
def get_pubmed_search():
    pubmed_searcher = PubMedSearcher()
    min_year_default = datetime.now().year - 5

    """
    Searches the PubMed API for medical research based on a free text query, returning a mix of matched articles.

    Args:
        query (str): Free text search query
        max_results (int): Maximum number of results to return (default: 10)
        min_year (int): Minimum publication year to consider (default: current year - 5)

    Returns:
        str: A list of articles matching the search query, including abstracts and metadata
    """

    async def execute(query: str, max_results: int = 10, min_year: int = min_year_default) -> str:
        pubmed_results = await pubmed_searcher.search_pubmed(query, max_results, min_year)
        return pubmed_results.prompt

    return execute
