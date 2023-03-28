from typing import (
    Any,
    Dict,
    List,
    Type,
    Union,
    Generic,
    TypeVar,
    Callable,
    Optional,
    Sequence,
)

from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel, create_model
from fastapi.types import DecoratedCallable
from tortoise.models import Model

from common.schemas import Pager
from common.responses import Resp, PageResp, generate_page_info
from apis.dependencies import get_pager

T = TypeVar("T", bound=BaseModel)


def schema_factory(
    schema_cls: Type[T], pk_field_name: str = "id", name: str = "Create"
) -> Type[T]:
    """
    Is used to create a CreateSchema which does not contain pk
    """

    fields = {
        f.name: (f.type_, ...)
        for f in schema_cls.__fields__.values()
        if f.name != pk_field_name
    }

    name = schema_cls.__name__ + name
    schema: Type[T] = create_model(__model_name=name, **fields)  # type: ignore
    return schema


PAGINATION = Dict[str, Optional[int]]


def pagination_factory(max_limit: Optional[int] = None) -> Pager:
    """
    Created the pagination dependency to be used in the router
    """

    return Depends(get_pager)


DEPENDENCIES = Optional[Sequence[Depends]]


class CURDGenerator(Generic[T], APIRouter):
    schema: Type[T]
    create_schema: Type[T]
    update_schema: Type[T]
    _base_path: str = "/"

    def __init__(
        self,
        schema: Type[T],
        db_model: Type[Model],
        create_schema: Optional[Type[T]] = None,
        update_schema: Optional[Type[T]] = None,
        retrieve_schema: Optional[Type[T]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = None,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:
        self.db_model = db_model
        self.db_model_label = self.db_model.Meta.table_description
        self._pk: str = db_model.describe()["pk_field"]["db_column"]

        self.schema = schema
        self.pagination: Pager = pagination_factory(max_limit=paginate)
        self._pk: str = self._pk if hasattr(self, "_pk") else "id"
        self.create_schema = (
            create_schema
            if create_schema
            else schema_factory(
                self.schema, pk_field_name=self._pk, name="Create"
            )
        )
        self.update_schema = (
            update_schema
            if update_schema
            else schema_factory(
                self.schema, pk_field_name=self._pk, name="Update"
            )
        )
        self.retrieve_schema = (
            retrieve_schema if retrieve_schema else self.schema
        )

        prefix = str(prefix if prefix else self.schema.__name__).lower()
        prefix = self._base_path + prefix.strip("/")
        tags = tags or [prefix.strip("/").capitalize()]

        super().__init__(prefix=prefix, tags=tags, **kwargs)

        if get_all_route:
            self._add_api_route(
                "",
                self._get_all(),
                methods=["GET"],
                response_model=PageResp[self.schema],
                summary=f"{self.db_model_label}列表",
                dependencies=get_all_route,
            )

        if create_route:
            self._add_api_route(
                "",
                self._create(),
                methods=["POST"],
                response_model=Resp[self.schema],
                summary=f"创建{self.db_model_label}",
                dependencies=create_route,
            )

        if delete_all_route:
            self._add_api_route(
                "",
                self._delete_all(),
                methods=["DELETE"],
                response_model=Resp,  # type: ignore
                summary=f"删除全部{self.db_model_label}",
                dependencies=delete_all_route,
            )

        if get_one_route:
            self._add_api_route(
                "/{item_id}",
                self._get_one(),
                methods=["GET"],
                response_model=Resp[self.retrieve_schema],
                summary=f"{self.db_model_label}详情",
                dependencies=get_one_route,
            )

        if update_route:
            self._add_api_route(
                "/{item_id}",
                self._update(),
                methods=["PUT"],
                response_model=Resp[self.retrieve_schema],
                summary=f"更新{self.db_model_label}",
                dependencies=update_route,
            )

        if delete_one_route:
            self._add_api_route(
                "/{item_id}",
                self._delete_one(),
                methods=["DELETE"],
                response_model=Resp,
                summary=f"删除{self.db_model_label}",
                dependencies=delete_one_route,
            )

    def _add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        dependencies: Union[bool, DEPENDENCIES],
        error_responses: Optional[List[HTTPException]] = None,
        **kwargs: Any,
    ) -> None:
        dependencies = [] if isinstance(dependencies, bool) else dependencies
        responses: Any = (
            {
                err.status_code: {"detail": err.detail}
                for err in error_responses
            }
            if error_responses
            else None
        )

        super().add_api_route(
            path,
            endpoint,
            dependencies=dependencies,
            responses=responses,
            **kwargs,
        )

    def api_route(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Overrides and exiting route if it exists"""
        methods = kwargs["methods"] if "methods" in kwargs else ["GET"]
        self.remove_api_route(path, methods)
        return super().api_route(path, *args, **kwargs)

    def get(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["Get"])
        return super().get(path, *args, **kwargs)

    def post(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["POST"])
        return super().post(path, *args, **kwargs)

    def put(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["PUT"])
        return super().put(path, *args, **kwargs)

    def delete(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["DELETE"])
        return super().delete(path, *args, **kwargs)

    def remove_api_route(self, path: str, methods: List[str]) -> None:
        methods_ = set(methods)

        for route in self.routes:
            if (
                route.path == f"{self.prefix}{path}"  # type: ignore
                and route.methods == methods_  # type: ignore
            ):
                self.routes.remove(route)

    def _get_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(pagination: Pager = self.pagination):
            query = await self.schema.from_queryset(
                self.db_model.all()
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            total = await self.db_model.all().count()
            return PageResp[self.schema](
                data=query, page_info=generate_page_info(total, pagination)
            )

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(id: str) -> Model:
            model = self.db_model.get_or_none(id=id)

            if model:
                return Resp[self.retrieve_schema](
                    data=await self.retrieve_schema.from_queryset_single(model)
                )
            else:
                return Resp.fail("对象不存在")

        return route

    def _create(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(model: self.create_schema) -> Model:  # type: ignore
            db_model = self.db_model(**model.dict())
            await db_model.save()

            return Resp[self.retrieve_schema](
                data=await self.retrieve_schema.from_tortoise_orm(db_model)
            )

        return route

    def _update(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(
            id: str, model: self.update_schema  # type: ignore
        ) -> Model:
            await self.db_model.filter(id=id).update(
                **model.dict(exclude_unset=True)
            )
            return Resp[self.retrieve_schema](data=await self._get_one()(id))

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(id: str) -> Model:
            await self.db_model.filter(id=id).delete()
            return Resp()

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route() -> List[Model]:
            await self.db_model.all().delete()
            return Resp()

        return route

    def _raise(self, e: Exception, status_code: int = 422) -> HTTPException:
        raise HTTPException(422, ", ".join(e.args)) from e

    @staticmethod
    def get_routes() -> List[str]:
        return [
            "get_all",
            "create",
            "delete_all",
            "get_one",
            "update",
            "delete_one",
        ]
