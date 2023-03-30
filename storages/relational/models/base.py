from typing import Any, List, Optional
from datetime import datetime, timedelta

from tortoise import fields
from tortoise.models import Model
from tortoise.expressions import Q
from tortoise.backends.base.client import BaseDBAsyncClient

from common.schemas import Pager
from common.responses import generate_page_info

# from tortoise.contrib.pydantic.creator import pydantic_model_creator, PydanticMeta

MIN_DELETED_DATETIME = datetime.min + timedelta(days=1)


def get_datetime_min():
    return MIN_DELETED_DATETIME


class UUIDPrimaryKeyModel(Model):
    id = fields.UUIDField(description="主键", pk=True)

    class Meta:
        abstract = True


class BigIntegerIDPrimaryKeyModel(Model):
    id = fields.BigIntField(description="主键", pk=True)

    class Meta:
        abstract = True


class TimeStampModel(Model):
    created_at = fields.DatetimeField(
        auto_now_add=True, description="创建时间", index=True
    )
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    deleted_at = fields.DatetimeField(
        default=get_datetime_min, description="更新时间"
    )

    class Meta:
        abstract = True

    async def save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[List[str]] = None,
        force_create: bool = False,
        force_update: bool = False,
    ) -> None:
        if update_fields:
            update_fields.append("updated_at")
        await super().save(using_db, update_fields, force_create, force_update)


class BaseModel(UUIDPrimaryKeyModel, TimeStampModel):
    class Meta:
        abstract = True

    @classmethod
    async def page_data(
        cls,
        pager: Pager,
        *args: Q,
        **kwargs: Any,
    ):
        queryset = cls.filter(*args, **kwargs)
        page_info = generate_page_info(await queryset.count(), pager)
        data = (
            await queryset.limit(pager.limit)
            .offset(pager.offset)
            .select_related(*cls.get_select_related_fields())
            .prefetch_related(*cls.get_prefetch_related_fields())
        )
        return page_info, data

    # @classmethod
    # def get_select_related_fields(cls) -> List[str]:
    #     select_related_fields = []
    #     pydantic_meta = getattr(cls, "PydanticMeta", PydanticMeta)
    #     for field_name, field_desc in cls._meta.fields_map.items():
    #         if (
    #             (
    #                 isinstance(field_desc, fields.relational.ForeignKeyFieldInstance)
    #                 or isinstance(field_desc, fields.relational.OneToOneFieldInstance)
    #             )
    #             and field_name not in getattr(pydantic_meta, "exclude", ())
    #             and (not getattr(pydantic_meta, "include", ()) or field_name in getattr(pydantic_meta, "include", ()))
    #         ):
    #             select_related_fields.append(field_name)
    #     return select_related_fields

    # @classmethod
    # def get_prefetch_related_fields(cls) -> List[str]:
    #     prefetch_related_fields = []
    #     pydantic_meta = getattr(cls, "PydanticMeta", PydanticMeta)
    #     for field_name, field_desc in cls._meta.fields_map.items():
    #         if (
    #             (
    #                 isinstance(field_desc, fields.relational.BackwardFKRelation)
    #                 or isinstance(field_desc, fields.relational.ManyToManyFieldInstance)
    #                 or isinstance(field_desc, fields.relational.BackwardOneToOneRelation)
    #             )
    #             and field_name not in getattr(pydantic_meta, "exclude", ())
    #             and (not getattr(pydantic_meta, "include", ()) or field_name in getattr(pydantic_meta, "include", ()))
    #         ):
    #             prefetch_related_fields.append(field_name)

    #     return prefetch_related_fields
