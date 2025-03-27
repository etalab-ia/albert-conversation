from pydantic import BaseModel, Field
from open_webui.utils.functions.agent1 import agent
import json
import time
import sys
import smolagents
import html
import re

# Import required functions from the middleware module


def serialize_content_blocks(content_blocks, raw=False):
    content = ""

    for block in content_blocks:
        if block["type"] == "text":
            content = f"{content}{block['content'].strip()}\n"
        elif block["type"] == "tool_calls":
            attributes = block.get("attributes", {})
            block_content = block.get("content", [])
            results = block.get("results", [])
            if results:
                result_display_content = ""
                for result in results:
                    tool_call_id = result.get("tool_call_id", "")
                    tool_name = ""
                    for tool_call in block_content:
                        if tool_call.get("id", "") == tool_call_id:
                            tool_name = tool_call.get("function", {}).get("name", "")
                            break
                    result_display_content = f"{result_display_content}\n> {tool_name}: {result.get('content', '')}"

                if not raw:
                    content = f'{content}\n<details type="tool_calls" done="true" content="{html.escape(json.dumps(block_content))}" results="{html.escape(json.dumps(results))}">\n<summary>Tool Executed</summary>\n{result_display_content}\n</details>\n'
            else:
                tool_calls_display_content = ""
                for tool_call in block_content:
                    tool_calls_display_content = f"{tool_calls_display_content}\n> Executing {tool_call.get('function', {}).get('name', '')}"

                if not raw:
                    content = f'{content}\n<details type="tool_calls" done="true" content="{html.escape(json.dumps(block_content))}">\n<summary>Tool Executing...</summary>\n{tool_calls_display_content}\n</details>\n'

        elif block["type"] == "reasoning":
            reasoning_display_content = "\n".join(
                (f"> {line}" if not line.startswith(">") else line)
                for line in block["content"].splitlines()
            )

            reasoning_duration = block.get("duration", None)

            if reasoning_duration is not None:
                if raw:
                    content = f'{content}\n<{block["start_tag"]}>{block["content"]}<{block["end_tag"]}>\n'
                else:
                    content = f'{content}\n<details type="reasoning" done="true" duration="{reasoning_duration}">\n<summary>Thought for {reasoning_duration} seconds</summary>\n{reasoning_display_content}\n</details>\n'
            else:
                if raw:
                    content = f'{content}\n<{block["start_tag"]}>{block["content"]}<{block["end_tag"]}>\n'
                else:
                    content = f'{content}\n<details type="reasoning" done="true">\n<summary>Step {block.get("step_number", "x")}</summary>\n{reasoning_display_content}\n</details>\n'

        elif block["type"] == "code_interpreter":
            attributes = block.get("attributes", {})
            output = block.get("output", None)
            lang = attributes.get("lang", "")

            content_stripped, original_whitespace = split_content_and_whitespace(
                content
            )
            if is_opening_code_block(content_stripped):
                content = content_stripped.rstrip("`").rstrip() + original_whitespace
            else:
                content = content_stripped + original_whitespace

            if output:
                output = html.escape(json.dumps(output))

                if raw:
                    content = f'{content}\n<code_interpreter type="code" lang="{lang}">\n{block["content"]}\n</code_interpreter>\n```output\n{output}\n```\n'
                else:
                    content = f'{content}\n<details type="code_interpreter" done="true" output="{output}">\n<summary>Analyzed</summary>\n```{lang}\n{block["content"]}\n```\n</details>\n'
            else:
                if raw:
                    content = f'{content}\n<code_interpreter type="code" lang="{lang}">\n{block["content"]}\n</code_interpreter>\n'
                else:
                    content = f'{content}\n<details type="code_interpreter" done="true">\n<summary>Analyzing...</summary>\n```{lang}\n{block["content"]}\n```\n</details>\n'

        else:
            block_content = str(block["content"]).strip()
            content = f"{content}{block['type']}: {block_content}\n"

    return content.strip()


class Pipe:
    class Valves(BaseModel):
        MODEL_ID: str = Field(default="")

    def __init__(self):
        self.valves = self.Valves()

    async def pipe(self, body: dict, __event_emitter__=None):
        try:
            # Log the input for debugging purposes
            print(body)  # This will print the configuration options and the input body

            # Create content blocks for intermediate steps
            content_blocks = []

            # Add a reasoning block at the start to track intermediate steps
            reasoning_start_time = time.time()
            reasoning_block = {
                "type": "reasoning",
                "content": "",
                "start_tag": "think",
                "end_tag": "/think",
                "attributes": {"type": "reasoning_content"},
                "started_at": reasoning_start_time,
            }
            content_blocks.append(reasoning_block)

            # Store intermediate steps and the final step
            intermediate_steps = []
            final_step = None

            # Iterate through steps returned from the agent's execution
            for step_number, step in enumerate(
                agent.run(body["messages"][-1]["content"], stream=True), 1
            ):
                if isinstance(
                    step, smolagents.memory.ActionStep
                ):  # Handle intermediate steps
                    print(
                        step, file=sys.stderr
                    )  # Log the intermediate steps for debugging
                    intermediate_steps.append(step)

                    # Serialize the current state of ALL content blocks
                    content_block = {
                        "type": "reasoning",
                        "content": step.model_output,
                        "step_number": step_number,
                    }
                    cumulative_content = serialize_content_blocks([content_block])

                    # Emit ALL content blocks so far, including intermediate reasoning
                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {
                                "content": cumulative_content,
                                "done": False,  # Mark as incomplete, to behave correctly
                                "hidden": False,
                            },
                        }
                    )

                # Track the final step
                final_step = step

            # Add the final reasoning block or result
            if content_blocks and content_blocks[-1]["type"] == "reasoning":
                reasoning_end_time = time.time()
                content_blocks[-1]["ended_at"] = reasoning_end_time
                content_blocks[-1]["duration"] = int(
                    reasoning_end_time - reasoning_start_time
                )

            # Serialize the **final state of all content blocks** (including all intermediate reasoning steps)
            final_content = serialize_content_blocks(content_blocks)

            if final_content and __event_emitter__:
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

            # Return the final step for further processing
            return
        except Exception as e:
            print(e)
            return "Désolé, une erreur est survenue, je crois que mes outils sont en panne."
