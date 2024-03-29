import os.path

import io

from ipystate.impl.dispatch.dispatcher import Dispatcher
import threading
import weakref
from types import CodeType, FunctionType, ModuleType
from ipystate.impl.utils import constructor, SAVE_GLOBAL_FUNC_ATTR, SAVE_GLOBAL, is_local_object
import importlib
import _thread
import sys

if sys.version_info[:2] == (3, 7):
    @constructor
    def _code_constructor(
            argcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars
    ):
        # noinspection PyTypeChecker
        return CodeType(
            argcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars,
        )


    @constructor
    def _code_constructor_python_3_8(
            argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars
    ):
        # noinspection PyTypeChecker
        return CodeType(
            argcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars,
        )

else:
    @constructor
    def _code_constructor(
            argcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars
    ):
        # noinspection PyTypeChecker
        return CodeType(
            argcount, 0, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars,
        )


    @constructor
    def _code_constructor_python_3_8(
            argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars
    ):
        # noinspection PyTypeChecker
        return CodeType(
            argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants, names,
            varnames, filename, name, firstlineno, lnotab, freevars, cellvars,
        )


def _function_constructor(code):
    pass


class CommonDispatcher(Dispatcher):
    @staticmethod
    def _create_weakref(obj, *args):
        from weakref import ref
        if obj is None:  # it's dead
            from collections import UserDict
            return ref(UserDict(), *args)
        return ref(obj, *args)

    @staticmethod
    def _reduce_weakref(wkref):
        obj = wkref()
        return CommonDispatcher._create_weakref, (obj,)

    if sys.version_info[:2] == (3, 7):
        @staticmethod
        def _reduce_code(code):
            return _code_constructor, (
                code.co_argcount, code.co_kwonlyargcount, code.co_nlocals, code.co_stacksize,
                code.co_flags, code.co_code, code.co_consts, code.co_names, code.co_varnames, code.co_filename,
                code.co_name, code.co_firstlineno, code.co_lnotab, code.co_freevars, code.co_cellvars,
            )
    else:
        @staticmethod
        def _reduce_code(code):
            return _code_constructor_python_3_8, (
                code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount, code.co_nlocals, code.co_stacksize,
                code.co_flags, code.co_code, code.co_consts, code.co_names, code.co_varnames, code.co_filename,
                code.co_name, code.co_firstlineno, code.co_lnotab, code.co_freevars, code.co_cellvars,
            )

    @staticmethod
    def _reduce_func(func):
        if hasattr(func, SAVE_GLOBAL_FUNC_ATTR):
            return SAVE_GLOBAL

        is_lambda_func = func.__name__ == '<lambda>'
        non_global_func = func.__module__ in (None, '__main__', 'builtins') or 'namedtuple' in func.__module__
        modified_dict = func.__dict__ and not (len(func.__dict__) == 1 and '__wrapped__' in func.__dict__)
        if not (is_lambda_func or modified_dict or non_global_func or is_local_object(func)):
            return SAVE_GLOBAL

        # noinspection PyUnresolvedReferences
        return _function_constructor, (
            func.__code__,
            # don't pass __globals__, etc to avoid grabbing function's scope
        )

    @staticmethod
    def _reduce_module(module):
        return importlib.import_module, (module.__name__,)

    @staticmethod
    def _create_file(name, mode, closed, encoding):
        names = {'<stdin>': sys.__stdin__, '<stdout>': sys.__stdout__,
                 '<stderr>': sys.__stderr__}
        if name in list(names.keys()):
            f = names[name]
        elif name == '<tmpfile>':
            f = os.tmpfile()
        elif name == '<fdopen>':
            import tempfile
            f = tempfile.TemporaryFile(mode)
        else:
            try:
                exists = os.path.exists(name)
            except:
                exists = False
            if not exists and "r" in mode:
                name = "<fdopen>"
            if name == "<fdopen>":
                import tempfile
                f = tempfile.TemporaryFile(mode)
            else:
                f = open(name, mode, encoding=encoding)
        if closed:
            f.close()
        return f

    @staticmethod
    def _reduce_filehandle(file):
        if "x" in file.mode:
            raise Exception("Can't serialize file with x mode")
        return CommonDispatcher._create_file, (
            file.name, file.mode, file.closed, file.encoding if hasattr(file, 'encoding') else None)

    def register(self, dispatch):
        dispatch[CodeType] = self._reduce_code
        dispatch[FunctionType] = self._reduce_func
        dispatch[ModuleType] = self._reduce_module
        dispatch[_thread.LockType] = self._reduce_without_args(_thread.LockType)
        # noinspection PyUnresolvedReferences
        dispatch[_thread.RLock] = self._reduce_without_args(_thread.RLock)
        # noinspection PyUnresolvedReferences
        dispatch[_thread._local] = self._reduce_without_args(_thread._local)
        dispatch[threading.Thread] = self._reduce_without_args(threading.Thread)
        # Files serialization
        dispatch[io.FileIO] = self._reduce_filehandle
        dispatch[io.TextIOWrapper] = self._reduce_filehandle
        dispatch[io.BufferedRandom] = self._reduce_filehandle
        dispatch[io.BufferedReader] = self._reduce_filehandle
        dispatch[io.BufferedWriter] = self._reduce_filehandle
        dispatch[weakref.ReferenceType] = self._reduce_weakref
