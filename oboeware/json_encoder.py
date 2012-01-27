"""
Handles JSON conversion for various object types that may be found in queries
"""
try:
    import json
except ImportError:
    import simplejson as json

import datetime
from bson.objectid import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)
