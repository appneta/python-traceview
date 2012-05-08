import sqlalchemy.engine.default

def wrap_default_dialect(module):
    """Returns a wrapped version of class"""

    class DefaultDialect(module.engine.default.DefaultDialect):

        def do_executemany(self, cursor, statement, parameters, context=None):
            try:
                import oboe
                oboe_enabled = True
            except ImportError:
                oboe_enabled = False
            if oboe_enabled:
                oboe.Context.log('sqlalchemy', 'entry', backtrace=False, Query=statement.replace('%s', "''"))
            try:
                super(DefaultDialect, self).do_executemany(cursor, statement, parameters, context=context)
            except Exception, e:
                if oboe_enabled:
                    oboe.Context.log(None, 'error', ErrorClass=e.__class__.__name__, ErrorMsg=str(e))
                raise
            finally:
                if oboe_enabled:
                    oboe.Context.log('sqlalchemy', 'exit')

        def do_execute(self, cursor, statement, parameters, context=None):
            try:
                import oboe
                oboe_enabled = True
            except ImportError:
                oboe_enabled = False
            if oboe_enabled:
                oboe.Context.log('sqlalchemy', 'entry', backtrace=False, Query=statement.replace('%s', "''"))
            try:
                super(DefaultDialect, self).do_execute(cursor, statement, parameters, context=context)
            except Exception, e:
                if oboe_enabled:
                    oboe.Context.log(None, 'error', ErrorClass=e.__class__.__name__, ErrorMsg=str(e))
                raise
            finally:
                if oboe_enabled:
                    oboe.Context.log('sqlalchemy', 'exit')

    return DefaultDialect

def wrap(module):
    """ wrap default SQLAlchemy dialect, to catch execute calls to the cursor. """
    module.engine.default.DefaultDialect = wrap_default_dialect(module)

try:
    import sqlalchemy
    wrap(sqlalchemy)
except ImportError:
    pass
