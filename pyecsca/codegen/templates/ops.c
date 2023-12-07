{% macro render_full_allocs(allocations, err_name="err") -%}
	{%- for alloc in allocations %}
		bn_t {{ alloc }};
	{%- endfor %}
	{{ err_name }} = bn_init_multi(&{{ allocations | join(", &") }}, NULL);
{%- endmacro %}

{% macro render_static_allocs(allocations) -%}
	{%- for alloc in allocations %}
		static bn_t {{ alloc }};
	{%- endfor %}
{%- endmacro %}

{% macro render_init_allocs(allocations, err_name="err") -%}
	{{err_name}} = bn_init_multi(&{{ allocations | join(", &") }}, NULL);
{%- endmacro %}

{% macro render_initializations(initializations) -%}
	{%- for init, (value, encode) in initializations.items() %}
		bn_from_int({{ value }}, &{{ init }});
		{%- if encode %}
		    bn_red_encode(&{{ init }}, &curve->p, &curve->p_red);
		{%- endif %}
	{%- endfor %}
{%- endmacro %}

{% macro render_ops(operations) -%}
	{%- for op, result, left, right in operations %}
		{{ render_op(op, result, left, right, "curve->p", "curve->p_red")}}
	{%- endfor %}
{%- endmacro %}

{% macro render_returns(returns) -%}
	{%- for src, dst in returns.items() %}
		bn_copy(&{{ src }}, &{{ dst }});
	{%- endfor %}
{%- endmacro %}

{% macro render_frees(frees) -%}
	{% if frees %}
		bn_clear_multi(&{{ frees | join(", &") }}, NULL);
	{%- endif %}
{%- endmacro %}

{% macro render_static_init(allocations, name) -%}
	{{ render_static_allocs(allocations) }}

	bool point_{{ name }}_init(void) {
		bn_err err;
		{{ render_init_allocs(allocations, "err") }}
		if (err != BN_OKAY) {
			return false;
		}
		return true;
	}
{%- endmacro %}

{% macro render_static_zero(allocations, name) -%}
	void point_{{ name }}_zero(void) {
		{%- for alloc in allocations -%}
		    bn_from_int(0, &{{alloc}});
		{%- endfor -%}
	}
{%- endmacro %}


{% macro render_static_clear(frees, name) -%}
	void point_{{ name }}_clear(void) {
		{{ render_frees(frees) }}
	}
{%- endmacro %}

{% macro render_all(allocations, initializations, operations, returns, frees, err_name="err") -%}
	bn_err {{err_name}};
	{{ render_full_allocs(allocations, err_name) }}
	{{ render_initializations(initializations) }}
	{{ render_ops(operations) }}
	{{ render_returns(returns) }}
	{{ render_frees(frees) }}
{%- endmacro %}
