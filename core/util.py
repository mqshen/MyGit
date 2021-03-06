'''
Created on May 2, 2013

@author: GoldRatio
'''
from sqlalchemy.orm import class_mapper
from tornado.options import options
from lib.vcs.backends.base import BaseChangeset
from core.database import db

def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    if isinstance(model, db.Model):
        columns = [c.key for c in class_mapper(model.__class__).columns]
        result = dict((c, getattr(model, c)) for c in columns if c not in options.jsonFilter)
        if hasattr(model, 'eagerRelation'):
            for key in model.eagerRelation:
                value = getattr(model, key)
                if isinstance(value, list):
                    result.update({key: [serialize(item) for item in value]})
                else:
                    result.update({key: serialize(value)})
            columns.extend(model.eagerRelation)
    elif hasattr(model, '__json__'):
        return model.__json__()
    elif isinstance(model, dict):
        return model
    else:
        columns = [c for c in model.__dict__]
        result = {}
        for c in columns:
            value = getattr(model, c)
            if hasattr(value, '__json__'):
                result.update({c: value.__json__()})
            else:
                result.update({c: value})
        #result = json.dumps(model, default=lambda o: o.__dict__)
    # then we return their values in a dict
    
    return result

def getSequence(name):
    """get sequecne for mysql """
    db.session.execute("UPDATE counter SET value = LAST_INSERT_ID(value+1) WHERE name = :name", {"name": name})
    result = db.session.execute("SELECT LAST_INSERT_ID()").first()
    db.session.commit()
    return result[0]
