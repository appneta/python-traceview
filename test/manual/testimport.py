import oboeware.imports as imports, sys

def try_imports_lib():
    a = imports.lazyModule('base64')

    HOOKS={ 'binascii' : ['b2a_hex'],
            'base64' : ['b64encode'],
            'oboeware.django' : ['OboeDjangoMiddleware']}

    def hook(module):
        print "hook", module.__name__

        def wrap(fn, *args, **kw):
            print "wrapped", fn.__name__
            return fn

        # wrap callables we want to wrap
        for attr in HOOKS[module.__name__]:
            setattr(module, attr, wrap(getattr(module, attr)))

        #print repr(obj)

    imports.whenImported('binascii', hook)
    imports.whenImported('base64', hook)

    from binascii import b2a_hex

    print b2a_hex('yo')

    from base64 import b64encode

    print b64encode("blah")
