import random
import threading

from unittest import mock

import pytest

import mpv
import mpv.templates


class TestLibraryLoading:
    def test_bad_lib(self):
        with pytest.raises(mpv.LibraryNotLoadedError):
            mpv.Mpv('_non_existant.dll')


class TestLibMpv:
    @pytest.fixture(scope='function')
    def libmpv(self, request):
        instance = mpv.libmpv.LibMPV()
        return instance

    def test_api_version(self, libmpv):
        version = libmpv.client_api_version()
        assert type(version) is tuple
        assert len(version) == 2

    def test_create_handle(self, libmpv):
        handle = libmpv.mpv_create()
        assert isinstance(handle, mpv.types.MpvHandle)

    def test_initialize(self, libmpv):
        handle = libmpv.mpv_create()

        prop = 'pause'
        mpv_type, access = mpv.PROPERTIES[prop]

        with pytest.raises(mpv.MpvError) as e:
            libmpv._get_property(handle, prop, mpv_type)
        assert e.value.error_code == mpv.ErrorCode.UNINITIALIZED

        libmpv.mpv_initialize(handle)

        libmpv._get_property(handle, prop, mpv_type)

    def test_quit(self, libmpv):
        handle = libmpv.mpv_create()
        libmpv.mpv_initialize(handle)

        libmpv.command(handle, 'quit')
        event = libmpv.mpv_wait_event(handle, 0).contents.as_object()
        while event.event_id != mpv.EventID.SHUTDOWN:
            event = libmpv.mpv_wait_event(handle, -1).contents.as_object()
            assert event.event_id in [mpv.EventID.SHUTDOWN,
                                      mpv.EventID.IDLE]
        assert event.event_id == mpv.EventID.SHUTDOWN

    def test_none_property(self, libmpv):
        handle = libmpv.mpv_create()
        with pytest.raises(TypeError):
            libmpv._get_property(handle, 'volume', mpv.Format.NONE)
        with pytest.raises(TypeError):
            libmpv._set_property(handle, 'volume', mpv.Format.NONE, 5)


class TestApi:
    @pytest.fixture(scope='function')
    def mpvinstance(self, request):
        instance = mpv.Mpv()
        instance.initialize()

        def fin():
            instance.command('quit')
        request.addfinalizer(fin)
        return instance

    def test_available_propertes(self, mpvinstance):
        yes = mpvinstance.available_properties()
        no = mpvinstance.unavailable_properties()

        assert set(yes).isdisjoint(no)

    def test_property_exists(self, mpvinstance):
        for name, (ptype, access) in mpv.PROPERTIES.items():
            if 'r' in access:
                name = name.replace('-', '_')
                try:
                    getattr(mpvinstance, name)
                except mpv.MpvError as e:
                    print(name)
                    assert e.error_code.value != mpv.ErrorCode.PROPERTY_NOT_FOUND

    def test_observe_property(self, mpvinstance):
        with pytest.raises(AttributeError):
            mpvinstance.observe_property('paused')
        mpvinstance.observe_property('pause')
        mpvinstance.observe_property('mute', reply_userdata=-15)

    def test_observe_unobserve_property(self, mpvinstance):
        id_ = 123
        mpvinstance.observe_property('pause', reply_userdata=id_)
        mpvinstance.unobserve_property(id_)

    def test_volume(self, mpvinstance):
        mpvinstance.volume = 50
        assert mpvinstance.volume == 50
        mpvinstance.volume = 50.5
        assert mpvinstance.volume == 50.5
        mpvinstance.volume = 50.0
        assert mpvinstance.volume == 50.0

    def test_wait_event(self, mpvinstance):
        event = mpvinstance.wait_event(timeout=-1)
        assert event is not None

    def test_command_node(self, mpvinstance):
        mpvinstance.command_node('loadfile', 'test', 'replace',
                                 {'start': '+100', 'vid': 'no'})
        with pytest.raises(mpv.MpvError):
            mpvinstance.command_node('loadfile', 'test', 'replace1',
                                     {'start': '+100', 'vid': 'no'})

    def test_command(self, mpvinstance):
        mpvinstance.command('loadfile', 'test', 'replace',
                            'start=+100,vid=no')
        with pytest.raises(mpv.MpvError):
            mpvinstance.command('loadfile', 'test', 'replace1',
                                'start=+100,vid=no')

    def test_set_option_bad_option(self, mpvinstance):
        option, value = 'non_existant_option', True

        with pytest.raises(mpv.MpvError) as e:
            mpvinstance.set_option(option, value)
        assert e.value.func == 'mpv_set_option'
        assert e.value.error_code == mpv.ErrorCode.OPTION_NOT_FOUND
        assert option in e.value.args
        assert value in e.value.args

    def test_wakeup_callback(self, mpvinstance):
        userdata = mock.Mock()

        def wakeup(ctx):
            assert ctx == userdata
            ctx(True)

        mpvinstance.observe_property('pause')
        assert not userdata.called

        mpvinstance.set_wakeup_callback(wakeup, userdata)
        mpvinstance.pause = True
        mpvinstance.pause = False

        assert userdata.called
        userdata.assert_called_with(True)


