import asyncio

from tasks import task_manager


@task_manager.task()
async def test():
    print("test")


if __name__ == "__main__":
    asyncio.run(test())
