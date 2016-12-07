"""
Modules are the blocks in Ringos building block archticture!
The term 'Modul' decribes the collection of all needed infrastructure to work
and store certain type of data. Where certain type of
data means users, files, movies etc. rather than integers or date values.

The moduls infrastructure consists of

1. *Views* to handle incoming request and generating the proper responses.
2. *Templates* to define the layout of the pages of the module
3. *Model* which defines the data fields of your modul.
4. *Forms* and *Table* confiuration which defines how forms and overview
   pages will be rendered.

Ringo provides some default infrastructure which is used for all modules
as long the modul does not implements it in a custom way. This default
infrastructure is present for *Views* and *Templates*. For those the
default views and templates are used. The views provide default LCRUDIE
:ref:`.ActionItem` for all modules:

* List: Listing all items of the module. This is slightly different to
  the action to read a single item.
* Create: Create new items.
* Read: Show the item in detail in readonly mode.
* Update: Edit items of the module.
* Delete: Deleting items.
* Import (CSV, JSON)
* Export (CSV, JSON)

These actions are defined in the :attr:`.ACTIONS` modul varialble.

Ringo already comes with many predifend moduls. Please refer to
documentation to see which moduls are available.

"""

import logging
import sqlalchemy as sa
from ringo.model import Base
from ringo.model.user import BaseItem
from ringo.lib.helpers import dynamic_import

log = logging.getLogger(__name__)


class ActionItem(BaseItem, Base):
    """A ActionItem is the configuration and representation of the
    :class:`.ModulItem` configured actions in the application. This
    class configures aspected of rendering and which view is called if
    the user selects the action."""
    __tablename__ = 'actions'
    _modul_id = 2
    id = sa.Column(sa.Integer, primary_key=True)
    mid = sa.Column(sa.Integer, sa.ForeignKey('modules.id'))
    """Foreign Key to the modull to which the action belongs to."""
    name = sa.Column(sa.String, nullable=False)
    """Name of the Action. E.g "Create" or "Read". The will be used for
     * rendering the action and
     * internal identification (lowercase version of the name) on
     * permission checks (see :attr:`.permission`).
    """
    url = sa.Column(sa.String, nullable=False)
    """The url which is called for this action if a user calls this
    actions. Used for rendering links in the application and while
    initialising the moduls on application start to setup the views."""
    icon = sa.Column(sa.String, nullable=False, default='')
    """A string which configures which icons should be used when
    rendering the action in the UI. The string will be usually rendered
    as class attribute of a bootstrap <i> element. Known predefined values are:

     * List: icon-list-alt
     * Add: icon-plus
     * Read: icon-eye-open
     * Edit: icon-edit
     * Delete: icon-eye-delete, icon-trash
     * Download: icon-download
     * Export: icon-export
     * Import: icon-import
     """
    description = sa.Column(sa.Text, nullable=False, default='')
    """Short description what the action does. Should be obvious by the
    name of the action anyway."""
    bundle = sa.Column(sa.Boolean, nullable=False, default=False)
    """Flag to indicate if the action should be available in the bundled
    actions"""
    display = sa.Column(sa.String, nullable=False, default="primary")
    """Optional. Configures a) If the action will be rendered at all and
    b) where to render the action in the context menu.

    The display variable is a comma separated list of values which
    defines the visibility. The following values are valid:

    ============== ===========
    value          description
    ============== ===========
    primary        Action is globally visible and will be rendered in
                   the primary context menu.
    secondary      Action is globally visible and will be rendered in
                   the secondary menu.
    hide           Completly hide the action. This effects both context
                   menu and overview.
    hide-context   Kind of modifier in addition to the `primary` and
                   `secondary` setting. Adding this value will still show
                   the action in the context but hide the action in the
                   overview.
    hide-overview  Kind of modifier in addition to the `primary` and
                   `secondary` setting. Adding this value will still show
                   the action in the overview but hide the action in the
                   context menu.
    ============== ===========

    Examples:

    * "primary,hide-context": Show action in overview only
    * "primary,hide-overview": Show action in context only, render
      action in primary context menu
    * "secondary": Show action globally, render action in secondary menu
      of context menu.
    * "hide": Completly hide the action.

    """
    permission = sa.Column(sa.String, nullable=False, default='')
    """Optional. Configure an alternative permission the user must have
    to be allowed to call this action. Known values are 'list', 'create',
    'read', 'update', 'delete', 'import', 'export'. If empty the
    permission system will use the the lowered name of the action."""

    def is_visible(self, location):
        """Checks based on the setting in the display configuration
        attribute if the action is visible in the given location.
        Location can be be `overview` or `context`.

        :location: String of location to check
        :returns: True or False
        """
        display = self.display.split(",")
        if "hide" in display:
            return False
        if location == "overview" and self.name.lower() == "list":
            return False
        if location == "overview" and self.url.find("{") > -1:
            return False
        if location == "overview" and "hide-overview" in display:
            return False
        if location == "context" and "hide-context" in display:
            return False
        return True

    def get_permission(self):
        if self.permission:
            return self.permission.lower()
        return self.name.lower()


