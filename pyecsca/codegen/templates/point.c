#include "point.h"
#include "action.h"
#include <stdlib.h>
{% import "ops.c" as ops %}
{% from "action.c" import start_action, end_action %}

/**
 * Constructs (allocates) a new point.
 */
point_t *point_new(void) {
	point_t *result = malloc(sizeof(point_t));
	{%- for variable in variables %}
	bn_init(&result->{{ variable }});
	{%- endfor %}
	result->infinity = false;
	return result;
}

/**
 * Creates a copy of a point.
 */
point_t *point_copy(const point_t *from) {
	point_t *result = point_new();
	point_set(from, result);
	return result;
}

void point_set(const point_t *from, point_t *out) {
	{%- for variable in variables %}
	bn_copy(&from->{{ variable }}, &out->{{ variable }});
	{%- endfor %}
	out->infinity = from->infinity;
}

void point_free(point_t *point) {
	{%- for variable in variables %}
	bn_clear(&point->{{ variable }});
	{%- endfor %}
	free(point);
}

bool point_equals(const point_t *one, const point_t *other) {
	if ((one->infinity && !other->infinity) || (other->infinity && !one->infinity)) {
		return false;
	}
	if (one->infinity && other->infinity) {
		return true;
	}

	{%- for variable in variables %}
	if (!bn_eq(&one->{{ variable }}, &other->{{ variable }})) {
		return false;
	}
	{%- endfor %}
	return true;
}

bool point_equals_affine(const point_t *one, const point_t *other, const curve_t *curve) {
	if ((one->infinity && !other->infinity) || (other->infinity && !one->infinity)) {
		return false;
	}
	if (one->infinity && other->infinity) {
		return true;
	}
	bool result = true;
	bn_t ax; bn_init(&ax);
	bn_t ay; bn_init(&ay);
	bn_t bx; bn_init(&bx);
	bn_t by; bn_init(&by);
	point_to_affine(one, curve, &ax, &ay);
	point_to_affine(other, curve, &bx, &by);
	if (!bn_eq(&ax, &bx)) {
		result = false;
	}
	if (!bn_eq(&ay, &by)) {
		result = false;
	}
	bn_clear(&ax);
	bn_clear(&ay);
	bn_clear(&bx);
	bn_clear(&by);
	return result;
}

void point_red_encode(point_t *point, const curve_t *curve) {
	#if REDUCTION == RED_MONTGOMERY
		{%- for variable in variables %}
		bn_red_encode(&point->{{ variable }}, &curve->p, &curve->p_red);
		{%- endfor %}
	#endif
}

void point_red_decode(point_t *point, const curve_t *curve) {
	#if REDUCTION == RED_MONTGOMERY
		{%- for variable in variables %}
		bn_red_decode(&point->{{ variable }}, &curve->p, &curve->p_red);
		{%- endfor %}
	#endif
}

void point_to_affine(const point_t *point, const curve_t *curve, bn_t *out_x, bn_t *out_y) {
	{{ start_action("coord_map") }}
	{{ ops.render_all(allocations, initializations, operations, returns, frees, "err") }}
	if (err != BN_OKAY) {
		return;
	}
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
	{{ end_action("coord_map") }}
}

void point_from_affine(bn_t *x, bn_t *y, const curve_t *curve, point_t *out) {
	{{ start_action("coord_map") }}
  	{# XXX: This just works for the stuff currently in EFD. #}
	{%- for variable in variables %}
		{%- if variable in ("X", "Y") %}
	bn_copy({{ variable | lower }}, &out->{{ variable }});
		{%- endif %}
		{%- if variable == "Z" %}
	bn_from_int(1, &out->Z);
	bn_red_encode(&out->Z, &curve->p, &curve->p_red);
		{%- endif %}
		{%- if variable == "T" %}
	bn_red_mul(x, y, &curve->p, &out->T);
		{%- endif %}
	{%- endfor %}
	{{ end_action("coord_map") }}
}
