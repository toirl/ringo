"""Modul with various methods to format and transform values"""
from datetime import (
    datetime,
    date,
    timedelta
)
from dateutil import tz
from babel.core import Locale
from babel.dates import (
    format_datetime as babel_format_datetime,
    format_date as babel_format_date
)
from webhelpers.html import literal
from pyramid.threadlocal import get_current_request
from ringo.lib.i18n import locale_negotiator
from formbar.converters import from_timedelta

########################################################################
#                          Formating content                           #
########################################################################


def prettify(request, value):
    """Generic function used in template rendering to prettify a given
    pythonic value into to a more human readable form. Depending on the
    datatype the function will call a specialised formatting function
    which takes care of localisation etc.

    The locale is determined from the given request.

    :request: Current request
    :value: Pythonic value
    :returns: Prettified (localized) value

    """
    if not request:
        request = get_current_request()
    locale_name = locale_negotiator(request)

    # Special handling for Dummyrequest from testing
    if not isinstance(locale_name, basestring):
        locale_name = None

    if isinstance(value, datetime):
        return format_datetime(get_local_datetime(value),
                               locale_name=locale_name, format="short")
    elif isinstance(value, date):
        return format_date(value,
                           locale_name=locale_name, format="short")
    elif isinstance(value, timedelta):
        return from_timedelta(value)
    elif isinstance(value, list):
        values = []
        is_literal = False
        for v in value:
            r = prettify(request, v)
            if isinstance(r, literal):
                is_literal = True
            values.append(r)
        if is_literal:
            return literal(", ").join(values)
        else:
            return ", ".join(values)
    elif hasattr(value, "render"):
        return value.render()
    elif value is None:
        return ""
    return value

###########################################################################
#                               Times & Dates                             #
###########################################################################


def get_local_datetime(dt, timezone=None):
    """Will return a datetime converted into to given timezone. If the
    given datetime is naiv and does not support timezone information
    then UTC timezone is assumed. If timezone is None, then the local
    timezone of the server will be used.

    :dt: datetime
    :timezone: String timezone (eg. Europe/Berin)
    :returns: datetime

    """
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=tz.gettz('UTC'))
    if not timezone:
        timezone = tz.tzlocal()
    return dt.astimezone(timezone)


def get_week(current_datetime):
    """Returns a tuple definig the start and end datetime for the week of
    the given date. Time from 00:00:00 -> 23:59:59"""
    last_day = 6
    current_day = current_datetime.weekday()
    _ws = current_datetime - timedelta(days=(current_day))
    _we = current_datetime + timedelta(days=(last_day - current_day))
    week_start = _ws.replace(hour=0, minute=0,
                             second=0, microsecond=0)
    week_end = _we.replace(hour=23, minute=59,
                           second=59, microsecond=0)
    return (week_start, week_end)


def format_timedelta(td):
    """Returns a formtted out put of a given timedelta in the form
    00:00:00"""
    if td < timedelta(0):
        return '-' + format_timedelta(-td)
    else:
        hours = td.total_seconds() // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
    return '%02d:%02d:%02d' % (hours, minutes, seconds)


def format_datetime(dt, locale_name=None, format="medium"):
    """Returns a prettyfied version of a datetime. If a locale_name is
    provided the datetime will be localized. Without a locale the
    datetime will be formatted into the form YYYY-MM-DD hh:ss"""
    if locale_name:
        locale = Locale(locale_name)
        return babel_format_datetime(dt, locale=locale, format=format)
    return dt.strftime("%Y-%m-%d %H:%M")


def format_date(dt, locale_name=None, format="medium"):
    """Returns a prettyfied version of a date. If a locale_name is
    provided the date will be localized. Without a locale the
    datetime will be formatted into the form YYYY-MM-DD hh:ss"""
    if locale_name:
        locale = Locale(locale_name)
        return babel_format_date(dt, locale=locale, format=format)
    return dt.strftime("%Y-%m-%d")
