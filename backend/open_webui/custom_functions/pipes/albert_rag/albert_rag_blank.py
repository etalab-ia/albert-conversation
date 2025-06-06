"""
title: Albert Rag
author: Camille Andre
version: 0.1
"""

import requests
import json


PROMPT_SEARCH = """
Exemples pour t'aider: 
<history>
Ma soeur va se marier, j'ai le droit a des jours de congés ?
</history>
réponse attenue : 
jours de congés mariage frere et soeur

<history>
Coucou
</history>
réponse attenue : 
no_search

En te basant sur cet historique de conversation : 
<history>
{history}
</history>
question de l'utilisateur : {question}
Réponds avec uniquement une recherche pour trouver des documents qui peuvent t'aider à répondre à la dernière question de l'utilisateur.
Réponds uniquement avec la recherche, rien d'autre.
Si aucune recherche n'est nécessaire, réponds "no_search".
"""



async def pipe(self, body: dict, __event_emitter__=None, collection_dict: dict = None, SYSTEM_PROMPT: str = None, PROMPT: str = None):
        session = requests.session()
        session.headers = {"Authorization": f"Bearer {self.valves.ALBERT_KEY}"}


        prompt = body["messages"][-1]["content"]  # last message from user

        print("LA ??",collection_dict)

        def search_api_albert(prompt: str, k: int = 5, collection_dict: dict = None) -> list:
            """
            Cet outil permet de chercher des bouts de documents sur le travail et le droit en france.

            Args:
                prompt: les mots clés ou phrases a chercher sémantiquement pour trouver des documents (ex: prompt="president france")
            """
            docs = []
            names = []
            print("OU LA ??",collection_dict)
            for coll in collection_dict.keys():
                coll_id = collection_dict[coll]
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

        def custom_model_albert(messages, stop_sequences=[], max_tokens=2048):
                    data = {
                        "model": self.valves.MODEL,
                        "messages": messages,
                        "stream": False,
                        "n": 1,
                        "temperature": 0.2,
                        "repetition_penalty": 1,
                        "max_tokens": max_tokens,
                        "stop": stop_sequences,
                    }
                    response = session.post(
                        url=f"{self.valves.ALBERT_URL}/chat/completions",
                        json=data,
                        timeout=100000,
                    )
                    answer = response.json()["choices"][0]["message"]
                    return answer['content']

        try:
            search = custom_model_albert([{"role": "user", "content": PROMPT_SEARCH.format(history=body["messages"][-5:-1], question=prompt)}], max_tokens=30)
            print("SEARCH : ",search)
            if search == "no_search":
                docs = []
                context = ""
            else:
                await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": f"Recherche en cours pour '{search}'",
                    "done": False,
                    "hidden": False,
                },
            }
        )
                docs = search_api_albert(search, 5, collection_dict)
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
            "content": SYSTEM_PROMPT.format(collections=collection_dict.keys()),
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
