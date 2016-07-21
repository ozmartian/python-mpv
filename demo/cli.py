import os
import sys
import logging
import mpv
import mpv.templates


class Mpv(mpv.templates.MpvTemplate):

    def on_log_message(self, event):
        super().on_log_message(event)

    def on_property_change(self, event):
        if event.data is None:
            return
        elif event.name == 'duration':
            property_log.info('duration: {}'.format(event.data))
        elif event.name == 'track-list':
            property_log.info('track-list: {}'.format(event.data))
        elif event.name == 'chapter-list':
            property_log.info('chapter-list: {}'.format(event.data))
        elif event.name == 'pause':
            property_log.info('paused!' if event.data else 'unpaused!')


if __name__ == '__main__':
    os.environ['LC_NUMERIC'] = 'C'
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-15s %(levelname)-8s %(message)s')
    mpv_log = logging.getLogger('libmpv')
    property_log = logging.getLogger('libmpv.property')
    if len(sys.argv) < 2:
        print('usage: python mpv-sample.py path-to-video')
        sys.exit(0)

    observe = [
        'duration', 'track-list', 'chapter-list', 'pause'
    ]
    options = {
        'hwdec': 'auto',
        'input-default-bindings': True,
        'input-vo-keyboard': True
    }
    try:
        with Mpv(options, observe, mpv.LogLevel.INFO, mpv_log.debug) as vid:
            vid.play(sys.argv[1])

    except mpv.ApiVersionError as e:
        print('libmpv version error. ' + str(e))
        sys.exit(0)
    except mpv.LibraryNotLoadedError as e:
        print('couldnt load libmpv. ' + str(e))
        sys.exit(0)
