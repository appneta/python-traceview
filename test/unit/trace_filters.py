""" Helpers for examining MockTrace events. """

def _and(*filters):
    def wrapped(*args, **kwargs):
        result = True
        for _filter in filters:
            result = result and _filter(*args, **kwargs)
        return result
    return wrapped
def has_prop(prop):
    return lambda ev: prop in ev.props
def prop_is_in(prop, values_set):
    return lambda ev: (prop in ev.props) and (ev.props[prop] in values_set)
def prop_is(prop, value):
    return lambda ev: (prop in ev.props) and (ev.props[prop] == value)
def label_is(label):
    return prop_is('Label', label)
def layer_is(layer):
    return prop_is('Layer', layer)
is_remote_host_event = _and(has_prop('RemoteHost'), label_is('info'))
is_entry_event = label_is('entry')
is_exit_event = label_is('exit')

