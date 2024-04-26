import time
from util import num_tokens_from_string, generate_random_string


class BaseAdapter:
    def to_openai_response_stream_begin(self, model):
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

    def to_openai_response_stream(self, model, content, role=None):
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

    def to_openai_response_stream_end(self, model):
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

    def to_openai_response(self, model, content):
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
