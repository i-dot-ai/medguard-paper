import asyncio
import random
from typing import List, Optional

from pydantic import BaseModel, Field

import asyncio
from typing import Dict, List, Type, TypeVar, Union

from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from medguard.scorer.models import FailureReason

T = TypeVar("T", bound=BaseModel)


class OpenAISemaphoreClient:
    """Client for theme extraction using a local vLLM server.

    Start the vLLM server with: make serve-vllm-docker
    See Makefile for model configuration details.
    """

    def __init__(
        self,
        max_concurrent_requests: int = 15,
        max_retries: int = 3,
        base_wait_seconds: int = 1,
        max_wait_seconds: int = 60,
        semaphore: asyncio.Semaphore | None = None,
    ):
        # Connects to local vLLM server (see: make serve-vllm-docker)
        self.client = AsyncOpenAI(
            api_key="token-abcd1234",  # Dummy key for local vLLM
            base_url="http://localhost:8000/v1",
        )
        if not semaphore:
            self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        else:
            self.semaphore = semaphore

        self.max_retries = max_retries
        self.base_wait_seconds = base_wait_seconds
        self.max_wait_seconds = max_wait_seconds

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((Exception,)),
    )
    async def _make_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response_format: Type[T],
        index: int | None = None,
        return_full_response: bool = False,
    ) -> T:
        if index is not None:
            print(f"Making request {index}")
        response = await self.client.responses.parse(
            model=model,
            input=messages,
            text_format=response_format,
        )
        if index is not None:
            print(f"Request completed {index}")
        if return_full_response:
            return response
        else:
            return response.output_parsed

    async def parse_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response_format: Type[T],
        index: int | None = None,
        return_full_response: bool = False,
    ) -> T:
        async with self.semaphore:
            return await self._make_request(
                model, messages, response_format, index, return_full_response
            )

    async def batch_parse_completions(
        self,
        model: str,
        messages_list: List[List[Dict[str, str]]],
        response_format: Type[T],
        return_full_response: bool = False,
    ) -> List[Union[T, Exception]]:
        """
        Process multiple completion requests in parallel, preserving order.

        Args:
            model: The model to use for all requests
            messages_list: List of message lists, one for each request
            response_format: Pydantic model class for parsing responses

        Returns:
            List of results in the same order as inputs. Each result is either:
            - A successfully parsed Pydantic model instance
            - An Exception if the request failed
        """

        async def _single_completion(
            index: int, messages: List[Dict[str, str]]
        ) -> Union[T, Exception]:
            try:
                return await self.parse_completion(
                    model, messages, response_format, index, return_full_response
                )
            except Exception as e:
                return e

        # Create tasks for all requests
        tasks = [
            _single_completion(index, messages) for index, messages in enumerate(messages_list)
        ]

        # Execute all tasks concurrently and preserve order
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()


class ThemeList(BaseModel):
    """List of discovered themes from reasoning traces"""

    reasoning: str = Field(description="Reasoning about the themes that were discovered")
    themes: List[str] = Field(description="List of distinct, self-explanatory theme names")


class RefinedThemes(BaseModel):
    """Refined and consolidated themes after critique"""

    consolidation_notes: str = Field(
        description="Reasoning about how the themes were refined, if at all"
    )
    themes: List[str] = Field(description="List of refined, self-explanatory themes")


class TraceClassification(BaseModel):
    """Classification result for a single trace"""

    applicable_themes: List[str] = Field(description="List of theme names that apply to this trace")


DISCOVERY_PROMPT = """You are an expert at identifying themes across a series of failure analyses.

Your task is to analyze a set of different failure reasons and specific ways in which you can subdivide the failure reasons provided. The themes have already been grouped into specific categories so they'll already be somewhat related to one another. You're job is to go one level deeper and identify a set of failure modes within this theme that provide an additional level of granularity.

Return a list of distinct themes that capture the different types of failures you observe. Each theme name should be:
- Self-explanatory (no separate description needed)
- Clearly distinguishable from others
- Specific enough to understand the granularity of this specific case of the failure mode

Good themes are a short phrase or sentence that captures the failure mode accurately. For example:
- Basing conclusions on one lab, vital sign, or entry without trend or corroboration
- Misread dosage frequency/Timing (e.g., "two tablets in the morning" interpreted as BID)

You should aim to identify {n_themes} themes.
"""

