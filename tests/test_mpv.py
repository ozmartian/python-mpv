import sys
import unittest
from unittest import mock
import time
import random
import threading
import logging
import mpv
mpv.load_library()


class TestMPV(unittest.TestCase):

    def setUp(self):
        self.m = mpv.MPV()

    def test_version(self):
        version = mpv.api_version()
        self.assertTrue(version >= (1, 20))

    def test_property_exists(self):
        for name, (ptype, access) in mpv.PROPERTIES.items():
            if 'r' in access:
                name = name.replace('-', '_')
                try:
                    rv = getattr(self.m, name)
                except mpv.MpvError as e:
                    self.assertNotEqual(e.error_code, mpv.ErrorCode.PROPERTY_NOT_FOUND)

    def test_volume(self):
        self.m.volume = 50
        self.assertEqual(self.m.volume, 50)
        self.m.volume = 50.5
        self.assertEqual(self.m.volume, 50.5)
        self.m.volume = 50.0
        self.assertEqual(self.m.volume, 50.0)

    def test_wait_event(self):
        event = self.m.wait_event(timeout=-1)
        self.assertNotEqual(event, None, msg=event.as_dict())

    def test_command_node(self):
        self.m.command_node('loadfile', '"test"', 'replace', {'start': '+100', 'vid': 'no'})
        self.assertRaises(mpv.MpvError, self.m.command_node, 'loadfile', 'test', 'replace1', {'start': '+100', 'vid': 'no'})

    def test_command(self):
        self.m.command('loadfile', '"test"', 'replace', 'start=+100,vid=no')
        self.assertRaises(mpv.MpvError, self.m.command, 'loadfile', 'test', 'replace1', 'start=+100,vid=no')


class TestTemplate(unittest.TestCase):

    def setUp(self):
        self.instance = mpv.MpvTemplate()

    def tearDown(self):
        try:
            self.instance.quit()
        except (OSError, AttributeError):
            pass

    def test_observed_property(self):
        self.instance.on_property_change = mock.Mock()
        self.instance.initialize(observe=['volume'])

        for val in [round(random.random() * 100, 1) for _ in range(10)]:
            self.instance.mpv.volume = val
            self.instance.on_property_change.assert_any({'name': 'volume', 'data': val})

    def test_not_observed_property(self):
        self.instance.on_property_change = mock.Mock()
        self.instance.initialize()

        for val in [round(random.random() * 100, 1) for _ in range(10)]:
            self.instance.mpv.volume = val
        self.assertEqual(self.instance.on_property_change.call_count, 0)

    def test_log_handler(self):
        log_handler = mock.Mock()
        self.instance.initialize(log_handler=log_handler)

        self.assertEqual(self.instance.log_handler, log_handler)
        self.assertIn('MPVEventHandlerThread', [t.name for t in threading.enumerate()])
        time.sleep(.5)
        self.instance.mpv.play('x')
        time.sleep(.5)
        self.assertNotEqual(log_handler.call_count, 0)

    def test_quit(self):
        self.instance.initialize()

        self.assertNotEqual(self.instance.mpv.handle, None)
        self.instance.quit()
        self.assertIsNone(self.instance.mpv)

    def test_thread(self):

        def threads():
            return [t.name for t in threading.enumerate()]

        self.assertNotIn('MPVEventHandlerThread', threads())
        self.instance.initialize()

        self.assertIn('MPVEventHandlerThread', threads())
        self.instance.quit()
        self.assertIsNone(self.instance.mpv)
        self.assertNotIn('MPVEventHandlerThread', threads())


if __name__ == "__main__":
    unittest.main()
