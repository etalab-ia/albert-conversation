"""
title: Albert Rag
author: Camille Andre
version: 0.1
"""

import re
import requests
from typing import List, Optional, Dict
from open_webui.config import OPENAI_API_KEYS, OPENAI_API_BASE_URL
from openai import OpenAI


### Parenthesis for confidence
async def confidence_message(client, model, context, question, answer, __event_emitter__):
    PROMPT_CONFIDENCE = """
    Tu es un assistant qui évalue la confiance de la réponse d'un assistant.
    Voilà un contexte :
    {context}
    Voilà une question :
    {question}
    Voilà une réponse :
    {answer}
    Réponds avec une note entre 0 et 100 pour la confiance de la réponse en se basant sur le contexte et la question posée.
    Si la réponse est "Je ne sais pas" et ne contient pas de sources, réponds 100.
    Réponds uniquement avec une note entre 0 et 100 et aucun commentaire.
    note : 
    """
    try:
        confidence = client.chat.completions.create(
                model=model,
                stream=False,
                temperature=0.1,
                max_tokens=3,
                messages=[{"role": "user", "content": PROMPT_CONFIDENCE.format(context=context, question=question, answer=answer)}],
            )
        confidence_text = confidence.choices[0].message.content
        confidence_match = re.search(r'\b([0-9]|[1-9][0-9]|100)\b', confidence_text)
        confidence = int(confidence_match.group(1)) if confidence_match else 0
        print("CONFIDENCE: ",confidence)
        if confidence < 80:
            return await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"🔴 Indice de confiance faible : {confidence}% — Vérifiez les sources.", "done": True, "hidden": False},
                }
            )
        else:
            return 0
    except Exception as e:
        print(f"Erreur lors de la génération de la note de confiance: {e}")
        return 0

### End parenthesis

# Prompt for docs search same for any rags
PROMPT_SEARCH_old = """
Tu es un assistant qui cherche des documents pour répondre à une question.
{prompt_search_addon}
Exemples pour t'aider: 
<history>
Ma soeur va se marier, j'ai le droit a des jours de congés ?
</history>
réponse attenue : 
jours de congés pour mariage frere ou soeur

<history>
Coucou
</history>
réponse attenue : 
no_search

<history>
Où travaille John Doe ?
</history>
réponse attenue : 
John Doe

En te basant sur cet historique de conversation : 
<history>
{history}
</history>
question de l'utilisateur : {question}
Réponds avec uniquement une recherche pour trouver des documents qui peuvent t'aider à répondre à la dernière question de l'utilisateur.
Réponds uniquement avec la recherche, rien d'autre. Donnes entre 2 et 10 mots clés pertinents.
Si aucune recherche n'est nécessaire, réponds "no_search".
"""

PROMPT_SEARCH = """
Tu es un assistant qui cherche des documents pour répondre à une question.
{prompt_search_addon}
Analyse cette question d'utilisateur et détermine si elle nécessite une recherche dans la base de données.

HISTORIQUE:
{history}

QUESTION ACTUELLE: "{question}"

TÂCHE:

    Si la question nécessite une recherche documentaire (informations factuelles, procédures, tarifs, etc.), reformule-la en une question complète et autonome qui intègre si besoin le contexte de l'historique. Réponds uniquement par la question reformulée.

    Si la question N'A PAS BESOIN de recherche documentaire, réponds exactement: no_search

Exemple de CAS de no_search:

    Salutations (bonjour, merci, au revoir)
    Questions sur ton fonctionnement
    Demandes de clarification vagues sans contexte suffisant
    Conversations générales
    Questions d'opinion

EXEMPLES:
Historique: "USER: Quel est le prix du renouvellement de carte d'identité ?"
Question: "Comment faire ?"
→ Comment renouveler une carte d'identité ?

Question: "Bonjour"
→ no_search

Question: "Tu peux m'aider ?"
→ no_search
"""


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
        print("OUTPUT: ",output)
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

def search_api(
    collection_ids: List[int],
    user_query: str,
    api_url: str,
    api_key: str = OPENAI_API_KEYS,
    top_k: int = 5,
    rff_k: int = 20,
    method: str = "semantic",
    score_threshold: float = 0,
    web_search: bool = False,
) -> Optional[Dict]:
    """
    Performs a search in Albert API collections.

    Args:
        collection_ids (List[int]): List of collection IDs to search
        user_query (str): User query
        api_url (str): Albert API base URL
        api_key (str): API key for authentication
        top_k (int): Number of results to return (default: 5)
        rff_k (int): RFF parameter for fusion (default: 20)
        method (str): Search method (default: "semantic")
        score_threshold (float): Minimum score threshold (default: 0)
        web_search (bool): Enable web search (default: False)

    Returns:
        Optional[Dict]: API JSON response or None in case of error

    Raises:
        requests.RequestException: In case of HTTP request error
        ValueError: In case of JSON response parsing error
    """
    url = f"{api_url}/search"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "collections": collection_ids,
        "rff_k": rff_k,
        "k": top_k,
        "method": method,
        "score_threshold": score_threshold,
        "web_search": web_search,
        "prompt": user_query,
        "additionalProp1": {},
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = []
        for result in response.json().get("data", []):
            if (
                result.get("score", 0) >= score_threshold
            ):  # We must verify that the score is above the threshold manually (independently from the API system)
                results.append(result)
        return results

    except requests.RequestException as e:
        print(f"HTTP request error: {e}")
        raise
    except ValueError as e:
        print(f"JSON parsing error: {e}")
        raise

