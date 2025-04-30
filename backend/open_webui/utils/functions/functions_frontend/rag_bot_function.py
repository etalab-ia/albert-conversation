"""
WIP: Script for a simple RAG bot without LLM. Outputs a list of relevant documents.
"""

from pydantic import BaseModel, Field
from typing import Optional
import requests
import os


class Pipe:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )
        max_turns: int = Field(
            default=8, description="Maximum allowable conversation turns for a user."
        )
        ALBERT_URL: str = Field(default="https://albert.api.staging.etalab.gouv.fr/v1")
        ALBERT_KEY: str = Field(default="")
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
        os.environ["ALBERT_URL"] = self.valves.ALBERT_URL
        os.environ["ALBERT_KEY"] = self.valves.ALBERT_KEY
        response = requests.get(
            url=f"{self.valves.ALBERT_URL}/collections",
            headers={"Authorization": f"Bearer {self.valves.ALBERT_KEY}"},
        )
        collections_dict = {}
        for stuff in response.json()["data"]:
            collections_dict[stuff["name"]] = stuff["id"]
        collection_names = list(collections_dict.keys())

        prompt = body["messages"][-1]["content"]

        def search_api_albert(prompt: str, k: int = 5) -> list:
            """
            Cet outil permet de chercher des bouts de documents sur le travail et le droit en france.

            Args:
                prompt: les mots clés ou phrases a chercher sémantiquement pour trouver des documents (ex: prompt="president france")
            """
            collections_wanted = os.getenv("COLLECTIONS").split(",")
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
                    print("METADATA DICT : ", metadata_dict)
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
                f"- **[{name}]** {doc[2]} {doc[0].split('Extrait article :')[-1][:100]} ...\n"
                for name, doc in zip(names, docs)
            ]
            return docs[:k]

        docs = search_api_albert(prompt)
        print(docs)
        await __event_emitter__(
            {
                "type": "message",
                "data": {
                    "content": "Ces documents peuvent vous intéresser : \n"
                    + "".join(docs),
                    "done": True,  # Mark completion explicitly
                    "hidden": False,
                },
            }
        )

        return

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # Modify or analyze the response body after processing by the API.
        # This function is the post-processor for the API, which can be used to modify the response
        # or perform additional checks and analytics.
        print(f"outlet:{__name__}")
        print(f"outlet:body:{body}")
        print(f"outlet:user:{__user__}")

        return body
