from typing import (
    Any,
    Dict,
    List,
    Type,
    Tuple,
    Union,
    Generic,
    TypeVar,
    Callable,
    Optional,
    Sequence,
)
from collections import defaultdict
from dataclasses import asdict, dataclass

from fastapi import Body, Depends, Request, APIRouter, HTTPException
from pydantic import BaseModel, create_model
from fastapi.types import DecoratedCallable
from tortoise.models import Model
from tortoise.queryset import QuerySet
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q
from tortoise.transactions import atomic

from common.schemas import CURDPager
from common.responses import Resp, PageResp, generate_page_info
from apis.dependencies import paginate
from common.exceptions import ApiException

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


def pagination_factory(
    db_model: Model, search_fields, max_limit: Optional[int] = None
) -> CURDPager:
    """
    Created the pagination dependency to be used in the router
    """

    return Depends(paginate(db_model, search_fields, max_limit))


DEPENDENCIES = Optional[Sequence[Depends]]


async def update_create_data_clean(
    data: dict, model: Model
) -> Tuple[dict, dict]:
    fields_map = model._meta.fields_map
    fk_fields = [f"{i}_id" for i in model._meta.fk_fields]
    m2m_fields = model._meta.m2m_fields

    cleaned_data = {}
    m2m_fields_data = defaultdict(list)

    for key in data.keys():
        if key not in fields_map:
            continue
        if key in fk_fields:
            if data[key]:
                field = fields_map[key.split("_id")[0]]
                obj = await field.related_model.get_or_none(
                    **{field.to_field: data[key]}
                )
                if not obj:
                    raise ApiException(f"{field.description}不存在")
            cleaned_data[key] = data[key]
            continue

        if key in m2m_fields:
            if not data[key]:
                continue
            field = fields_map[key]
            model = field.related_model
            for related_id in data[key]:
                obj = await model.get_or_none(id=related_id)
                if not obj:
                    raise ApiException(
                        f"id为{related_id}的{model._meta.table_description}不存在"
                    )
                m2m_fields_data[key].append(obj)
            continue

        cleaned_data[key] = data[key]

    return cleaned_data, m2m_fields_data


def default_filter():
    @dataclass
    class DefaultFilterSchema:
        pass

    return DefaultFilterSchema


async def default_get_queryset(
    self: "CURDGenerator", request: Request
) -> QuerySet:
    return self.queryset or self.db_model.all()


class CURDGenerator(Generic[T], APIRouter):
    db_model: Type[Model]
    queryset: Optional[QuerySet]
    schema: Type[T]
    create_schema: Type[T]
    update_schema: Type[T]
    filter_schema: Type[T]
    retrieve_schema: Type[T]
    _base_path: str = "/"
    get_queryset: Callable[["CURDGenerator", Request], QuerySet]

    def __init__(
        self,
        schema: Type[T],
        db_model: Type[Model],
        queryset: Optional[QuerySet] = None,
        get_queryset: Callable[["CURDGenerator", Request], QuerySet] = None,
        create_schema: Optional[Type[T]] = None,
        update_schema: Optional[Type[T]] = None,
        retrieve_schema: Optional[Type[T]] = None,
        filter_schema: Optional[Type[T]] = None,
        search_fields: Optional[List[str]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_paginate_limit: Optional[int] = None,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:
        self.db_model = db_model
        self.queryset = queryset
        self.get_queryset = get_queryset or default_get_queryset
        self.db_model_label = self.db_model.Meta.table_description
        self._pk: str = db_model.describe()["pk_field"]["db_column"]

        self.schema = schema
        self.pagination: CURDPager = pagination_factory(
            db_model,
            search_fields=set(search_fields or []),
            max_limit=max_paginate_limit,
        )
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
        self.filter_schema = filter_schema or default_filter()
        self.search_fields = set(search_fields or [])

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
                response_model=Resp[self.retrieve_schema],
                summary=f"创建{self.db_model_label}",
                dependencies=create_route,
            )

        if delete_all_route:
            self._add_api_route(
                "",
                self._batch_delete(),
                methods=["DELETE"],
                response_model=Resp,  # type: ignore
                summary=f"批量删除{self.db_model_label}",
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
                summary=f"单个删除{self.db_model_label}",
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
        async def route(
            request: Request,
            filter_: self.filter_schema = Depends(),
            pagination: CURDPager = self.pagination,
        ):
            exclude_fields = getattr(filter_, "exclude_fields", [])

            extra_args = getattr(filter_, "extra_args", [])
            extra_kwargs = getattr(filter_, "extra_kwargs", {})

            filter_dict = asdict(
                filter_,
                dict_factory=lambda x: {
                    k: v
                    for (k, v) in x
                    if v is not None and k not in exclude_fields
                },
            )

            filter_dict.update(extra_kwargs)

            queryset: QuerySet[self.db_model] = await self.get_queryset(
                self, request
            )

            queryset = (
                queryset.filter(*extra_args)
                .filter(**filter_dict)
                .order_by(*pagination.order_by)
            )

            search = pagination.search
            if search is not None and self.search_fields:
                sub_q_exps = []
                for search_field in self.search_fields:
                    sub_q_exps.append(
                        Q(**{f"{search_field}__icontains": search})
                    )
                q_expression = Q(*sub_q_exps, join_type=Q.OR)
                queryset = queryset.filter(q_expression)

            data = await self.schema.from_queryset(
                queryset.offset(pagination.offset).limit(pagination.limit)
            )
            total = await queryset.count()
            return PageResp[self.schema](
                data=data, page_info=generate_page_info(total, pagination)
            )

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(
            request: Request,
            id: str,
        ):
            model = await (await self.get_queryset(self, request)).get_or_none(
                id=id
            )

            if model:
                return Resp[self.retrieve_schema](
                    data=await self.retrieve_schema.from_tortoise_orm(model)
                )
            else:
                return Resp.fail("对象不存在")

        return route

    def _create(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        @atomic("default")
        async def route(
            request: Request, model: self.create_schema
        ):  # type: ignore
            data, m2m_data = await update_create_data_clean(
                model.dict(), self.db_model
            )

            obj = self.db_model(**data)
            try:
                await obj.save()
            except IntegrityError:
                raise ApiException(
                    f"{self.db_model._meta.table_description}已存在"
                )

            for k, v in m2m_data.items():
                if v:
                    await getattr(obj, k).add(*v)

            return Resp[self.retrieve_schema](
                data=await self.retrieve_schema.from_tortoise_orm(obj)
            )

        return route

    def _update(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        @atomic("default")
        async def route(
            request: Request, id: str, model: self.update_schema
        ):  # type: ignore
            obj = await (await self.get_queryset(self, request)).get_or_none(
                id=id
            )
            if not obj:
                return Resp.fail("对象不存在")
            data, m2m_data = await update_create_data_clean(
                model.dict(exclude_unset=True), self.db_model
            )
            if data:
                try:
                    await (await self.get_queryset(self, request)).filter(
                        id=id
                    ).update(**data)
                except IntegrityError:
                    raise ApiException(
                        f"{self.db_model._meta.table_description}已存在"
                    )
            if m2m_data:
                for k, v in m2m_data.items():
                    await getattr(obj, k).add(*v)
            await obj.refresh_from_db()
            return Resp[self.retrieve_schema](data=obj)

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(request: Request, id: str):
            await (await self.get_queryset(self, request)).filter(
                id=id
            ).delete()
            return Resp()

        return route

    def _batch_delete(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        async def route(
            request: Request, ids: List[str] = Body(..., description="id列表")
        ):
            await (await self.get_queryset(self, request)).filter(
                id__in=ids
            ).delete()
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
