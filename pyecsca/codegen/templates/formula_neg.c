void point_neg(const point_t *one, const curve_t *curve, point_t *out_one) {
	{%- if short_circuit %}
		if (point_equals(one, curve->neutral)) {
			point_set(one, out_one);
			return;
		}
	{%- endif %}
	{%- include "ops.c" %}
}