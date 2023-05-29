import os
import sys
import ctypes
import tempfile
from typing import Union
from subprocess import CalledProcessError, check_call

from extensions.cpp.eval.base import BASE_DIR

# _CppFilename = "literal_evald.cpp"
_BinFilename = "literal_eval.bin"
_LibFilename = "libliteraleval.so"


# def cpp_compile():
#     check_call(["c++", "-std=c++11", _CppFilename, "-o", _BinFilename])
#     check_call(["c++", "-std=c++11", "-DLIB", _CppFilename, "-shared", "-fPIC", "-o", _LibFilename])


def py_to_pickle_tmp(s: Union[str, bytes]) -> bytes:
    if isinstance(s, str):
        s = s.encode("utf8")
    with tempfile.NamedTemporaryFile("wb", suffix=".py") as f_py:
        f_py.write(s)
        f_py.write(b"\n")
        f_py.flush()

        with tempfile.NamedTemporaryFile(
            "w", suffix=".pkl", prefix=os.path.basename(f_py.name)
        ) as f_pkl:
            try:
                check_call(
                    [
                        f"{BASE_DIR.absolute()}/{_BinFilename}",
                        f_py.name,
                        f_pkl.name,
                    ]
                )
            except CalledProcessError as exc:
                print(f"{_BinFilename} returned error code {exc.returncode}")
                sys.exit(1)
            return open(f_pkl.name, "rb").read()


def py_to_pickle(s: Union[str, bytes]) -> bytes:
    if isinstance(s, bytes):
        in_bytes = s
    else:
        in_bytes = s.encode("utf8")
    in_ = ctypes.create_string_buffer(in_bytes)
    in_len = len(in_bytes)
    out_len = (
        in_len + 1000
    )  # should always be enough (some buffer len + len of literal Python code)
    out_ = ctypes.create_string_buffer(out_len)

    lib = ctypes.CDLL(f"{BASE_DIR.absolute()}/{_LibFilename}")
    lib.py_to_pickle.argtypes = (
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_char_p,
        ctypes.c_size_t,
    )
    lib.py_to_pickle.restype = ctypes.c_int

    res = lib.py_to_pickle(in_, in_len, out_, out_len)
    assert res == 0, "there was some error in %r" % in_bytes
    return out_.raw
