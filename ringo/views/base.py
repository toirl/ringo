import uuid
import logging
import transaction
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config

from formbar.form import Form

from ringo.model.base import BaseList, BaseFactory
from ringo.model.user import User
from ringo.lib.renderer import ListRenderer, ConfirmDialogRenderer,\
DropdownFieldRenderer, ListingFieldRenderer
from ringo.lib.sql import invalidate_cache
from ringo.views import handle_history

log = logging.getLogger(__name__)


def _load_item(clazz, request):
    """Will load an item from the given clazz. The id of the item to
    load is taken from the request matchdict. If no item can be found an
    Exception is raised.

    :clazz: Class of the item to load
    :request: Current request having the id in the matchdict
    :returns: Loaded item

    """
    id = request.matchdict.get('id')
    factory = clazz.get_item_factory()
    item = factory.load(id, request.db)
    return item


def get_current_form_page(clazz, request):
    """Returns the id of the currently selected page. The currently
    selected page is saved in the session. If there is no saved value
    then the the first page is returned

    :clazz: The clazz for which the form is displayed
    :request: Current request
    :returns: id of the currently selected page. Default: 1
    """
    itemid = request.matchdict.get('id')
    item = clazz.__tablename__
    page = request.session.get('%s.%s.form.page' % (item, itemid))
    if page:
        return int(page)
    else:
        return 1


@view_config(route_name='set_current_form_page')
def set_current_form_page(request):
    """Will save the currently selected page of a form in the session.
    The request will have some attributes in the GET request which will
    config which page, of which item is currently shown. This function
    is used as a callback function within formbar.

    :request: Current request
    :returns: Response
    """
    page = request.GET.get('page')
    item = request.GET.get('item')
    itemid = request.GET.get('itemid')
    if page and item and itemid:
        #request.session['%s.form.page' % key] = page_id
        request.session['%s.%s.form.page' % (item, itemid)] = page
        request.session.save()
    return Response(body='OK', content_type='text/plain')


def handle_sorting(clazz, request):
    """Return a tuple of *fieldname* and *sortorder* (asc, desc). The
    sorting is determined in the follwoing order: First try to get the
    sorting from the current request (GET-Param). If there are no
    sorting params try to get the params saved in the session or if
    requested from a saved search. As last
    fallback use the default sorting for the table.
    """
    name = clazz.__tablename__

    # Default sorting options
    default_field = clazz.get_table_config().get_default_sort_column()
    default_order = 'asc'

    # Get sorting from the session. If there is no saved sorting use the
    # default value.
    field = request.session.get('%s.list.sort_field' % name, default_field)
    order = request.session.get('%s.list.sort_order' % name, default_order)

    # Get saved sorting from the the saved search.
    saved_search_id = request.params.get('saved')
    if saved_search_id:
        searches_dic = request.user.settings.get('searches', {})
        if searches_dic:
            search = searches_dic.get(name)
            if search:
                field, order = search.get(saved_search_id, [[], [], None])[1]

    # Get sorting from the request. If there is no sorting option in
    # the request then use the saved sorting options.
    field = request.GET.get('sort_field', field)
    order = request.GET.get('sort_order', order)

    # Save current sorting in the session
    if request.params.has_key('reset'):
        request.session['%s.list.sort_field' % name] = default_field
        request.session['%s.list.sort_order' % name] = default_order
    else:
        request.session['%s.list.sort_field' % name] = field
        request.session['%s.list.sort_order' % name] = order
    request.session.save()

    return field, order