REFINEMENT_PROMPT = """You are an expert at refining a list of possible themes. You've been given a list of themes identified failure modes of clinical decision making.

Your task is to:
1. Review the themes for overlap and redundancy
2. Merge similar themes that capture the same underlying failure type
3. Otherwise keep the names of the themes unchanged


The goal is to create a minimal but comprehensive set of themes with names that are immediately understandable without needing additional description.

Good theme names are specific and actionable, and are just the sentence used to describe the theme:
- "Dismissing critical symptoms as benign"
- "Miscalculating weight-based dosages"
- "Delaying emergency interventions"
Good theme names do not contain any additional ordering, emojis, or other non-essential text.

Avoid vague names like:
- "Clinical Error"
- "Wrong Assessment"
- "Bad Judgment"

You must ensure that you return exactly {n_themes} themes.
 """


CLASSIFICATION_PROMPT = """You are an expert at classifying text according to predefined themes.

Given a piece of text and a list of possible themes, identify which themes apply to the text. A text may have multiple applicable themes or none at all.

Available themes:
{themes}

Only select themes that clearly apply to the specific failures in the reasoning trace. The theme names are self-explanatory.

When assigning themes, ensure you write the theme exactly as it is provided. Do not add or remove any words or characters."""

CANDIDATE_THEMES = {
    FailureReason.HALLUCINATION: [
        "Misinterpreting medication status (active vs discontinued, repeat medication flag, not being taken notes)",
        "Omitting crucial clinical facts (lab results, vital signs, diagnoses, procedures, adverse event entries)",
        "Misreading dosage and administration details (duplicate prescriptions, ambiguous frequency wording, strength vs dose errors)",
        "Erroneous temporal reasoning (treating historic events, old labs, or past diagnoses as current; ignoring required monitoring windows)",
        "Assuming record completeness (equating missing documentation with absence of therapy, monitoring, or screening)",
    ],
}


