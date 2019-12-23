#include "point.h"
#include <stdlib.h>

point_t *point_new(void) {
	point_t *result = malloc(sizeof(point_t));
	{%- for variable in variables %}
	bn_init(&result->{{ variable }});
	{%- endfor %}

	return result;
}

point_t *point_copy(const point_t *from) {
	point_t *result = point_new();
	point_set(from, result);
	return result;
}

void point_set(const point_t *from, point_t *out) {
	{%- for variable in variables %}
	bn_copy(&from->{{ variable }}, &out->{{ variable }});
	{%- endfor %}
}

void point_free(point_t *point) {
	{%- for variable in variables %}
	bn_clear(&point->{{ variable }});
	{%- endfor %}
	free(point);
}

bool point_equals(const point_t *one, const point_t *other) {
	{%- for variable in variables %}
	if (!bn_eq(&one->{{ variable }}, &other->{{ variable }})) {
		return false;
	}
	{%- endfor %}
	return true;
}

void point_to_affine(point_t *point, curve_t *curve, bn_t *out_x, bn_t *out_y) {
	{%- include "ops.c" %}
	{%- if "x" in allocations %}
	if (out_x) {
		bn_copy(&x, out_x);
	}
	{%- endif %}
	{%- if "y" in allocations %}
	if (out_y) {
		bn_copy(&y, out_y);
	}
	{%- endif %}
	{%- for free in to_affine_frees %}
	bn_clear(&{{ free }});
	{%- endfor %}
}

void point_from_affine(bn_t *x, bn_t *y, curve_t *curve, point_t *out) {
  	{# XXX: This just works for the stuff currently in EFD. #}
	{%- for variable in variables %}
		{%- if variable in ("X", "Y") %}
	bn_copy({{ variable | lower }}, &out->{{ variable }});
		{%- endif %}
		{%- if variable == "Z" %}
	bn_from_int(1, &out->Z);
		{%- endif %}
		{%- if variable == "T" %}
	bn_mod_mul(x, y, &curve->p, &out->T);
		{%- endif %}
	{%- endfor %}
}
