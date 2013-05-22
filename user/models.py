'''
Created on Feb 4, 2013

@author: GoldRatio
'''
from core.database import db
from repository.models import Repository
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy

__all__ = ['User', 'UserObj']

'''
team_user_rel = Table('team_user_rel', db.Model.metadata,
    Column('team_id', Integer, ForeignKey('team.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)
'''

class User(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    url = Column(String(30))
    nickName = Column(String(30))
    email = Column(String(60), index=True)
    password = Column(String(60))
    description = Column(String(100))
    avatar = Column(String(60))


    ownedRepositories = relationship("Repository", backref="own")

class UserObj(object):
    def __init__(self, user, teamId = None):
        self.id = user.id
        self.name = user.name
        self.nickName = user.nickName
        self.email = user.email
        self.description = user.description
        self.avatar = user.avatar
        self.url = user.url
