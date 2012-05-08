import oboe

def wrap_execute(func, f_args, f_kwargs, return_val):
    return { 'Query': f_args[2].replace('%s', "''") }

def wrap(module):
    """ wrap default SQLAlchemy dialect, to catch execute calls to the cursor. """
    cls = getattr(module, 'DefaultDialect', None)
    if cls:
        do_execute = getattr(cls, 'do_execute', None)
        if do_execute:
            cls.do_execute = oboe.Context.log_method(layer='sqlalchemy', backtrace=True, callback=wrap_execute)(do_execute.im_func)
        do_executemany = getattr(cls, 'do_executemany', None)
        if do_executemany:
            cls.do_executemany = oboe.Context.log_method(layer='sqlalchemy', backtrace=True, callback=wrap_execute)(do_executemany.im_func)

try:
    import sqlalchemy
    wrap(sqlalchemy.engine.default)
except ImportError:
    pass
