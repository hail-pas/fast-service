from __future__ import annotations

import abc
import enum
import string
import asyncio
from typing import TypeVar
from functools import partial

import httpx
from loguru import logger

from common.regexes import validate_ip_or_host, only_alphabetic_numeric

DATA_SEND_WAYS = ["auto", "json", "params", "data"]
PROTOCOLS = ["http", "https"]


@enum.unique
class RequestMethodEnum(enum.Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"
    # OPTIONS = "options"
    # HEAD = "head"
    # CONNECT = "connect"
    # TRACE = "trace"


class Response:
    success: bool = False
    status_code: int = None
    data: dict | str | None = None
    request_context: dict

    def __init__(
        self,
        success: bool,
        status_code: int,
        data: dict | str | None,
        request_context: dict,
        **kwargs,
    ) -> None:
        self.success = success
        self.status_code = status_code
        self.data = data
        self.request_context = request_context
        for k, v in kwargs.items():
            setattr(self, k, v)

    def json(self) -> dict | str | None:
        return self.data

    @classmethod
    def parse_response(
        cls,
        raw_response: httpx.Response,
        request_context: dict,
    ) -> ResponseType:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"success: {self.success}, status_code: {self.status_code}"


ResponseType = TypeVar("ResponseType", bound=Response)


class DefaultResponse(Response):
    @classmethod
    def parse_response(
        cls,
        raw_response: httpx.Response,
        request_context: dict,
    ) -> Response:
        status_code = raw_response.status_code
        success = False
        try:
            data = raw_response.json()
            if data.get("code") == 0:
                success = True
        except Exception:
            data = raw_response.text
        return cls(
            success=success,
            status_code=status_code,
            data=data,
            request_context=request_context,
        )


class APIBaseConfig:
    name: str
    protocol: str
    host: str
    port: int | None
    headers: dict
    params: dict
    data: dict
    json: dict
    response_cls: type[Response]
    timeout: int
    cookies: dict

    def __init__(
        self,
        name: str,
        protocol: str,
        host: str = None,
        port: int | None = None,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        response_cls: type[Response] = None,
        cookies: dict = None,
        timeout: int = None,
    ) -> None:
        if name and isinstance(self, API):
            assert (
                only_alphabetic_numeric(name) and name[0] not in string.digits
            ), "name of api is unique identifier under third which can only contains alphabet or number or underscore"
        self.name = name
        if protocol:
            assert (
                protocol in PROTOCOLS
            ), f"invalid request protocol: {protocol}"
        self.protocol = protocol
        if host:
            self.host = validate_ip_or_host(host)
        else:
            self.host = host
        self.port = port
        self.headers = headers
        self.params = params
        self.data = data
        self.json = json
        self.response_cls = response_cls
        self.cookies = cookies
        self.timeout = timeout

    def __repr__(self) -> str:
        return self.name


class API(APIBaseConfig):
    method: str
    uri: str  # /xx

    def __init__(
        self,
        name: str,
        method: str,
        uri: str,
        protocol: str = None,
        host: str = None,
        port: int | None = None,
        response_cls: type[Response] = None,
        headers: dict = None,
        cookies: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        timeout: int = None,
    ) -> None:
        assert name, "name cannot be empty"
        method = method.lower()
        assert method in [
            m.value for m in RequestMethodEnum
        ], f"invalid request method: {method}"
        self.method = method
        assert uri and uri.startswith("/"), "URI string must starts with '/'"
        self.uri = uri
        super().__init__(
            name=name,
            protocol=protocol,
            host=host,
            port=port,
            headers=headers,
            params=params,
            data=data,
            json=json,
            response_cls=response_cls,
            cookies=cookies,
            timeout=timeout,
        )


class Third(APIBaseConfig):
    apis: set[API] = set()
    _api_names: set[str] = set()
    # _request = requests.request
    api_key: str | None = None
    sign_key: str | None = None

    def __init__(
        self,
        name: str,
        protocol: str,
        host: str,
        response_cls: type[Response],
        port: int | None = None,
        apis: list[API] = None,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        cookies: dict = None,
        timeout: int = 6,
        # request: Optional[Callable] = None,
    ) -> None:
        assert all(
            [name, protocol, host, response_cls],
        ), f"value required parameters: {', '.join(['name', 'protocol', 'host', 'headers', 'data', 'response'])}"  # noqa
        super().__init__(
            name="",
            protocol=protocol,
            host=host,
            port=port,
            headers=headers,
            params=params,
            data=data,
            json=json,
            response_cls=response_cls,
            cookies=cookies,
            timeout=timeout,
        )
        self.name = name
        if apis:
            self.apis = set(apis)
            for api in apis:
                assert (
                    all(
                        i
                        in string.ascii_lowercase
                        + string.ascii_uppercase
                        + string.digits
                        + "_"
                        for i in api.name
                    )
                    and api.name[0] not in string.digits
                ), "illegal api name"
                if api.name in self._api_names:
                    raise Exception(f"two API use the same name: {api.name}")
                setattr(self, api.name, partial(self.request, api=api))
                self._api_names.add(api.name)
        # if request:
        # self._request = request

    def register_api(self, api: API) -> None:
        assert (
            all(
                i
                in string.ascii_lowercase
                + string.ascii_uppercase
                + string.digits
                + "_"
                for i in api.name
            )
            and api.name[0] not in string.digits
        ), "illegal api name"
        if api.name in self._api_names:
            raise Exception(f"the {api.name} API already exists")
        self.apis.add(api)
        setattr(self, api.name, partial(self.request, api=api))

    def update_dict(self, attr_name: str, api: API, _d: dict) -> dict:
        data = getattr(self, attr_name) or {}
        api_data = getattr(api, attr_name)
        if api_data:
            data.update(api_data)
        if _d:
            data.update(_d)
        return data

    async def request(
        self,
        api: API,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        headers: dict = None,
        cookies: dict = None,
        timeout: int = None,
        **kwargs,
    ) -> ResponseType:
        protocol = api.protocol if api.protocol else self.protocol
        host = api.host if api.host else self.host
        prefix = f"{protocol}://{host}"
        port = self.port
        if api.port:
            port = api.port
        if port:
            prefix += ":" + str(port)

        request_params = self.update_dict("params", api, params)

        request_data = self.update_dict("data", api, data)

        request_json = self.update_dict("json", api, json)

        request_headers = self.update_dict("headers", api, headers)

        request_cookies = self.update_dict("cookies", api, cookies)

        if not timeout:
            timeout = self.timeout
            if api.timeout:
                timeout = api.timeout
        response_cls = kwargs.get("response_cls")
        if not response_cls:
            response_cls = self.response_cls
            if api.response_cls:
                response_cls = api.response_cls
        request_kwargs = {
            "method": api.method,
            "url": prefix + api.uri,
            "params": request_params,
            "data": request_data,
            "json": request_json,
            "headers": request_headers,
            "cookies": request_cookies,
            "timeout": timeout,
            **kwargs,
        }

        request_context = {
            "method": api.method,
            "url": prefix + api.uri,
            "headers": request_headers,
            "params": request_params,
            "data": request_data,
            "json": request_json,
            "cookies": request_cookies,
            "kwargs": kwargs,
        }
        try:
            async with httpx.AsyncClient() as client:
                raw_response: httpx.Response = await client.request(
                    **request_kwargs,
                )
        except Exception as e:
            logger.bind(json=True).error(
                {
                    "Trigger": f"Third-{self.name}",
                    "request_context": request_context,
                    "request_error": repr(e),
                    "raw_response": None,
                },
            )
            return response_cls(
                success=False,
                status_code=None,
                data=None,
                request_context=request_context,
            )
        else:
            try:
                response = raw_response.json()
            except Exception:
                response = raw_response.text

            logger.debug(
                {
                    "Trigger": f"Third-{self.name}",
                    "request_context": request_context,
                    "response": response,
                },
            )

            return self.parse_response(
                api,
                request_context,
                raw_response,
                response_cls,
            )

    def parse_response(
        self,
        api: API,
        request_context: dict,
        raw_response: httpx.Response,
        response_cls: ResponseType = None,
    ) -> Response:
        if not response_cls:
            response_cls = self.response_cls
            if api.response_cls:
                response_cls = api.response_cls
        return response_cls.parse_response(raw_response, request_context)


if __name__ == "__main__":

    class GoogleAPI(Third):
        @abc.abstractmethod
        async def search(self, *args, **kwargs) -> ResponseType:
            pass

    google_apis = [
        API(
            "search",
            method="GET",
            uri="/search",
            response_cls=DefaultResponse,
        ),
    ]
    google_api = GoogleAPI(
        name="GoogleAPI",
        protocol="https",
        host="www.google.com",
        port=None,
        response_cls=DefaultResponse,
        timeout=6,
        headers={"auth": ":"},
    )
    for api in google_apis:
        google_api.register_api(api)
    google_api.register_api(API("search", method="GET", uri="/search"))
    asyncio.run(google_api.search(params={"q": "test"}))
