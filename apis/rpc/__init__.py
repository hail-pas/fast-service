"""
GRPC Service Build Steps:
    > GRPC Server Stub  <--protocol buffers-->  GRPC Client Stub
1. Define data format with protocol buffers
2. Generate protocol buffers code and client/server code
    shell: python -m grpc_tools.protoc -I .  --python_out=. --grpc_python_out=.  ./rpcs/hello/hello.proto
    output: xxx_pb2.py    xxx_pb2_grpc.py
3. create side code
    3.1 create server
        - implement all methods of xxxServicer which is subclass of xxxServicer in xxx_pb2_grpc.py
    3.2 create client
        - channel initialize
        - stub initialize (Stub class in xxx_pb2_grpc.py)
        - call
4.
"""
from concurrent import futures

import grpc

from apis.rpc.hello import hello_pb2_grpc
from apis.rpc.hello.hello_pb2_grpc import HelloServicer

rpc_server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
rpc_server.add_insecure_port("[::]:50051")
hello_pb2_grpc.add_HelloServicer_to_server(HelloServicer(), rpc_server)


async def serve():
    await rpc_server.start()
    await rpc_server.wait_for_termination()
