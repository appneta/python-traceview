""" RUM script injection helper methods

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""

from oboe_ext import Context as SwigContext
import hashlib, binascii, re, logging
_log = logging.getLogger('oboe')

CUSTOMER_RUM_ID = None

def _get_customer_rum_id():
    TLY_CONF_FILE = '/etc/tracelytics.conf'
    UUID_RE = '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\Z'
    global CUSTOMER_RUM_ID
    if CUSTOMER_RUM_ID:
        return
    try:
        access_key = ([l.rstrip().split('=')[1] for l in open(TLY_CONF_FILE, 'r')
                       if l.startswith('tracelyzer.access_key=')] + [None])[0]
    except IOError as e:
        # couldn't open config file, try settings
        _log.warn("RUM initialization: couldn't read %s (RUM is disabled): %s.",
                  TLY_CONF_FILE, e.strerror)
        return
    if access_key and re.match(UUID_RE, access_key):
        CUSTOMER_RUM_ID = binascii.b2a_base64(hashlib.sha1('RUM'+access_key).digest()).rstrip()
_get_customer_rum_id()

def rum_header():
    """ Return the RUM header for use in your app's HTML response,
    near the beginning of the <head> element, but after your meta tags."""
    if not CUSTOMER_RUM_ID or not SwigContext.isValid():
        # no valid customer UUID found, or not tracing this request: no RUM injection
        return ''
    return r'''<script type="text/javascript">(function(){var e=this._tly={q:[],mark:function(a,b){e.q.push(["mark",a,b||(new Date).getTime()])},measure:function(a,b,c){e.q.push(["measure",a,b,c||(new Date).getTime()])},done:function(a){e.q.push(["done",a])},cid:"''' + CUSTOMER_RUM_ID + r'''",xt:"''' + SwigContext.toString() + r'''"};e.mark("firstbyte");var f;f=function(){};var g=0;function h(a){return function(b){b[a]||(b[a]=!0,e.measure(["_ajax",b.a,a]))}}var i=h("recv"),j=h("send");
function l(){var a=this&&this._tl,b=a.b;4===this.readyState&&i(a);f();for(a=0;a<b.length;a++)b[a].apply(this,arguments)}var m=this.XMLHttpRequest,n=m&&m.prototype;
if(n){var o=n.open;n.open=function(a,b,c,d,r){f();this._tl||(this._tl={a:g++,async:c,b:[]},e.measure(["_ajax",this._tl.a,"init",a,b]));return d?o.call(this,a,b,c,d,r):o.call(this,a,b,c)};var p=n.send;n.send=function(a){function b(){try{var a;a:{var b=l;try{if(c.addEventListener){c.addEventListener("readystatechange",b);a=!0;break a}}catch(t){}a=!1}if(!a){var k=c.onreadystatechange;if(k){if(!k.apply)return;f();d.b.push(k)}f();c.onreadystatechange=l}}catch(u){}}var c=this,d=c&&c._tl;f();b();j(d);a=
p.call(c,a);!d.async||4===c.readyState?i(d):setTimeout(function(){try{4===c.readyState?i(d):c.onreadystatechange!==l&&b()}catch(a){}},0);return a}}this.onerror=function(a,b,c){e.measure(["_jserror ",a,"|",b,"|",c].join(""))};var q=document.createElement("script");q.type="text/javascript";q.async=!0;q.src=("http:"===document.location.protocol?"http:":"https:")+"//d2gfdmu30u15x7.cloudfront.net/tly.js";var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(q,s);}());</script>
'''

def rum_footer():
    """ Return the RUM footer for use in your app's HTML response,
    just before the </body> tag. """
    if not CUSTOMER_RUM_ID or not SwigContext.isValid():
        return ''
    else:
        return r'''<script type="text/javascript">this._tly&&this._tly.measure("domload");</script>
'''