def get_search(clazz, request):
    """Returns a list of tuples with the search word and the fieldname.
    The function will first look if there is already a saved search in
    the session for the overview of the given clazz. If there is no
    previous search the start with an empty search stack.  The following
    behavior differs depending if it is a POST or GET request:

    1. GET
    Return either an empty search stack or return the saved stack in the
    session.

    2. POST
    Get the new submitted search. If the search is not already on the
    stack, then push it.  If the search word is empty, then pop the last
    search from the stack.  Finally return the modified stack.

    Please note the this function will not save the modified search
    stack in the session! This should be done elsewhere. E.g Depending
    if the search was successfull.
    """
    name = clazz.__tablename__
    # Check if there is already a saved search in the session
    saved_search = request.session.get('%s.list.search' % name, [])

    if request.params.has_key('reset'):
        return []

    # If the request is not a equest from the search form then
    # abort here and return the saved search params if there are any.
    form_name = request.params.get('form')
    if form_name != "search":
        return saved_search

    saved_search_id = request.params.get('saved')
    if saved_search_id:
        searches_dic = request.user.settings.get('searches', {})
        if searches_dic:
            searches_dic_search = searches_dic.get(name)
            if searches_dic_search:
                return searches_dic_search.get(saved_search_id, [[], [], None])[0]
    elif request.params.has_key('save'):
        return saved_search
    elif request.params.has_key('delete'):
        return saved_search
    else:
        search = request.params.get('search')
        search_field = request.params.get('field')

    # If search is empty try to pop the last filter in the saved search
    if search == "" and len(saved_search) > 0:
        popped = saved_search.pop()
        log.debug('Popping %s from search stack' % repr(popped))

    # Iterate over the saved search. If the search is not already in the
    # stack push it.
    if search != "":
        found = False
        for x in saved_search:
            if search == x[0] and search_field == x[1]:
                found = True
                break
        if not found:
            log.debug('Adding search for "%s" in field "%s"' % (search, search_field))
            saved_search.append((search, search_field))
    return saved_search


def list_(clazz, request):
    # Important! Prevent any write access on the database for this
    # request. This is needed as transform would modify the items values
    # else.
    # TODO: Fix transform call to not modify the items in the
    # list.(None) <2013-08-12 21:26> 
    transaction.doom()
    handle_history(request)
    rvalue = {}
    search = get_search(clazz, request)
    sorting = handle_sorting(clazz, request)
    listing = BaseList(clazz, request.db)
    listing.transform()
    listing.sort(sorting[0], sorting[1])
    listing.filter(search)
    # Only save the search if there are items
    if len(listing.items) > 0:
        request.session['%s.list.search' % clazz.__tablename__] = search
        if (request.params.get('form') == "search"):
            if request.params.has_key('save'):
                query_name = request.params.get('save')
                user = BaseFactory(User).load(request.user.id)
                searches_dic = user.settings.get('searches', {})
                searches_dic_search = searches_dic.get(clazz.__tablename__, {})

                # Check if there is already a search saved with the name
                found = False
                for xxx in searches_dic_search.values():
                    if xxx[1] == query_name:
                        found = True
                        break
                if not found:
                    searches_dic_search[str(uuid.uuid1())] = (search, sorting, query_name)
                searches_dic[clazz.__tablename__] = searches_dic_search
                user.settings.set('searches', searches_dic)
                request.db.flush()
            elif request.params.has_key('delete'):
                query_key = request.params.get('delete')
                user = BaseFactory(User).load(request.user.id)
                searches_dic = user.settings.get('searches', {})
                searches_dic_search = searches_dic.get(clazz.__tablename__, {})
                try:
                    del searches_dic_search[query_key]
                except:
                    pass
                searches_dic[clazz.__tablename__] = searches_dic_search
                user.settings.set('searches', searches_dic)
                request.db.flush()
        request.session.save()


    renderer = ListRenderer(listing)
    rendered_page = renderer.render(request)
    rvalue['clazz'] = clazz
    rvalue['listing'] = rendered_page
    return rvalue


def create_(clazz, request, callback=None, renderers={}):
    """Base view to create a new item of type clazz. This view will
    render a create form to create new items. It the user submits the
    data (POST) that the data will be validated and the new item will be
    saved to the database. Finally after saving on the POST-request the
    optional callback will be called.

    :clazz: Class of items which will be created.
    :request: The current request
    :callback: A callback function [function(request, item)] which
    returns the item again.
    :renderers: A optional dictionary of custom renderers which are
    provided to the form to render specific formelements.
    :returns: Dictionary with the following keys 'clazz', 'item', 'form'
    """
    handle_history(request)
    _ = request.translate
    rvalue = {}
    # Add ringo specific renderers
    if not "dropdown" in renderers:
        renderers["dropdown"] = DropdownFieldRenderer
    if not "listing" in renderers:
        renderers["listing"] = ListingFieldRenderer
    factory = clazz.get_item_factory()
    item = factory.create(request.user)
    form = Form(item.get_form_config('create'), item, request.db, translate=_,
                renderers=renderers,
                change_page_callback={'url': 'set_current_form_page',
                                      'item': clazz.__tablename__,
                                      'itemid': None})
    if request.POST:
        item_label = clazz.get_item_modul().get_label()
        mapping = {'item_type': item_label}
        if form.validate(request.params):
            sitem = form.save()
            msg = _('Created new ${item_type} successfull.',
                    mapping=mapping)
            log.info(msg)
            request.session.flash(msg, 'success')
            # flush the session to make the new id in the element
            # presistent.
            request.db.flush()
            route_name = sitem.get_action_routename('update')
            url = request.route_url(route_name, id=sitem.id)
            if callback:
                sitem = callback(request, sitem)
            # Invalidate cache
            invalidate_cache()
            # Redirect to the update view.
            return HTTPFound(location=url)
        else:
            msg = _('Error on validation the data'
                    ' for new ${item_type}', mapping=mapping)
            request.session.flash(msg, 'error')
    rvalue['clazz'] = clazz
    rvalue['item'] = item
    rvalue['form'] = form.render(page=get_current_form_page(clazz, request))
    return rvalue


