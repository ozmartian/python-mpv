import logging
import threading
from mpv.api import MPV
from mpv.types import MpvLogLevel, MpvEventID
from mpv.exceptions import MpvError
log = logging.getLogger(__name__)


class _EventThread(threading.Thread):

    def __init__(self, mpv_instance, event_callback):
        super().__init__(name='MPVEventHandlerThread')
        self.mpv = mpv_instance
        self.callback = event_callback

    def run(self):
        log.debug('Event loop: starting.')
        while True:
            try:
                event = self.mpv.wait_event(timeout=-1)
                devent = event.as_dict()
            except Exception as e:
                log.debug('Event loop: ' + str(e))
                break
            if devent['event_id'] == MpvEventID.NONE:
                log.debug('Event loop: None event.')
                self.callback(devent)
                break
            elif devent['event_id'] == MpvEventID.SHUTDOWN:
                log.debug('Event loop: Shutdown event.')
                self.mpv.detach_destroy()
                self.mpv = None
                self.callback(devent)
                break
            self.callback(devent)


class MpvTemplate(object):

    def __init__(self):
        self.mpv = None

    def initialize(self, observe=None, log_level=MpvLogLevel.INFO, log_handler=None, **kwargs):
        self.mpv = MPV(**kwargs)

        if observe is not None:
            for prop in observe:
                self.mpv.observe_property(prop)

        if log_handler is not None:
            self.mpv.request_log_messages(log_level)
            self.log_handler = log_handler

        self._event_loop = _EventThread(self.mpv, self._handle_event)
        self._event_loop.start()

    def _handle_event(self, event):
        handler = getattr(self, 'on_{}'.format(MpvEventID.name(event['event_id']).lower()))
        handler(event['event'])

    def quit(self):
        log.debug('quit')
        self.mpv.quit()  # trigger a SHUTDOWN event.
        self._event_loop.join()  # block until mpv dies.
        self.mpv = None

    def on_none(self, event):
        pass

    def on_shutdown(self, event):
        pass

    def on_log_message(self, event):
        msg = '{}: {}'.format(event['prefix'], event['text'])
        self.log_handler(msg)

    def on_get_property_reply(self, event):
        pass

    def on_set_property_reply(self, event):
        pass

    def on_command_reply(self, event):
        pass

    def on_start_file(self, event):
        pass

    def on_end_file(self, event):
        pass

    def on_file_loaded(self, event):
        pass

    def on_tracks_changed(self, event):
        """ deprecated """
        pass

    def on_track_switched(self, event):
        """ deprecated """
        pass

    def on_idle(self, event):
        pass

    def on_pause(self, event):
        """ deprecated """
        pass

    def on_unpause(self, event):
        """ deprecated """
        pass

    def on_tick(self, event):
        pass

    def on_script_input_dispatch(self, event):
        """ deprecated """
        pass

    def on_client_message(self, event):
        pass

    def on_video_reconfig(self, event):
        pass

    def on_audio_reconfig(self, event):
        pass

    def on_metadata_update(self, event):
        """ deprecated """
        pass

    def on_seek(self, event):
        pass

    def on_playback_restart(self, event):
        pass

    def on_property_change(self, event):
        pass

    def on_chapter_change(self, event):
        """ deprecated """
        pass

    def on_queue_overflow(self, event):
        pass
