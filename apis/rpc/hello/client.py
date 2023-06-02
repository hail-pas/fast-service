import random
from collections.abc import Iterable

import grpc

from apis.rpc.hello import hello_pb2_grpc
from apis.rpc.hello.hello_pb2 import HelloIn

channel = grpc.insecure_channel("localhost:50055")
stub = hello_pb2_grpc.HelloStub(channel)


def request_iterator() -> Iterable[HelloIn]:
    for _ in range(10):
        num = random.choice(range(10))  # noqa
        temp = generate_hello_in()
        temp.name = f"req{num}"
        temp.age = num
        yield temp


def generate_hello_in() -> HelloIn:
    hello_in = HelloIn()
    hello_in.name = "phoenix"
    hello_in.age = 26
    hello_in.super_user = True
    hello_in.corpus = HelloIn.Corpus.WEB
    return hello_in


def call_simple() -> None:
    # Simple
    simple_res = stub.HelloRPC(generate_hello_in())
    # async
    # simple_res_future = stub.GetFeature.future(hello_in)
    # simple_res = simple_res_future.result()
    print("simple_res: ", simple_res)


def call_list() -> None:
    multi_res = stub.MultiHelloRPC(generate_hello_in())
    for i in multi_res.replies:
        print("Multi: ", i)


def call_resp_stream() -> None:
    stream_res = stub.ResStreamHelloRPC(generate_hello_in())
    for i in stream_res:
        print("Stream Res: ", i)


def call_reqs_stream() -> None:
    stream_req = stub.ReqStreamHelloRPC(request_iterator())
    for i in stream_req.replies:
        print("Stream Req: ", i)


def call_bi_stream() -> None:
    bi_stream = stub.BiStreamHelloRPC(request_iterator())
    for i in bi_stream:
        print("Bi Stream: ", i)


if __name__ == "__main__":
    call_simple()
    call_list()
    call_resp_stream()
    call_reqs_stream()
    call_bi_stream()
