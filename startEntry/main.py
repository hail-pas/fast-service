import uvicorn

from conf.config import local_configs

"""FastAPI"""

if __name__ == "__main__":
    uvicorn.run(
        "core.factory:app",
        host=local_configs.SERVER.HOST,
        port=local_configs.SERVER.PORT,
        reload=local_configs.PROJECT.DEBUG,
    )
