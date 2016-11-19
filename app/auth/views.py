# -*- coding: UTF-8 -*-
from flask import render_template, url_for, g, redirect
from flask_login import logout_user, current_user
from datetime import datetime
from importlib import import_module

from .. import db, login_manager
from ..models import User
from . import auth


@auth.route('/login')
def login():
    return render_template('auth/login.html')


@auth.route('/login/<string:authtype>')
def login_authorize(authtype):
    oauth = import_module(authtype, '{}.{}'.format(__package__, authtype))
    return oauth.authorize(callback=url_for('auth.{}_authorized'.format(authtype), _external=True))


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@auth.before_app_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
