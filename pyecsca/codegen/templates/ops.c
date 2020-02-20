{% macro render_full_allocs(allocations) -%}
	{%- for alloc in allocations %}
		bn_t {{ alloc }}; bn_init(&{{ alloc }});
	{%- endfor %}
{%- endmacro %}

{% macro render_static_allocs(allocations) -%}
	{%- for alloc in allocations %}
		static bn_t {{ alloc }};
	{%- endfor %}
{%- endmacro %}

{% macro render_init_allocs(allocations) -%}
	{%- for alloc in allocations %}
		bn_init(&{{ alloc }});
	{%- endfor %}
{%- endmacro %}

{% macro render_initializations(initializations) -%}
	{%- for init, value in initializations.items() %}
		bn_from_int({{ value }}, &{{ init }});
	{%- endfor %}
{%- endmacro %}

{% macro render_ops(operations) -%}
	{%- for op, result, left, right in operations %}
		{{ render_op(op, result, left, right, "curve->p")}}
	{%- endfor %}
{%- endmacro %}

{% macro render_returns(returns) -%}
	{%- for src, dst in returns.items() %}
		bn_copy(&{{ src }}, &{{ dst }});
	{%- endfor %}
{%- endmacro %}

{% macro render_frees(frees) -%}
	{%- for free in frees %}
		bn_clear(&{{ free }});
	{%- endfor %}
{%- endmacro %}

{% macro render_static_init(allocations, initializations, name) -%}
	{{ render_static_allocs(allocations) }}

	void point_{{ name }}_init(void) {
		{{ render_init_allocs(allocations) }}
		{{ render_initializations(initializations) }}
	}
{%- endmacro %}

{% macro render_static_clear(frees, name) -%}
	void point_{{ name }}_clear(void) {
		{{ render_frees(frees) }}
	}
{%- endmacro %}

{% macro render_all(allocations, initializations, operations, returns, frees) -%}
	{{ render_full_allocs(allocations) }}
	{{ render_initializations(initializations) }}
	{{ render_ops(operations) }}
	{{ render_returns(returns) }}
	{{ render_frees(frees) }}
{%- endmacro %}
