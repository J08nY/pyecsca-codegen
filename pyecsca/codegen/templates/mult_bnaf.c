#include "mult.h"
#include "point.h"

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *neg = point_new();
	point_neg(point, curve, neg);
	point_t *q = point_copy(curve->neutral);

	wnaf_t *naf = bn_bnaf(scalar);

	for (long i = naf->length - 1; i >= 0; i--) {
		point_dbl(q, curve, q);
		if (naf->data[i] == 1) {
			point_add(q, point, curve, q);
		} else if (naf->data[i] == -1) {
			point_add(q, neg, curve, q);
		}
	}
	free(naf->data);
	free(naf);

    {%- if "scl" in scalarmult.formulas %}
    	point_scl(q, curve, q);
    {%- endif %}
    point_set(q, out);
	point_free(neg);
	point_free(q);
}