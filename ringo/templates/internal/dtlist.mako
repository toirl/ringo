<%
from ringo.lib.helpers import prettify
%>
<form id="data-table" name="data-table" role="form" action="${request.route_path(h.get_action_routename(clazz, 'bundle'))}" method="POST">
<table id="data" class="table table-condensed table-striped table-hover datatable-simple">
  <thead>
    <tr>
      % if bundled_actions:
      <th width="2em">
        <input type="checkbox" name="check_all" onclick="checkAll('id');">
      </th>
      % endif
      % for field in tableconfig.get_columns():
      <th width="${field.get('width')}">${_(field.get('label'))}</th>
      % endfor
    </tr>
  </thead>
  <tbody>
    % for item in items[listing.pagination_start:listing.pagination_end]:
      <%
      permission = None
      if s.has_permission("update", item, request):
        permission = "update"
      elif s.has_permission("read", item, request):
        permission = "read"
      %>
    <tr item-id="${item.id}">
      % if bundled_actions:
        <td>
          <input type="checkbox" name="id" value="${item.id}">
        </td>
      % endif
      % for field in tableconfig.get_columns():
        % if permission:
          <td onclick="openItem('${request.route_path(h.get_action_routename(clazz, permission), id=item.id)}')" class="link">
        % else:
          <td>
        % endif
          <%
            try:
              value = prettify(request, item.get_value(field.get('name'), expand=field.get('expand')))
            except AttributeError:
              value = "NaF"
          %>
          ## Escape value here
          % if isinstance(value, list):
            ${", ".join(_(v) for v in value)}
          % else:
            ${_(value)}
          % endif
        </td>
      % endfor 
    </tr>
    % endfor

    % if len(items) == 0:
    <tr>
      % if bundled_actions:
        <td colspan="${len(tableconfig.get_columns())+1}">
      % else:
        <td colspan="${len(tableconfig.get_columns())}">
      % endif
      ${_('No items found')}
      </td>
    </tr>
  % endif
  </tbody>
</table>

<%include file="list_footer.mako"/>
