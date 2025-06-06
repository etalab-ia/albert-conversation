"""
title: Albert Rag
author: Camille Andre
version: 0.1
"""

from pydantic import BaseModel, Field
from typing import Optional
import requests
import json

SYSTEM_PROMPT = """
Tu es un assistant qui répond à des questions en te basant sur un contexte.
Tu parles en français. Tu es précis, concis et poli.
Tu es connecté aux collections suivantes : {collections} sur AlbertAPI.
Ce que tu sais faire : Tu sais répondre aux questions et chercher dans les bases de connaissance de Albert API.
Ne donnes pas de sources si tu réponds à une question meta ou sur toi.
"""

PROMPT = """
<context trouvé dans la base>
{context}
</context trouvé dans la base>

En t'aidant si besoin du le contexte ci-dessus, réponds à la question suivante :
<question>
{question}
</question>

Réponds uniquement à la question sans aucun commentaire supplémentaire. 
A la fin de ta réponse, ajoute les sources ou liens urls utilisés pour répondre à la question. Quand tu mets des liens donne leurs des noms simples avec la notation markdown.
Si tu mets des sources en fin de réponse, ne mets QUE les sources liées à ta réponse, jamais de source inutilement.
Si tu ne trouves pas d'éléments de réponse dans le contexte ou dans ton prompt system, réponds que tu manques d'informations et demande des précisions. Sois poli.
"""


