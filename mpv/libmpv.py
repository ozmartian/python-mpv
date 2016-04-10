import os
import logging
import platform
from ctypes import (CDLL, POINTER, addressof, cast, c_int, c_ulong, c_void_p,
                    c_char_p, c_ulonglong, c_double)
from mpv.types import (MpvHandle, ErrorCode, MpvFormat, MpvLogLevel,
                       MpvEventID, MpvEvent, MpvEventProperty, MpvNode,
                       MpvNodeList, MpvByteArray, MpvEventLogMessage,
                       MpvEndFileReason, MpvEventEndFile,
                       MpvEventScriptInputDispatch, MpvEventClientMessage,
                       WakeupCallback, NodeBuilder,
                       MpvOpenGLCbContext, MpvSubApi, OpenGlCbUpdateFn, OpenGlCbGetProcAddrFn)
from mpv.exceptions import MpvError
log = logging.getLogger(__name__)


def load_lua(name='liblua.so'):
    """ Use this function if you intend to use mpv's built-in lua interpreter.
    This is e.g. needed for playback of youtube urls. """
    CDLL(name, mode=RTLD_GLOBAL)


class LibMPV(object):

    def __init__(self):
        self.backend = None

    def client_api_version(self):
        ver = self.backend.mpv_client_api_version()
        return (ver >> 16, ver & 0xFFFF)

    def load_library(self, name=None):
        os.environ['LC_NUMERIC'] = 'C'
        if name is not None:
            self.backend = CDLL(name)
        else:
            if platform.system() == 'Windows':
                self.backend = CDLL('mpv-1.dll')
            elif platform.system() == 'Linux':
                self.backend = CDLL('libmpv.so.1')
            elif platform.system() == 'Darwin':
                self.backend = CDLL('libmpv.dylib')
        self.initialize()

    def initialize(self):
        self.backend.mpv_client_api_version.restype = c_ulong

        self.backend.mpv_free.argtypes = [c_void_p]
        self.mpv_free = self.backend.mpv_free

        self.backend.mpv_create.restype = MpvHandle
        self.mpv_create = self.backend.mpv_create

        self.backend.mpv_free_node_contents.argtypes = [POINTER(MpvNode)]
        self.mpv_free_node_contents = self.backend.mpv_free_node_contents

        self.backend.mpv_free.argtypes = [c_void_p]
        self.mpv_free = self.backend.mpv_free

        self.backend.mpv_create.restype = MpvHandle
        self.mpv_create = self.backend.mpv_create

        self.backend.mpv_free_node_contents.argtypes = [POINTER(MpvNode)]
        self.mpv_free_node_contents = self.backend.mpv_free_node_contents

        self.backend.mpv_event_name.restype = c_char_p
        self.backend.mpv_event_name.argtypes = [c_int]
        self.mpv_event_name = self.backend.mpv_event_name

        self.backend.mpv_error_string.restype = c_char_p
        self.backend.mpv_error_string.argtypes = [c_int]
        self.mpv_error_string = self.backend.mpv_error_string

        def _handle_func(name, args=[], res=None, ctx=[MpvHandle]):
            func = getattr(self.backend, name)
            if res is not None:
                func.restype = res
            func.argtypes = ctx + args

            def wrapper(*args):
                try:
                    if res is ErrorCode:
                        result = func(*args)
                        if result.value < 0:
                            try:
                                reason = self.mpv_error_string(result.value).decode()
                            except Exception:
                                reason = 'N/A'
                            raise MpvError(func.__name__, result.value, reason,
                                           [(x.decode() if type(x) is bytes else x) for x in args])
                        else:
                            return result
                    else:
                            return func(*args)
                except OSError:
                    pass
            setattr(self, name, wrapper)

        _handle_func('mpv_create_client', [c_char_p], MpvHandle)
        _handle_func('mpv_client_name', [], c_char_p)
        _handle_func('mpv_initialize', [], ErrorCode)
        _handle_func('mpv_detach_destroy', [], c_int)
        _handle_func('mpv_terminate_destroy', [], c_int)
        _handle_func('mpv_load_config_file', [c_char_p], ErrorCode)
        _handle_func('mpv_suspend')
        _handle_func('mpv_resume')
        _handle_func('mpv_get_time_us', [], c_ulonglong)
        _handle_func('mpv_wait_async_requests')
        _handle_func('mpv_set_option', [c_char_p, MpvFormat, c_void_p], ErrorCode)
        _handle_func('mpv_set_option_string', [c_char_p, c_char_p], ErrorCode)
        _handle_func('mpv_command', [POINTER(c_char_p)], ErrorCode)
        _handle_func('mpv_command_string', [c_char_p], ErrorCode)
        _handle_func('mpv_command_async', [c_ulonglong, POINTER(c_char_p)], ErrorCode)
        _handle_func('mpv_command_node', [POINTER(MpvNode), POINTER(MpvNode)], ErrorCode)
        _handle_func('mpv_set_property', [c_char_p, MpvFormat, c_void_p], ErrorCode)
        _handle_func('mpv_set_property_string', [c_char_p, c_char_p], ErrorCode)
        _handle_func('mpv_set_property_async', [c_ulonglong, c_char_p, MpvFormat, c_void_p], ErrorCode)
        _handle_func('mpv_get_property', [c_char_p, MpvFormat, c_void_p], ErrorCode)
        _handle_func('mpv_get_property_string', [c_char_p], c_char_p)
        _handle_func('mpv_get_property_osd_string', [c_char_p], c_char_p)
        _handle_func('mpv_get_property_async', [c_ulonglong, c_char_p, MpvFormat], ErrorCode)
        _handle_func('mpv_observe_property', [c_ulonglong, c_char_p, MpvFormat], ErrorCode)
        _handle_func('mpv_unobserve_property', [c_ulonglong], ErrorCode)
        _handle_func('mpv_request_event', [MpvEventID, c_int], ErrorCode)
        _handle_func('mpv_request_log_messages', [c_char_p], ErrorCode)
        _handle_func('mpv_wait_event', [c_double], POINTER(MpvEvent))
        _handle_func('mpv_wakeup', [], c_int)
        _handle_func('mpv_set_wakeup_callback', [WakeupCallback, c_void_p])
        _handle_func('mpv_get_wakeup_pipe', [], c_int)
        _handle_func('mpv_get_sub_api', [MpvSubApi], c_void_p)

        def _handle_func_cb(name, args=[], res=None):
            return _handle_func(name, args, res, [MpvOpenGLCbContext])

        _handle_func_cb('mpv_opengl_cb_set_update_callback', [OpenGlCbUpdateFn, c_void_p])
        _handle_func_cb('mpv_opengl_cb_init_gl', [c_char_p, OpenGlCbGetProcAddrFn, c_void_p], ErrorCode)
        _handle_func_cb('mpv_opengl_cb_draw', [c_int, c_int, c_int], c_int)
        _handle_func_cb('mpv_opengl_cb_render', [c_int, c_int], c_int)  # deprecated
        _handle_func_cb('mpv_opengl_cb_report_flip', [c_ulonglong], ErrorCode)
        _handle_func_cb('mpv_opengl_cb_uninit_gl', [], ErrorCode)

    def get_sub_api(self, ctx, sub_api):
        if sub_api == MpvSubApi.MPV_SUB_API_OPENGL_CB:
            return cast(self.mpv_get_sub_api(ctx, sub_api), POINTER(MpvOpenGLCbContext))

    def opengl_cb_set_update_callback(self, ctx, callback, callback_ctx):
        self._opengl_update_cb = OpenGlCbUpdateFn(callback)
        self._opengl_cb_ctx = cast(None, c_void_p)
        self.mpv_opengl_cb_set_update_callback(ctx, self._opengl_update_cb, self._opengl_cb_ctx)

    def opengl_cb_init_gl(self, ctx, exts, get_proc_address, get_proc_address_ctx):
        self._opengl_proc_address_fn = OpenGlCbGetProcAddrFn(get_proc_address)
        self._opengl_proc_address_ctx = cast(None, c_void_p)
        self.mpv_opengl_cb_init_gl(ctx, cast(None, c_char_p), self._opengl_proc_address_fn, self._opengl_proc_address_ctx)

    def set_wakeup_callback(self, ctx, func, d):
        self.wakeup = WakeupCallback(func) if func is not None else cast(None, WakeupCallback)
        self.wakeup_data = cast(None, c_void_p)
        self.mpv_set_wakeup_callback(ctx, self.wakeup, self.wakeup_data)

    def command(self, ctx, name, *args):
        """ Execute a raw command """
        args = [name.encode()] + [str(arg).encode() for arg in args if arg is not None] + [None]
        self.mpv_command(ctx, (c_char_p * len(args))(*args))

    def command_node(self, ctx, *args):
        """Send a command with an MpvNode instead of strings."""
        nb = NodeBuilder(args)
        res = MpvNode()
        self.mpv_command_node(ctx, cast(addressof(nb.node), POINTER(MpvNode)),
                              cast(addressof(res), POINTER(MpvNode)))
        data = res.get_value()
        self.mpv_free_node_contents(cast(addressof(res), POINTER(MpvNode)))
        return data

    def set_option(self, ctx, name, v):
        nb = NodeBuilder(v)
        self.mpv_set_option(ctx, name.encode(), MpvFormat.NODE, cast(addressof(nb.node), POINTER(MpvNode)))

    def _get_property(self, ctx, prop, mpv_format):
        if mpv_format == MpvFormat.NONE:
            return None
        res = MpvFormat.ctype(mpv_format)()
        self.mpv_get_property(ctx, prop.encode(), mpv_format, addressof(res))
        if mpv_format in [MpvFormat.STRING, MpvFormat.OSD_STRING]:
            data = res.value.decode()
            self.mpv_free(res)
            return data
        elif mpv_format == MpvFormat.FLAG:
            return bool(res.value)
        elif mpv_format == MpvFormat.INT64:
            return int(res.value)
        elif mpv_format == MpvFormat.DOUBLE:
            return float(res.value)
        elif mpv_format == MpvFormat.NODE:
            data = res.get_value()
            self.mpv_free_node_contents(cast(addressof(res), POINTER(MpvNode)))
            return data

    def _set_property(self, ctx, prop, mpv_format, value):
        if mpv_format == MpvFormat.NONE:
            return None
        val = MpvFormat.ctype(mpv_format)()
        if mpv_format in [MpvFormat.STRING, MpvFormat.OSD_STRING]:
            val.value = value.encode()
        elif mpv_format == MpvFormat.FLAG:
            val.value = int(value)
        elif mpv_format == MpvFormat.INT64:
            val.value = int(value)
        elif mpv_format == MpvFormat.DOUBLE:
            val.value = float(value)
        elif mpv_format == MpvFormat.NODE:
            raise NotImplementedError
        self.mpv_set_property(ctx, prop.encode(), mpv_format, addressof(val))


LIBMPV = LibMPV()
