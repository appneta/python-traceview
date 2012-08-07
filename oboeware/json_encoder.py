""" Handles JSON conversion for various object types that may be found in queries

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
try:
    import json
except ImportError:
    import simplejson as json

import datetime
from bson.objectid import ObjectId
from bson.dbref import DBRef

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId) or isinstance(obj, DBRef):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            try:
                return json.JSONEncoder.default(self, obj)
            except:
                # so we don't fail the request:
                return "[unsupported type %s]" % (type(obj))
