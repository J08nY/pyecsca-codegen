#include "mult.h"
#include "point.h"
#include "action.h"
{% from "action.c" import start_action, end_action %}

void scalar_mult(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	{{ start_action("mult") }}
	{%- if scalarmult.complete %}
		point_t *q = point_copy(point);
		point_t *r = point_copy(curve->neutral);
		int nbits = bn_bit_length(&curve->n) - 1;
	{%- else %}
		point_t *q = point_copy(point);
		point_t *r = point_copy(point);
		int nbits = bn_bit_length(scalar) - 2;
	{%- endif %}

	{%- if scalarmult.always %}
		point_t *dummy = point_new();
	{%- endif %}

    for (int i = nbits; i >= 0; i--) {
        point_dbl(r, curve, r);
        if (bn_get_bit(scalar, i) == 1) {
            point_add(r, q, curve, r);
        } else {
        	{%- if scalarmult.always %}
			point_add(r, q, curve, dummy);
			{%- endif %}
        }
    }
    {%- if "scl" in scalarmult.formulas %}
    	point_scl(r, curve, r);
    {%- endif %}

    point_set(r, out);
    point_free(q);
    point_free(r);
	{%- if scalarmult.always %}
		point_free(dummy);
	{%- endif %}
	{{ end_action("mult") }}
}