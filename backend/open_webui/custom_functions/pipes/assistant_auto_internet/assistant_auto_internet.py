"""
title: Assistant Auto Web
author: Camille Andre
version: 0.1
This pipe should be integrated on the frontend.
"""

import os
from pydantic import BaseModel, Field
from typing import Literal

from open_webui.custom_functions.pipes.assistant_auto_internet.assistant_auto_internet_settings import (
    PROMPT_COMPLEXE_OR_NOT,
    PROMPT_SEARCH,
)
from openai import OpenAI
from open_webui.config import OPENAI_API_KEYS, OPENAI_API_BASE_URL


async def stream_albert(client, model, max_tokens, messages, __event_emitter__):
    try:
        chat_response = client.chat.completions.create(
            model=model,
            stream=True,
            temperature=0.2,
            max_tokens=max_tokens,
            messages=messages,
        )

        output = ""
        for chunk in chat_response:
            try:
                choices = chunk.choices
                if not choices or not hasattr(choices[0], "delta"):
                    continue

                delta = choices[0].delta
                token = delta.content if delta and hasattr(delta, "content") else ""

                if token:
                    output += token
                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {
                                "content": token,
                                "done": False,
                            },
                        }
                    )

            except Exception as inner_e:
                print(f"Erreur dans un chunk : {inner_e}")
                continue

        await __event_emitter__(
            {
                "type": "message",
                "data": {"content": "", "done": True},
            }
        )
        print("OUTPUT: ", output)
        return output

    except Exception as e:
        await __event_emitter__(
            {
                "type": "chat:message:delta",
                "data": {
                    "content": f"Erreur globale API : {str(e)}",
                    "done": True,
                },
            }
        )


class Pipe:
    class Valves(BaseModel):
        max_turns: int = Field(
            default=4, description="Maximum allowable conversation turns for a user."
        )

        ALBERT_URL: str = Field(default="https://albert.api.etalab.gouv.fr/v1")
        ALBERT_KEY: str = Field(default="")
        MODEL: Literal[
            "meta-llama/Llama-3.1-8B-Instruct",
            "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
        ] = Field(default="mistralai/Mistral-Small-3.1-24B-Instruct-2503")
        RERANK_MODEL: str = Field(default="BAAI/bge-reranker-v2-m3")
        NUMBER_OF_CHUNKS: int = Field(default=5)
        SEARCH_SCORE_THRESHOLD: float = Field(default=0.35)
        RERANKER_SCORE_THRESHOLD: float = Field(default=0.1)
        REDACTOR_MODEL: str = Field(default="meta-llama/Llama-3.1-8B-Instruct")
        ANALYTICS_MODEL: str = Field(
            default="mistralai/Mistral-Small-3.1-24B-Instruct-2503"
        )
        SUPERVISOR_MODEL: str = Field(
            default="mistralai/Mistral-Small-3.1-24B-Instruct-2503"
        )
        DEFAULT_MODEL: str = Field(
            default="mistralai/Mistral-Small-3.1-24B-Instruct-2503"
        )
        pass

    def __init__(self):
        self.valves = self.Valves()
        pass

    async def pipe(
        self,
        body: dict,
        __event_emitter__=None,
    ):

        ALBERT_URL = self.valves.ALBERT_URL
        ALBERT_KEY = (
            self.valves.ALBERT_KEY if self.valves.ALBERT_KEY else OPENAI_API_KEYS
        )

        os.environ["REDACTOR_MODEL"] = self.valves.REDACTOR_MODEL
        os.environ["ANALYTICS_MODEL"] = self.valves.ANALYTICS_MODEL
        os.environ["SUPERVISOR_MODEL"] = self.valves.SUPERVISOR_MODEL
        os.environ["DEFAULT_MODEL"] = self.valves.DEFAULT_MODEL
        os.environ["COLLECTIONS"] = ""
        os.environ["ALBERT_URL"] = self.valves.ALBERT_URL
        os.environ["ALBERT_KEY"] = self.valves.ALBERT_KEY

        model = self.valves.MODEL
        max_tokens = 2000
        PROMPT_COMPLEXE_OR_NOT_ADDON = ""
        PROMPT_SEARCH_ADDON = ""

        user_query = body.get("messages", [])[-1]["content"]
        messages = body.get("messages", [])

        from open_webui.custom_functions.pipes.assistant_auto_internet.tools import (
            run_research,
        )

        client = OpenAI(
            api_key=ALBERT_KEY,
            base_url=self.valves.ALBERT_URL,
        )

        search = client.chat.completions.create(
            model=model,
            stream=False,
            temperature=0.1,
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT_SEARCH.format(
                        prompt_search_addon=PROMPT_SEARCH_ADDON,
                        history=messages[1:],
                        question=user_query,
                    ),
                }
            ],
        )
        search = search.choices[0].message.content.strip().lower()
        print("SEARCH CHOSEN:", search)

        if search.strip().lower() != "no_search":
            complex_or_not = (
                client.chat.completions.create(
                    model=model,
                    stream=False,
                    temperature=0.1,
                    max_tokens=50,
                    messages=[
                        {
                            "role": "user",
                            "content": PROMPT_COMPLEXE_OR_NOT.format(
                                prompt_complex_or_not_addon=PROMPT_COMPLEXE_OR_NOT_ADDON,
                                history=messages[1:],
                                question=user_query,
                            ),
                        }
                    ],
                )
                .choices[0]
                .message.content
            )
            complex_or_not = complex_or_not.strip().lower()
            print("COMPLEX OR NOT : ", complex_or_not)
        else:
            complex_or_not = "no_search"
            search = "no_search"
            result = await stream_albert(
                client, model, max_tokens, messages, __event_emitter__
            )

        if complex_or_not.strip().lower() == "complex":
            print("COMPLEX")
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool,
                    lambda: run_research(
                        client=client,
                        user_query=search,
                        internet=True,
                        iteration_limit=2,
                        prompt_suffix="",
                max_tokens=2048,
                        num_queries=3,
                        k=3,
                        lang="fr",
                        event_emitter=__event_emitter__,
                    )[0]
            )

            result = await stream_albert(
                client, model, max_tokens, result, __event_emitter__
            )
            #result = result.replace(
            #    " \n\nSi cette réponse convient, appelle juste final_answer(ta_variable) pour l'envoyer à l'utilisateur. Sinon continue les recherches ou pose une question à l'utilisateur.",
            #    "",
            #)
