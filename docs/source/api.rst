.. _api:

.. module:: mpv

The Mpv Object
==============

.. autoclass:: mpv.Mpv
    :inherited-members:
    :members:

Templates
=========

Base
----

.. autoclass:: mpv.templates.AbstractTemplate
    :members:
    :exclude-members: initialize

Pure Python Template
--------------------

.. autoclass:: mpv.templates.MpvTemplate
    :members:


PyQt5 Template
--------------

.. autoclass:: mpv.templates.MpvTemplatePyQt
    :members:


Events
======

Event
-----

.. autoclass:: mpv.events.Event()
    :members:

Property
--------

.. autoclass:: mpv.events.Property()
    :members:

LogMessage
----------

.. autoclass:: mpv.events.LogMessage()
    :members:

ClientMessage
-------------

.. autoclass:: mpv.events.ClientMessage()
    :members:

EndFile
-------

.. autoclass:: mpv.events.EndFile()
    :members:


Enums
=====

EventID
-------

.. autoclass:: mpv.EventID
    :member-order: bysource
    :members:

LogLevel
--------

.. autoclass:: mpv.LogLevel
    :member-order: bysource
    :members:

Formats
-------

.. autoclass:: mpv.Format
    :member-order: bysource
    :members:

Errors
------

.. autoclass:: mpv.ErrorCode
    :member-order: bysource
    :members:

End File
--------

.. autoclass:: mpv.EndFileReason
    :member-order: bysource
    :members:

Sub Api
-------

.. autoclass:: mpv.SubApi
    :member-order: bysource
    :members:


Exceptions
==========

.. autoexception:: mpv.MpvError()
    :members:

.. autoexception:: mpv.LibraryNotLoadedError()
    :members:

.. autoexception:: mpv.ApiVersionError()
    :members: