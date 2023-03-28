# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: rpcs/hello/hello.proto
"""Generated protocol buffer code."""
from google.protobuf import message as _message
from google.protobuf import descriptor as _descriptor
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor.FileDescriptor(
    name="rpcs/hello/hello.proto",
    package="",
    syntax="proto3",
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
    serialized_pb=b'\n\x16rpcs/hello/hello.proto"\xb5\x01\n\x07HelloIn\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0b\n\x03\x61ge\x18\x02 \x01(\x05\x12\x12\n\nsuper_user\x18\x03 \x01(\x08\x12\x1f\n\x06\x63orpus\x18\x04 \x01(\x0e\x32\x0f.HelloIn.Corpus"Z\n\x06\x43orpus\x12\r\n\tUNIVERSAL\x10\x00\x12\x07\n\x03WEB\x10\x01\x12\n\n\x06IMAGES\x10\x02\x12\t\n\x05LOCAL\x10\x03\x12\x08\n\x04NEWS\x10\x04\x12\x0c\n\x08PRODUCTS\x10\x05\x12\t\n\x05VIDEO\x10\x06"\x19\n\x08HelloOut\x12\r\n\x05infos\x18\x01 \x01(\t"+\n\rMultiHelloOut\x12\x1a\n\x07replies\x18\x01 \x03(\x0b\x32\t.HelloOut2\xdd\x01\n\x05Hello\x12\x1f\n\x08HelloRPC\x12\x08.HelloIn\x1a\t.HelloOut\x12)\n\rMultiHelloRPC\x12\x08.HelloIn\x1a\x0e.MultiHelloOut\x12*\n\x11ResStreamHelloRPC\x12\x08.HelloIn\x1a\t.HelloOut0\x01\x12/\n\x11ReqStreamHelloRPC\x12\x08.HelloIn\x1a\x0e.MultiHelloOut(\x01\x12+\n\x10\x42iStreamHelloRPC\x12\x08.HelloIn\x1a\t.HelloOut(\x01\x30\x01\x62\x06proto3',  # noqa
)


