""" RUM script injection helper methods

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
import sys

try:
    from oboe_ext import Context as SwigContext, Event as SwigEvent, UdpReporter, Metadata
except ImportError, e:
    from oboe_noop import Context as SwigContext, Event as SwigEvent, UdpReporter, Metadata

import hashlib, binascii, re, logging
_log = logging.getLogger('oboe')

CUSTOMER_RUM_ID = None

_RUM_LOADED = None # either False (disabled), True, or None (not loaded)
_UUID_RE = re.compile('[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\Z')

def _access_key_to_rum_id(uuid):
    # RFC 4648 base64url encoding
    return binascii.b2a_base64(hashlib.sha1('RUM'+uuid).digest())\
        .rstrip().replace('+', '-').replace('/', '_')

def _initialize_rum():
    TLY_CONF_FILE = '/etc/tracelytics.conf'
    global CUSTOMER_RUM_ID, _RUM_LOADED
    if _RUM_LOADED:
        return
    try:
        access_key = ([l.rstrip().split('=')[1] for l in open(TLY_CONF_FILE, 'r')
                       if l.startswith('tracelyzer.access_key=')] + [None])[0]
    except IOError, e:
        _log.warn("RUM initialization: couldn't read %s (%s). "
                  "RUM will be disabled unless oboe.config['access_key'] is set.",
                  TLY_CONF_FILE, e.strerror)
        return
    if access_key and _UUID_RE.match(access_key):
        CUSTOMER_RUM_ID = _access_key_to_rum_id(access_key)
        _RUM_LOADED = True
_initialize_rum()

def _check_rum_config():
    # if /etc/tracelytics.conf is not available, check for user-configured value
    # oboe.config['access_key'] once (after init has finished).
    import oboe
    global CUSTOMER_RUM_ID, _RUM_LOADED
    access_key = oboe.config.get('access_key', None)
    if isinstance(access_key, basestring) and _UUID_RE.match(access_key):
        CUSTOMER_RUM_ID = _access_key_to_rum_id(access_key)
        _RUM_LOADED = True  # success finding access key
    else:
        _RUM_LOADED = False # checked oboe.config, but failed

def rum_header(trace_ajax=False):
    """ Return the RUM header for use in your app's HTML response,
    near the beginning of the <head> element, but after your meta tags."""
    if _RUM_LOADED == None:
        _check_rum_config()
    if not CUSTOMER_RUM_ID or not SwigContext.isValid():
        # no valid customer UUID found, or not tracing this request: no RUM injection
        return ''
    if trace_ajax:
        return r'''<script type="text/javascript">(function(){var d=this._tly={q:[],mark:function(a,b){d.q.push(["mark",a,b||(new Date).getTime()])},measure:function(a,b,c){d.q.push(["measure",a,b,c||(new Date).getTime()])},done:function(a){d.q.push(["done",a])},cid:"''' + CUSTOMER_RUM_ID + r'''",xt:"''' + SwigContext.toString() + r'''"};d.mark("firstbyte");var f;f=function(){};var g=0;function h(a){return function(b){b[a]||(b[a]=!0,d.measure(["_ajax",b.a,a]))}}var i=h("recv"),j=h("send");
function l(){var a=this&&this._tl,b=a.b;4===this.readyState&&i(a);f();for(a=0;a<b.length;a++)b[a].apply(this,arguments)}var m=this.XMLHttpRequest,n=m&&m.prototype;
if(n){var o=n.open;n.open=function(a,b,c,e,u){f();this._tl||(this._tl={a:g++,async:c,b:[]},d.measure(["_ajax",this._tl.a,"init",a,b]));return e?o.call(this,a,b,c,e,u):o.call(this,a,b,c)};var p=n.send;n.send=function(a){function b(){try{var a;a:{var b=l;try{if(c.addEventListener){c.addEventListener("readystatechange",b);a=!0;break a}}catch(w){}a=!1}if(!a){var k=c.onreadystatechange;if(k){if(!k.apply)return;f();e.b.push(k)}f();c.onreadystatechange=l}}catch(x){}}var c=this,e=c&&c._tl;f();b();j(e);a=
p.call(c,a);!e.async||4===c.readyState?i(e):setTimeout(function(){try{4===c.readyState?i(e):c.onreadystatechange!==l&&b()}catch(a){}},0);return a}}this.onerror=function(a,b,c){d.measure(["_jserror ",a,"|",b,"|",c].join(""))};var q=this.attachEvent,r=this.addEventListener;var s=function(){d.measure("winload");d.done()};q?q("onload",s):r&&r("load",s,!1);var t=document.createElement("script");t.type="text/javascript";t.async=!0;t.src=("http:"===document.location.protocol?"http:":"https:")+"//d2gfdmu30u15x7.cloudfront.net/1/tly.js";
var v=document.getElementsByTagName("script")[0];v.parentNode.insertBefore(t,v);}());</script>
'''
    else:
        return r'''<script type="text/javascript">(function(){var b=this._tly={q:[],mark:function(a,c){b.q.push(["mark",a,c||(new Date).getTime()])},measure:function(a,c,e){b.q.push(["measure",a,c,e||(new Date).getTime()])},done:function(a){b.q.push(["done",a])},cid:"''' + CUSTOMER_RUM_ID + r'''",xt:"''' + SwigContext.toString() + r'''"};b.mark("firstbyte");this.onerror=function(a,c,e){b.measure(["_jserror ",a,"|",c,"|",e].join(""))};var d=this.attachEvent,f=this.addEventListener;var g=function(){b.measure("winload");b.done()};d?d("onload",g):f&&f("load",g,!1);var h=document.createElement("script");
h.type="text/javascript";h.async=!0;h.src=("http:"===document.location.protocol?"http:":"https:")+"//d2gfdmu30u15x7.cloudfront.net/1/tly.js";var i=document.getElementsByTagName("script")[0];i.parentNode.insertBefore(h,i);}());</script>
'''

def rum_footer():
    """ Return the RUM footer for use in your app's HTML response,
    just before the </body> tag. """
    if _RUM_LOADED == None:
        _check_rum_config()
    if not CUSTOMER_RUM_ID or not SwigContext.isValid():
        return ''
    else:
        return r'''<script type="text/javascript">this._tly&&this._tly.measure("domload");</script>
'''
