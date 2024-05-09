import asyncio
import time
from util import num_tokens_from_string, generate_random_string


class BaseAdapter:
    @staticmethod
    def to_openai_response_stream_begin(model):
        return {
            "id": f"chatcmpl-{generate_random_string(29)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "delta": {
                        "content": "",
                        "role": "assistant"
                    },
                    "index": 0,
                    "finish_reason": None
                }
            ]
        }

    @staticmethod
    def to_openai_response_stream(model, content, role=None):
        openai_response = {
            "id": f"chatcmpl-{generate_random_string(29)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "delta": {
                        "content": content,
                    },
                    "index": 0,
                    "finish_reason": None
                }
            ],
        }

        if role is not None:
            openai_response['choices'][0]['delta']['role'] = role

        return openai_response

    @staticmethod
    def to_openai_response_stream_end(model):
        return {
            "choices": [
                {
                    "delta": {},
                    "finish_reason": "stop",
                    "index": 0
                }
            ],
            "created": int(time.time()),
            "id": f"chatcmpl-{generate_random_string(29)}",
            "model": model,
            "object": "chat.completion.chunk"
        }

    @staticmethod
    def to_openai_response(model, content):
        completion_tokens = num_tokens_from_string(content)
        openai_response = {
            "id": f"chatcmpl-{generate_random_string(29)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": completion_tokens,
                "total_tokens": completion_tokens,
            },
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "index": 0,
                    "finish_reason": "stop"
                }
            ],
        }

        return openai_response

    @staticmethod
    async def rate_limit_sleep_async(last_time, min_elapsed_time=0.02):
        if last_time:
            elapsed_time = time.time() - last_time
            if elapsed_time < min_elapsed_time:
                await asyncio.sleep(min_elapsed_time - elapsed_time)

    @staticmethod
    def get_request_api_key(headers):
        auth_header = headers.get("authorization", None)
        if auth_header:
            auth_header_array = auth_header.split(" ")
            if len(auth_header_array) == 1:
                return ""
            return auth_header_array[1]
        else:
            return ""
