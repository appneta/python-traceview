def doit1():
    import oboe
    oboe.Context.isValid()

#import oboe
#def doit2():
#    oboe.Context.isValid()

oboe = None
def import_oboe():
    """ low-overhead version of 'import oboe', following advice from
        http://wiki.python.org/moin/PythonSpeed/PerformanceTips#Import_Statement_Overhead
    """
    global oboe
    if oboe is None:
        try:
            import oboe
        except ImportError:
            return None
    return oboe

def doit2():
    global oboe
    oboe.Context.isValid()

import timeit
t = timeit.Timer(setup='from __main__ import doit1', stmt='doit1()')
print t.timeit()

t = timeit.Timer(setup='from __main__ import doit2', stmt='doit2()')
print t.timeit()
