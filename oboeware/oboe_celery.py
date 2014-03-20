""" AppNeta TraceView instrumentation for celery.

Copyright (C) 2014 AppNeta Inc.
All rights reserved.
"""
import sys
import oboe

from oboeware import oninit, loader

CELERY_LAYER = 'Celery'

def register_wrapper(orig_register):
    def task_instrumenter(self, task):
        """This wrapper class lives around TaskRegistry.register and makes
           Task objects into instrumented Task objects on register."""

        ret = orig_register(self, task)

        try:
            if task.name in oboe.config['inst']['celery']['wrap']:
                kvs = {#'Domain': defaulted to system hostname
                    'URL': task.name,
                    'Controller': 'Celery',
                    'Action': task.name}
                instrumented_run = oboe.trace(CELERY_LAYER, kvs=kvs, is_method=False)(self[task.name].run)
                setattr(self[task.name], 'run', instrumented_run)
        except Exception, e:
            print >> sys.stderr, "Oboe error:", str(e)
        finally:
            return ret

    return task_instrumenter


def wrap(module):
    try:
        # register(self, Task)
        setattr(module.TaskRegistry, 'register', register_wrapper(module.TaskRegistry.register))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)


def enable_tracing(task_identifier):
    """ Add task or tasks to whitelist for celery tracing.

        task_identifier - a string representing a task name or a list of strings
            representing multiple tasks"""

    if isinstance(task_identifier, str):
        task_identifier = [task_identifier]
    elif not isinstance(task_identifier, list):
        print >> sys.stderr, "Oboe error: add_celery_hooks takes either string or list argument"
        return

    for s in task_identifier:
        oboe.config['inst']['celery']['wrap'].add(s)

    # also, since we're tracing at least one task here, report init and load instrumentation
    oninit.report_layer_init(layer=CELERY_LAYER)
    loader.load_inst_modules()

try:
    import celery

    # we hook into TaskRegistry; it was moved in the 3.0 refactor
    if celery.__version__[0] == '3':
        from celery.app import registry
    else:
        from celery import registry

    wrap(registry)
except ImportError, e:
    pass
