'''
Created on Feb 4, 2013

@author: GoldRatio
'''
from user.models import User
from .models import Organization
import logging
import tornado
from tornado.options import options
from tornado.web import RequestHandler
from tornado.web import HTTPError
import hashlib
from core.BaseHandler import BaseHandler 
from forms import Form, TextField, ListField, BooleanField
from core.database import db
from core.quemail import QueMail, Email
from core.util import getSequence 
import core.web
from uuid import uuid4
from datetime import datetime
import pinyin

class ProfileHandler(BaseHandler):
    _error_message = "用户已存在"
    def get(self):

        self.render("settings/profile.html")

    def post(self):
        self.redirect("/")

class OrganizationForm(Form):
    name = TextField('name')
    description = TextField('description')

class InviteesForm(Form):
    email = ListField('email')

class OrganizationHandler(BaseHandler):
    _error_message = ""
    def get(self):
        currentUser = self.current_user
        user = User.query.filter_by(id= currentUser.id).first()

        self.render("settings/organizations.html", organizations= user.organizations)

    def post(self):
        form = OrganizationForm(self.request.arguments, locale_code=self.locale.code)
        currentUser = self.current_user
        organization = Organization.query.filter_by(name=form.name.data).first()
        if organization:
            return
        users = []
        user = User.query.filter_by(id= currentUser.id).first()
        users.append(user)
        url = pinyin.get(form.name.data)
        organization = Organization(name = form.name.data, description=form.description.data, own_id= currentUser.id, users = users, url = url)
        db.session.add(organization)
        db.session.commit()
        self.render("settings/organizations.html")


class OrganizationSettingsHandler(BaseHandler):
    _error_message = ""
    def get(self, url):
        currentUser = self.current_user
        organization = Organization.query.filter_by(url = url).first()

        self.render("settings/organization.html", organization = organization )

    def post(self, url):
        form = InviteesForm(self.request.arguments, locale_code=self.locale.code)
        organization = Organization.query.filter_by(url = url).first()
        if not organization:
            return
        users = organization.users
        for userEmail in form.email.data:
            print(userEmail)
            user = User.query.filter_by(email= userEmail).first()
            if user:
                print(userEmail)
                users.append(user)
        organization.users = users
        db.session.add(organization)
        db.session.commit()
        self.get(url)

handlers = [
    ('/settings/profile', ProfileHandler),
    ('/settings/organizations', OrganizationHandler),
    ('/settings/organizations/([a-zA-Z0-9]+)', OrganizationSettingsHandler),
]
