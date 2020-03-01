#include "mult.h"
#include "point.h"

void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *p0 = point_copy(&curve->neutral);
	point_t *p1 = point_copy(point);
	{%- if scalarmult.complete %}
		int nbits = bn_bit_length(&curve->n) - 1;
	{%- else %}
		int nbits = bn_bit_length(scalar) - 1;
	{%- endif %}

	for (int i = nbits; i >= 0; i--) {
		if (bn_get_bit(scalar, i) == 1) {
			point_add(p0, p1, curve, p1);
			point_dbl(p0, curve, p0);
		} else {
			point_add(p0, p1, curve, p0);
			point_dbl(p1, curve, p1);
		}
	}

	{%- if "scl" in scalarmult.formulas %}
    	point_scl(p0, curve, p0);
    {%- endif %}
	point_set(p0, out);
	point_free(p0);
	point_free(p1);
}