class ModulItem(BaseItem, Base):
    """A ModulItem is the representation and configuration of a
    :mod:`.modul` in the application.

    Each module has a common set of configuration options which can be
    configured directly in the web interface and are stored in instances
    of :class:`.ModulItem`.  This includes the configuration of

    * visual aspects and how the modul and/or items of the modul will be
      rendered or displayed.
    * model configuration as which :class:`.ActionItem` should be
      available.

    Default usergroup: Write me!
    """

    __tablename__ = 'modules'
    _modul_id = 1
    _sql_eager_loads = ['actions']
    id = sa.Column(sa.Integer, primary_key=True)
    """Internal ID of the modul."""
    name = sa.Column(sa.String, unique=True, nullable=False)
    """Internal name of the modul which is usually autogenrated and must
    not be changed!. The name is crucial for the application as it also
    defines some other namings as the name of configuration files for
    forms or tables."""
    clazzpath = sa.Column(sa.String, unique=True, nullable=False)
    """Path to the moduls model in dot notation"""
    label = sa.Column(sa.String, nullable=False, default='')
    """The label in single form of the modul. Used for display in
    various places of the application."""
    label_plural = sa.Column(sa.String, nullable=False, default='')
    """The label in plural form of the modul. Used for display in
    various places of the application."""
    description = sa.Column(sa.Text, nullable=False, default='')
    """The label in plural form of the modul. Used for display in
    various places of the application."""
    str_repr = sa.Column(sa.String, nullable=False, default='%s|id')
    """Format string which defines how items of the modul will be renderered
    when the __unicode__ or __str__ method is called for the items. This
    is often the case in dropdown lists or overview tables. The string
    is a bar seperated string and defined as '%s-%s|foo, bar'. The left
    side of the configuration defines the "layout" with placeholder (%s)
    and the right part the attributes which will be used to replace the
    placeholders."""
    display = sa.Column(sa.String, nullable=False, default='hidden')
    """Configures where the items will be displayed in the web
    application. Possibile options are:

     * header-menu
     * user-menu
     * admin-menu
     * hidden
    """
    default_gid = sa.Column(sa.Integer, sa.ForeignKey('usergroups.id'))
    """Link to a usergroup which will be set as default useroup for new
    items of the modul if nothing other is defined."""

    default_group = sa.orm.relationship("Usergroup", uselist=False,
                                        foreign_keys=[default_gid])
    actions = sa.orm.relationship("ActionItem",
                                  backref="modul",
                                  lazy="joined",
                                  cascade="all")
    """List of :class:`.ActionItem` which are available for the modul."""

    _sql_eager_loads = ['actions.roles']
    """Preload the actions and associated roles to the action of the
    modul.  Are needed for permission checks. This will reduce the
    number of SQL-queries very much!"""

    @property
    def clazzbases(self):
        """Property which returns the base classes of the model of the
        modul. This is usefull and currently used for filtering in
        forms. e.g filtering modules which are tagable"""
        return [b.__name__ for b in self.get_clazz().__bases__]

    def get_clazz(self):
        """Returns the class defined in the clazzpath attribute.

        :returns: :class:`.BaseItem`
        """
        return dynamic_import(self.clazzpath)

    def get_label(self, plural=False):
        """Returns the label of the modul.

        :plural: If true the plural form is returned.
        :returns: String with label"""
        if plural:
            return self.label_plural
        return self.label

    def has_action(self, name):
        """Will return True if the modul has a ActionItem configured
        with given name. Else false.

        :name: Name of the action 
        :returns: True or False
        """
        for action in self.actions:
            if action.name.lower() == name.lower():
                return True
        return False


    def get_action(self, name):
        """Will return action item if the modul has a ActionItem configured
        with given name. Else None.

        :name: Name of the action
        :returns: ActionItem or None
        """
        for action in self.actions:
            if action.name.lower() == name.lower():
                return action
        return None


    def get_str_repr(self):
        """Return a tupel with format str and a list of fields."""
        # "%s - %s"|field1, field2 -> ("%s - %s", ["field1", "field2"])
        try:
            format_str, fields = self.str_repr.split("|")
            return (format_str, [f.strip() for f in fields.split(",")])
        except:
            return ("%s", ["id"])

_ = lambda msgid: msgid
ACTIONS = {
    "list":   ActionItem(name=_("List"),
                         url="list",
                         icon="icon-list-alt"),
    "create": ActionItem(name=_("Create"),
                         url="create",
                         icon=" icon-plus"),
    "read":   ActionItem(name=_("Read"),
                         url="read/{id}",
                         icon="icon-eye-open"),
    "update": ActionItem(name=_("Update"),
                         url="update/{id}",
                         icon="icon-edit"),
    "delete": ActionItem(name=_("Delete"),
                         url="delete/{id}",
                         icon="icon-trash",
                         bundle=True),
    "import": ActionItem(name=_("Import"),
                         url="import",
                         icon="icon-import"),
    "export": ActionItem(name=_("Export"),
                         url="export/{id}",
                         icon="icon-export",
                         bundle=True)
}
"""Default available actions in Ringo"""
