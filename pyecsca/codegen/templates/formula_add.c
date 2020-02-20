#include "point.h"
{% import "ops.c" as ops %}

{{ ops.render_static_init(allocations, initializations, formula.shortname) }}

{{ ops.render_static_clear(frees, formula.shortname) }}

void point_add(const point_t *one, const point_t *other, const curve_t *curve, point_t *out_one) {
	{%- if short_circuit %}
		if (point_equals(one, curve->neutral)) {
			point_set(other, out_one);
			return;
		}
		if (point_equals(other, curve->neutral)) {
			point_set(one, out_one);
			return;
		}
	{%- endif %}
	{{ ops.render_ops(operations) }}
	{{ ops.render_returns(returns) }}
}