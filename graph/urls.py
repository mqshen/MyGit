'''
Created on Feb 4, 2013

@author: GoldRatio
'''
import os
from repository.models import Repository
from user.models import User
import logging
import tornado
from tornado.options import options
from tornado.web import HTTPError
from core.BaseHandler import BaseHandler
import core.web 
from forms import Form, TextField, ListField, IntField, BooleanField
from datetime import datetime
from core.database import db
from lib.vcs.backends.git import GitRepository
from lib.vcs.backends.base import EmptyChangeset
from lib import diffs
from itertools import groupby

class GraphHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        currentUser = self.current_user
        self.render("graph/graphIndex.html", repository= repository, userUrl= userUrl)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        collection = repo.get_changesets(start=0, branch_name=tag, reverse= True)
        page_revisions = [repo[x.raw_id] for x in collection]
        self.writeSuccessResult(page_revisions)

class ContributorsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        currentUser = self.current_user
        self.render("graph/contributors.html", repository= repository, userUrl= userUrl)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        collection = repo.get_changesets(start=0, branch_name=tag, reverse= True)
        page_revisions = [repo[x.raw_id] for x in collection]
        self.writeSuccessResult(page_revisions)

class ContributeDataHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        currentUser = self.current_user

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        collection = repo.get_changesets(start=0, branch_name='master', reverse= True)
        def keyfunc(data):
            return data.date.date().strftime("%Y-%m-%d")
        '''
        contribute = {k:list(v) for k,v in groupby(collection, keyfunc)}
        for changeset in contribute:
            print(len(contribute[changeset]))'''
        commitDateList = [{"date": k, "value":len(list(v))} for k,v in groupby(collection, keyfunc)]
            
        self.writeSuccessResult(commitDateList)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        collection = repo.get_changesets(start=0, branch_name=tag, reverse= True)
        page_revisions = [repo[x.raw_id] for x in collection]
        self.writeSuccessResult(page_revisions)
handlers = [
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/graphs', GraphHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/contributors', ContributorsHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/contributeData', ContributeDataHandler),
]
