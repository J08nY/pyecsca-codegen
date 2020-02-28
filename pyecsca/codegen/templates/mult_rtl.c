#include "mult.h"
#include "point.h"
#include "action.h"
{% from "action.c" import start_action, end_action %}

void scalar_mult(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	{{ start_action("mult") }}
	point_t *q = point_copy(point);
	point_t *r = point_copy(curve->neutral);

	{%- if scalarmult.always %}
		point_t *dummy = point_new();
	{%- endif %}
	bn_t copy;
	bn_init(&copy);
	bn_copy(scalar, &copy);

    while (!bn_is_0(&copy)) {
        if (bn_get_bit(&copy, 0) == 1) {
            point_add(r, q, curve, r);
        } else {
        	{%- if scalarmult.always %}
			point_add(r, q, curve, dummy);
			{%- endif %}
        }
        point_dbl(q, curve, q);
        bn_rsh(&copy, 1, &copy);
    }
    {%- if "scl" in scalarmult.formulas %}
    	point_scl(r, curve, r);
    {%- endif %}

    point_set(r, out);
    point_free(q);
    point_free(r);
    bn_clear(&copy);
	{%- if scalarmult.always %}
		point_free(dummy);
	{%- endif %}
	{{ end_action("mult") }}
}