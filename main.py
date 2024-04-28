import json
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from adapters.ai_pro_adapter import AIProAdapter
from models import models_list

LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
PORT = int(os.getenv("PORT", 8000))
PROXY = os.getenv("PROXY")
PASSWORD = os.getenv("PASSWORD", "ninomae")

adapter = AIProAdapter(password=PASSWORD, proxy=PROXY)
print('adapter: ' + str(adapter))

app = FastAPI()
print('app: ' + str(app))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods, including OPTIONS
    allow_headers=["*"],
)


@app.api_route(
    "/v1/chat/completions",
    methods=["POST", "OPTIONS"],
)
@app.api_route(
    "/hf/v1/chat/completions",
    methods=["POST", "OPTIONS"],
)
async def chat(request: Request):
    openai_params = await request.json()
    if openai_params.get("stream", False):

        async def generate():
            async for response in adapter.chat(request):
                if response == "[DONE]":
                    yield "data: [DONE]"
                    break
                yield f"data: {json.dumps(response)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        response = adapter.chat(request)
        openai_response = await response.__anext__()
        return JSONResponse(content=openai_response)


@app.get("/v1/models")
@app.get("/hf/v1/models")
async def models(request: Request):
    # return a dict with key "object" and "data", "object" value is "list", "data" values is models list
    return JSONResponse(content={"object": "list", "data": models_list})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level=LOG_LEVEL)
