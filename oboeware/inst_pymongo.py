""" Tracelytics instrumentation for pymongo (MongoDB client).

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
import sys

import oboe

try:
    import json
except ImportError:
    import simplejson as json

PYMONGO_LAYER = "pymongo"


### Helper methods for pymongo instrumentation:
def profile_find(func, args, kwargs, func_result):
    """ Oboe callback for pymongo 'find' profiling """
    collection = args[0]
    if (len(args) > 1):
        query = args[1]
    else:
        query = 'all'

    return _profile_query(collection, query, op='find')

def profile_update(func, args, kwargs, func_result):
    """ Oboe callback for pymongo 'update' profiling """
    (collection, query, doc, _upsert, _manipulate, safe, multi) = args[:7]

    report_kvs = _profile_query(collection, query, op='update', safe=safe, result=func_result)
    report_kvs['Update_Document'] = _to_json(doc)

    if multi:
        report_kvs['Multi'] = True

    return report_kvs

def profile_insert(func, args, kwargs, func_result):
    """ Oboe callback for pymongo 'insert' profiling """
    (collection, docs, _manipulate, safe) = args[:4]
    if isinstance(docs, dict):
        docs = [docs]

    # Only first doc is finger printed
    report_kvs = _profile_query(collection, docs[0], op='insert', safe=safe,
                                result=func_result, docs_affected=len(docs))

    return report_kvs

def profile_remove(func, args, kwargs, func_result):
    """ Oboe callback for pymongo 'remove' profiling """
    (collection, spec_or_id, safe) = args[:3]

    if spec_or_id is None:
        spec_or_id = {}

    if not isinstance(spec_or_id, dict):
        spec_or_id = {"_id": spec_or_id}

    return _profile_query(collection, spec_or_id, op='remove', safe=safe, result=func_result)

def profile_drop(func, args, kwargs, func_results):
    """ Oboe callback for pymongo 'drop' profiling """
    return _profile_query(args[0], None)

def profile_index(func, args, kwargs, func_result):
    """ Oboe callback for pymongo create/remove/ensure index profiling """
    collection = args[0]

    report_kvs = _profile_query(collection)

    if len(args) > 1:
        report_kvs['Index'] = _to_json(args[1])

    return report_kvs

def profile_group(func, args, kwargs, func_result):
    """ Oboe callback for pymongo collection group profiling """
    (collection, key, condition, initial, reduce) = args[:5]
    report_kvs = _profile_query(collection)

    if key:
        report_kvs['Group_Key'] = _to_json(key)

    if condition:
        report_kvs['Group_Condition'] = _to_json(condition)

    if initial:
        report_kvs['Group_Initial'] = _to_json(initial)

    if reduce:
        report_kvs['Group_Reduce'] = reduce

    return report_kvs


def profile_distinct(func, args, kwargs, func_result):
    """ Oboe callback for pymongo collection distinct profiling """
    collection = args[0]

    report_kvs = _profile_query(collection)
    report_kvs['Key'] = args[1]

    return report_kvs

def profile_map_reduce(func, args, kwargs, func_result):
    """ Oboe callback for pymongo collection map/reduce """
    (collection, map_fn, reduce_fn)  = args[:3]

    report_kvs = _profile_query(collection)
    report_kvs['Map_Function'] = map_fn
    report_kvs['Reduce_Function'] = reduce_fn

    return report_kvs

def profile_find_and_modify(func, args, kwargs, func_result):
    """ Oboe callback for pymongo collection map/reduce """
    (collection, query, update)  = args[:3]

    report_kvs = _profile_query(collection, query, op='find_and_modify')
    if update is not None:
        report_kvs['Update_Document'] = _to_json(update)

    return report_kvs

def profile_create_collection(func, args, kwargs, func_results):
    """ Oboe callback for pymongo 'create collection' profiling """
    collection = func_results
    if collection is not None:
        return _profile_query(collection)

def profile_rename_collection(func, args, kwargs, func_results):
    """ Oboe callback for pymongo 'rename collection' profiling """
    (collection, new_name) = args[:2]
    report_kvs = _profile_query(collection)
    report_kvs['New_Collection_Name'] = new_name
    return report_kvs

def profile_drop_collection(func, args, kwargs, func_results):
    """ Oboe callback for pymongo 'drop collection' profiling """
    (db, name_or_collection) = args[:2]
    report_kvs = {}

    if isinstance(name_or_collection, basestring):
        collection_name = name_or_collection
    else:
        collection_name = name_or_collection.name

    _add_connection_info(report_kvs, db)
    report_kvs['Collection'] = collection_name

    return report_kvs

def profile_command(func, args, kwargs, func_results):
    """ Oboe callback for pymongo database 'command' profiling """
    (db, command) = args[:2]
    report_kvs = {}

    _add_connection_info(report_kvs, db)
    if not isinstance(command, basestring):
        command = _to_json(command)

    report_kvs['Command'] = command

    return report_kvs

def _profile_query(collection, query=None, op=None, safe=None, result=None, docs_affected=None):
    """ Gathers report key/values from collection and (optional) query """

    report_kvs = {}
    _add_connection_info(report_kvs, collection.database)
    report_kvs['Collection'] = collection.name

    if isinstance(query, dict):
        report_kvs['Query'] = _to_json(query)
        if op:
            if op == 'find' and collection.name == '$cmd':
                report_kvs['QueryFingerprint'] = '%s.command(%s)' % (collection.database.name,
                    _command_fingerprint(query))
            else:
                report_kvs['QueryFingerprint'] = '%s.%s.%s(%s)' % (collection.database.name,
                    collection.name, op, _query_fingerprint(query))

    if op:
        report_kvs['QueryOp'] = op

    if safe is not None:
        report_kvs['SafeMode'] = safe
        # We only get document count if safe mode is true
        if safe and docs_affected is None and result is not None and 'n' in result:
            report_kvs['NumDocumentsAffected'] = result['n']

    if docs_affected is not None: # Used for insert
        report_kvs['NumDocumentsAffected'] = docs_affected

    return report_kvs


def _add_connection_info(report_kvs, db):
    """ Connection info common to every mongodb trace """
    report_kvs['Flavor'] = 'mongodb'
    report_kvs['Database'] = db.name
    report_kvs['RemoteHost'] = db.connection.host
    report_kvs['RemotePort'] = db.connection.port

def _to_json(obj):
    try:
        return json.dumps(obj, cls=JSONEncoder)
    except Exception, e:
        return "{'OboeError': 'Could not dump data to JSON.'}"

def _query_fingerprint(query):
    try:
        return skeleton(dict(query))
    except:
        # For safety, in case skeleton encounters something unexpected we won't fail the query:
        return ""

def _command_fingerprint(query):
    """ Special case for commands: preserve order of arguments, and save
        first argument name/value
    """
    fp = None
    if query and isinstance(query, SON) and len(query) > 0:
        cmd_args = [ {item[0] : item[1]} for item in query.items() ]
        try:
            fp = skeleton(cmd_args, preserve_first=True, no_wrap=True)
        except:
            # For safety, in case skeleton encounters something unexpected we won't fail the query:
            pass

    return fp


### Parameter dicts for method instrumentation:

# For pymongo.collection.Collection:
COLLECTION_METHOD_INST = {
    'save': {},
    'insert': {
        'callback': profile_insert,
        'store_backtrace': True,
    },
    'update': {
        'callback': profile_update,
        'store_backtrace': True,
    },
    'drop': {
        'callback': profile_drop,
        'store_backtrace': True,
    },
    'remove': {
        'callback': profile_remove,
        'store_backtrace': True,
    },
    'find': {
        'callback': profile_find,
        'store_backtrace': True,
    },
    'count': {},
    'create_index': {
        'callback': profile_index,
        'store_backtrace': True,
    },
    'ensure_index': {
        'callback': profile_index,
        'store_backtrace': True,
    },
    'drop_indexes': {
        'callback': profile_index,
    },
    'drop_index': {
        'callback': profile_index,
        'store_backtrace': True,
    },
    'reindex': {
        'callback': profile_index,
        'store_backtrace': True,
    },
    'index_information': {
        'callback': profile_index,
        'store_backtrace': True,
    },
    'options': {
        'store_backtrace': True,
    },
    'group': {
        'callback': profile_group,
        'store_backtrace': True,
    },
    'rename': {
        'callback': profile_rename_collection,
        'store_backtrace': True,
    },
    'distinct': {
        'callback': profile_distinct,
    },
    'map_reduce': {
        'callback': profile_map_reduce,
        'store_backtrace': True,
    },
    'inline_map_reduce': {
        'callback': profile_map_reduce,
        'store_backtrace': True,
    },
    'find_and_modify': {
        'callback': profile_find_and_modify,
        'store_backtrace': True,
    },
}

# For pymongo.database.Database
DATABASE_METHOD_INST = {
    'create_collection': {
        'callback': profile_create_collection,
    },
    'command': {
        'callback': profile_command,
    },
    'drop_collection': {
        'callback': profile_drop_collection,
    },
}

# For pymongo.cursor.Cursor
CURSOR_METHOD_INST = {
    'sort': {},
    'count': {},
    'distinct': {},
}

def wrap_class(cls, class_name, class_method_inst):
    """ wrap class methods with instrumentation calls """
    if not cls:
        return
    for (method, method_log_args) in class_method_inst.iteritems():
        fn = getattr(cls, method, None)
        if not fn:
            # Not all methods may be in all versions of pymongo...
            continue
        kvs = { 'Class': '%s.%s' % (cls.__module__, cls.__name__),
                 'Function': method,
                 'Action': '%s.%s' % (class_name, method),
               }
        # XXX Not Python2.4-friendly
        setattr(cls, method, oboe.log_method(PYMONGO_LAYER, entry_kvs=kvs, **method_log_args)(fn))

def wrap(module):
    """ wrap pymongo module, adding instrumentation to core classes """
    try:
        wrap_class(module.collection.Collection, 'collection', COLLECTION_METHOD_INST)
        wrap_class(module.database.Database, 'database', DATABASE_METHOD_INST)
        wrap_class(module.cursor.Cursor, 'cursor', CURSOR_METHOD_INST)
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

try:
    import pymongo
    from oboeware.json_encoder import JSONEncoder
    from oboeware.skeleton import skeleton
    from bson.son import SON
    wrap(pymongo)
except ImportError, e:
    pass
