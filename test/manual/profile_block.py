import oboe

evt = oboe.Context.startTrace()
evt.addInfo('Layer', 'test')
evt.addInfo('Label', 'entry')
oboe.reporter().sendReport(evt)

with oboe.Context.profile_block('test_block', profile=True, store_backtrace=True):
    for i in xrange(1000):
        z = i*i
        print z

evt = oboe.Context.createEvent()
evt.addInfo('Layer', 'test')
evt.addInfo('Label', 'exit')
oboe.reporter().sendReport(evt)
