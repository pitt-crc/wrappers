{% if not obj.display %}
:orphan:

{% endif %}
{{ obj.name }}
=========={{ "=" * obj.name|length }}

{% if obj.docstring %}
.. autoapi-nested-parse::

   {{ obj.docstring|indent(3) }}

{% endif %}

{% block content %}

{% if obj.all is not none %}
{% set visible_children = obj.children|selectattr("short_name", "in", obj.all)|list %}
{% else %}
{% set visible_children = obj.children|selectattr("display")|rejectattr("imported")|list %}
{% endif %}

{% if visible_children %}
Module Contents
---------------

{% for obj_item in visible_children %}
{{ obj_item.render()|indent(0) }}
{% endfor %}

{% endif %}
{% endblock %}
