"""
This script is used to create a pipe that can be used to call the agent function from the frontend.
Copy and paste this directly onto the frontend in the admin panel.
"""

from pydantic import BaseModel, Field
import requests
from types import SimpleNamespace
import os
import numpy as np
import json
import io
import time
from open_webui.storage.redis_client import redis_client
import ast
from open_webui.config import OPENAI_API_BASE_URL, OPENAI_API_KEYS
import logging
from openai import OpenAI

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

OPENAI_API_BASE_URL = "https://albert.api.etalab.gouv.fr/v1"
default_model = "meta-llama/Llama-3.1-8B-Instruct"

TOC_PROMPT_SYSTEM = """
Tu es un agent de l'administration française qui fait des synthèses de textes. Tu sais en particulier faire des plans de synthèses. Tu parles en français.
"""
TOC_PROMPT_USER = """
Génère un plan simple mais structuré pour une synthèse du texte suivant :

'''
{context}
'''

Instructions :
    •   Le plan doit comporter 2, 3 ou 4 grandes parties.
    •   Uniquement des titres de chapitres (pas de sous-parties).
    •   Les titres doivent être clairs, synthétiques et pertinents par rapport au contenu du texte.
    •   La réponse doit être en français.

Format attendu :
    1.  Titre du premier chapitre
    2.  Titre du deuxième chapitre
    3.  (Éventuellement) Titre du troisième chapitre
    4.  (Éventuellement) Titre du quatrième chapitre

Instructions importantes : 
{instructions}

Réponds uniquement avec le plan, pas de commentaires supplémentaire.
"""


SUM_PROMPT_SYSTEM = """Tu es un agent de l'administration française qui fait des synthèses de textes. Tu sais en particulier faire des plans et des synthèses. Tu parles en français."""
SUM_PROMPT_USER = """Génère un résumé du texte suivant :
'''
{context}
'''
Instructions :
    •   Ne conserve que les éléments importants et pertinents.
    •   Garde les idées générales et les conclusions.
    •   Si des chiffres ou des exemples sont significatifs, inclue-les dans le résumé.
    •   Le résumé doit être clair, concis et structuré.
"""

MERGE_PROMPT_USER = """Fusionne les résumés suivants en une seule synthèse cohérente du document initial :

'''
{context}
'''

Instructions :
    •   Respecte le plan suivant qui t'es donné. 
    •   Structure ta synthèse en utilisant des connecteurs logiques.
    •   Suis rigoureusement le plan suivant:

'''
{toc}
'''
"""

MODIFY_RESUME_PROMPT_USER = """
A partir de ce contexte si besoin:
'''
{context}
'''

Modifies le résumé suivant :

'''
{resume}
'''

L'utilisateur a demandé les modififications suivantes : 

'''
{modifs}
'''

Réponds uniquement avec le nouveau résumé en respectant les demandes de l'utilisateur.
"""


