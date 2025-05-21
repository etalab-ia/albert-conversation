
"""
This script is used to create a pipe that can be used to call the agent function from the frontend.
Copy and paste this directly onto the frontend in the admin panel.
"""

from pydantic import BaseModel, Field
import smolagents
import requests
from types import SimpleNamespace
from smolagents.agents import CodeAgent
from open_webui.custom_functions.prompts.code_agent_V2 import sys_prompt
import os
import numpy as np

#print current directory
print(os.getcwd())

# Can be empty
ADDON_INSTRUCTION = "\n Refuse toutes questions non liées à de l'administratif, et invites l'utilisateur à utiliser un autre compagnon spécialisé si tu ne peux pas répondre. En cas de doute sur une question, demande à l'utilisateur de préciser sa demande."


# Parsing request metadata to get potential files or collections attached
def parse_metadata(metadata):
    """
    Given a metadata dict, returns a tuple:
        (list_of_collection_names, list_of_file_names)
    """
    collections_set = set()
    description_set = set()
    file_names = []

    files = metadata.get("files")

    # No files in the metadata.
    if not files:
        return {
            "collections": [],
            "collections_descriptions": [],
            "files": [],
        }

    for item in files:
        # --- Case A: Item with a nested "file" key (new structure) ---
        if "file" in item:
            file_obj = item["file"]
            # Try a few places for the file name.
            file_name = (
                file_obj.get("filename")
                or file_obj.get("meta", {}).get("name")
                or file_obj.get("name")
                or "Unnamed File"
            )
            file_names.append(file_name)

            # Check if there is a collection info.
            collection_name = file_obj.get("meta", {}).get(
                "collection_name"
            ) or file_obj.get("collection_name")
            if collection_name:
                collections_set.add(collection_name)
                description_set.add(file_obj.get("description", ""))

        # --- Case B: Item that is a collection  ---
        elif item.get("type") == "collection":
            # For a collection item, we may use `name` (preferred) or fallback to an identifier.
            collection_name = (
                item.get("collection_name") or item.get("id") or "Unnamed Collection"
            )
            collections_set.add(collection_name)
            description_set.add(item.get("description"))

            # If there is an internal file list inside the collection, process them.
            internal_files = item.get("files", [])
            if internal_files and isinstance(internal_files, list):
                for f in internal_files:
                    file_name = (
                        f.get("meta", {}).get("name")
                        or f.get("name")
                        or f.get("id")
                        or "Unnamed File"
                    )
                    file_names.append(file_name)
        # --- Case C: Item that is a file (or contains a "collection" key) ---
        elif item.get("type") == "file" or ("collection" in item):
            # Try to extract the file name (check in meta, then top-level)
            file_name = (
                item.get("meta", {}).get("name") or item.get("name") or "Unnamed File"
            )
            file_names.append(file_name)

            # If the file item has a collection associated with it, add that into the collection list.
            if "collection" in item and isinstance(item["collection"], dict):
                collection_name = item["meta"].get("collection_name")
                collection_description = item["description"]
                if collection_name:
                    collections_set.add(collection_name)
                    description_set.add(collection_description)
            # Alternatively, sometimes the collection is indicated at the top level.
            if "collection_name" in item:
                collections_set.add(item["collection_name"])

        # --- Case D: Fallback if none of the above patterns match ---
        else:
            file_name = (
                item.get("meta", {}).get("name") or item.get("name") or "Unnamed File"
            )
            file_names.append(file_name)

    # Convert set of collections to list; if you care about order, you might sort.
    collections_list = list(collections_set)
    description_list = list(description_set)
    return {
        "collections": collections_list,
        "collections_descriptions": description_list,
        "files": file_names,
    }


def serialize_content_blocks(content_blocks):
    content = ""

    for block in content_blocks:
        if not block:
            return
        reasoning_display_content = "\n".join(
            (f"> {line}" if not line.startswith(">") else line)
            for line in block["content"].splitlines()
        )
        reasoning_duration = block.get("duration", None)
        content = f'{content}\n<details type="reasoning" done="true" duration="{reasoning_duration}">\n<summary>Thought for {reasoning_duration} seconds</summary>\n{reasoning_display_content}\n</details>\n'

    return content.strip()