_HELLOIN_CORPUS = _descriptor.EnumDescriptor(
    name="Corpus",
    full_name="HelloIn.Corpus",
    filename=None,
    file=DESCRIPTOR,
    create_key=_descriptor._internal_create_key,
    values=[
        _descriptor.EnumValueDescriptor(
            name="UNIVERSAL",
            index=0,
            number=0,
            serialized_options=None,
            type=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.EnumValueDescriptor(
            name="WEB",
            index=1,
            number=1,
            serialized_options=None,
            type=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.EnumValueDescriptor(
            name="IMAGES",
            index=2,
            number=2,
            serialized_options=None,
            type=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.EnumValueDescriptor(
            name="LOCAL",
            index=3,
            number=3,
            serialized_options=None,
            type=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.EnumValueDescriptor(
            name="NEWS",
            index=4,
            number=4,
            serialized_options=None,
            type=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.EnumValueDescriptor(
            name="PRODUCTS",
            index=5,
            number=5,
            serialized_options=None,
            type=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.EnumValueDescriptor(
            name="VIDEO",
            index=6,
            number=6,
            serialized_options=None,
            type=None,
            create_key=_descriptor._internal_create_key,
        ),
    ],
    containing_type=None,
    serialized_options=None,
    serialized_start=118,
    serialized_end=208,
)
_sym_db.RegisterEnumDescriptor(_HELLOIN_CORPUS)


_HELLOIN = _descriptor.Descriptor(
    name="HelloIn",
    full_name="HelloIn",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    create_key=_descriptor._internal_create_key,
    fields=[
        _descriptor.FieldDescriptor(
            name="name",
            full_name="HelloIn.name",
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=b"".decode("utf-8"),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.FieldDescriptor(
            name="age",
            full_name="HelloIn.age",
            index=1,
            number=2,
            type=5,
            cpp_type=1,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.FieldDescriptor(
            name="super_user",
            full_name="HelloIn.super_user",
            index=2,
            number=3,
            type=8,
            cpp_type=7,
            label=1,
            has_default_value=False,
            default_value=False,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.FieldDescriptor(
            name="corpus",
            full_name="HelloIn.corpus",
            index=3,
            number=4,
            type=14,
            cpp_type=8,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
            create_key=_descriptor._internal_create_key,
        ),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[
        _HELLOIN_CORPUS,
    ],
    serialized_options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=27,
    serialized_end=208,
)


_HELLOOUT = _descriptor.Descriptor(
    name="HelloOut",
    full_name="HelloOut",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    create_key=_descriptor._internal_create_key,
    fields=[
        _descriptor.FieldDescriptor(
            name="infos",
            full_name="HelloOut.infos",
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=b"".decode("utf-8"),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
            create_key=_descriptor._internal_create_key,
        ),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=210,
    serialized_end=235,
)


_MULTIHELLOOUT = _descriptor.Descriptor(
    name="MultiHelloOut",
    full_name="MultiHelloOut",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    create_key=_descriptor._internal_create_key,
    fields=[
        _descriptor.FieldDescriptor(
            name="replies",
            full_name="MultiHelloOut.replies",
            index=0,
            number=1,
            type=11,
            cpp_type=10,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
            create_key=_descriptor._internal_create_key,
        ),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=237,
    serialized_end=280,
)

_HELLOIN.fields_by_name["corpus"].enum_type = _HELLOIN_CORPUS
_HELLOIN_CORPUS.containing_type = _HELLOIN
_MULTIHELLOOUT.fields_by_name["replies"].message_type = _HELLOOUT
DESCRIPTOR.message_types_by_name["HelloIn"] = _HELLOIN
DESCRIPTOR.message_types_by_name["HelloOut"] = _HELLOOUT
DESCRIPTOR.message_types_by_name["MultiHelloOut"] = _MULTIHELLOOUT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

HelloIn = _reflection.GeneratedProtocolMessageType(
    "HelloIn",
    (_message.Message,),
    {
        "DESCRIPTOR": _HELLOIN,
        "__module__": "rpcs.hello.hello_pb2"
        # @@protoc_insertion_point(class_scope:HelloIn)
    },
)
_sym_db.RegisterMessage(HelloIn)

HelloOut = _reflection.GeneratedProtocolMessageType(
    "HelloOut",
    (_message.Message,),
    {
        "DESCRIPTOR": _HELLOOUT,
        "__module__": "rpcs.hello.hello_pb2"
        # @@protoc_insertion_point(class_scope:HelloOut)
    },
)
_sym_db.RegisterMessage(HelloOut)

MultiHelloOut = _reflection.GeneratedProtocolMessageType(
    "MultiHelloOut",
    (_message.Message,),
    {
        "DESCRIPTOR": _MULTIHELLOOUT,
        "__module__": "rpcs.hello.hello_pb2"
        # @@protoc_insertion_point(class_scope:MultiHelloOut)
    },
)
_sym_db.RegisterMessage(MultiHelloOut)


_HELLO = _descriptor.ServiceDescriptor(
    name="Hello",
    full_name="Hello",
    file=DESCRIPTOR,
    index=0,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
    serialized_start=283,
    serialized_end=504,
    methods=[
        _descriptor.MethodDescriptor(
            name="HelloRPC",
            full_name="Hello.HelloRPC",
            index=0,
            containing_service=None,
            input_type=_HELLOIN,
            output_type=_HELLOOUT,
            serialized_options=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.MethodDescriptor(
            name="MultiHelloRPC",
            full_name="Hello.MultiHelloRPC",
            index=1,
            containing_service=None,
            input_type=_HELLOIN,
            output_type=_MULTIHELLOOUT,
            serialized_options=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.MethodDescriptor(
            name="ResStreamHelloRPC",
            full_name="Hello.ResStreamHelloRPC",
            index=2,
            containing_service=None,
            input_type=_HELLOIN,
            output_type=_HELLOOUT,
            serialized_options=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.MethodDescriptor(
            name="ReqStreamHelloRPC",
            full_name="Hello.ReqStreamHelloRPC",
            index=3,
            containing_service=None,
            input_type=_HELLOIN,
            output_type=_MULTIHELLOOUT,
            serialized_options=None,
            create_key=_descriptor._internal_create_key,
        ),
        _descriptor.MethodDescriptor(
            name="BiStreamHelloRPC",
            full_name="Hello.BiStreamHelloRPC",
            index=4,
            containing_service=None,
            input_type=_HELLOIN,
            output_type=_HELLOOUT,
            serialized_options=None,
            create_key=_descriptor._internal_create_key,
        ),
    ],
)
_sym_db.RegisterServiceDescriptor(_HELLO)

DESCRIPTOR.services_by_name["Hello"] = _HELLO

# @@protoc_insertion_point(module_scope)
