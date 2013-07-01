'''
Created on Feb 4, 2013

@author: GoldRatio
'''
import os
from .models import Repository
from settings.models import Organization 
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
from subprocess import Popen, PIPE, STDOUT
import subprocess
from stat import S_ISDIR
from lib.vcs.backends.git import GitRepository
from lib.vcs.backends.base import EmptyChangeset
from lib import diffs
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from lib.helpers import CodeHtmlFormatter 

from sqlalchemy.orm import aliased

Organizationalias = aliased(Organization)

class RepositoryForm(Form):
    name = TextField('name')
    description = TextField('description')
    public = IntField('public')
    ownType = IntField('ownType')
    teamId = TextField('teamId')


class RepositoryHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        currentUser = self.current_user
        repositories = Repository.query.join(Repository.users).filter(User.id==currentUser.id, Repository.public==0, Repository.ownType==0).all()
        team_repositories = Repository.query.join(Organization.users, Organizationalias ).filter(Repository.public==0, Repository.ownType==1, 
                User.id==currentUser.id).all()
        repositories += team_repositories 
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
                own_id=currentUser.id, createTime= now, public= form.public.data, users= users,
                ownType=form.ownType.data, organizationId =form.teamId.data)
        db.session.add(repository)

        db.session.commit()
        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath, currentUser.url, form.name.data)
        GitRepository(filePath, create= True, bare= True)
        self.writeSuccessResult(repository, successUrl='/%s/%s'%(currentUser.url, repository.name))

class RepositoryNewHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        currentUser = self.current_user
        user = User.query.filter_by(id= currentUser.id).first()

        self.render("repository/newRepository.html", organizations= user.organizations)

    @tornado.web.authenticated
    def post(self):
        self.redirect("/")

class RepositoryDetailHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        currentUser = self.current_user
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath, currentUser.url, repository.name)
        repo = GitRepository(filePath)
        if repo.revisions:
            lastCommit = repo.get_changeset('HEAD')
            try:
                readmeMarkdown = lastCommit.get_node('README.md')
                readme = markdown.markdown(readmeMarkdown._blob.data.decode("utf-8"))
            except exception:
                readme = ""
            self.render("repository/repositoryDetail.html", repository= repository, userUrl= userUrl, lastCommit= lastCommit, readme= readme)
        else:
            self.render("repository/repositoryEmpty.html", repository= repository, userUrl= userUrl)

    @tornado.web.authenticated
    def post(self):
        self.redirect("/")

class RepositoryFile(object):
    def __init__(self, name, stat, id, path = None):
        self.id = str(id)
        if S_ISDIR(stat):
            self.type = 0
        else:
            self.type = 1
        self.stat = stat
        self.commit = name.decode("utf-8")
        self.name = name.decode("utf-8")
        if path:
            self.path = "%s/%s"%(path, self.name)
        else:
            self.path = self.name

class RepositoryMasterHandler(BaseHandler):
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
        repo = GitRepository(filePath)
        head = repo.get_changeset('HEAD')
        nodes = head.get_nodes('/')
        self.writeSuccessResult(nodes)


class RepositoryCommandHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repocurrentUser.urlsitoryPath, userUrl, repositoryName)
        repo = GitRepository(filePath)

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
        repo = GitRepository(filePath)
        head = repo.get_changeset(tag)
        nodes = head.get_nodes(path)
        self.writeSuccessResult(nodes)

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
        repo = GitRepository(filePath)
        head = repo.get_changeset(tag)
        node = head.get_node(path)
        
        lexer = get_lexer_by_name(node.lexer_alias, stripall=True)
        formatter = CodeHtmlFormatter(linenos=True, cssclass="file-code file-diff")
        code = highlight(node._blob.data.decode("utf-8"), lexer, formatter)
        self.writeSuccessResult(node, highlight = code)

class RepositoryCommitsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName, tag):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        currentUser = self.current_user
        self.render("repository/repositoryCommits.html", repository= repository, userUrl= userUrl)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName, tag):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        collection = repo.get_changesets(start=0, branch_name=tag, reverse= True)
        page_revisions = [repo[x.raw_id] for x in collection]
        self.writeSuccessResult(page_revisions)

class RepositoryCommitHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName, raw_id):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)
        currentUser = self.current_user

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        changeset = repo.get_changeset(raw_id)
        cs2 = changeset.raw_id
        cs1 = changeset.parents[0].raw_id if changeset.parents else EmptyChangeset()

        diff = repo.get_diff(cs1, cs2)
        diff_processor = diffs.DiffProcessor(diff, vcs= repo.alias, format='gitdiff')
        
        _parsed = diff_processor.prepare()
        diff_lines = diff_processor.parsed_diff
                    
        self.render("repository/repositoryCommit.html", repository= repository, userUrl= userUrl, raw_id=raw_id, diff_lines= diff_lines)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName, tag):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        collection = repo.get_changesets(start=0, branch_name=tag)
        page_revisions = [repo[x.raw_id] for x in collection]
        self.writeSuccessResult(page_revisions)

class RepositoryBranchesHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userUrl, repositoryName):
        self.post(userUrl, repositoryName)

    @tornado.web.authenticated
    def post(self, userUrl, repositoryName):
        repository = Repository.query.join(Repository.users).filter(Repository.name==repositoryName, User.url==userUrl).first()
        if not repository:
            raise HTTPError(404)

        repositoryPath = options.repositoryPath 
        filePath = '%s/%s/%s'%(repositoryPath , userUrl, repositoryName)
        repo = GitRepository(filePath)
        branches = repo.branches
        brancheArray = [(branch, repo[branch]) for branch in branches]
        self.render("repository/repositoryBranches.html", repository= repository, userUrl= userUrl, branches = brancheArray ) 

handlers = [
    ('/', RepositoryHandler),
    ('/new', RepositoryNewHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)', RepositoryDetailHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/tree-commit/([a-z\/A-Z]+)', RepositoryMasterHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)\.git', RepositoryCommandHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)\.git/info/refs', RepositoryInfoHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)\.git/git-upload-pack', RepositoryInfoHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)\.git/git-receive-pack', RepositoryReceiveHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/tree/([a-zA-Z]+)/([\/a-zA-Z0-9]+)', RepositoryTreeHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/blob/([a-zA-Z]+)/([\/\.a-zA-Z0-9]+)', RepositoryBlobHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/commits/([a-zA-Z]+)', RepositoryCommitsHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/commit/([a-zA-Z0-9]+)', RepositoryCommitHandler),
    ('/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/branches', RepositoryBranchesHandler),
]
