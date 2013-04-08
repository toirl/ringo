import logging
from pyramid.view import view_config

from pyramid.security import (
    Allow,
)

from ringo.views.base import list_, create_, update_, read_, delete_
from ringo.model.user import Role

log = logging.getLogger(__name__)


class RessourceFactory(object):

    def __init__(self, request):
        self.__acl__ = [(Allow, 'role:admin', ('create', 'read', 'update',
                                'delete', 'list'))]


@view_config(route_name=Role.get_action_routename('list'),
             renderer='/default/list.mako',
             permission='list')
def list(request):
    return list_(Role, request)


@view_config(route_name=Role.get_action_routename('create'),
             renderer='/default/create.mako',
             permission='create')
def create(request):
    return create_(Role, request)


@view_config(route_name=Role.get_action_routename('update'),
             renderer='/default/update.mako',
             permission='update')
def update(request):
    return update_(Role, request)


@view_config(route_name=Role.get_action_routename('read'),
             renderer='/default/read.mako',
             permission='read')
def read(request):
    return read_(Role, request)


@view_config(route_name=Role.get_action_routename('delete'),
             renderer='/default/confirm.mako',
             permission='delete')
def delete(request):
    return delete_(Role, request)