def reranker(
    query: str,
    chunks: list,
    api_url: str,
    api_key: str = OPENAI_API_KEYS,
    score_threshold: Optional[float] = 0,
    rerank_model: str = "BAAI/bge-reranker-v2-m3",
    min_chunks: int = 1,
):
    """
    Reorders documents by relevance to a user query using Albert's reranking API.

    Args:
        query (str): User question to rank documents against
        chunks (list): List of document chunks with structure:
                      [{"chunk": {"content": str, ...}, "score": float, ...}]
        rerank_model (str, optional): Reranking model name.
                                     Default: "BAAI/bge-reranker-v2-m3"

    Returns:
        list: Chunks reordered by relevance (best first), or original list if error

    Raises:
        requests.RequestException: HTTP request error
        KeyError: Invalid chunk structure
    """
    chunks_questions = []

    chunks_questions.extend((chunk.get("chunk").get("content")) for chunk in chunks)

    request_body = {
        "prompt": query,
        "input": chunks_questions,
        "model": rerank_model,
    }

    # API call
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.post(
        url=f"{api_url}/rerank", json=request_body, headers=headers
    )

    if response.status_code == 200:
        results = response.json()
        # The response contains a 'data' field with a list of objects having a 'score' and an 'index'
        if "data" in results:
            # Get the indices of the chunks sorted by the highest score
            ranked_indices = [item["index"] for item in results["data"]]
            # Reorganize chunks based on the ranked indices
            if score_threshold is not None:
                reranked_chunks = [
                    chunks[idx]
                    for idx in ranked_indices
                    if results["data"][idx]["score"] >= score_threshold
                ]
            else:
                reranked_chunks = [chunks[idx] for idx in ranked_indices]
            # for chunk in reranked_chunks:
            #     print(chunk)
            if len(reranked_chunks) < min_chunks:
                print("Rerank failed (score threshold), returning original chunks")
                #print(chunks)
                return chunks
            else:
                print("Rerank success, returning reranked chunks")
                return reranked_chunks
        else:
            print("Format de réponse inattendu:", results)
            return chunks  # Returns unsorted documents in case of error
    else:
        print(f"Erreur lors du reranking: {response.status_code}")
        return chunks  # Returns unsorted documents in case of error

async def pipe(self, body: dict, __event_emitter__=None, collection_dict: dict = None, SYSTEM_PROMPT: str = None, PROMPT: str = None, PROMPT_SEARCH_ADDON: str = None, format_chunks_to_text: callable = None):
        prompt = body["messages"][-1]["content"]  # last message from user

        print("CONFIG")
        #### CONFIG
        ALBERT_API_URL = self.valves.ALBERT_API_URL
        ALBERT_API_KEY = (
            self.valves.ALBERT_API_KEY
            if self.valves.ALBERT_API_KEY
            else OPENAI_API_KEYS
        )
        model = self.valves.MODEL
        rerank_model = self.valves.RERANK_MODEL
        number_of_chunks = self.valves.NUMBER_OF_CHUNKS
        max_tokens = 2000

        user_query = body.get("messages", [])[-1]["content"]

        client = OpenAI(
            api_key=ALBERT_API_KEY,
            base_url=self.valves.ALBERT_API_URL,
        )
        print("END CONFIG")
        # Prepare messages : History + Last prompt for rag understanding
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
            # Generating search prompt
            search = client.chat.completions.create(
                model=model,
                stream=False,
                temperature=0.1,
                max_tokens=50,
                messages=[{"role": "user", "content": PROMPT_SEARCH.format(prompt_search_addon=PROMPT_SEARCH_ADDON, history=messages[1:], question=prompt)}],
            )
            print("SEARCH MESSAGES")
            [print(message) for message in messages[1:]]
            search = search.choices[0].message.content
            print("SEARCH : ",search)
            if search.strip().lower() == "no_search":
                top_chunks = []
                context = "Aucun contexte n'est nécessaire, réponds gentillement à l'utilisateur. N'ajoutes pas de sources en fin de réponse."
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

                print("SEARCH")
                search_results = search_api(
                    collection_ids=list(collection_dict.values()),
                    user_query=search,
                    api_url=ALBERT_API_URL,
                    api_key=ALBERT_API_KEY,
                    top_k=20,
                    rff_k=20,  # Unuseful for semantic search
                    method="semantic",
                    score_threshold=self.valves.SEARCH_SCORE_THRESHOLD,
                    web_search=False,
                )
                print("SEARCH_RESULTS",len(search_results))
                print("RERANK")
                top_chunks = reranker(
                    query=user_query,
                    chunks=search_results,
                    api_url=ALBERT_API_URL,
                    api_key=ALBERT_API_KEY,
                    score_threshold=self.valves.RERANKER_SCORE_THRESHOLD,
                    rerank_model=rerank_model,
                    min_chunks=number_of_chunks,
                )[:number_of_chunks]

                references = ""
                for k, chunk in enumerate(top_chunks):
                    references += f"""
- Document {k+1}:
{format_chunks_to_text(chunk = chunk.get("chunk").get("metadata"))}
"""
                print("RERANK_RESULTS",len(top_chunks))
                print("CONTEXT:\n",references)
                context = references

        except Exception as e:
            print("ERROR : ", e)
            await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Erreur lors de la recherche.",
                    "done": True,
                    "hidden": False,
                },
            }
            )
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

        # Add formatted last user message with context
        messages.append({
            "role": "user",
            "content": PROMPT.format(context=context, question=prompt),
        })

        print("MESSAGES HE KNOWS")
        [print(message) for message in messages]

        answer = await stream_albert(client, model, max_tokens, messages, __event_emitter__)

        #answer = "Le directeur de l'ONF est Julien COUREAU." # For testing to induce a wrong answer
        await confidence_message(client, model, context, prompt, answer, __event_emitter__)

        return body
