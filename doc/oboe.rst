Oboe
====================================

Oboe is the base library for reporting events to Tracelytics.

.. module:: oboe

Convenience Functions
------------------------------------

These decorators / functions / classes are Python-specific constructs that can
help expand the coverage of existing installations or trace new code paths.

.. autofunction:: trace
.. autoclass:: profile_block
.. autoclass:: profile_function
.. autofunction:: log_method

High-Level API
------------------------------------

The high-level API mimics a logging library. It is most useful in annotating
single-threaded code or synchronous code.

.. autofunction:: log
.. autofunction:: start_trace
.. autofunction:: end_trace
.. autofunction:: log_entry
.. autofunction:: log_error
.. autofunction:: log_exception
.. autofunction:: log_exit
.. autofunction:: last_id


Low-Level API
------------------------------------

The low-level API introduces the concept of a Context, as well as an Event. It
is most useful for annotating webservers or evented code.

.. autoclass:: Context
   :members:

.. autoclass:: Event
   :members:

.. autoclass:: NullEvent
   :members:

