import os
import warnings
from typing import Any, Dict, List, Optional

import dotenv
import httpx
from inspect_ai.tool import tool
from tenacity import retry, stop_after_attempt, wait_exponential

from medguard.tools.models import (
    NICEGuidance,
    NICEGuidanceChapter,
    NICEGuidanceResults,
    NICEGuidanceSection,
)


class NICEGuidanceAPI:
    BASE_URL = "https://api.nice.org.uk/services/"

    def __init__(self):
        dotenv.load_dotenv()
        self.NICE_API_KEY = os.environ.get("NICE_API_KEY")
        if not self.NICE_API_KEY:
            warnings.warn("No NICE API key loaded, this tool will not work.")

        self.headers = {"API-Key": self.NICE_API_KEY, "Accept": "application/json"}
        self.exclude_chapters = [
            "evaluation-committee-members-and-nice-project-team",
            "appraisal-committee-members-and-nice-project-team",
            "update-information",
            "diversity-equality-and-language",
            "about-this-quality-standard",
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_request(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{endpoint}"
        response = await client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    async def search_guidance(self, query: str, max_results: int = 5) -> NICEGuidanceResults:
        """
        Search the NICE Guidance API based on a free text query.

        :param query: Free text search query
        :param max_results: Maximum number of results to return
        :return: List of guidance documents matching the search query, including titles and metadata
        """

        # first get the guidance documents
        results = await self.get_guidance()

        guidance_items = results["IndexItems"]

        # filter the results based on the query
        filtered_results = [
            guidance for guidance in guidance_items if query.lower() in guidance["Title"].lower()
        ]

        # limit the number of results
        filtered_results = filtered_results[:max_results]

        # get the full details for each guidance document
        guidance_documents = []
        for guidance in filtered_results:
            guidance_id = guidance["GuidanceNumber"]
            guidance_details = await self.get_guidance_details(guidance_id)

            guidance_chapters = []
            for chapter in guidance_details["Chapters"]:
                if chapter["ChapterId"] not in self.exclude_chapters:
                    sections = [
                        NICEGuidanceSection(title=section["Title"], content=section["Content"])
                        for section in chapter["Sections"]
                    ]
                    chapter = NICEGuidanceChapter(
                        title=chapter["Title"],
                        id=chapter["ChapterId"],
                        content=chapter["Content"],
                        sections=sections,
                    )
                    guidance_chapters.append(chapter)

            guidance_documents.append(
                NICEGuidance(
                    title=guidance_details["MetadataApplicationProfile"]["Title"],
                    guidanceNumber=guidance_details["GuidanceNumber"],
                    uri=guidance_details["Uri"],
                    publicationDate=guidance_details["MetadataApplicationProfile"]["Issued"],
                    lastModified=guidance_details["MetadataApplicationProfile"]["Modified"],
                    chapters=guidance_chapters,
                )
            )

        return NICEGuidanceResults(results=guidance_documents)

    # TODO Cache the guidance list or use a local version
    # @cache_response(seconds=600)
    async def get_guidance(self) -> List[Dict[str, Any]]:
        """
        Get the list of guidance documents from the NICE Guidance API.

        :return: List of guidance documents
        """
        # hierarchical taxonomy
        # endpoint = "guidance/current/newtaxonomy.json"

        # flat index
        endpoint = "guidance/index/current.json"

        async with httpx.AsyncClient() as client:
            return await self._make_request(client, endpoint)

    async def get_guidance_details(self, guidance_id: str) -> Dict[str, Any]:
        """
        Fetch details of a specific guidance document.

        :param guidance_id: ID of the guidance document
        :return: Guidance document details
        """
        endpoint = f"guidance/structured-documents/{guidance_id}.json"
        async with httpx.AsyncClient() as client:
            return await self._make_request(client, endpoint)


@tool
def get_nice_guidance():
    nice_guidance_api = NICEGuidanceAPI()

    async def execute(query: str, max_results: int = 10) -> str:
        """
        Gets the NICE (National Institute for Health and Care Excellence) medical and healthcare guidance.

        Args:
            query (str): Keyword text search query, use a condition or drug keyword to exact match in NICE guidance titles
            max_results (int): Maximum number of results to return (default: 10)

        Returns:
            str: A list of guidance documents matching the search query, including titles and metadata
        """
        nice_guidance_results = await nice_guidance_api.search_guidance(query, max_results)
        return nice_guidance_results.prompt

    return execute
