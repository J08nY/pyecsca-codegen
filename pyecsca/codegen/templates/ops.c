{%- for alloc in allocations %}
	bn_t {{ alloc }}; bn_init(&{{ alloc }});
{%- endfor %}

{%- for init, value in initializations.items() %}
	bn_from_int({{ value }}, &{{ init }});
{%- endfor %}

{%- for op, result, left, right in operations %}
	{{ render_op(op, result, left, right, "curve->p")}}
{%- endfor %}

{%- for free in frees %}
	bn_clear(&{{ free }});
{%- endfor %}