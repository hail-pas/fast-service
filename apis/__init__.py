from typing import List, Union

from fastapi import FastAPI

from apis.http import http_app
from apis.websocket import ws_app

roster: List[List[Union[FastAPI, str]]] = [
    [ws_app, "/ws", "Socket IO"],
    [http_app, "", "API"],
]
