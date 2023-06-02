from typing import Union

from fastapi import FastAPI

from apis.http import http_routes
from apis.websocket import ws_app
from apis.http.apps.outer import api_app as outer_app

roster: list[list[Union[FastAPI, str]]] = [
    [ws_app, "/ws", "Socket IO"],
    [http_routes, "", "API"],
    [outer_app, "/api", "Outer"],
]
