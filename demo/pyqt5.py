import sys
import os
import logging
from PyQt5.QtWidgets import (QWidget, QMainWindow, QAction, QApplication,
                             QHBoxLayout, QSlider, QFileDialog, QLabel)
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QPoint
import mpv
import mpv.templates


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-15s %(levelname)-8s %(message)s')
mpv_log = logging.getLogger('libmpv')


class Mpv(mpv.templates.MpvTemplatePyQt):
    duration = pyqtSignal(float)
    playback_time = pyqtSignal(float)

    def on_property_change(self, event):
        if event.data is None:
            return

        if event.name == 'playback-time':
            self.playback_time.emit(event.data)
        elif event.name == 'duration':
            self.duration.emit(event.data)


class PlayerControls(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        self.seek_slider = QSlider(orientation=Qt.Horizontal, parent=self)
        self.volume_slider = QSlider(orientation=Qt.Horizontal, maximum=1000,
                                     parent=self)
        self.playback_time = QLabel(parent=self)
        self.duration = QLabel(parent=self)

        layout.addWidget(self.seek_slider)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.playback_time)
        layout.addWidget(self.duration)

        self.setLayout(layout)

    @pyqtSlot(float)
    def update_seek_slider_position(self, val):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setSliderPosition(val * 1000)

    @pyqtSlot(float)
    def update_seek_slider_maximum(self, val):
        self.seek_slider.setMaximum(val * 1000)

    @pyqtSlot(float)
    def update_duration(self, val):
        self.duration.setText('{:.2f}'.format(val))

    @pyqtSlot(float)
    def update_playback_time(self, val):
        self.playback_time.setText('{:.2f}'.format(val))


class Player(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        # mpv setup
        self.mpv_container = QWidget(self)
        self.setCentralWidget(self.mpv_container)
        self.mpv_container.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.mpv_container.setAttribute(Qt.WA_NativeWindow)
        wid = int(self.mpv_container.winId())
        self.mpv = Mpv(parent=self,
                       wid=wid,
                       log_handler=mpv_log.debug,
                       log_level=mpv.LogLevel.INFO,
                       input_cursor=False,
                       hwdec='auto',
                       observe=['track-list', 'playback-time', 'duration'])

        # ui setup
        menu = self.menuBar().addMenu('&File')
        on_open = QAction('Open', self)
        on_open.triggered.connect(self.on_file_open)
        menu.addAction(on_open)

        self.controller = PlayerControls()
        self.controller.show()

        self.mpv.duration.connect(self.controller.update_seek_slider_maximum)
        self.mpv.duration.connect(self.controller.update_duration)
        self.mpv.playback_time.connect(self.controller.update_seek_slider_position)
        self.mpv.playback_time.connect(self.controller.update_playback_time)

        self.controller.seek_slider.sliderReleased.connect(self.slider_seek)
        self.controller.volume_slider.valueChanged.connect(self.slider_volume)

    @pyqtSlot()
    def on_file_open(self):
        open_file, filtr = QFileDialog.getOpenFileName(self, 'Open File')
        logging.debug('Opening file: {}'.format(open_file))
        if open_file:
            self.mpv.play(os.path.abspath(open_file))

    @pyqtSlot()
    def slider_seek(self):
        self.mpv.seek_absolute(self.controller.seek_slider.value())

    @pyqtSlot(int)
    def slider_volume(self, val):
        self.mpv.set_volume(val / 10.0)

    def closeEvent(self, event):
        self.controller.close()
        self.mpv.quit()


if __name__ == '__main__':
    os.environ['LC_NUMERIC'] = 'C'

    app = QApplication(sys.argv)
    try:
        window = Player()
    except mpv.ApiVersionError as e:
        print('libmpv version error. ' + str(e))
        sys.exit(0)
    except mpv.LibraryNotLoadedError as e:
        print('couldnt load libmpv. ' + str(e))
        sys.exit(0)
    else:
        window.show()
        window.controller.move(QPoint(window.x() + window.width(), window.y()))
        sys.exit(app.exec_())
