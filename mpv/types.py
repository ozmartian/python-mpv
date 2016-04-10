import logging
from ctypes import (c_void_p, c_int, c_longlong, c_ulonglong, c_ulong,
                    c_char_p, c_size_t, c_double, Structure, Union, POINTER,
                    CFUNCTYPE, cast, addressof)
from mpv.exceptions import MpvError
log = logging.getLogger(__name__)


class MpvHandle(c_void_p):
    pass


class MpvOpenGLCbContext(c_void_p):
    pass


class MpvSubApi(c_int):
    MPV_SUB_API_OPENGL_CB = 1


class ErrorCode(c_int):
    """ For documentation on these, see mpv's libmpv/client.h """
    SUCCESS                 = 0
    EVENT_QUEUE_FULL        = -1
    NOMEM                   = -2
    UNINITIALIZED           = -3
    INVALID_PARAMETER       = -4
    OPTION_NOT_FOUND        = -5
    OPTION_FORMAT           = -6
    OPTION_ERROR            = -7
    PROPERTY_NOT_FOUND      = -8
    PROPERTY_FORMAT         = -9
    PROPERTY_UNAVAILABLE    = -10
    PROPERTY_ERROR          = -11
    COMMAND                 = -12
    LOADING_FAILED          = -13
    AO_INIT_FAILED          = -14
    VO_INIT_FAILED          = -15
    NOTHING_TO_PLAY         = -16
    UNKNOWN_FORMAT          = -17
    UNSUPPORTED             = -18
    NOT_IMPLEMENTED         = -19


class MpvFormat(c_int):
    NONE        = 0
    STRING      = 1
    OSD_STRING  = 2
    FLAG        = 3
    INT64       = 4
    DOUBLE      = 5
    NODE        = 6
    NODE_ARRAY  = 7  # Used by NODE
    NODE_MAP    = 8  # Used by NODE
    BYTE_ARRAY  = 9  # Used by NODE

    def __repr__(self):
        return ['NONE', 'STRING', 'OSD_STRING', 'FLAG', 'INT64', 'DOUBLE',
                'NODE', 'NODE_ARRAY', 'NODE_MAP', 'BYTE_ARRAY'][self.value]

    def to_ctype(self):
        return MpvFormat.ctype(self.value)

    @staticmethod
    def ctype(value):
        return [None, c_char_p, c_char_p, c_int, c_longlong, c_double, MpvNode,
                MpvNodeList, MpvNodeList, MpvByteArray][value]


