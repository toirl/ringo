<%inherit file="/main.mako" />
<div class="page-header">
<h1>${app_title}  ${app_version}</h1>
</div>
<h2>${_('License')}</h2>
<p>
${_('This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.')}
</p>
<h2>${_('Core Components')}</h2>
<h3><img src="${request.static_path('ringo:static/images/ringo-logo-64.png')}" alt="Ringo logo"/>Ringo ${ringo_version}</h3>
<p>${h.literal(_('<a href="https://github.com/ringo-framework/ringo" target="_blank">Ringo</a> is a small Python based high level web application framework build with Pyramid . It provides basic functionality which is often used in modern web applications'))}</p>
<h3>Formbar ${formbar_version}</h3>
<p>${h.literal(_('<a href="https://github.com/ringo-framework/formbar" target="_blank">Formbar</a> is a Python library to layout, render and validate HTML forms in web applications.'))} </p>
<h3><img src="${request.static_path('ringo:static/images/sqla-logo.gif')}" alt="SQLAlchemy logo"/>SQLAlchemy ${sqlalchemy_version}</h3>
<p>${h.literal(_('<a href="https://www.sqlalchemy.org" target="_blank">SQLAlchemy</a> is Python based ORM mapper.'))}</p>
<h3><img src="${request.static_path('ringo:static/images/pyramid-logo.jpeg')}" alt="Pyramid logo" width="64"/>&nbsp;Pyramid ${pyramid_version}</h3>
<p>${h.literal(_('<a href="http://www.pylonsproject.org/" target="_blank">Pyramid</a></a> is a Python based web application framework.'))}</p>
