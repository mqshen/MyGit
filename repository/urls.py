'''
Created on Feb 4, 2013

@author: GoldRatio
'''
import os
from .models import Repository
from user.models import User
import logging
import tornado
from tornado.options import options
from tornado.web import HTTPError
from core.BaseHandler import BaseHandler 
from core import subprocessio
import core.web 
from forms import Form, TextField, ListField, IntField, BooleanField
from datetime import datetime
from core.database import db
import pygit2
import json
import pinyin
from subprocess import Popen, PIPE, STDOUT
import subprocess


class RepositoryForm(Form):
    name = TextField('name')
    description = TextField('description')
    public = BooleanField('public')

class RepositoryHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        currentUser = self.current_user
        repositories = Repository.query.join(Repository.users).filter(User.id==currentUser.id).all()
        self.render("main.html", repositories = repositories )

    def post(self):
        form = RepositoryForm(self.request.arguments, locale_code=self.locale.code)
        currentUser = self.current_user
        repository = Repository.query.join(Repository.users).filter(Repository.name==form.name.data, User.id==currentUser.id).first()
        if repository :
            self.writeFailedResult()
            self.finish()
            return
        users = []
        users.append(User.query.filter_by(id=currentUser.id).first())

        now = datetime.now()
        repository = Repository(name=form.name.data, description=form.description.data, 
                own_id=currentUser.id, createTime= now, public= form.public.data, users= users)
        db.session.add(repository)

        db.session.commit()
        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath, currentUser.url, form.name.data)
        subprocess.call('git init --bare "%s" ' % filePath, shell=True)
        self.writeSuccessResult(repository, successUrl='/%s/%s'%(currentUser.url, repository.name))

class RepositoryNewHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        self.render("repository/newRepository.html")

    @tornado.web.authenticated
    def post(self):
        self.redirect("/")

class RepositoryDetailHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        self.render("repository/repositoryDetail.html", repository= repository, userUrl= userUrl)

    @tornado.web.authenticated
    def post(self):
        self.redirect("/")

class RepositoryFile(object):
    def __init__(self, line, path = None):
        items = line.split()
        self.id = items[0]
        if items[1] == 'tree':
            self.type = 0
        else:
            self.type = 1
        self.commit = items[2]
        name = items[3]
        self.path = name
        if path is not None:
            name = name[len(path)+1:]
        self.name = name

class RepositoryCommitHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName, tag):
        self.post(userUrl, repositoryName, tag)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName, tag):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        proc = Popen('git --git-dir %s ls-tree "%s"' % (filePath, tag) ,
            shell = True,
            stdout=PIPE, 
            stderr=STDOUT, 
            close_fds=True)

        files = []
        while True:
            output = proc.stdout.readline()
            if not output or proc.returncode is not None or len(output) == 0:
                break
            line = output.decode('utf-8').strip()
            files.append(RepositoryFile(line))
        files = sorted(files, key=lambda repository: repository.type)
        self.writeSuccessResult(files)


class RepositoryCommandHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repocurrentUser.urlsitoryPath, userUrl, repositoryName)
        repo = pygit2.Repository(filePath)

        self.render("repository/repositoryDetail.html", repository= repository, userUrl= userUrl)


class RepositoryInfoForm(Form):
    service = TextField('service')

class RepositoryInfoHandler(BaseHandler):
    git_folder_signature = set(['config', 'head', 'info', 'objects', 'refs'])
    commands = ['git-upload-pack', 'git-receive-pack']


    def get(self, userUrl, repositoryName):
        '''
        try:
            out = subprocessio.SubprocessIOChunker(
                r'git %s --stateless-rpc --advertise-refs "%s"' % (git_command[4:], filePath),
                starting_values = [ 
                )
        except EnvironmentError as e:
            raise HTTPError(404)
        '''
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        form = RepositoryInfoForm(self.request.arguments, locale_code=self.locale.code)
        git_command = form.service.data
        if git_command not in self.commands:
            raise HTTPError(404)

        smart_server_advert = '# service=%s' % git_command
        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath, userUrl, repositoryName)
        self.set_header("Content-Type", 'application/x-%s-advertisement' % git_command)  
        self.write(str(hex(len(smart_server_advert)+4)[2:].rjust(4,'0') + smart_server_advert + '0000'))
        proc = Popen('git %s --stateless-rpc --advertise-refs "%s"' % (git_command[4:], filePath) ,
            shell = True,
            stdout=PIPE, 
            stderr=STDOUT, 
            close_fds=True)
        output = proc.stdout.read()
        self.write(output)

    def post(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)
        fileDescription = self.request.body
        repositoryPath = options.repositoryPath 
        git_command = "git-upload-pack"
        smart_server_advert = '# service=%s' % git_command
        filePath = '%s/%s/%s'%(repositoryPath, userUrl, repositoryName)
        self.set_header("Content-Type", 'application/x-%s-result' % git_command)  
        proc = Popen('git %s --stateless-rpc "%s"' % (git_command[4:], filePath) ,
            shell = True,
            stdin=PIPE,
            stdout=PIPE, 
            stderr=STDOUT, 
            close_fds=True)
        proc.stdin.write(fileDescription)
        proc.stdin.close()
        output = proc.stdout.read()
        self.write(output)