class TestTemplate:
    @pytest.fixture(scope='function')
    def template(self, request):
        instance = mpv.templates.MpvTemplate()

        def fin():
            instance.exit()
        request.addfinalizer(fin)
        return instance

    def test_observed_property(self, template):
        prop = 'volume'
        prop_mock = mock.Mock()
        condition = threading.Condition(template._lock)

        def on_property_change(event):
            if event.name == prop:
                prop_mock(event)
                with condition:
                    condition.notify_all()

        template.on_property_change = on_property_change

        template.observe_property(prop)

        with condition:
            template.volume = 0
            condition.wait(1)

        for val in [random.randint(1, 100) for _ in range(10)]:
            with condition:
                template.volume = val
                condition.wait(5)
            prop_mock.assert_any_call(mpv.events.Property(prop, val))

    def test_not_observed_property(self, template):
        template.on_property_change = mock.Mock()

        for val in [random.randint(0, 100) for _ in range(10)]:
            template.volume = val
        assert template.on_property_change.call_count == 0

    def test_observe_unobserve_property_via_reply_userdata(self, template):
        prop_mock = mock.Mock()
        cond = threading.Condition(template._lock)

        def on_property_change(event):
            if event.name == 'pause':
                prop_mock(event)
                with cond:
                    cond.notify_all()

        template.on_property_change = on_property_change

        id_ = 123

        template.pause = False
        prop_mock.assert_not_called()

        template.observe_property('pause', reply_userdata=id_)

        with cond:
            template.pause = False
            cond.wait(1)

        for state in [True, False, True, False, True]:
            with cond:
                template.pause = state
                cond.wait(5)

        assert (mock.call(mpv.events.Property('pause', True)) in
                prop_mock.call_args_list)

        template.unobserve_property(id_)

        with template._event_condition:
            template._event_condition.wait(1)

        prop_mock.reset_mock()

        template.pause = False
        prop_mock.assert_not_called()

    def test_log_handler(self, template):
        log_handler = mock.Mock()
        cond = threading.Condition()

        def on_log_message(event):
            log_handler(event)
            with cond:
                cond.notify_all()

        template.on_log_message = on_log_message

        assert 'MPVEventHandlerThread' in [t.name for t in threading.enumerate()]

        with cond:
            template.request_log_messages(mpv.LogLevel.INFO)
            template.play('x')
            cond.wait(5)

        assert log_handler.call_count != 0


def test_template_threads():

    def threads():
        return [t.name for t in threading.enumerate()]

    assert 'MPVEventHandlerThread' not in threads()

    template = mpv.templates.MpvTemplate()
    assert 'MPVEventHandlerThread' in threads()

    template.quit()
    template._event_loop.join()
    assert template.handle is None

    assert 'MPVEventHandlerThread' not in threads()


def test_template_threads_context_handler():

    def threads():
        return [t.name for t in threading.enumerate()]

    assert 'MPVEventHandlerThread' not in threads()

    with mpv.templates.MpvTemplate() as template:
        assert template.handle is not None
        assert 'MPVEventHandlerThread' in threads()
        template.quit()  # this would be called by closing the window.

    assert template.handle is None
    assert 'MPVEventHandlerThread' not in threads()


class TestEnums:
    def test_name(self):
        ec = mpv.ErrorCode(0)
        assert ec.name == 'SUCCESS'

    def test_bad_value(self):
        ec = mpv.ErrorCode(5)
        with pytest.raises(ValueError):
            ec.name

    def test_equality(self):
        success = mpv.ErrorCode.SUCCESS
        uninit = mpv.ErrorCode.UNINITIALIZED
        assert type(success) is int and type(uninit) is int
        a = mpv.ErrorCode(success)
        b = mpv.ErrorCode(success)
        c = mpv.ErrorCode(uninit)
        assert not isinstance(a, int)
        assert a == success and a == b
        assert c == uninit and a != c


class TestFormat:
    def test_none(self):
        data = ''
        fmt = mpv.Format(mpv.Format.NONE)
        decoded = fmt.decode(data)
        assert decoded is None

    def test_string_encode_decode(self):
        data = 'testing'
        fmt = mpv.Format(mpv.Format.STRING)
        encoded = fmt.encode(data)
        decoded = fmt.decode(encoded)
        assert decoded == data

    def test_int64_encode(self):
        data = 12345
        fmt = mpv.Format(mpv.Format.INT64)
        encoded = fmt.encode(data)
        decoded = fmt.decode(encoded)
        assert decoded == data

    def test_node_encode_decode(self):
        data = {
            '1': 2,
            '2': '3',
            '3': True,
            '4': 4.0,
            '5': [1, 2, 3],
            '6': {'11': 11, '22': False, '33': [True, False, True, 5.5]}
        }
        fmt = mpv.Format(mpv.Format.NODE)
        encoded = fmt.encode(data)
        decoded = fmt.decode(encoded)
        assert decoded == data

    def test_node_bad_type(self):
        fmt = mpv.Format(mpv.Format.NODE)
        data = {'1': object()}
        with pytest.raises(TypeError):
            fmt.encode(data)

    def test_node_bad_key(self):
        fmt = mpv.Format(mpv.Format.NODE)
        data = {1: True}
        with pytest.raises(KeyError):
            fmt.encode(data)


class TestEvents:
    def test_equality(self):
        a = mpv.events.Event(1, 2, 3, 4)
        b = mpv.events.Event(1, 2, 3, 4)
        c = mpv.events.Event(1, 2, 3, 5)
        d = (1, 2, 3, 4)
        assert a == b
        assert a != c
        assert a != d
