'''
Created on Feb 4, 2013

@author: GoldRatio
'''
from core.database import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship


__all__ = ['Repository'] 

repository_user_rel= Table('repository_user_rel', db.Model.metadata,
    Column('repository_id', Integer, ForeignKey('repository.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

class Repository(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(180))
    description = Column(String(300))
    own_id = Column(Integer, ForeignKey('user.id'))    
    public = Column(Integer, default=0)
    createTime = Column(DateTime)

    users = relationship("User", secondary=repository_user_rel, backref="repositorys")
