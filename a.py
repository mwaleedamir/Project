import os
import ctypes
import sys
from abc import ABC, abstractmethod
from contextlib import ContextDecorator
from typing import final

__version__ = "1.0.0"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "True")

_SYSTEM_UINT = ctypes.c_uint64 if sys.maxsize > 2**32 else ctypes.c_uint32

class LibController(ABC):
    def __init__(self, filepath):
        self.filepath = filepath
        self.dynlib = ctypes.CDLL(filepath, mode=os.RTLD_LOCAL)
        self.version = self.get_version()

    def info(self):
        return {
            "version": self.version,
            "num_threads": self.num_threads,
        }

    @property
    def num_threads(self):
        return self.get_num_threads()

    @abstractmethod
    def get_num_threads(self):
        pass

    @abstractmethod
    def set_num_threads(self, num_threads):
        pass

    @abstractmethod
    def get_version(self):
        pass

class OpenBLASController(LibController):
    def get_num_threads(self):
        get_num_threads_func = getattr(self.dynlib, "openblas_get_num_threads", None)
        return get_num_threads_func() if get_num_threads_func else None

    def set_num_threads(self, num_threads):
        set_num_threads_func = getattr(self.dynlib, "openblas_set_num_threads", None)
        if set_num_threads_func:
            set_num_threads_func(num_threads)

    def get_version(self):
        get_version_func = getattr(self.dynlib, "openblas_get_config", None)
        if get_version_func:
            get_version_func.restype = ctypes.c_char_p
            config = get_version_func().split()
            if config[0] == b"OpenBLAS":
                return config[1].decode("utf-8")
        return None

class ThreadpoolController:
    def __init__(self):
        self.lib_controllers = [OpenBLASController("/path/to/libopenblas.so")]
    
    def info(self):
        return [lib_controller.info() for lib_controller in self.lib_controllers]

    def set_threadpool_limits(self, num_threads):
        for lib_controller in self.lib_controllers:
            lib_controller.set_num_threads(num_threads)

class threadpool_limits(ContextDecorator):
    def __init__(self, limits):
        self.controller = ThreadpoolController()
        self.limits = limits

    def __enter__(self):
        self.original_info = self.controller.info()
        self.controller.set_threadpool_limits(self.limits)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for lib_controller, original_info in zip(self.controller.lib_controllers, self.original_info):
            lib_controller.set_num_threads(original_info["num_threads"])

# Usage example for house price prediction
with threadpool_limits(limits=4):
    # House price prediction code here
    pass
