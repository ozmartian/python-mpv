import logging
from mpv.api import MPV
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from mpv.types import MpvLogLevel, MpvEventID
from mpv.exceptions import MpvError
log = logging.getLogger(__name__)


class EventThread(QThread):
    mpv_event = pyqtSignal(dict)

    def __init__(self, mpv_instance, parent=None):
        super().__init__(parent)
        self.mpv = mpv_instance

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
                self.mpv_event.emit(devent)
                break
            elif devent['event_id'] == MpvEventID.SHUTDOWN:
                log.debug('Event loop: Shutdown event.')
                self.mpv.detach_destroy()
                self.mpv = None
                self.mpv_event.emit(devent)
                break
            self.mpv_event.emit(devent)


class MpvTemplatePyQt(QObject):
    wakeup = pyqtSignal()

    def initialize(self, observe=None, log_level=MpvLogLevel.INFO, log_handler=None, **kwargs):
        self.mpv = MPV(**kwargs)

        if observe is not None:
            for prop in observe:
                self.mpv.observe_property(prop)

        if log_handler is not None:
            self.mpv.request_log_messages(log_level)
            self.log_handler = log_handler

        self.event_loop = EventThread(self.mpv)
        self.wakeup.connect(self.event_loop.start)
        self.event_loop.mpv_event.connect(self.handle_event)
        self.wakeup.emit()

    def quit(self):
        log.debug('quit')
        self.mpv.quit()  # trigger a SHUTDOWN event.
        self.event_loop.wait()  # block until mpv dies.
        self.mpv = None

    def handle_event(self, event):
        handler = getattr(self, 'on_{}'.format(MpvEventID.name(event['event_id']).lower()))
        handler(event['event'])

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

    @pyqtSlot(str)
    def play(self, path):
        self.mpv.play(path)

    @pyqtSlot(int)
    def seek_absolute(self, ms):
        try:
            self.mpv.seek(ms / 1000.0, 'absolute+exact')
        except MpvError as e:
            log.debug(e)
            pass

    @pyqtSlot(int)
    def seek_relative(self, ms):
        self.mpv.seek(ms / 1000.0, 'relative+exact')

    @pyqtSlot(int)
    def set_volume(self, val):
        """ :param val: volume percentage as a float. [0.0, 100.0] """
        self.mpv.volume = val
