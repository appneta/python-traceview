""" Tracelytics instrumentation for Django's template system

Copyright (C) 2014 AppNeta, Inc.
All rights reserved.
"""
import sys
import oboe

TEMPLATE_LAYER = 'template'

def before_render_cb(func, f_args, f_kwargs):
    """ Callback to django.template.base.Template.render(),
        retrieves template name from Template object and
        manually turns a log_method into a profile_function,
        (necessary to dynamically generate profile name...) """
    template_name = f_args[0].name
    keys={'Language': 'template',
          'ProfileName': template_name}
    return (f_args, f_kwargs, keys)

def after_render_cb(func, f_args, f_kwargs, ret):
    template_name = f_args[0].name
    keys={'Language': 'template',
          'ProfileName': template_name}
    return (keys, None)

def wrap(module):
    try:
        # profile on specific template name (inner wrap)
        profile_wrapper_render = oboe.log_method(None,
                                                    before_callback=before_render_cb,
                                                    callback=after_render_cb)

        # overall template layer (outer wrap)
        layer_wrapper_render = oboe.log_method(TEMPLATE_LAYER)

        setattr(module.Template, 'render',
                layer_wrapper_render(profile_wrapper_render(module.Template.render)))

    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)
