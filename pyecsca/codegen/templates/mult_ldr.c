#include "mult.h"
#include "point.h"

void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	{%- if scalarmult.complete %}
		point_t *p0 = point_copy(curve->neutral);
		point_t *p1 = point_copy(point);
		int nbits = bn_bit_length(&curve->n) - 1;
	{%- else %}
		point_t *p0 = point_copy(point);
		point_t *p1 = point_new();
		point_dbl(point, curve, p1);
		int nbits = bn_bit_length(scalar) - 2;
	{%- endif %}

	for (int i = nbits; i >= 0; i--) {
		if (bn_get_bit(scalar, i) == 0) {
			point_ladd(p0, p1, point, curve, p0, p1);
		} else {
			point_ladd(p1, p0, point, curve, p1, p0);
		}
	}

	{%- if "scl" in scalarmult.formulas %}
    	point_scl(p0, curve, p0);
    {%- endif %}
	point_set(p0, out);
	point_free(p0);
	point_free(p1);
}