#include "mult.h"
#include "point.h"



static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *a = point_copy(curve->neutral);
	point_t *b = point_copy(curve->neutral);

	int order_blen = bn_bit_length(&curve->n);
	int d = (order_blen + {{ scalarmult.width }} - 1) / {{ scalarmult.width }};

    point_t **points = malloc(sizeof(point_t *) * d);

    point_t *current = point_copy(point);
    for (int i = 0; i < d; i++) {
        points[i] = point_copy(current);
        if (i != d - 1) {
            for (int j = 0; j < {{ scalarmult.width }}; j++) {
                point_dbl(current, curve, current);
            }
        }
    }
    point_free(current);

    small_base_t *bs = bn_convert_base_small(scalar, {{ 2**scalarmult.width }});

	for (int j = {{ 2**scalarmult.width }}; j > 0; j--) {
        {%- if scalarmult.direction == ProcessingDirection.RTL %}
            for (int i = 0; i < bs->length; i++) {
                if (bs->data[i] == j) {
                    point_accumulate(b, points[i], curve, b);
                }
            }
        {%- else %}
            for (int i = bs->length - 1; i >= 0; i--) {
                if (bs->data[i] == j) {
                    point_accumulate(b, points[i], curve, b);
                }
            }
        {%- endif -%}

        {%- if scalarmult.short_circuit %}
            if (point_equals(a, b)) {
                point_dbl(b, curve, a);
                continue;
            }
        {%- endif %}
        point_accumulate(a, b, curve, a);
	}
	bn_small_base_clear(bs);

    {%- if "scl" in scalarmult.formulas %}
    	point_scl(a, curve, a);
    {%- endif %}
    point_set(a, out);
    for (long i = 0; i < d; i++) {
        point_free(points[i]);
    }
    free(points);
	point_free(a);
	point_free(b);
}