class Pipe:
    class Valves(BaseModel):
        ALBERT_URL: str = Field(default="https://albert.api.staging.etalab.gouv.fr/v1")
        ALBERT_KEY: str = Field(default="")
        DEFAULT_MODEL: str = Field(default="meta-llama/Llama-3.1-8B-Instruct")
        ANALYTICS_MODEL: str = Field(default="meta-llama/Llama-3.3-70B-Instruct")
        REDACTOR_MODEL: str = Field(default="meta-llama/Llama-3.3-70B-Instruct")
        SUPERVISOR_MODEL: str = Field(default="meta-llama/Llama-3.3-70B-Instruct")
        COLLECTIONS: str = Field(default="fiches_vos_droits,fiches_travail")
        DESCRIPTION: str = Field(
            "Contient des informations intéressantes sur le travail et le droit en France. Base de données administrative."
        )
        MESSAGES_MEMORY: int = Field(default=5)
        SHOW_CODE: bool = Field(default=True)

    def __init__(self):
        self.valves = self.Valves()
        # If set to true it will prevent default RAG pipeline
        self.file_handler = True
        self.citation = True

    async def pipe(
        self,
        body: dict,
        request=None,
        __event_emitter__=None,
        __user__=None,
        __request__=None,
        __metadata__=None,
    ):

        # attach REDACTOR_MODEL, ANALYTICS_MODEL, SUPERVISOR_MODEL into new env variables
        os.environ["REDACTOR_MODEL"] = self.valves.REDACTOR_MODEL
        os.environ["ANALYTICS_MODEL"] = self.valves.ANALYTICS_MODEL
        os.environ["SUPERVISOR_MODEL"] = self.valves.SUPERVISOR_MODEL
        os.environ["DEFAULT_MODEL"] = self.valves.DEFAULT_MODEL
        os.environ["COLLECTIONS"] = self.valves.COLLECTIONS
        os.environ["ALBERT_URL"] = self.valves.ALBERT_URL
        os.environ["ALBERT_KEY"] = self.valves.ALBERT_KEY
        show_code = self.valves.SHOW_CODE

        session = requests.session()
        session.headers = {"Authorization": f"Bearer {self.valves.ALBERT_KEY}"}

        # We have to wait until now to import this, so it can read the env vars
        from open_webui.custom_functions.tools.tools_creation import create_tools

        def remove_consecutive_assistants(messages):
            filtered_messages = []
            last_role = None
            for msg in messages:
                if msg["role"] == "assistant" and last_role == "assistant":
                    continue  # Ignore consecutive assistant messages
                filtered_messages.append(msg)
                last_role = msg["role"]
            return filtered_messages

        # Flatten the roles to have a messages history as flat dict (readable by every model)
        from smolagents.models import MessageRole
        flatten_roles = {
            MessageRole.SYSTEM: "system",
            MessageRole.USER: "user",
            MessageRole.ASSISTANT: "assistant",
            MessageRole.TOOL_RESPONSE: "user",
            MessageRole.TOOL_CALL: "user",
        }
        # This will be used for the agent
        def custom_model_albert(messages, stop_sequences=[]):
            messages = remove_consecutive_assistants(messages)
            messages = [
                {
                    "role": flatten_roles[message["role"]],
                    "content": message["content"][0]["text"],
                }
                for message in messages
            ]

            data = {
                "model": self.valves.SUPERVISOR_MODEL,
                "messages": messages,
                "stream": False,
                "n": 1,
                "temperature": 0.2,
                "repetition_penalty": 1,
                "max_tokens": 1024,
                "stop": stop_sequences,
            }
            response = session.post(
                url=f"{self.valves.ALBERT_URL}/chat/completions",
                json=data,
                timeout=100000,
            )
            print(response.text)
            answer = response.json()["choices"][0]["message"]
            return SimpleNamespace(**answer)  # needed to have a 'json'

        # Detecting if user is attaching files or collections on the frontend
        collections = parse_metadata(__metadata__)["collections"]
        description = " ".join(parse_metadata(__metadata__)["collections_descriptions"])

        # If user is attaching files or collections, we need to use the RAG tool
        if collections != []:
            prefix = "(APPELLE LE TOOL RAG)"
            description = ""

        # If user is not attaching files or collections, we can use the Albert RAG
        else:
            prefix = ""
            description = self.valves.DESCRIPTION

        tools = create_tools(
            custom_model_albert,
            collections,
            description,
            __user__,
            __request__,
            __event_emitter__,
        )
        # Messages memory
        n_depth_message = (
            self.valves.MESSAGES_MEMORY + 1
            if self.valves.MESSAGES_MEMORY % 2 == 0
            else self.valves.MESSAGES_MEMORY
        )
        conversation_history = str(body["messages"][-n_depth_message:-1])
        print(sys_prompt)

        agent = CodeAgent(
            tools=tools,
            model=custom_model_albert,
            max_steps=5,
            verbosity_level=3,
            prompt_templates={
                "system_prompt": sys_prompt.replace(
                    "{{conversation_history}}", conversation_history
                )
                + ADDON_INSTRUCTION
            },
        )

        try:
            # Iterate through steps returned from the agent's execution
            for step_number, step in enumerate(
                agent.run(prefix + body["messages"][-1]["content"], stream=True), 1
            ):
                if isinstance(
                    step, smolagents.memory.ActionStep
                ):  # Handle intermediate steps and ignore final step

                    # Serialize the current state of ALL content blocks
                    if not show_code:
                        content = step.model_output.split("Code:")[0].replace(
                            "Thought: ", ""
                        )
                    else:
                        content = step.model_output

                    content_block = {
                        "type": "reasoning",
                        "content": content,
                        "step_number": step_number,
                        "duration": np.round(step.duration, 2),
                    }

                    pretty_content = serialize_content_blocks([content_block])

                    # Emit ALL content blocks so far, including intermediate reasoning
                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {
                                "content": pretty_content,
                                "done": False,  # Mark as incomplete, to behave correctly
                                "hidden": False,
                            },
                        }
                    )

                # Track the final step
            final_step = step.replace(
                            "\nSi cette réponse convient, appelle juste final_answer(ta_variable) pour l'envoyer à l'utilisateur. Sinon continue les recherches ou pose une question à l'utilisateur.",
                            "")

            if final_step and __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {
                            "content": final_step,
                            "done": True,  # Mark completion explicitly
                            "hidden": False,
                        },
                    }
                )
            return #final_step # This is only needed for endpoint testing but would break the reasonning stream if left
        except Exception as e:
            print(e)
            return "Désolé, une erreur est survenue, je crois que mes outils sont en panne."

        return #body # This is only needed for endpoint testing but would break the reasonning stream if left
