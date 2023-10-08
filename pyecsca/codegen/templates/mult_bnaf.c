#include "mult.h"
#include "point.h"

point_t *scalar_mult_ltr(point_t *point, point_t *neg, curve_t *curve, wnaf_t *naf) {
    point_t *q = point_copy(curve->neutral);
	for (long i = naf->length - 1; i >= 0; i--) {
		point_dbl(q, curve, q);
		if (naf->data[i] == 1) {
			point_accumulate(q, point, curve, q);
		} else if (naf->data[i] == -1) {
			point_accumulate(q, neg, curve, q);
		}
	}
    return q;
}

point_t* scalar_mult_rtl(point_t *point, point_t *neg, curve_t *curve, wnaf_t *naf) {
    point_t *r = point_copy(point);
    point_t *q = point_copy(curve->neutral);
    point_t *r_neg = point_new();
    for (long i = 0; i < naf->length; i++) {
        if (naf->data[i] == 1) {
            point_accumulate(q, r, curve, q);
        } else if (naf->data[i] == -1) {
            point_neg(r, curve, r_neg);
            point_accumulate(q, r_neg, curve, q);
        }
        point_dbl(r, curve, r);
    }
    point_free(r_neg);
    point_free(r);

    return q;
}

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *neg = point_new();
	point_neg(point, curve, neg);
	wnaf_t *naf = bn_bnaf(scalar);

    {% if scalarmult.direction == ProcessingDirection.LTR %}
        point_t *q = scalar_mult_ltr(point, neg, curve, naf);
    {% elif scalarmult.direction == ProcessingDirection.RTL %}
        point_t *q = scalar_mult_rtl(point, neg, curve, naf);
    {% endif %}

    free(naf->data);
	free(naf);

    {%- if "scl" in scalarmult.formulas %}
    	point_scl(q, curve, q);
    {%- endif %}
    point_set(q, out);
	point_free(neg);
	point_free(q);
}