def upload_file_to_albert_api(session, file_name, file_content, ALBERT_URL):
    # TODO : add this later for bigger files
    # split the file content into a list of chunks of 3500 characters
    # chunks = [file_content[i : i + 3500] for i in range(0, len(file_content), 3500)]

    # formated_file = list()
    # sample_size = -1

    # formated_file = [
    #    {"title": file_name, "text": chunk, "metadata": {}} for chunk in chunks
    # ]

    response = session.get(f"{OPENAI_API_BASE_URL}/models")
    response = response.json()
    model = [
        model
        for model in response["data"]
        if model["type"] == "text-embeddings-inference"
    ][0]["id"]
    log.info(f"Embeddings model: {model}")

    collection = "tmp_cam"

    response = session.post(
        f"{OPENAI_API_BASE_URL}/collections",
        json={
            "name": collection,
            "model": model,
            "type": "private",
            "description": "tmp_cam desc",
        },
    )
    response = response.json()
    collection_id = response["id"]
    log.info(f"Collection ID: {collection_id}")

    # Création du contenu du fichier
    formated_file = [{"title": file_name, "text": file_content, "metadata": {}}]
    file_content_json = json.dumps(formated_file).encode("utf-8")

    # Vérification de la taille du contenu
    assert (
        len(file_content_json) < 10 * 1024 * 1024
    ), "Le fichier ne doit pas dépasser 10MB"

    # Création d'un flux de données en mémoire
    #file_like_object = io.BytesIO(file_content_json)

    # Préparation des données pour la requête
    files = {
        "file": (
            'tmp.txt',  # Nom du fichier
            file_content.encode('utf-8'),  # Flux de données
            "text/plain",  # Type MIME
        )
    }

    #file_content = file_content.encode('utf-8')
            
    #files = {
    #    'file': (file_name, file_content, 'text/plain')
    #}
    
    data = {
        'collection': str(collection_id),  # Use the same extracted ID
        'chunk_size': '3000',
        'chunk_overlap': '100',
        'chunker': 'RecursiveCharacterTextSplitter',
        'length_function': 'len',
        'chunk_min_size': '0',
        'is_separator_regex': 'false',
        'metadata': ''
    }
    
    response = requests.post(
        f"{OPENAI_API_BASE_URL}/documents",
        headers={"Authorization": f"Bearer {OPENAI_API_KEYS}"},
        files=files,
        data=data
    )


    document_id = response.json()["id"]
    assert response.status_code == 201, "Erreur lors de l'importation du fichier"

    return str(collection_id), str(document_id)


