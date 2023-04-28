from typing import List, Union

from fastapi import FastAPI

from apis.http import http_routes
from apis.websocket import ws_app
from apis.http.apps.outer import api_app as outer_app

roster: List[List[Union[FastAPI, str]]] = [
    [ws_app, "/ws", "Socket IO"],
    [http_routes, "", "API"],
    [outer_app, "/api", "Outer"],
]
