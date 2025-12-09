import re
from abc import abstractmethod
from typing import Dict, List

from markdownify import markdownify
from pydantic import BaseModel


def remove_excessive_newlines(text: str) -> str:
    # Replace three or more consecutive newline characters (including spaces) with just two
    return re.sub(r"(\s*\n\s*){3,}", "\n\n", text)


def process_prompt_decorator(func):
    """wrapper for tool response model prompt method, only removes excess lines atm"""

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return remove_excessive_newlines(result)

    return wrapper


class ToolResponseModel(BaseModel):
    @property
    @abstractmethod
    @process_prompt_decorator
    def prompt(self) -> str:
        "The part of the response to send to the model"
        pass


class FailedToolResponse(ToolResponseModel):
    """Tool response model for failed tool calls"""

    error: str

    @property
    def prompt(self) -> str:
        return f"Error: {self.error}"


class JournalList(ToolResponseModel):
    query: str
    articles: List[Dict]
    abstracts: List

    @property
    def prompt(self) -> str:
        prompt = f"\n====\nExperimental research summaries on '{self.query}' "
        for idx, abstract in enumerate(self.abstracts):
            prompt += f"\n====\nPaper Summary {idx}:"
            try:
                prompt += abstract
            except TypeError:
                if isinstance(abstract, dict):
                    prompt += abstract["#text"]
                elif isinstance(abstract, list):
                    prompt += abstract[-1]
                else:
                    continue
        return prompt  # Added return statement


class NICEGuidanceSection(BaseModel):
    title: str
    content: str


class NICEGuidanceChapter(BaseModel):
    title: str
    id: str
    content: str
    sections: List[NICEGuidanceSection]


class NICEGuidance(ToolResponseModel):
    """NICE guidance document"""

    title: str
    guidanceNumber: str
    uri: str
    publicationDate: str
    lastModified: str
    chapters: List[NICEGuidanceChapter]

    @property
    def prompt(self) -> str:
        prompt = f"{self.title} ({self.guidanceNumber})\n\r"
        for chapter in self.chapters:
            if chapter.id in ["overview", "introduction", "recommendations", "advice"]:
                prompt += markdownify(chapter.content)
                if chapter.sections:
                    for section in chapter.sections:
                        prompt += markdownify(section.content)
        return prompt


class NICEGuidanceResults(ToolResponseModel):
    """NICE guidance search results"""

    results: List[NICEGuidance]

    @property
    def prompt(self) -> str:
        prompt = "The following NICE guidance documents were found:\r\n"
        for result in self.results:
            prompt += result.prompt
            prompt += "\n\r====\n\r"
        return prompt