class Pipe:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )
        max_turns: int = Field(
            default=4, description="Maximum allowable conversation turns for a user."
        )
        ALBERT_URL: str = Field(default="https://albert.api.etalab.gouv.fr/v1")
        ALBERT_KEY: str = Field(default="")
        COLLECTIONS: str = Field(default="travail-emploi,service-public")
        MODEL: str = Field(default="mistralai/Mistral-Small-3.1-24B-Instruct-2503")
        pass

    class UserValves(BaseModel):
        max_turns: int = Field(
            default=4, description="Maximum allowable conversation turns for a user."
        )
        pass

    def __init__(self):
        # Indicates custom file handling logic. This flag helps disengage default routines in favor of custom
        # implementations, informing the WebUI to defer file-related operations to designated methods within this class.
        # Alternatively, you can remove the files directly from the body in from the inlet hook
        # self.file_handler = True

        # Initialize 'valves' with specific configurations. Using 'Valves' instance helps encapsulate settings,
        # which ensures settings are managed cohesively and not confused with operational flags like 'file_handler'.
        self.valves = self.Valves()
        pass

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # Modify the request body or validate it before processing by the chat completion API.
        # This function is the pre-processor for the API where various checks on the input can be performed.
        # It can also modify the request before sending it to the API.
        print(f"inlet:{__name__}")
        print(f"inlet:body:{body}")
        print(f"inlet:user:{__user__}")

        if __user__.get("role", "admin") in ["user", "admin"]:
            messages = body.get("messages", [])

            max_turns = min(__user__["valves"].max_turns, self.valves.max_turns)
            if len(messages) > max_turns:
                raise Exception(
                    f"Conversation turn limit exceeded. Max turns: {max_turns}"
                )

        return body

    async def pipe(self, body: dict, __event_emitter__=None):
        session = requests.session()
        session.headers = {"Authorization": f"Bearer {self.valves.ALBERT_KEY}"}

        # Get available collections
        response = requests.get(
            url=f"{self.valves.ALBERT_URL}/collections?limit=50",
            headers={"Authorization": f"Bearer {self.valves.ALBERT_KEY}"},
        )
        collections_dict = {}
        for stuff in response.json()["data"]:
            collections_dict[stuff["name"]] = stuff["id"]

        print("### COLLECTIONS ###")
        print(collections_dict)
        print("### END COLLECTIONS ###")

        prompt = body["messages"][-1]["content"]  # last message from user

        def search_api_albert(prompt: str, k: int = 5) -> list:
            """
            Cet outil permet de chercher des bouts de documents sur le travail et le droit en france.

            Args:
                prompt: les mots clés ou phrases a chercher sémantiquement pour trouver des documents (ex: prompt="president france")
            """
            collections_wanted = self.valves.COLLECTIONS.split(",")
            print("COLLECTIONS WANTED : ", collections_wanted)
            docs = []
            names = []
            for coll in collections_wanted:
                coll_id = collections_dict[coll]
                data = {"collections": [coll_id], "k": k, "prompt": prompt}
                response = requests.post(
                    url=f"{self.valves.ALBERT_URL}/search",
                    json=data,
                    headers={"Authorization": f"Bearer {self.valves.ALBERT_KEY}"},
                )
                docs_coll = []
                # print(response.text)
                for result in response.json()["data"]:
                    content = result["chunk"]["content"]
                    if len(content) < 150:
                        continue
                    name = result["chunk"]["metadata"]["document_name"]
                    names.append(name)
                    score = result["score"]
                    metadata_dict = result["chunk"]["metadata"]
                    source = f"[{coll}] - " + " - ".join(
                        [
                            f"{metadata_dict[stuff]}"
                            for stuff in metadata_dict
                            if stuff
                            in ["titre", "title", "client", "url", "id_decision"]
                        ]
                    )
                    docs_coll.append((content, name, source, score))
                docs = docs + docs_coll
            docs = sorted(docs, key=lambda x: x[3], reverse=True)
            docs = [
                f"- **[{name}]** {doc[2]} {doc[0].split('Article :')[-1]} ...\n"
                for name, doc in zip(names, docs)
            ]
            return docs[:k]

        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Je cherche...",
                    "done": False,
                    "hidden": False,
                },
            }
        )

        # Search for documents
        try:
            docs = search_api_albert(prompt, 5)
            context = "\n".join(docs)
        except Exception as e:
            print("ERROR : ", e)
            return "Désolé, on dirait que la connection à AlbertAPI est perdue. Veuillez réessayer plus tard."

        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Terminé.",
                    "done": True,
                    "hidden": True,
                },
            }
        )

        # Format messages for albert, ensuring it starts with a user message and that the length is max_turns
        messages = []
        # 1. SYSTEM PROMPT first
        messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT.format(collections=self.valves.COLLECTIONS),
        })

        history = body.get('messages', [])
        max_hist = self.valves.max_turns
        # Get rolling window of history, but ensure it starts with a user message
        if history and max_hist > 0:
            recent_history = history[-max_hist:-1]
            # Find the first user message in the window
            start_idx = 0
            for i, msg in enumerate(recent_history):
                if msg.get('role') == 'user':
                    start_idx = i
                    break
            # Add history starting from the first user message
            messages += recent_history[start_idx:]

        # Last user message
        messages.append({
            "role": "user",
            "content": PROMPT.format(context=context, question=prompt),
        })

        async def custom_model_albert_stream(messages, stop_sequences=[]):
            data = {
                "model": self.valves.MODEL,
                "messages": messages,
                "stream": True,
                "n": 1,
                "temperature": 0.2,
                "repetition_penalty": 1,
                "max_tokens": 2048,
                "stop": stop_sequences,
            }
            response = session.post(
                url=f"{self.valves.ALBERT_URL}/chat/completions",
                json=data,
                timeout=100000,
                stream=True,
            )
            partial_answer = ""
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    decoded = line.decode("utf-8").strip()
                    if decoded.startswith("data:"):
                        decoded = decoded[5:].strip()
                    if not decoded:
                        continue
                    data_json = json.loads(decoded)
                except Exception as e:
                    print("@STREAM/JSON ERROR: ", e)
                    break  # Stop if JSON error

                # Stop if unexpected format or end of stream
                if (
                    "choices" not in data_json or
                    not data_json["choices"] or
                    "delta" not in data_json["choices"][0] or
                    "content" not in data_json["choices"][0]["delta"]
                ):
                    print("STOPPING: ", data_json)
                    break

                # Concatenate content
                partial_answer += data_json["choices"][0]["delta"]["content"]
                await __event_emitter__({
                    "type": "replace",
                    "data": {
                        "content": partial_answer,
                    }
                })
            # End: last send with done=True
            await __event_emitter__({
                "type": "replace",
                "data": {
                    "content": partial_answer,
                }
            })

        await custom_model_albert_stream(messages)
        return

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # Modify or analyze the response body after processing by the API.
        # This function is the post-processor for the API, which can be used to modify the response
        # or perform additional checks and analytics.
        print(f"outlet:{__name__}")
        print(f"outlet:body:{body}")
        print(f"outlet:user:{__user__}")

        return body
