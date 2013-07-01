'''
Created on Feb 4, 2013

@author: GoldRatio
'''
from core.database import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy


__all__ = ['Organization'] 

organization_user_rel= Table('organization_user_rel', db.Model.metadata,
    Column('organization_id', Integer, ForeignKey('organization.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

class Organization(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(180))
    description = Column(String(300))
    own_id = Column(Integer, ForeignKey('user.id'))    
    url = Column(String(30))
    createTime = Column(DateTime)

    users = relationship("User", secondary=organization_user_rel, backref="organizations")
