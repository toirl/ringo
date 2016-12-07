<%
from ringo.lib.helpers import prettify
%>
<script>
  ${dtconfig | n}
</script>
<form class="form-inline" id="data-table" name="data-table" role="form" action="${request.route_path(h.get_action_routename(clazz, 'bundle'))}" method="POST">
<table id="${tableid}" class="table table-condensed table-striped table-hover">
  <thead>
    <tr>
      % if bundled_actions and len(items) > 0:
        <th width="2em" class="checkboxrow">
        <input type="checkbox" name="check_all" onclick="checkAll('id');">
      </th>
      % endif
      % for field in tableconfig.get_columns(request.user):
        <th
        % if not field.get('visible', True):
          style="display: none;"
        % endif
        width="${field.get('width')}" title="${field.get('title') or _(field.get('label'))}">${_(field.get('label'))}</th>
      % endfor
    </tr>
  </thead>
  <tbody>
    % for item in items[listing.pagination_start:listing.pagination_end]:
      <%
      permission = None
      data_link = "#"
      if s.has_permission("update", item, request):
        permission = "update"
        data_link = request.route_path(h.get_action_routename(clazz, permission), id=item.id)
      elif s.has_permission("read", item, request):
        permission = "read"
        data_link = request.route_path(h.get_action_routename(clazz, permission), id=item.id)
      %>
      <tr item-id="${item.id}" data-link="${data_link}">
      % if bundled_actions:
        <td>
          <input type="checkbox" name="id" value="${item.id}">
        </td>
      % endif
      % for field in tableconfig.get_columns(request.user):
        <td 
        % if permission:
          class="link"
        % endif
        % if not field.get('visible', True):
          style="display: none;"
        % endif
        >
          <%
            try:
              colrenderer = tableconfig.get_renderer(field)
              if colrenderer:
                value = colrenderer(request, item, field, tableconfig)
              else:
                value = prettify(request, item.get_value(field.get('name'), expand=field.get('expand')))
                if field.get('expand'):
                  ## In contrast to "freeform" fields expanded values coming from a
                  ## selection usually needs to be translated as they are
                  ## stored as static text in aspecific language in the
                  ## form config.
                  value = _(value)
            except AttributeError:
              value = "NaF"
          %>
          ${value}
        </td>
      % endfor
    </tr>
    % endfor
  </tbody>
</table>

<%include file="list_footer.mako"/>
