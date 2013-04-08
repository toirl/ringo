import os
import pkg_resources
from pyramid.config import Configurator
from pyramid.events import BeforeRender, NewRequest
from pyramid_beaker import session_factory_from_settings

from sqlalchemy import engine_from_config


from ringo.model import (
    DBSession,
    Base,
)
from ringo.lib import (
    helpers,
    security
)
from ringo.lib.i18n import (
    locale_negotiator,
)

base_dir = pkg_resources.get_distribution("ringo").location
template_dir = os.path.join(base_dir, 'ringo', 'templates')


def add_renderer_globals(event):
    request = event['request']
    event['h'] = helpers
    event['s'] = security
    event['_'] = request.translate
    event['N_'] = request.translate
    event['localizer'] = request.localizer


def connect_on_request(event):
    request = event.request
    request.db = DBSession
    request.add_finished_callback(close_db_connection)


def close_db_connection(request):
    request.db.close()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings,
                          locale_negotiator=locale_negotiator)
    config.set_session_factory(session_factory_from_settings(settings))
    config.include('pyramid_handlers')
    config.include('pyramid_beaker')
    config.include('ringo.lib.security.setup_ringo_security')
    config.add_subscriber(connect_on_request, NewRequest)
    config.add_subscriber(add_renderer_globals, BeforeRender)

    config.add_route('home', '/')
    config.add_route('login', 'auth/login')
    config.add_route('logout', 'auth/logout')

    # Roles admininistration
    config.add_route('modules-list', 'modules/list',
                     factory='ringo.views.modules.RessourceFactory')
    config.add_route('modules-create', 'modules/create',
                     factory='ringo.views.modules.RessourceFactory')
    config.add_route('modules-read', 'modules/read/{id}',
                     factory='ringo.views.modules.RessourceFactory')
    config.add_route('modules-update', 'modules/update/{id}',
                     factory='ringo.views.modules.RessourceFactory')
    config.add_route('modules-delete', 'modules/delete/{id}',
                     factory='ringo.views.modules.RessourceFactory')
    # Users admininistration
    config.add_route('users-list', 'users/list',
                     factory='ringo.views.users.RessourceFactory')
    config.add_route('users-create', 'users/create',
                     factory='ringo.views.users.RessourceFactory')
    config.add_route('users-read', 'users/read/{id}',
                     factory='ringo.views.users.RessourceFactory')
    config.add_route('users-update', 'users/update/{id}',
                     factory='ringo.views.users.RessourceFactory')
    config.add_route('users-delete', 'users/delete/{id}',
                     factory='ringo.views.users.RessourceFactory')
    # Usergroups admininistration
    config.add_route('usergroups-list', 'usergroups/list',
                     factory='ringo.views.usergroups.RessourceFactory')
    config.add_route('usergroups-create', 'usergroups/create',
                     factory='ringo.views.usergroups.RessourceFactory')
    config.add_route('usergroups-read', 'usergroups/read/{id}',
                     factory='ringo.views.usergroups.RessourceFactory')
    config.add_route('usergroups-update', 'usergroups/update/{id}',
                     factory='ringo.views.usergroups.RessourceFactory')
    config.add_route('usergroups-delete', 'usergroups/delete/{id}',
                     factory='ringo.views.usergroups.RessourceFactory')
    # Roles admininistration
    config.add_route('roles-list', 'roles/list',
                     factory='ringo.views.roles.RessourceFactory')
    config.add_route('roles-create', 'roles/create',
                     factory='ringo.views.roles.RessourceFactory')
    config.add_route('roles-read', 'roles/read/{id}',
                     factory='ringo.views.roles.RessourceFactory')
    config.add_route('roles-update', 'roles/update/{id}',
                     factory='ringo.views.roles.RessourceFactory')
    config.add_route('roles-delete', 'roles/delete/{id}',
                     factory='ringo.views.roles.RessourceFactory')
    # Profile admininistration
    config.add_route('profiles-list', 'profiles/list')
    config.add_route('profiles-create', 'profiles/create')
    config.add_route('profiles-read', 'profiles/read/{id}')
    config.add_route('profiles-update', 'profiles/update/{id}')
    config.add_route('profiles-delete', 'profiles/delete/{id}')

    config.add_translation_dirs('ringo:locale/')
    config.add_static_view('static',
                           path='ringo:static',
                           cache_max_age=3600)
    config.add_static_view('images',
                           path='ringo:static/images',
                           cache_max_age=3600)
    config.add_static_view('bootstrap',
                           path='ringo:static/bootstrap',
                           cache_max_age=3600)
    config.add_static_view('css',
                           path='ringo:static/css',
                           cache_max_age=3600)
    config.scan()
    return config.make_wsgi_app()
