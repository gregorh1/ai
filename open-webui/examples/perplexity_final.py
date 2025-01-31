"""
title: Perplexity Manifold Pipe
author: justinh-rahb and moblangeois
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.1.1
license: MIT
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator
from open_webui.utils.misc import get_last_user_message
from open_webui.utils.misc import pop_system_message

import os
import requests
import json


class Pipe:
    class Valves(BaseModel):
        NAME_PREFIX: str = Field(
            default="Perplexity/",
            description="The prefix applied before the model names.",
        )
        PERPLEXITY_API_BASE_URL: str = Field(
            default="https://api.perplexity.ai",
            description="The base URL for Perplexity API endpoints.",
        )
        PERPLEXITY_API_KEY: str = Field(
            default="",
            description="Required API key to access Perplexity services.",
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()

    def pipes(self):
        return [
            {
                "id": "sonar",
                "name": f"{self.valves.NAME_PREFIX}Sonar",
            },
            {
                "id": "sonar-pro",
                "name": f"{self.valves.NAME_PREFIX}Sonar Pro",
            },
            {
                "id": "sonar-reasoning",
                "name": f"{self.valves.NAME_PREFIX}Sonar Reasoning",
            },
        ]

    def pipe(self, body: dict, __user__: dict) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")

        if not self.valves.PERPLEXITY_API_KEY:
            raise Exception("PERPLEXITY_API_KEY not provided in the valves.")

        headers = {
            "Authorization": f"Bearer {self.valves.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }

        system_message, messages = pop_system_message(body.get("messages", []))
        system_prompt = "You are a helpful assistant."
        if system_message is not None:
            system_prompt = system_message["content"]

        model_id = body["model"]
        # Remove all possible prefixes to get the raw model name
        prefixes_to_remove = [
            self.valves.NAME_PREFIX,  # Removes "Perplexity/"
            "perplexity.",           # Removes "perplexity."
            "perplexity_via_api."    # Removes "perplexity_via_api."
        ]
        
        for prefix in prefixes_to_remove:
            if model_id.startswith(prefix):
                model_id = model_id[len(prefix):]

        payload = {
            "model": model_id,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "stream": body.get("stream", True),
            "temperature": 0.2,
            "top_p": 0.9,
        }

        if body.get("return_citations"):
            payload["return_citations"] = body["return_citations"]
        if body.get("return_images"):
            payload["return_images"] = body["return_images"]

        print(payload)

        try:
            r = requests.post(
                url=f"{self.valves.PERPLEXITY_API_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
            )

            r.raise_for_status()

            if body.get("stream", False):
                def process_stream():
                    citations = []
                    content_finished = False
                    
                    for line in r.iter_lines():
                        if line:
                            try:
                                json_response = json.loads(line.decode('utf-8').replace('data: ', ''))
                                
                                # Handle content
                                if 'choices' in json_response:
                                    content = json_response['choices'][0].get('delta', {}).get('content', '')
                                    if content:
                                        yield content
                                    # Check if this is the last content chunk
                                    if json_response['choices'][0].get('finish_reason') == 'stop':
                                        content_finished = True
                                
                                # Store citations
                                if 'citations' in json_response:
                                    citations = json_response['citations']
                                
                                # Add citations only after content is complete
                                if content_finished and citations:
                                    def shorten_url(url, max_length=50):
                                        if len(url) <= max_length:
                                            return url
                                        return url[:max_length-3] + "..."
                                    
                                    citation_links = '\n\nSources:\n' + '\n'.join(
                                        f'[{i+1}]({citation}) - {shorten_url(citation)}' 
                                        for i, citation in enumerate(citations)
                                    )
                                    yield citation_links
                                    break  # Exit after adding citations
                                    
                            except json.JSONDecodeError:
                                continue
                return process_stream()
            else:
                response = r.json()
                formatted_response = {
                    "id": response["id"],
                    "model": response["model"],
                    "created": response["created"],
                    "usage": response["usage"],
                    "object": response["object"],
                    "choices": [
                        {
                            "index": choice["index"],
                            "finish_reason": choice["finish_reason"],
                            "message": {
                                "role": choice["message"]["role"],
                                "content": choice["message"]["content"],
                            },
                            "delta": {"role": "assistant", "content": ""},
                        }
                        for choice in response["choices"]
                    ],
                }

                # Add citations if present
                if "citations" in response:
                    citation_links = '\n\nSources:\n' + '\n'.join(
                        f'[{i+1}]({citation})' 
                        for i, citation in enumerate(response["citations"])
                    )
                    formatted_response["choices"][0]["message"]["content"] += citation_links

                return formatted_response

        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP Error: {e}"
            try:
                error_json = r.json()
                if 'error' in error_json:
                    error_message = f"API Error: {error_json['error']}"
            except:
                pass
            return error_message
        except Exception as e:
            return f"Error: {str(e)}"
