import asyncio

from storages import enums
from core.factory import app
from common.command.shell import init_ctx_db
from storages.relational.models.account import Permission


def get_url_list():
    url_list = []
    for route in app.routes:
        route_info = {
            "path": route.path,
            "name": getattr(route, "summary", None) or route.name,
            "tags": getattr(route, "tags", []),
        }
        if getattr(route, "methods", []):
            for method in route.methods:
                if method in ["HEAD", "OPTIONS"]:
                    continue
                url_list.append(
                    {
                        "method": method,
                        **route_info,
                    }
                )
    return url_list


async def update_or_creaete_perm_code():
    await init_ctx_db()
    url_list = get_url_list()
    latest_codes = []
    for url in url_list:
        # method, path, name, tags
        method = url.get("method")
        if not method:
            continue
        code = f'{method}:{url["path"]}'
        print(code)
        await Permission.update_or_create(
            code=code,
            defaults={
                "label": url["name"],
                "type": enums.PermissionTypeEnum.api,
                "is_deprecated": False,
            },
        )
        latest_codes.append(code)
    for permission in await Permission.filter(
        type=enums.PermissionTypeEnum.api
    ):
        if permission.code not in latest_codes:
            await permission.update(is_deprecated=True)


if __name__ == "__main__":
    asyncio.run(update_or_creaete_perm_code())
