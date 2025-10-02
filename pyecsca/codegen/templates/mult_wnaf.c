#include "mult.h"
#include "point.h"

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *q = point_copy(curve->neutral);
    point_t *points[{{ 2 ** (scalarmult.width - 2) }}];
    {%- if scalarmult.precompute_negation %}
        point_t *points_neg[{{ 2 ** (scalarmult.width - 2) }}];
    {%- else %}
        point_t *neg = point_new();
    {%- endif %}

    point_t *current = point_copy(point);
    point_t *dbl = point_new();
    point_dbl(current, curve, dbl);
    for (long i = 0; i < {{ 2 ** (scalarmult.width - 2) }}; i++) {
        points[i] = point_copy(current);
        {%- if scalarmult.precompute_negation %}
            points_neg[i] = point_copy(current);
            point_neg(points_neg[i], curve, points_neg[i]);
        {%- endif %}
        point_add(current, dbl, curve, current);
    }
    point_free(current);
    point_free(dbl);

	wnaf_t *naf = bn_wnaf(scalar, {{ scalarmult.width }});

	for (long i = 0; i < naf->length; i++) {
		point_dbl(q, curve, q);
		int8_t val = naf->data[i];
		if (val > 0) {
			point_accumulate(q, points[(val - 1) / 2], curve, q);
		} else if (val < 0) {
		    {%- if scalarmult.precompute_negation %}
		        point_accumulate(q, points_neg[(-val - 1) / 2], curve, q);
		    {%- else %}
		        point_neg(points[(-val - 1) / 2], curve, neg);
                point_accumulate(q, neg, curve, q);
		    {%- endif %}
		}
	}
	free(naf->data);
	free(naf);

    {%- if "scl" in scalarmult.formulas %}
    	point_scl(q, curve, q);
    {%- endif %}
    point_set(q, out);
    for (long i = 0; i < {{ 2 ** (scalarmult.width - 2) }}; i++) {
        point_free(points[i]);
        {%- if scalarmult.precompute_negation %}
            point_free(points_neg[i]);
        {%- endif %}
    }
    {%- if not scalarmult.precompute_negation %}
    point_free(neg);
    {%- endif %}
	point_free(q);
}