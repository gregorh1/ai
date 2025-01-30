"""
title: Azure OpenAI Pipe
author: open-webui, adapted by nomppy
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.1.0
license: MIT
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests
import os


class Pipe:
    class Valves(BaseModel):
        # You can add your custom valves here.
        AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY_GPT", "API_KEY")
        AZURE_OPENAI_ENDPOINT: str = os.getenv(
            "AZURE_OPENAI_ENDPOINT_GPT", "API_ENDPOINT"
        )
        AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv(
            "AZURE_OPENAI_DEPLOYMENT_NAME_GPT", "DEPLOYMENT_NAME"
        )
        AZURE_OPENAI_API_VERSION: str = os.getenv(
            "AZURE_OPENAI_API_VERSION_GPT", "API_VERSION"
        )

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "azure_openai_pipeline"
        self.name = "Azure OpenAI Pipe"
        self.valves = self.Valves()
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        headers = {
            "api-key": self.valves.AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json",
        }

        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/deployments/{self.valves.AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={self.valves.AZURE_OPENAI_API_VERSION}"

        allowed_params = {
            "messages",
            "temperature",
            "role",
            "content",
            "contentPart",
            "contentPartImage",
            "enhancements",
            "dataSources",
            "n",
            "stream",
            "stop",
            "max_tokens",
            "presence_penalty",
            "frequency_penalty",
            "logit_bias",
            "user",
            "function_call",
            "funcions",
            "tools",
            "tool_choice",
            "top_p",
            "log_probs",
            "top_logprobs",
            "response_format",
            "seed",
        }
        # remap user field
        if "user" in body and not isinstance(body["user"], str):
            body["user"] = (
                body["user"]["id"] if "id" in body["user"] else str(body["user"])
            )
        filtered_body = {k: v for k, v in body.items() if k in allowed_params}
        # log fields that were filtered out as a single line
        if len(body) != len(filtered_body):
            print(
                f"Dropped params: {', '.join(set(body.keys()) - set(filtered_body.keys()))}"
            )

        try:
            r = requests.post(
                url=url,
                json=filtered_body,
                headers=headers,
                stream=True,
            )

            r.raise_for_status()
            if body["stream"]:
                return r.iter_lines()
            else:
                return r.json()
        except Exception as e:
            print("Requests error in Azure pipeline")
            if r:
                text = r.text
                return f"Error: {e} ({text})"
            else:
                return f"Error: {e}"