class MpvLogLevel(c_int):
    NONE  = 0    # "no"    - disable absolutely all messages
    FATAL = 10   # "fatal" - critical/aborting errors
    ERROR = 20   # "error" - simple errors
    WARN  = 30   # "warn"  - possible problems
    INFO  = 40   # "info"  - informational message
    V     = 50   # "v"     - noisy informational message
    DEBUG = 60   # "debug" - very noisy technical information
    TRACE = 70   # "trace" - extremely noisy

    def __repr__(self):
        return ['no', 'fatal', 'error', 'warn',
                'info', 'v', 'debug', 'trace'][self.value // 10]


class MpvEventID(c_int):
    NONE                    = 0
    SHUTDOWN                = 1
    LOG_MESSAGE             = 2
    GET_PROPERTY_REPLY      = 3
    SET_PROPERTY_REPLY      = 4
    COMMAND_REPLY           = 5
    START_FILE              = 6
    END_FILE                = 7
    FILE_LOADED             = 8
    TRACKS_CHANGED          = 9   # deprecated: equivalent to using mpv_observe_property() on the "track-list" property.
    TRACK_SWITCHED          = 10  # deprecated: equivalent to using mpv_observe_property() on the "vid", "aid", "sid" property.
    IDLE                    = 11
    PAUSE                   = 12  # deprecated
    UNPAUSE                 = 13  # deprecated
    TICK                    = 14
    SCRIPT_INPUT_DISPATCH   = 15  # deprecated
    CLIENT_MESSAGE          = 16
    VIDEO_RECONFIG          = 17
    AUDIO_RECONFIG          = 18
    METADATA_UPDATE         = 19  # deprecated: equivalent to using mpv_observe_property() on the "metadata" property.
    SEEK                    = 20
    PLAYBACK_RESTART        = 21
    PROPERTY_CHANGE         = 22
    CHAPTER_CHANGE          = 23  # depricated: equivalent to using mpv_observe_property() on the "chapter" property.
    QUEUE_OVERFLOW          = 24

    def to_ctype(self):
        return MpvEventID.ctype(self.value)

    @staticmethod
    def name(value):
        return ['NONE', 'SHUTDOWN', 'LOG_MESSAGE', 'GET_PROPERTY_REPLY',
                'SET_PROPERTY_REPLY', 'COMMAND_REPLY', 'START_FILE', 'END_FILE',
                'FILE_LOADED', 'TRACKS_CHANGED', 'TRACK_SWITCHED', 'IDLE',
                'PAUSE', 'UNPAUSE', 'TICK', 'SCRIPT_INPUT_DISPATCH',
                'CLIENT_MESSAGE', 'VIDEO_RECONFIG', 'AUDIO_RECONFIG', 'METADATA_UPDATE',
                'SEEK', 'PLAYBACK_RESTART', 'PROPERTY_CHANGE', 'CHAPTER_CHANGE',
                'QUEUE_OVERFLOW'][value]

    @staticmethod
    def ctype(value):
        return [None, None, MpvEventLogMessage, None, None, None, None, MpvEventEndFile,
                None, None, None, None, None, None, None, MpvEventScriptInputDispatch,
                MpvEventClientMessage, None, None, None, None, None, MpvEventProperty, None][value]


class MpvEvent(Structure):
    _fields_ = [('event_id', MpvEventID),
                ('error', c_int),
                ('reply_userdata', c_ulonglong),
                ('data', c_void_p)]

    def as_dict(self):
        dtype = self.event_id.to_ctype()
        return {'event_id': self.event_id.value,
                'error': self.error,
                'reply_userdata': self.reply_userdata,
                'event': cast(self.data, POINTER(dtype)).contents.as_dict() if dtype else None}


class MpvEventProperty(Structure):
    _fields_ = [('name', c_char_p),
                ('format', MpvFormat),
                ('data', c_void_p)]

    def as_dict(self):
        dpointer = cast(self.data, POINTER(self.format.to_ctype()))
        if self.format.value == MpvFormat.NONE:
            data = None
        elif self.format.value == MpvFormat.NODE:
            data = dpointer.contents.get_value()
        elif self.format.value == MpvFormat.STRING:
            data = dpointer.contents.value.decode()
        else:
            data = dpointer.contents.value
        return {'name': self.name.decode(),
                #'format': self.format.value,
                'data': data}


class MpvNodeList(Structure):

    def __init__(self, is_map, num):
        self.num = num
        v = (MpvNode * num)()
        self.values = cast(v, POINTER(MpvNode))
        if is_map:
            k = (c_char_p * num)()
            self.keys = cast(k, POINTER(c_char_p))

    def as_list(self):
        return [self.values[i] for i in range(self.num)]

    def as_dict(self):
        return {self.keys[i].decode(): self.values[i] for i in range(self.num)}


class MpvByteArray(Structure):
    _fields_ = [('data', c_void_p),
                ('size', c_size_t)]


class _MpvNodeUnion(Union):
    _fields_ = [('string', c_char_p),
                ('flag', c_int),
                ('int64', c_longlong),
                ('double_', c_double),
                ('list', POINTER(MpvNodeList)),
                ('ba', POINTER(MpvByteArray))]


class MpvNode(Structure):
    _anonymous_ = ('u',)
    _fields_ = [('u', _MpvNodeUnion),
                ('format', MpvFormat)]

    def get_value(self):
        # this doesn't work with {}[] instead of if statements.
        if self.format.value in [MpvFormat.STRING, MpvFormat.OSD_STRING]:
            return self.string.decode()
        elif self.format.value == MpvFormat.FLAG:
            return bool(self.flag)
        elif self.format.value == MpvFormat.INT64:
            return self.int64
        elif self.format.value == MpvFormat.DOUBLE:
            return self.double_
        elif self.format.value == MpvFormat.NODE_ARRAY:
            return [node.get_value() for node in self.list.contents.as_list()]
        elif self.format.value == MpvFormat.NODE_MAP:
            return {key: node.get_value() for key, node in self.list.contents.as_dict().items()}
        elif self.format.value == MpvFormat.BYTE_ARRAY:
            raise NotImplementedError
        else:
            return None


MpvNodeList._fields_ = [('num', c_int),
                        ('values', POINTER(MpvNode)),
                        ('keys', POINTER(c_char_p))]


class MpvEventLogMessage(Structure):
    _fields_ = [('prefix', c_char_p),
                ('level', c_char_p),
                ('text', c_char_p)]

    def as_dict(self):
        return {name: getattr(self, name).decode().rstrip('\n') for name, _t in self._fields_}


class MpvEndFileReason(c_int):
    EOF = 0
    STOP = 2
    QUIT = 3
    ERROR = 4
    REDIRECT = 5

    def __repr__(self):
        return ['EOF', '', 'STOP', 'QUIT', 'ERROR', 'REDIRECT'][self.value]


class MpvEventEndFile(Structure):
    _fields_ = [('reason', MpvEndFileReason),
                ('error', ErrorCode)]

    def as_dict(self):
        return {'reason': self.reason.value,
                'error': (self.error.value if self.reason.value == MpvEndFileReason.ERROR
                          else None)}


class MpvEventScriptInputDispatch(Structure):  # deprecated
    _fields_ = [('arg0', c_int),
                ('type', c_char_p)]

    def as_dict(self):
        pass


class MpvEventClientMessage(Structure):
    _fields_ = [('num_args', c_int),
                ('args', POINTER(c_char_p))]

    def as_dict(self):
        return {'args': [self.args[i].value for i in range(self.num_args.value)]}


WakeupCallback = CFUNCTYPE(None, c_void_p)
OpenGlCbUpdateFn = CFUNCTYPE(None, c_void_p)
OpenGlCbGetProcAddrFn = CFUNCTYPE(c_int, c_void_p, c_char_p)


class NodeBuilder(object):

    def __init__(self, value):
        self.heap = []
        self.node = MpvNode()
        self.set(self.node, value)

    def set(self, dst, src):
        src_t = type(src)
        if src_t is str:
            dst.format.value = MpvFormat.STRING
            dst.string = src.encode()
        elif src_t is bool:
            dst.format.value = MpvFormat.FLAG
            dst.flag = int(src)
        elif src_t is int:
            dst.format.value = MpvFormat.INT64
            dst.int64 = src
        elif src_t is float:
            dst.format.value = MpvFormat.DOUBLE
            dst.double_ = src
        elif src_t in (list, tuple):
            l = MpvNodeList(False, len(src))
            self.heap.append(l)
            dst.format.value = MpvFormat.NODE_ARRAY
            dst.list = cast(addressof(l), POINTER(MpvNodeList))
            for i, item in enumerate(src):
                self.set(dst.list.contents.values[i], item)
        elif src_t is dict:
            l = MpvNodeList(True, len(src))
            self.heap.append(l)
            dst.format.value = MpvFormat.NODE_MAP
            dst.list = cast(addressof(l), POINTER(MpvNodeList))
            for i, (k, v) in enumerate(src.items()):
                dst.list.contents.keys[i] = k.encode()
                self.set(dst.list.contents.values[i], v)
        else:
            return
