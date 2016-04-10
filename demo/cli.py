import sys
import logging
import mpv


class Mpv(mpv.MpvTemplate):

    def on_log_message(self, event):
        super().on_log_message(event)

    def on_property_change(self, event):
        if event['data'] is None:
            return
        if event['name'] == 'playback-time':
            pass
        elif event['name'] == 'duration':
            property_log.info('duration: {}'.format(event['data']))
        elif event['name'] == 'track-list':
            property_log.info('track-list: {}'.format(event['data']))
        elif event['name'] == 'chapter-list':
            property_log.info('chapter-list: {}'.format(event['data']))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-15s %(levelname)-8s %(message)s')
    mpv_log = logging.getLogger('libmpv')
    property_log = logging.getLogger('libmpv.property')
    if len(sys.argv) < 2:
        print('usage: python mpv-sample.py path-to-video')
        sys.exit(0)

    mpv.load_library()
    vid = Mpv()
    vid.initialize(log_handler=mpv_log.debug,
                   log_level=mpv.MpvLogLevel.INFO,
                   hwdec='auto',
                   input_default_bindings=True,
                   input_vo_keyboard=True,
                   observe=['playback-time', 'duration', 'track-list', 'chapter-list'])
    vid.mpv.play(sys.argv[1])