#
            ## Fake a stream of the result
            #for chunk in result:
            #    await __event_emitter__(
            #        {
            #            "type": "message:delta",
            #            "data": {
            #                "content": chunk,
            #            },
            #        }
            #    )
        elif complex_or_not.strip().lower() == "easy":
            print("EASY")
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool,
                    lambda: run_research(
                        client=client,
                        user_query=user_query,
                        internet=True,
                        iteration_limit=1,
                        prompt_suffix="Ignores les instructions précédentes, fais une réponse courte et concise qui répond à la question. L'utilisateur ne veut pas de réponse détaillée avec des informations inutiles.",
                        max_tokens=400,
                        num_queries=1,
                        k=2,
                        lang="fr",
                        event_emitter=__event_emitter__,
                    )[0]
                )

            result = result.replace(
                "\n Voilà les documents que j'ai trouvé pour ta recherche, utilises ces informations pour répondre à la question de l'utilisateur avec final_answer en format markdown. Donnes les sources et liens intéressants si il y en a. CETTE REPONSE N'EST PAS COMPLETE, TU DOIS REDIGER LA REPONSE dans final_answer.",
                "",
            )

            messages = [
                {
                    "role": "user",
                    "content": f"Tu es un assistant qui répond à des questions en te basant sur un contexte. Tu parles en français. Tu es précis et poli. En te basant sur le contexte suivant : {result}, réponds à la question de l'utilisateur : {user_query}",
                },
                {"role": "user", "content": user_query},
            ]

            result = await stream_albert(
                client, model, max_tokens, messages, __event_emitter__
            )

        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Réponse envoyée à l'utilisateur",
                    "done": True,
                    "hidden": True,
                },
            }
        )

        return result
