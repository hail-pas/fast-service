import asyncio

from apis.rpc import serve

"""gRPC"""

if __name__ == "__main__":
    asyncio.run(serve())
