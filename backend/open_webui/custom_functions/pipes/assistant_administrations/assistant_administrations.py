"""
title: Assistant Administrations
author: Camille Andre
version: 0.1
This pipe should be integrated on the frontend.
"""

from pydantic import BaseModel, Field
from typing import Literal

from open_webui.custom_functions.pipes.assistant_administrations.assistant_administrations_settings import (
    collection_dict,
    SYSTEM_PROMPT,
    PROMPT,
    PROMPT_SEARCH_ADDON,
    format_chunks_to_text,
)
from open_webui.custom_functions.pipes.albert_rag.albert_rag import (
    pipe as albert_rag_pipe,
)


class Pipe:
    class Valves(BaseModel):
        max_turns: int = Field(
            default=4, description="Maximum allowable conversation turns for a user."
        )

        ALBERT_API_URL: str = Field(default="https://albert.api.etalab.gouv.fr/v1")
        ALBERT_API_KEY: str = Field(default="")
        MODEL: Literal[
            "meta-llama/Llama-3.1-8B-Instruct",
            "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
        ] = Field(default="mistralai/Mistral-Small-3.1-24B-Instruct-2503")
        RERANK_MODEL: str = Field(default="BAAI/bge-reranker-v2-m3")
        NUMBER_OF_CHUNKS: int = Field(default=5)
        SEARCH_SCORE_THRESHOLD: float = Field(default=0.35)
        RERANKER_SCORE_THRESHOLD: float = Field(default=0.1)
        pass

    def __init__(self):
        self.valves = self.Valves()
        self.collection_dict = collection_dict
        self.SYSTEM_PROMPT = SYSTEM_PROMPT
        self.PROMPT = PROMPT
        self.PROMPT_SEARCH_ADDON = PROMPT_SEARCH_ADDON

        self.citation = False
        pass

    async def pipe(
        self,
        body: dict,
        __event_emitter__=None,
    ):

        return await albert_rag_pipe(
            self,
            body,
            __event_emitter__,
            self.collection_dict,
            self.SYSTEM_PROMPT,
            self.PROMPT,
            self.PROMPT_SEARCH_ADDON,
            format_chunks_to_text,
        )