async def stream_albert(client, model, max_tokens, messages, __event_emitter__):
    await __event_emitter__(
        {
            "type": "message",
            "data": {"content": "Messages:\n" + str(messages), "done": False},
        }
    )
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
                    for char in token:
                        output += char
                        await __event_emitter__(
                            {
                                "type": "message",
                                "data": {
                                    "content": char,
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

class Pipe:

    class Valves(BaseModel):
        SUPERVISOR_MODEL: str = Field(default=default_model)

    def __init__(self):
        self.valves = self.Valves()
        # If set to true it will prevent default RAG pipeline
        self.file_handler = True
        # self.citation = True

    async def pipe(
        self,
        body: dict,
        request=None,
        __event_emitter__=None,
        __event_call__=None,
        __user__=None,
        __request__=None,
        __metadata__=None,
        __files__=None,
    ):

        client = OpenAI(
            api_key=OPENAI_API_KEYS,
            base_url=OPENAI_API_BASE_URL,
        )

        def update_state(synth_id, state_dict):
            redis_client.set(
                synth_id,
                str(state_dict),
            )

        synth_id = (
            str(__metadata__["user_id"]) + str(__metadata__["chat_id"]) + "_synthetizer"
        )

        os.environ["SUPERVISOR_MODEL"] = self.valves.SUPERVISOR_MODEL

        session = requests.session()
        session.headers = {"Authorization": f"Bearer {OPENAI_API_KEYS}"}

        messages = body.get("messages", [])
        last_user_message = messages[-1]["content"] if messages else ""

        state_dict = redis_client.get(synth_id)

        if state_dict is None:
            state_dict = {
                "step": 0,
                "sommaire": None,
                "response_sommaire": None,
                "resume": None,
                "instructions_supp": "",
                "file_content": None,
                "collection_id": None,
                "document_id": None,
            }
            redis_client.set(
                synth_id,
                str(state_dict),
            )
            log.info("STATE DOES NOT EXISTS : Initialised it")
        else:
            state_dict = ast.literal_eval(state_dict)

        # ------ SOUS-FONCTIONS ---------
        async def upload_doc_if_needed(session):
            if not __files__:
                time.sleep(0.2)
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {
                            "content": """
### 👋 Bienvenue sur **Assistant Résumé** !
---
> *Ce pipeline est expérimental et fonctionne différemment d’un modèle classique.
> Suivez simplement les quelques étapes qui vous seront indiquées pour générer la synthèse de votre document.*
---
*Astuce : Pour ne plus voir ce message, commencez vos prochaines conversations avec ce modèle en attachant directement un fichier.*

📁 Pour commencer, **téléversez** un fichier de votre choix pour débuter l’analyse.
""",
                            "done": True,
                            "hidden": False,
                        },
                    }
                )
                return None, None, None

            file_names = [x["file"]["filename"] for x in __files__]
            file_contents = [x["file"]["data"]["content"] for x in __files__]
            file_name = file_names[-1]
            file_content = file_contents[-1]
            try:
                collection_id, document_id = upload_file_to_albert_api(
                    session, file_name, file_content, OPENAI_API_BASE_URL
                )
            except Exception as e:
                log.info(e)
                update_state(synth_id, {"step": 99, "response_sommaire": "problem"})
                return None, None, None
            return file_content, collection_id, document_id

        async def demande_sommaire_ou_gen(synth_id, state_dict):
            """
            Demande à l'utilisateur s'il veut fournir le sommaire.
            Si oui: step=2, sinon step=3.
            """
            response = await __event_call__(
                {
                    "type": "input",
                    "data": {
                        "title": "Plan du résumé",
                        "message": "Voulez-vous me donner un plan à suivre ou souhaitez-vous que je le crée ? "
                        "Donnez moi des instructions/un plan ou Confirmer pour que je génère un plan moi même",
                        "placeholder": "Instructions/Plan/Confirmer",
                    },
                }
            )
            log.info(f"REPONSE SOMMAIRE: {response}")
            state_dict["response_sommaire"] = response
            # User cancelled
            if response is False:
                log.info("Pipeline cancelled.")
                state_dict["step"] = 99
            # User gives plan or instructions
            elif str(response).strip() not in [
                "True",
                "",
                "confirmer",
                "ok",
                "none",
            ]:
                state_dict["sommaire"] = response
                state_dict["step"] = 4
                log.info("Got plan from user.")
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {
                            "content": f"""
> *Vos intructions :
{state_dict["sommaire"]}*\n\n
""",
                        },
                    }
                )
            # User gives nothing
            else:
                log.info("I need to work on this.")
                state_dict["step"] = 3

            update_state(synth_id, state_dict)
            return state_dict

        async def genere_et_valide_sommaire(synth_id, state_dict):
            """
            Génère un sommaire à valider, intègre les instructions utilisateur si présentes.
            """

            log.info(f"Instructions : {state_dict['instructions_supp']}")
            sommaire = await generate_toc(synth_id, state_dict)
            log.info("TOC generated")

            state_dict["step"] = 31
            state_dict["sommaire"] = sommaire

            #await __event_emitter__(
            #    {
            #        "type": "message",
            #        "data": {
            #            "content": f"Voici le plan de résumé proposé :\n\n{sommaire}\n\n***Pour valider, répondez 'ok'. Sinon, indiquez des instructions supplémentaires.***",
            #        },
            #    }
            #)
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {
                        "content": "\n\n***Pour valider, répondez 'ok'. Sinon, indiquez des instructions supplémentaires.***",
                    },
                }
            )
            update_state(synth_id, state_dict)
            return body

        async def generate_toc(synth_id, state_dict):
            instructions = ""
            if state_dict["sommaire"]:
                instructions = (
                    f"Sachant que le plan pour l'instant est : {state_dict['sommaire']}\n"
                    + state_dict["instructions_supp"]
                )
            messages = [
                {
                    "role": "system",
                    "content": TOC_PROMPT_SYSTEM,
                },
                {
                    "role": "user",
                    "content": TOC_PROMPT_USER.format(
                        context=state_dict["file_content"][:10000],
                        instructions=instructions,
                    ),
                },
            ]

            await __event_emitter__(
                {
                    "type": "message",
                    "data": {
                        "content": "Voici le plan de résumé proposé :\n\n",
                    },
                }
            )
            return await stream_albert(client, self.valves.SUPERVISOR_MODEL, 2048, messages, __event_emitter__)

        async def genere_resume_et_valide(synth_id, state_dict, session):
            """
            Fait la synthèse du document selon le sommaire. Demande validation ou modifications à l'utilisateur.
            """

            sommaire = state_dict["sommaire"]
            # Get chunks with search to have whole context
            url = f"{OPENAI_API_BASE_URL}/chunks/{state_dict['document_id']}?limit=100&offset=0"
            response = session.get(url)
            chunks = [chunk["content"] for chunk in response.json()["data"]]
            map_reduce_outputs = []
            import asyncio
            
            async def process_chunk(chunk):
                prompt = SUM_PROMPT_USER.format(context=chunk)
                messages_sum = [
                    {"role": "system", "content": SUM_PROMPT_SYSTEM},
                    {"role": "user", "content": prompt},
                ]

                output = client.chat.completions.create(
                model=self.valves.SUPERVISOR_MODEL,
                stream=False,
                temperature=0.1,
                max_tokens=400,
                messages=messages_sum,
                ).choices[0].message.content
                return output
            
            # Process chunks in batches of 5
            batch_size = 3
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                percent = int(((i + len(batch)) / len(chunks)) * 100)
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Lecture du document... {percent:02d} %",
                            "done": False,
                            "hidden": False,
                        },
                    }
                )
                
                # Process batch concurrently
                batch_tasks = [process_chunk(chunk) for chunk in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                map_reduce_outputs.extend(batch_results)
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Génération du résumé...",
                        "done": False,
                        "hidden": False,
                    },
                }
            )
            merge_prompt = MERGE_PROMPT_USER.format(
                context=map_reduce_outputs, toc=sommaire
            )
            messages_merge = [
                {"role": "system", "content": SUM_PROMPT_SYSTEM},
                {"role": "user", "content": merge_prompt},
            ]

            resume =await stream_albert(client, self.valves.SUPERVISOR_MODEL, 2048, messages_merge, __event_emitter__)

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Résumé généré.",
                        "done": True,
                        "hidden": False,
                    },
                }
            )
            state_dict["resume"] = resume
            state_dict["step"] = 41
            update_state(synth_id, state_dict)
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {
                        "content": "\n\n***Pour valider, répondez 'ok'. Sinon, indiquez des instructions supplémentaires.***",#
                        "done": False,
                        "hidden": False,
                    },
                }
            )
            return body

        async def relance_synthese_si_modif(synth_id, state_dict):
            """
            Si utilisateur a fait une modif, relancer la fusion + reformulation avec l'instruction/retour user.
            """

            user_modif = last_user_message

            # Search chunks to get some context if needed
            log.info(f"COLLECTION : {state_dict['collection_id']}")
            data = {
                "collections": [int(state_dict["collection_id"])],
                "k": 2,
                "prompt": user_modif,
            }
            response = requests.post(
                url=f"{OPENAI_API_BASE_URL}/search",
                json=data,
                headers={"Authorization": f"Bearer {OPENAI_API_KEYS}"},
            )

            chunks = "\n".join(
                [chunk["chunk"]["content"] for chunk in response.json()["data"]]
            )

            update_resume_prompt = MODIFY_RESUME_PROMPT_USER.format(
                context=chunks,
                resume=state_dict["resume"],
                modifs=user_modif,
            )

            messages_merge = [
                {"role": "system", "content": SUM_PROMPT_SYSTEM},
                {"role": "user", "content": update_resume_prompt},
            ]
            log.info(f"MODIF NEEDED:\n {update_resume_prompt}")
            resume_corrige =await stream_albert(client, self.valves.SUPERVISOR_MODEL, 2048, messages_merge, __event_emitter__)

            state_dict["resume"] = resume_corrige
            update_state(synth_id, state_dict)
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Synthèse modifiée.",
                        "done": True,
                        "hidden": False,
                    },
                }
            )
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {
                        "content": "\n\n***Pour valider, répondez 'ok'. Sinon, indiquez des instructions supplémentaires.***",#resume_corrige
                        "done": False,
                        "hidden": False,
                    },
                }
            )
            return body

        # ------ CONTRÔLEUR PRINCIPAL AVEC CHEMINEMENT ---------
        try:
            if state_dict["step"] == 0:
                log.info("STEP 0: Checking if file is uploaded")
                file_content, collection_id, document_id = await upload_doc_if_needed(
                    session
                )
                if not file_content:  # No file uploaded
                    return body
                state_dict["step"] = 1
                state_dict["file_content"] = file_content
                state_dict["collection_id"] = collection_id
                state_dict["document_id"] = document_id

                log.info("STEP 1: Asking user for a plan")
                state_dict = await demande_sommaire_ou_gen(synth_id, state_dict)
                log.info("STEP 2: Generating a plan")
                # Step 1 is consumed in the same session thanks to event_call
                # so we continue...

            if state_dict["step"] == 3:
                log.info("STEP 3: Generating a plan")
                return await genere_et_valide_sommaire(synth_id, state_dict)
            log.info("STEP 4: Validating the plan")
            if state_dict["step"] == 31:
                log.info("STEP 31: Validating the plan again")
                user_confirm = last_user_message.strip().lower()
                if user_confirm in ["ok", "oui", "yes", "valider", ""]:
                    state_dict["step"] = 4
                else:
                    state_dict["instructions_supp"] = last_user_message
                    # Start again for the plan
                    return await genere_et_valide_sommaire(synth_id, state_dict)

            if (
                state_dict["step"] == 4
            ):  # Generate the resume, then propose it for validation
                return await genere_resume_et_valide(synth_id, state_dict, session)

            if state_dict["step"] == 41:  # Final validation of the resume/add modifications
                user_confirm = last_user_message.strip().lower()
                if user_confirm in ["ok", "oui", "yes", "valider", ""]:
                    response = session.delete(
                        f"{OPENAI_API_BASE_URL}/collections/{state_dict['collection_id']}"
                    )
                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {
                                "content": """
---
#### ✅ Mission accomplie !
Le travail ici est terminé.  
Pour travailler sur une nouvelle synthèse, **ouvrez une nouvelle conversation**.

Merci pour votre confiance ! 😊

---
                                """,
                                "done": True,
                                "hidden": False,
                            },
                        }
                    )
                    # Only keep step and response sommaire to know if user canceled pipeline or not
                    state_dict = {
                        "step": 99,
                        "response_sommaire": state_dict["response_sommaire"],
                        "collection_id": state_dict["collection_id"],
                    }
                    update_state(synth_id, state_dict)

                    # __files__ = None  #Does not work, api call to delete?
                    return body
                else:
                    return await relance_synthese_si_modif(synth_id, state_dict)
            if state_dict["step"] == 99:
                # Only keep step and response sommaire to know if user canceled pipeline or not and display a message on the front
                state_dict = {
                    "step": 99,
                    "response_sommaire": state_dict["response_sommaire"],
                    "collection_id": state_dict["collection_id"],
                }
                update_state(synth_id, state_dict)
                try:
                    response = session.delete(
                        f"{OPENAI_API_BASE_URL}/collections/{state_dict['collection_id']}"
                    )
                except Exception as e:
                    log.info(f"No collections to delete ({response.text})")
                    log.info(e)
                if state_dict["response_sommaire"] is False:
                    message = "#### Le pipeline a été annulé."
                elif state_dict["response_sommaire"] == "problem":
                    message = "#### Le pipeline a rencontré un problème."
                else:
                    message = "#### ✅ Mission accomplie !"
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {
                            "content": f"""
---
{message}
Le travail ici est terminé.  
Pour travailler sur une nouvelle synthèse, **ouvrez une nouvelle conversation**.

Merci pour votre confiance ! 😊

---
    
                                """,
                            "done": True,
                            "hidden": False,
                        },
                    }
                )
                return body

            # Security / fallback
            update_state(synth_id, {"step": 99, "response_sommaire": "problem"})
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {
                        "content": "On dirait que le pipeline a un problème, mes excuses pour le désagrément et merci de réessayer plus tard.",
                        "done": True,
                        "hidden": False,
                    },
                }
            )
            return body
        except Exception as e:
            update_state(synth_id, {"step": 99, "response_sommaire": "problem"})
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {
                        "content": f"On dirait que le pipeline a un problème, mes excuses pour le désagrément et merci de réessayer plus tard. ({e})",
                        "done": True,
                        "hidden": False,
                    },
                }
            )
            return body
