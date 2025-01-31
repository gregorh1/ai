"""
title: AGI Chat Pipe
version: 0.1.0
license: MIT
"""

from typing import Union, Generator, Iterator, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import requests
import os
import json


class Pipe:
    class Valves(BaseModel):
        AGI_API_URL: str = Field(
            default="http://localhost:8080/api/agi/chat",
            description="AGI chat endpoint URL"
        )
        AGI_API_KEY: str = Field(
            default=os.getenv("AGI_API_KEY", ""),
            description="API key for authentication"
        )
        DEFAULT_MODEL: str = Field(
            default="gpt-4o",
            description="Default model to use"
        )
        DEFAULT_TEMPERATURE: float = Field(
            default=0.7,
            description="Default temperature for generation"
        )
        DEFAULT_MAX_TOKENS: int = Field(
            default=16384,
            description="Default max tokens for generation"
        )

    def __init__(self):
        self.name = "AGI Chat Pipe"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"Starting {self.name}")
        pass

    async def on_shutdown(self):
        print(f"Shutting down {self.name}")
        pass

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        headers = {
            "Authorization": f"Bearer {self.valves.AGI_API_KEY}",
            "Content-Type": "application/json",
            "X-Session-Id": body.get("user", {}).get("id", "default")
        }

        # Prepare the request payload
        payload = {
            "model": body.get("model", self.valves.DEFAULT_MODEL),
            "messages": body.get("messages", []),
            "stream": body.get("stream", False),
            "temperature": body.get("temperature", self.valves.DEFAULT_TEMPERATURE),
            "max_tokens": body.get("max_tokens", self.valves.DEFAULT_MAX_TOKENS),
            "user": {
                "uuid": body.get("user", {}).get("id", "default"),
                "name": body.get("user", {}).get("name", "User"),
                "context": body.get("user", {}).get("context", ""),
                "environment": json.dumps(body.get("user", {}).get("environment", {}))
            }
        }

        try:
            response = requests.post(
                url=self.valves.AGI_API_URL,
                json=payload,
                headers=headers,
                stream=payload["stream"]
            )
            
            response.raise_for_status()

            if payload["stream"]:
                return response.iter_lines()
            else:
                return response.json()

        except Exception as e:
            error_message = f"Error connecting to AGI chat: {str(e)}"
            if 'response' in locals():
                try:
                    error_details = response.json()
                    error_message += f" - {json.dumps(error_details)}"
                except:
                    error_message += f" - {response.text}"
            return {"error": error_message}

    async def pipe_async(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> dict:
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"status": "in_progress"}})

        try:
            result = self.pipe(body)
            
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"status": "complete"}})
            
            return result
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {
                    "status": "error",
                    "error": str(e)
                }})
            return {"error": str(e)}