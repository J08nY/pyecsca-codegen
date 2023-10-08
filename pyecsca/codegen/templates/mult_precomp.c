#include "mult.h"
#include "point.h"

void scalar_mult_ltr(int order_blen, point_t **points, bn_t *scalar, point_t *point, curve_t *curve) {
    {%- if scalarmult.complete %}
        int nbits = order_blen - 1;
    {%- else %}
        int nbits = bn_bit_length(scalar) - 1;
    {%- endif %}

    {%- if scalarmult.always %}
		point_t *dummy = point_new();
	{%- endif %}

    for (int i = nbits; i >= 0; i--) {
        if (bn_get_bit(scalar, i) == 1) {
            point_accumulate(point, points[i], curve, point);
        } else {
        	{%- if scalarmult.always %}
			    point_accumulate(point, points[i], curve, dummy);
			{%- endif %}
        }
    }

    {%- if scalarmult.always %}
	    point_free(dummy);
	{%- endif %}
}

void scalar_mult_rtl(int order_blen, point_t **points, bn_t *scalar, point_t *point, curve_t *curve) {
    {%- if scalarmult.complete %}
        int nbits = order_blen;
    {%- else %}
        int nbits = bn_bit_length(scalar);
    {%- endif %}

    {%- if scalarmult.always %}
		point_t *dummy = point_new();
	{%- endif %}

    for (int i = 0; i < nbits; i++) {
        if (bn_get_bit(scalar, i) == 1) {
            point_accumulate(point, points[i], curve, point);
        } else {
            {%- if scalarmult.always %}
			    point_accumulate(point, points[i], curve, dummy);
			{%- endif %}
        }
    }

    {%- if scalarmult.always %}
	    point_free(dummy);
	{%- endif %}
}

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *q = point_copy(curve->neutral);
	int order_blen = bn_bit_length(&curve->n);
    point_t **points = malloc(sizeof(point_t *) * (order_blen + 1));

    point_t *current = point_copy(point);
    for (int i = 0; i < order_blen + 1; i++) {
        points[i] = point_copy(current);
        if (i != order_blen) {
            point_dbl(current, curve, current);
        }
    }
    point_free(current);

    {%- if scalarmult.direction == ProcessingDirection.LTR %}
        scalar_mult_ltr(order_blen, points, scalar, q, curve);
    {%- else %}
        scalar_mult_rtl(order_blen, points, scalar, q, curve);
    {%- endif %}

    {%- if "scl" in scalarmult.formulas %}
    	point_scl(q, curve, q);
    {%- endif %}
    point_set(q, out);
    for (int i = 0; i < order_blen + 1; i++) {
        point_free(points[i]);
    }
    free(points);
	point_free(q);
}