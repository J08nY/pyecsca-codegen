#include "mult.h"
#include "point.h"

void scalar_mult_by_m_pow2(point_t *point, curve_t *curve) {
    unsigned int m = {{ scalarmult.m }} >> 1;
    while (m) {
        point_dbl(point, curve, point);
        m >>= 1;
    }
}

void scalar_mult_by_m_base(point_t *point, curve_t *curve) {
    point_t *orig = point_copy(point);
    point_dbl(orig, curve, point);
    for (int i = 0; i < {{ scalarmult.m - 2}}; i++) {
        point_add(point, orig, curve, point);
    }
    point_free(orig);
}

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *q = point_copy(curve->neutral);
    point_t *points[{{ scalarmult.m }}];

    point_t *current = point_copy(point);
    point_t *dbl = point_new();
    point_dbl(current, curve, dbl);
    points[0] = point_copy(current);
    points[1] = point_copy(dbl);
    point_set(dbl, current);
    for (long i = 2; i < {{ scalarmult.m }}; i++) {
        point_add(current, point, curve, current);
        points[i] = point_copy(current);
    }
    point_free(current);
    point_free(dbl);

    base_t *bs = bn_convert_base(scalar, {{ scalarmult.m }});

	for (long i = bs->length - 1; i >= 0; i--) {
	    {%- if bin(scalarmult.m).count("1") == 1 %}
	        scalar_mult_by_m_pow2(q, curve);
	    {%- else %}
	        scalar_mult_by_m_base(q, curve);
	    {%- endif %}

		uint8_t val = bs->data[i];
		if (val) {
			point_accumulate(q, points[val-1], curve, q);
        }
	}
	free(bs->data);
	free(bs);

    {%- if "scl" in scalarmult.formulas %}
    	point_scl(q, curve, q);
    {%- endif %}
    point_set(q, out);
    for (long i = 0; i < {{ scalarmult.m }}; i++) {
        point_free(points[i]);
    }
	point_free(q);
}