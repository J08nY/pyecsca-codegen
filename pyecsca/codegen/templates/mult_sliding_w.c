#include "mult.h"
#include "point.h"

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *q = point_copy(curve->neutral);
    point_t *points[{{ 2 ** (scalarmult.width - 1) }}];

    point_t *current = point_copy(point);
    point_t *dbl = point_new();
    point_dbl(current, curve, dbl);
    for (long i = 0; i < {{ 2 ** (scalarmult.width - 1) }}; i++) {
        points[i] = point_copy(current);
        point_add(current, dbl, curve, current);
    }
    point_free(current);
    point_free(dbl);

    {% if scalarmult.recoding_direction == ProcessingDirection.LTR %}
	    wsliding_t *ws = bn_wsliding_ltr(scalar, {{ scalarmult.width }});
	{% elif scalarmult.recoding_direction == ProcessingDirection.RTL %}
	    wsliding_t *ws = bn_wsliding_rtl(scalar, {{ scalarmult.width }});
	{% endif %}
	printf("ws %p\n", ws);
	printf("len = %li\n", ws->length);

	for (long i = 0; i < ws->length; i++) {
		point_dbl(q, curve, q);
		uint8_t val = ws->data[i];
		printf("i = %li, val = %i\n", i, val);
		if (val) {
		    printf("adding %i\n", (val - 1) / 2);
			point_accumulate(q, points[(val - 1) / 2], curve, q);
        }
	}
	free(ws->data);
	free(ws);

    {%- if "scl" in scalarmult.formulas %}
    	point_scl(q, curve, q);
    {%- endif %}
    point_set(q, out);
    for (long i = 0; i < {{ 2 ** (scalarmult.width - 1) }}; i++) {
        point_free(points[i]);
    }
	point_free(q);
}