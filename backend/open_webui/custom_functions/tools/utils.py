

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


