"""Test celery instrumentation"""

import base
from distutils.version import LooseVersion # pylint: disable-msg=W0611
from oboeware import oboe_celery # pylint: disable-msg=W0611
import trace_filters as f
import unittest2 as unittest
import mock


# Filters for assertions re: inspecting Events in Traces
is_celery_layer = f.prop_is_in('Layer', ['Celery'])


class TestCelery(base.TraceTestCase):
    """ Tests for the celery instrumentation.
    """

    def __init__(self, *args, **kwargs):
        super(TestCelery, self).__init__(*args, **kwargs)

    def assertHasCeleryEntryAndExit(self, num=1):
        self.assertEqual(num, len(self._last_trace.pop_events(f.is_entry_event, is_celery_layer)))
        exits = self._last_trace.pop_events(f.is_exit_event, is_celery_layer)
        self.assertEqual(num, len(exits))

    def assertSimpleTrace(self, num=1):
        self.assertHasCeleryEntryAndExit(num)
        self.assertNoExtraEvents()

    def test_basic_task(self):
        """ test registering and running a basic task """
        oboe_celery.enable_tracing('add')

        from celery.task import task
        @task(name='add')
        def add(x,y):
            return x+y

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                res = add.apply_async(args=(2,3))
                res = res.get()
        self.assertSimpleTrace()
        self.assertEquals(res, 5)

    def test_method_task(self):
        """ test registering and running a class method task """
        oboe_celery.enable_tracing('add')

        from celery.task import task
        class TaskHolder(object):
            @task(name='add')
            def add(x,y):
                return x+y

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                t = TaskHolder()
                res = t.add.apply_async(args=(2,3))
                res = res.get()
        self.assertSimpleTrace()
        self.assertEquals(res, 5)

    def test_class_task(self):
        """ test registering and running a custom task subclass """
        oboe_celery.enable_tracing('test.unit.test_celery.AddTask')

        from celery import Task
        class AddTask(Task):
            def run(self, x, y):
                return x+y

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                t = AddTask()
                res = t.apply_async(args=(2,3))
                res = res.get()
        self.assertSimpleTrace()
        self.assertEquals(res, 5)

    def test_retry_task_20(self):
        """ test running and retrying basic task, celery 2.x style """
        oboe_celery.enable_tracing('add_and_retry')

        from celery.task import task

        @task(name='add_and_retry')
        def add_and_retry(x, y):
            """ fails once """
            print x,y
            if x == 2:
                add_and_retry.retry(args=(3,3), countdown=0)
            return x+y

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                res = add_and_retry.apply_async(args=(2,3))
                # issue: can't get return value from retry with always eager
        self.assertSimpleTrace()


    def test_retry_task_30(self):
        """ test running and retrying basic task, celery 3.x style """
        oboe_celery.enable_tracing('add')

        from celery.task import task

        @task(name='add_and_retry', bind=True)
        def add_and_retry(self, x, y):
            """ fails once """
            if x == 2:
                raise self.retry(args=(3,3))
            return x+y

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                res = add_and_retry.apply_async(args=(2,3))
                # issue: can't get return value from retry with always eager
        self.assertSimpleTrace()


    def test_two_tasks(self):
        """ Test that we can trace two distinct tasks in a shot """
        oboe_celery.enable_tracing('add')
        oboe_celery.enable_tracing('subtract')

        from celery.task import task
        @task(name='add')
        def add(x,y):
            return x+y

        @task(name='subtract')
        def subtract(x,y):
            return x-y

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                res = add.apply_async(args=(2,3))
                res = res.get()
        self.assertSimpleTrace()
        self.assertEquals(res, 5)

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                res = subtract.apply_async(args=(2,3))
                res = res.get()
        self.assertSimpleTrace()
        self.assertEquals(res, -1)

    def test_multi_enable(self):
        """ Make sure nothing goes wrong if a user enables the same task too many times """
        oboe_celery.enable_tracing('add')
        oboe_celery.enable_tracing('add')
        oboe_celery.enable_tracing('add')

        from celery.task import task
        @task(name='add')
        def add(x,y):
            return x+y

        oboe_celery.enable_tracing('add')
        oboe_celery.enable_tracing('add')
        oboe_celery.enable_tracing('add')

        with self.new_trace(wrap_trace=False):
            with mock.patch('celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
                res = add.apply_async(args=(2,3))
                res = res.get()
        self.assertSimpleTrace()
        self.assertEquals(res, 5)

if __name__ == '__main__':
    unittest.main
