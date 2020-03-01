#include "mult.h"
#include "point.h"

void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *p0 = point_copy(point);
	point_t *p1 = point_new();

	int nbits = bn_bit_length(scalar);
	for (int i = nbits - 2; i >= 0; i--) {
	  point_dbl(p0, curve, p0);
	  point_add(p0, point, curve, p1);
	  if (bn_get_bit(scalar, i) != 0) {
		 point_set(p1, p0);
	  }
	}
	{%- if "scl" in scalarmult.formulas %}
		point_scl(p0, curve, p0);
	{%- endif %}
	point_set(p0, out);
	point_free(p0);
	point_free(p1);
}