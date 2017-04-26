import os
import logging
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings

from ringo.resources import get_resource_factory
from ringo.lib.i18n import locale_negotiator
from ringo.lib.sql.db import setup_db_session, setup_db_engine
from ringo.model import Base
from ringo.model.user import User, Usergroup

log = logging.getLogger(__name__)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # Setup two db sessions. One using transactions (default) and one
    # without transactions.
    databaseurl = os.environ.get('DATABASE_URL')
    if databaseurl:
        settings['sqlalchemy.url'] = databaseurl
        log.info("Using database url from ENV: %s" % databaseurl)
    engine = setup_db_engine(settings)
    setup_db_session(engine, settings)
    Base.metadata.bind = engine
    config = Configurator(settings=settings,
                          locale_negotiator=locale_negotiator)
    config.set_session_factory(session_factory_from_settings(settings))
    config.include('ringo')
    return config.make_wsgi_app()


def includeme(config):
    log.info('Setup of Ringo...')
    # Configure pyramid modules
    config.include('pyramid_beaker')
    config.include('pyramid_mako')
    config.include('ringo.config.setup')
    config = setup_static_views(config)
    config = setup_routes(config)
    config.scan()
    log.info('OK :) Setup of Ringo finished.')


def setup_static_views(config):
    settings = config.registry.settings
    http_cache = settings.get('security.static_http_cache', '3600')
    config.add_static_view('formbar-static',
                           path='formbar:static',
                           cache_max_age=int(http_cache))
    config.add_static_view('ringo-static',
                           path='ringo:static',
                           cache_max_age=int(http_cache))
    config.add_static_view(name='ringo-customstatic',
                           path=settings.get('app.customstatic', 'ringo:static'),
                           cache_max_age=int(http_cache))
    return config


def setup_routes(config):
    """Function which will setup the routes of the ringo application"""

    # SINGLE PAGES
    ##############
    config.add_route('start_test_case', '_test_case/start')
    config.add_route('stop_test_case', '_test_case/stop')
    config.add_route('login', 'auth/login')
    config.add_route('register_user', 'auth/register_user')
    config.add_route('confirm_user', 'auth/confirm_user/{token}')
    config.add_route('forgot_password', 'auth/forgot_password')
    config.add_route('reset_password', 'auth/reset_password/{token}')
    config.add_route('logout', 'auth/logout')
    config.add_route('autologout', 'auth/autologout')
    config.add_route('accountdisabled', 'auth/disabled')
    config.add_route('version', 'version')
    config.add_route('contact', 'contact')
    config.add_route('about', 'about')
    config.add_route('home', '/')

    # Helpers
    #########
    config.add_route('set_current_form_page', 'set_current_form_page')
    config.add_route('users-changepassword',
                     'users/changepassword/{id}',
                     factory=get_resource_factory(User))
    config.add_route('users-removeaccount',
                     'users/removeaccount/{id}',
                     factory=get_resource_factory(User))
    config.add_route('users-accountremoved',
                     'users/accountremoved')
    config.add_route('usergroups-setstandin',
                     'usergroups/setstandin/{id}',
                     factory=get_resource_factory(Usergroup))
    config.add_route('rules-evaluate', 'rest/rule/evaluate')
    config.add_route('form-render', 'rest/form/render')
    config.add_route('keepalive', 'rest/keepalive')
    return config
