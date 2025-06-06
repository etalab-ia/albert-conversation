"""
title: Albert Rag
author: Camille Andre
version: 0.1
"""

from pydantic import BaseModel, Field
from typing import Optional
import requests
import json

from open_webui.custom_functions.pipes.albert_france_services.albert_france_services_settings import (
    collection_dict,
    SYSTEM_PROMPT,
    PROMPT,
)
from open_webui.custom_functions.pipes.albert_rag.albert_rag_blank import (
    pipe as albert_rag_pipe,
)


class Pipe:
    class Valves(BaseModel):
        max_turns: int = Field(
            default=4, description="Maximum allowable conversation turns for a user."
        )
        ALBERT_URL: str = Field(default="https://albert.api.etalab.gouv.fr/v1")
        ALBERT_KEY: str = Field(default="")
        MODEL: str = Field(default="mistralai/Mistral-Small-3.1-24B-Instruct-2503")
        pass

    def __init__(self):
        self.valves = self.Valves()
        self.collection_dict = collection_dict
        self.SYSTEM_PROMPT = SYSTEM_PROMPT
        self.PROMPT = PROMPT
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
        )