class ThemeDiscoveryPipeline:
    def __init__(
        self,
        discovery_model: str = "openai/gpt-oss-120b",
        refinement_model: str = "openai/gpt-oss-120b",
        classification_model: str = "openai/gpt-oss-120b",
        max_concurrent_requests: int = 15,
    ):
        self.discovery_model = discovery_model
        self.refinement_model = refinement_model
        self.classification_model = classification_model
        self.max_concurrent_requests = max_concurrent_requests

    async def discover_themes(
        self,
        traces: List[str],
        sample_size: Optional[int] = None,
        n_themes: int = 10,
        client: Optional[OpenAISemaphoreClient] = None,
    ) -> ThemeList:
        """Discover common themes from a sample of reasoning traces"""

        # Sample traces if requested
        if sample_size and sample_size < len(traces):
            sampled_traces = random.sample(traces, sample_size)
        else:
            sampled_traces = traces

        # Prepare the traces for analysis
        traces_text = "\n\n".join(
            [f"Trace {i + 1}: {trace}" for i, trace in enumerate(sampled_traces)]
        )

        messages = [
            {"role": "system", "content": DISCOVERY_PROMPT.format(n_themes=n_themes)},
            {
                "role": "user",
                "content": f"Analyze these {len(sampled_traces)} reasoning traces and identify the distinct failure themes:\n\n{traces_text}",
            },
        ]

        if client:
            result = await client.parse_completion(
                model=self.discovery_model, messages=messages, response_format=ThemeList
            )
        else:
            async with OpenAISemaphoreClient(
                max_concurrent_requests=self.max_concurrent_requests
            ) as temp_client:
                result = await temp_client.parse_completion(
                    model=self.discovery_model, messages=messages, response_format=ThemeList
                )

        return result

    async def refine_themes(
        self,
        initial_themes: List[str],
        n_themes: int = 10,
        client: Optional[OpenAISemaphoreClient] = None,
    ) -> RefinedThemes:
        """Refine and consolidate themes using o4-mini"""

        themes_text = "\n".join([f"- {theme}" for theme in initial_themes])

        messages = [
            {"role": "system", "content": REFINEMENT_PROMPT.format(n_themes=n_themes)},
            {
                "role": "user",
                "content": f"Please refine and consolidate these failure themes:\n\n{themes_text}",
            },
        ]

        if client:
            result = await client.parse_completion(
                model=self.refinement_model, messages=messages, response_format=RefinedThemes
            )
        else:
            async with OpenAISemaphoreClient(
                max_concurrent_requests=self.max_concurrent_requests
            ) as temp_client:
                result = await temp_client.parse_completion(
                    model=self.refinement_model, messages=messages, response_format=RefinedThemes
                )

        return result

    async def classify_trace(
        self, trace: str, themes: List[str], client: OpenAISemaphoreClient
    ) -> TraceClassification:
        """Classify a single trace against the refined themes"""

        # Format themes as a bullet list
        themes_text = "\n".join([f"- {theme}" for theme in themes])

        messages = [
            {"role": "system", "content": CLASSIFICATION_PROMPT.format(themes=themes_text)},
            {"role": "user", "content": f"Classify this reasoning trace:\n\n{trace}"},
        ]

        result = await client.parse_completion(
            model=self.classification_model, messages=messages, response_format=TraceClassification
        )

        return result

    async def classify_all_traces(
        self, traces: List[str], themes: List[str], client: Optional[OpenAISemaphoreClient] = None
    ) -> List[List[str]]:
        """Classify all traces against the refined themes"""

        if client:
            tasks = [self.classify_trace(trace, themes, client) for trace in traces]
            classifications = await asyncio.gather(*tasks)
        else:
            async with OpenAISemaphoreClient(
                max_concurrent_requests=self.max_concurrent_requests
            ) as temp_client:
                tasks = [self.classify_trace(trace, themes, temp_client) for trace in traces]
                classifications = await asyncio.gather(*tasks)

        # Extract just the theme names for each trace
        results = []
        for classification in classifications:
            results.append(classification.applicable_themes)

        return results

    async def classify_all_traces_multiple_themes(
        self, traces_and_themes: list[tuple[list[str], list[str]]], client: OpenAISemaphoreClient
    ) -> list[list[str]]:
        """Classify all traces against multiple themes"""

        tasks = []
        for trace_and_themes in traces_and_themes:
            traces, themes = trace_and_themes
            for trace in traces:
                tasks.append(self.classify_trace(trace, themes, client))

        classifications = await asyncio.gather(*tasks)

        # Extract just the theme names for each trace
        results = []
        for classification in classifications:
            results.append(classification.applicable_themes)

        return results

    async def run_themefinder(
        self,
        traces: List[str],
        themes: Optional[List[str]] = None,
        refine_themes: bool = True,
        discovery_sample_size: Optional[int] = 50,
        n_themes: int = 10,
    ) -> List[List[str]]:
        """
        Complete pipeline to analyze reasoning traces for failure themes.

        Args:
            traces: List of reasoning traces to analyze
            themes: Optional pre-defined themes (skips discovery and refinement if provided)
            discovery_sample_size: Number of traces to sample for theme discovery

        Returns:
            List of lists containing applicable theme names for each trace
        """

        async with OpenAISemaphoreClient(
            max_concurrent_requests=self.max_concurrent_requests
        ) as client:
            if themes is None:
                # Stage 1: Discover themes
                print(
                    f"Stage 1: Discovering themes from {min(discovery_sample_size or len(traces), len(traces))} traces..."
                )
                discovered = await self.discover_themes(
                    traces, discovery_sample_size, n_themes, client
                )
                print(f"Reasoning: {discovered.reasoning}")
                print(f"Discovered {len(discovered.themes)} initial themes: {discovered.themes}")

                if refine_themes:
                    # Stage 2: Refine themes
                    print(f"\nStage 2: Refining themes using {self.refinement_model}...")
                    refined = await self.refine_themes(discovered.themes, n_themes, client)
                    print(f"Refined to {len(refined.themes)} themes: {refined.themes}")
                    print(f"Consolidation notes: {refined.consolidation_notes}")
                    final_themes = refined.themes
                else:
                    final_themes = discovered.themes

            else:
                # Use provided themes
                print(f"Using provided themes: {themes}")
                final_themes = themes

            # Stage 3: Classify all traces
            print(
                f"\nStage 3: Classifying {len(traces)} traces against {len(final_themes)} themes..."
            )
            results = await self.classify_all_traces(traces, final_themes, client)

            return results
