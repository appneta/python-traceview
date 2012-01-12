import oboe

# Event::addInfo(char *,void *)
# Event::addInfo(char *,std::string const &)
# Event::addInfo(char *,long)
# Event::addInfo(char *,double)

evt = oboe.Context.startTrace()
evt.addInfo('String', 'teststring')
evt.addInfo('Null', None)
evt.addInfo('Int', 33)
evt.addInfo('Float', 33.33)
evt.addInfo('Array', [33.33, 22])
evt.addInfo('Map', {'key': 'val'})

oboe.reporter().sendReport(evt)
