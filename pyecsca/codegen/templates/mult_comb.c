#include "mult.h"
#include "point.h"

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *q = point_copy(curve->neutral);

	int order_blen = bn_bit_length(&curve->n);
	int d = (order_blen + {{ scalarmult.width }} - 1) / {{ scalarmult.width }};

	point_t *base_points[{{ scalarmult.width }}];

	point_t *current = point_copy(point);
	for (int i = 0; i < {{ scalarmult.width }}; i++) {
        base_points[i] = point_copy(current);
        if (i != d - 1) {
            for (int j = 0; j < d; j++) {
                point_dbl(current, curve, current);
            }
        }
	}
	point_free(current);

	point_t *points[{{ 2**scalarmult.width }}];
	for (int j = 0; j < {{ 2**scalarmult.width }}; j++) {
	    point_t *alloc_point = NULL;
	    for (int i = 0; i < {{ scalarmult.width }}; i++) {
	        if (j & (1 << i)) {
	            if (alloc_point) {
	                point_accumulate(alloc_point, base_points[i], curve, alloc_point);
	            } else {
	                alloc_point = point_copy(base_points[i]);
	            }
	        }
	    }
        points[j] = alloc_point;
	}

	bn_t base; bn_init(&base);
	bn_from_int(1, &base);
    bn_lsh(&base, d, &base);

	large_base_t *bs = bn_convert_base_large(scalar, &base);
	for (int i = d - 1; i >= 0; i--) {
        point_dbl(q, curve, q);
        int word = 0;
        for (int j = 0; j < {{ scalarmult.width }}; j++) {
            if (j < bs->length) {
                word |= bn_get_bit(&bs->data[j], i) << j;
            }
        }
        if (word) {
            point_accumulate(q, points[word], curve, q);
        }
	}
	for (int i = 0; i < bs->length; i++) {
	    bn_clear(&bs->data[i]);
	}
	free(bs->data);
	bn_clear(&bs->m);
	free(bs);
	bn_clear(&base);


    {%- if "scl" in scalarmult.formulas %}
    	point_scl(a, curve, a);
    {%- endif %}
    point_set(q, out);
    for (int i = 0; i < {{ scalarmult.width }}; i++) {
        point_free(base_points[i]);
    }
    for (int i = 0; i < {{ 2**scalarmult.width }}; i++) {
        if (points[i]) {
            point_free(points[i]);
        }
    }
	point_free(q);
}