def update_(clazz, request, callback=None, renderers={}):
    handle_history(request)
    _ = request.translate
    rvalue = {}
    # Add ringo specific renderers
    if not "dropdown" in renderers:
        renderers["dropdown"] = DropdownFieldRenderer
    if not "listing" in renderers:
        renderers["listing"] = ListingFieldRenderer
    id = request.matchdict.get('id')
    factory = clazz.get_item_factory()
    item = factory.load(id, request.db)
    form = Form(item.get_form_config('update'), item, request.db, translate=_,
                renderers=renderers,
                change_page_callback={'url': 'set_current_form_page',
                                      'item': clazz.__tablename__,
                                      'itemid': id})
    if request.POST:
        item_label = clazz.get_item_modul().get_label()
        mapping = {'item_type': item_label, 'item': item}
        if form.validate(request.params):
            form.save()
            msg = _('Edited ${item_type} "${item}" successfull.',
                    mapping=mapping)
            log.info(msg)
            request.session.flash(msg, 'success')
            route_name = item.get_action_routename('update')
            url = request.route_url(route_name, id=item.id)
            if callback:
                item = callback(request, item)
            # Invalidate cache
            invalidate_cache()
            # Redirect to the update view.
            return HTTPFound(location=url)
        else:
            msg = _('Error on validation the data for '
                    '${item_type} "${item}".', mapping=mapping)
            log.info(msg)
            request.session.flash(msg, 'error')

    rvalue['clazz'] = clazz
    rvalue['item'] = item
    rvalue['form'] = form.render(page=get_current_form_page(clazz, request))
    return rvalue


def read_(clazz, request, renderers={}):
    handle_history(request)
    _ = request.translate
    rvalue = {}
    # Add ringo specific renderers
    if not "dropdown" in renderers:
        renderers["dropdown"] = DropdownFieldRenderer
    if not "listing" in renderers:
        renderers["listing"] = ListingFieldRenderer
    id = request.matchdict.get('id')
    factory = clazz.get_item_factory()
    item = factory.load(id, request.db)
    form = Form(item.get_form_config('read'), item, request.db, translate=_,
                renderers=renderers,
                change_page_callback={'url': 'set_current_form_page',
                                      'item': clazz.__tablename__,
                                      'itemid': id})
    rvalue['clazz'] = clazz
    rvalue['item'] = item
    rvalue['form'] = form.render(page=get_current_form_page(clazz, request))
    return rvalue


def delete_(clazz, request):
    handle_history(request)
    _ = request.translate
    rvalue = {}
    id = request.matchdict.get('id')
    factory = clazz.get_item_factory()
    item = factory.load(id, request.db)
    if request.method == 'POST' and confirmed(request):
        request.db.delete(item)
        route_name = clazz.get_action_routename('list')
        url = request.route_url(route_name)
        item_label = clazz.get_item_modul().get_label()
        mapping = {'item_type': item_label, 'item': item}
        msg = _('Deleted ${item_type} "${item}" successfull.', mapping=mapping)
        log.info(msg)
        request.session.flash(msg, 'success')
        # Invalidate cache
        invalidate_cache()
        return HTTPFound(location=url)
    else:
        # FIXME: Get the ActionItem here and provide this in the Dialog to get
        # the translation working (torsten) <2013-07-10 09:32> 
        renderer = ConfirmDialogRenderer(request, item, 'delete')
        rvalue['dialog'] = renderer.render()
        rvalue['clazz'] = clazz
        rvalue['item'] = item
        return rvalue


def confirmed(request):
    """Returns True id the request is confirmed"""
    return request.params.get('confirmed') == "1"
