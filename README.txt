AppNeta TraceView instrumentation libraries for Python
=====================================================

The 'oboe' and 'oboeware' modules provide support for instrumenting
programs for use with the Tracelytics Oboe instrumentation library.

The oboe module provides a Pythonic interface to liboboe for C, and
the oboeware module provides middleware and other components for
popular web frameworks such as Django, Tornado, Pylons, and WSGI.

For more help, please contact traceviewsupport@appneta.com or visit:
  https://support.appneta.com/cloud

Thanks for using TraceView!

- The TraceView Team


--


Running the Tests
=====================================================

The instrumentation uses tox to test against different versions of python and
instrumented modules.

The tests currently run against 2.6 and 2.7.

To set up multiple versions of python:

    sudo apt-get install python-software-properties software-properties-common
    sudo add-apt-repository ppa:fkrull/deadsnakes
    sudo apt-get update
    sudo apt-get install python2.6 python2.6-dev

To run tests (requires `virtualenv` >= 1.11.2 and a running a
Redis <http://redis.io/> server):

    tox

Tests in test/unit are actually functional tests; naming is for historic
reasons.  Tests in test/manual are for manual verification of certain
behaviors.

MySQL SQLAlchemy tests require no-auth TCP connection (as testing user).

PostgreSQL SQLAlchemy tests requires no-auth (trust) TCP connection (as testing user).

    # in pg_hba.conf: Don't use this in production!!
    host    all             all             127.0.0.1/32            trust
