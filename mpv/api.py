import platform
import logging
from mpv.types import NodeBuilder, MpvFormat, MpvNode, MpvLogLevel, MpvSubApi
from mpv.exceptions import MpvError
from mpv.properties import PROPERTIES
from mpv.libmpv import LIBMPV
log = logging.getLogger(__name__)


def load_library(name=None):
    """ Load the libmpv library.

    :param name: (optional) the pathname of the shared library. """
    LIBMPV.load_library(name)


def load_lua(name=None):
    """Load the liblua library. Use this function if you intend to use mpv's built-in lua interpreter.

    :param name: (optional) the pathname of the shared library. """
    LIBMPV.load_lua(name)


def api_version():
    """Returns the libmpv version as a tuple."""
    return LIBMPV.client_api_version()


class MPV(object):

    def __init__(self, **kwargs):
        """ Create an MPV instance. Any kwargs given will be passed to mpv as options. """
        self.handle = LIBMPV.mpv_create()
        self.opengl = None
        log.debug('libmpv API Version: {}.{}'.format(*api_version()))
        for k, v in kwargs.items():
            try:
                LIBMPV.set_option(self.handle, k.replace('_', '-'), v)
            except MpvError as e:
                log.debug(e)
        LIBMPV.mpv_initialize(self.handle)

    def wait_event(self, timeout=0):
        return LIBMPV.mpv_wait_event(self.handle, float(timeout)).contents

    def terminate_destroy(self):
        self.handle, handle = None, self.handle
        LIBMPV.mpv_terminate_destroy(handle)

    def detach_destroy(self):
        self.handle, handle = None, self.handle
        LIBMPV.mpv_detach_destroy(handle)

    def request_log_messages(self, level):
        if type(level) is int:
            level = repr(MpvLogLevel(level))
        LIBMPV.mpv_request_log_messages(self.handle, level.encode())

    def observe_property(self, name, mpv_format=None, reply_userdata=None):
        if name not in PROPERTIES:
            raise AttributeError('Property "{}" not available.'.format(name))
        if mpv_format is None:
            mpv_format = PROPERTIES[name][0]
        if reply_userdata is None:
            reply_userdata = name
        LIBMPV.mpv_observe_property(self.handle, hash(reply_userdata), name.encode(), mpv_format)

    def unobserve_property(self, reply_userdata):
        LIBMPV.mpv_unobserve_property(self.handle, hash(reply_userdata))

    def command(self, name, *args):
        """Send a command to the player. Commands are the same as those used in ``input.conf``"""
        LIBMPV.command(self.handle, name, *args)

    def command_node(self, *args):
        return LIBMPV.command_node(self.handle, *args)

    def get_opengl_api(self):
        """ load the opengl sub api """
        self.opengl = LIBMPV.get_sub_api(self.handle, MpvSubApi.MPV_SUB_API_OPENGL_CB)

    def opengl_set_update_callback(self, callback, ctx=None):
        LIBMPV.opengl_cb_set_update_callback(self.opengl, callback, ctx)

    def opengl_init_gl(self, get_proc_address, exts=None, ctx=None):
        LIBMPV.opengl_cb_init_gl(self.opengl, exts, get_proc_address, ctx)

    def opengl_draw(self, fbo, w, h):
        LIBMPV.mpv_opengl_cb_draw(self.opengl, fbo, w, h)

    # Shortcuts
    def seek(self, amount, reference='relative', precision='default-precise'):
        self.command_node('seek', amount, reference, precision)

    def revert_seek(self):
        self.command('revert_seek')

    def frame_step(self):
        self.command('frame_step')

    def frame_back_step(self):
        self.command('frame_back_step')

    def add_property(self, name, value=None):
        self.command('add_property', name, value)

    def cycle_property(self, name, direction='up'):
        self.command('cycle_property', name, direction)

    def multiply_property(self, name, factor):
        self.command('multiply_property', name, factor)

    def screenshot(self, includes='subtitles', mode='single'):
        self.command('screenshot', includes, mode)

    def screenshot_to_file(self, filename, includes='subtitles'):
        self.command('screenshot_to_file', filename, includes)

    def playlist_next(self, mode='weak'):
        self.command('playlist_next', mode)

    def playlist_prev(self, mode='weak'):
        self.command('playlist_prev', mode)

    def loadfile(self, filename, mode='replace'):
        self.command('loadfile', filename, mode)

    def loadlist(self, playlist, mode='replace'):
        self.command('loadlist', playlist, mode)

    def playlist_clear(self):
        self.command('playlist_clear')

    def playlist_remove(self, index='current'):
        self.command('playlist_remove', index)

    def playlist_move(self, index1, index2):
        self.command('playlist_move', index1, index2)

    def run(self, command, *args):
        self.command('run', command, *args)

    def quit(self, code=None):
        self.command('quit', code)

    def quit_watch_later(self, code=None):
        self.command('quit_watch_later', code)

    def sub_add(self, filename):
        self.command('sub_add', filename)

    def sub_remove(self, sub_id=None):
        self.command('sub_remove', sub_id)

    def sub_reload(self, sub_id=None):
        self.command('sub_reload', sub_id)

    def sub_step(self, skip):
        self.command('sub_step', skip)

    def sub_seek(self, skip):
        self.command('sub_seek', skip)

    def toggle_osd(self):
        self.command('osd')

    def show_text(self, string, duration='-', level=None):
        self.command('show_text', string, duration, level)

    def show_progress(self):
        self.command('show_progress')

    def discnav(self, command):
        self.command('discnav', command)

    def write_watch_later_config(self):
        self.command('write_watch_later_config')

    def overlay_add(self, overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride):
        self.command('overlay_add', overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride)

    def overlay_remove(self, overlay_id):
        self.command('overlay_remove', overlay_id)

    def script_message(self, *args):
        self.command('script_message', *args)

    def script_message_to(self, target, *args):
        self.command('script_message_to', target, *args)

    # Convenience functions
    def play(self, filename):
        self.loadfile(filename)

    def stop(self):
        self.command('stop')


def _bindproperty(MPV, name, proptype, access):

    def getter(self):
        cval = LIBMPV._get_property(self.handle, name, proptype)
        return cval

    def setter(self, value):
        LIBMPV._set_property(self.handle, name, proptype, value)

    def barf(*args):
        raise NotImplementedError('Access denied')

    setattr(MPV, name.replace('-', '_'), property(getter if 'r' in access else barf, setter if 'w' in access else barf))


for name, (proptype, access) in PROPERTIES.items():
    _bindproperty(MPV, name, proptype, access)
