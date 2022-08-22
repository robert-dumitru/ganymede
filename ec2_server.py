"""
This is a temporary workaround to get around the docker chromium limitation on lambda. If you're using this, clone
this repo, install the requirements, and start the uvicorn server with the following command: ec2_server:app
"""

import logging
import subprocess
from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/")
async def forward_tb_request(request: Request) -> None:
    logging.debug(f"Captured request: {request}")
    event: dict = {"body": request.json()}
    context: dict = {}
    subprocess.Popen(["python", "-c", f"import app.process_messages.handler as handler; handler({event}, {context})"])
    return
