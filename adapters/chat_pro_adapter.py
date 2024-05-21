import asyncio
import json
import time
import uuid

import httpx
from fastapi import Request

from adapters.base_adapter import BaseAdapter
from event_stream_resolver import EventStreamResolver


class ChatProAdapter(BaseAdapter):
    def __init__(self, password, proxy, api_proxy):
        self.password = password
        self.last_time = None
        if proxy:
            self.proxies = {
                'http://': proxy,
                'https://': proxy,
            }
        else:
            self.proxies = None

        if api_proxy:
            self.api_base = api_proxy
        else:
            self.api_base = 'https://chatpro.ai-pro.org'

    @staticmethod
    def convert_messages_to_prompt(messages):
        content_array = []
        for message in messages:
            content = message["content"]
            content_array.append(content)
        return "\n---------\n".join(content_array)

    def convert_openai_data(self, openai_params):
        # openAI_models = ["gpt-3.5-turbo", "gpt-4-1106-preview", "gpt-4-pro-max"]

        messages = openai_params["messages"]
        temperature = openai_params.get("temperature", 1)
        top_p = openai_params.get("top_p", 1)
        text = self.convert_messages_to_prompt(messages)
        model: str = openai_params["model"]

        return {
            'sender': 'User',
            'text': text,
            'current': True,
            'isCreatedByUser': True,
            'parentMessageId': '00000000-0000-0000-0000-000000000000',
            'conversationId': None,
            'messageId': str(uuid.uuid4()),
            'error': False,
            'generation': '',
            'responseMessageId': None,
            'overrideParentMessageId': None,
            'endpoint': "openAI",
            'model': model,
            'chatGptLabel': None,
            'promptPrefix': None,
            'temperature': temperature,
            'top_p': top_p,
            'presence_penalty': 0,
            'frequency_penalty': 0,
            'token': None,
            'isContinued': False,
            'isLimited': False,
        }

    def convert_google_data(self, openai_params, model):
        # google_models = ["chat-bison", "text-bison", "codechat-bison"]

        messages = openai_params["messages"]
        temperature = openai_params.get("temperature", 1)
        text = self.convert_messages_to_prompt(messages)

        return {
            'sender': 'User',
            'text': text,
            'current': True,
            'isCreatedByUser': True,
            'parentMessageId': '00000000-0000-0000-0000-000000000000',
            'conversationId': None,
            'messageId': str(uuid.uuid4()),
            'error': False,
            'generation': '',
            'responseMessageId': None,
            'overrideParentMessageId': None,
            'endpoint': 'google',
            'model': model,
            'modelLabel': None,
            'promptPrefix': None,
            'temperature': temperature,
            'maxOutputTokens': 1024,
            'topP': 0.95,
            'topK': 40,
            'token': None,
            'isContinued': False,
            'isLimited': False,
        }

    async def chat(self, request: Request):
        openai_params = await request.json()
        headers = request.headers
        stream = openai_params.get("stream")
        model = openai_params.get("model")
        google_model_prefix = "google-"
        if model.startswith(google_model_prefix):
            google_model = model.removeprefix(google_model_prefix)
            json_data = self.convert_google_data(openai_params, google_model)
        else:
            json_data = self.convert_openai_data(openai_params)

        api_key = self.get_request_api_key(headers)
        if api_key != self.password:
            raise Exception(f"Error: 密钥无效")

        headers = {
            'Host': 'chatpro.ai-pro.org',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer undefined',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
            'Accept': '*/*',
            'Origin': 'https://chatpro.ai-pro.org',
            'Referer': 'https://chatpro.ai-pro.org/chat/new',
        }

        api_url = f'{self.api_base}/api/ask/{json_data["endpoint"]}'
        last_text = ""
        last_time = time.time()
        event_stream_resolver = EventStreamResolver()
        async with httpx.AsyncClient(http2=False, timeout=120.0, verify=False, proxies=self.proxies) as client:
            if not stream:
                response = await client.post(
                    url=api_url,
                    headers=headers,
                    json=json_data,
                )
                if response.is_error:
                    raise Exception(f"Error: {response.status_code}")

                raw_data = response.text
                event_stream_resolver.buffer(raw_data)
                for message in event_stream_resolver.get_messages():
                    data = self.get_data(message)
                    if data.get("final"):
                        text = data["responseMessage"]["text"]

                if text:
                    yield self.to_openai_response(model=model, content=text)
                else:
                    raise Exception(f"no result")
            else:
                async with client.stream(
                        method="POST",
                        url=api_url,
                        headers=headers,
                        json=json_data
                ) as response:
                    if response.is_error:
                        raise Exception(f"Error: {response.status_code}")

                    yield self.to_openai_response_stream_begin(model=model)
                    async for raw_data in response.aiter_text():
                        if raw_data:
                            event_stream_resolver.buffer(raw_data)
                            for message in event_stream_resolver.get_messages():
                                try:
                                    data = self.get_data(message)
                                    text = self.take_text(data)
                                except json.JSONDecodeError as ex:
                                    print("incomplete!!! ", ex)
                                    continue

                                if text == "":
                                    continue

                                new_text = text[len(last_text):]
                                last_text = text

                                yield self.to_openai_response_stream(model=model, content=new_text)
                                await self.rate_limit_sleep_async(last_time)
                                last_time = time.time()

                    await asyncio.sleep(1)
                    yield self.to_openai_response_stream_end(model=model)
                    yield "[DONE]"

    @staticmethod
    def get_data(message: str) -> json:
        if message.startswith("event: message"):
            return json.loads(message.lstrip("event: message\ndata:"))
        return None

    @staticmethod
    def take_text(data: json) -> str:
        if data.get("message") == True:
            return data["text"]
        elif data.get("final"):
            return data["responseMessage"]["text"]
        return ""