class RepositoryReceiveHandler(BaseHandler):
    git_folder_signature = set(['config', 'head', 'info', 'objects', 'refs'])
    commands = ['git-upload-pack', 'git-receive-pack']

    def get(self, userUrl, repositoryName):
        '''
        try:
            out = subprocessio.SubprocessIOChunker(
                r'git %s --stateless-rpc --advertise-refs "%s"' % (git_command[4:], filePath),
                starting_values = [ 
                )
        except EnvironmentError as e:
            raise HTTPError(404)
        '''
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        form = RepositoryInfoForm(self.request.arguments, locale_code=self.locale.code)
        git_command = form.service.data
        if git_command not in self.commands:
            raise HTTPError(404)

        smart_server_advert = '# service=%s' % git_command
        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath, userUrl, repositoryName)
        self.set_header("Content-Type", 'application/x-%s-advertisement' % git_command)  
        self.write(str(hex(len(smart_server_advert)+4)[2:].rjust(4,'0') + smart_server_advert + '0000'))
        proc = Popen('git %s --stateless-rpc --advertise-refs "%s"' % (git_command[4:], filePath) ,
            shell = True,
            stdout=PIPE, 
            stderr=STDOUT, 
            close_fds=True)
        output = proc.stdout.read()
        self.write(output)

    def post(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)
        fileDescription = self.request.body
        repositoryPath = options.repositoryPath 
        git_command = "git-receive-pack"
        smart_server_advert = '# service=%s' % git_command
        filePath = '%s/%s/%s'%(repositoryPath, userUrl, repositoryName)
        self.set_header("Content-Type", 'application/x-%s-result' % git_command)  
        proc = Popen('git %s --stateless-rpc "%s"' % (git_command[4:], filePath) ,
            shell = True,
            stdin=PIPE,
            stdout=PIPE, 
            stderr=STDOUT, 
            close_fds=True)
        proc.stdin.write(fileDescription)
        proc.stdin.close()
        subprocess.call('git --git-dir "%s/.git" update-server-info' % filePath, shell=True)
        output = proc.stdout.read()
        self.write(output)

class RepositoryTreeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName, tag, path):
        self.post(userUrl, repositoryName, tag, path)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName, tag, path):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        proc = Popen('git --git-dir %s ls-tree "%s" %s/' % (filePath, tag, path) ,
            shell = True,
            stdout=PIPE, 
            stderr=STDOUT, 
            close_fds=True)

        files = []
        while True:
            output = proc.stdout.readline()
            if not output or proc.returncode is not None or len(output) == 0:
                break
            line = output.decode('utf-8').strip()
            files.append(RepositoryFile(line, path))
        files = sorted(files, key=lambda repository: repository.type)
        self.writeSuccessResult(files)

class RepositoryBlobHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName, tag, path):
        self.post(userUrl, repositoryName, tag, path)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName, tag, path):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        proc = Popen('git --git-dir %s show "%s:%s" ' % (filePath, tag, path) ,
            shell = True,
            stdout=PIPE, 
            stderr=STDOUT, 
            close_fds=True)

        output = proc.stdout.read()

        self.writeSuccessResult(fileContent=output.decode('utf-8'))

handlers = [
    ('/', RepositoryHandler),
    ('/new', RepositoryNewHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)', RepositoryDetailHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)/tree-commit/([a-z\/A-Z]+)', RepositoryCommitHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)\.git', RepositoryCommandHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)\.git/info/refs', RepositoryInfoHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)\.git/git-upload-pack', RepositoryInfoHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)\.git/git-receive-pack', RepositoryReceiveHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)/tree/([a-zA-Z]+)/([\/a-zA-Z]+)', RepositoryTreeHandler),
    ('/([a-zA-Z]+)/([a-zA-Z]+)/blob/([a-zA-Z]+)/([\/\.a-zA-Z]+)', RepositoryBlobHandler),
]
