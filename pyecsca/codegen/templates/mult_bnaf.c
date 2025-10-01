#include "mult.h"
#include "point.h"

point_t *scalar_mult_ltr(point_t *point, point_t *neg, curve_t *curve, wnaf_t *naf) {
    {% if scalarmult.always %}
        point_t *q_copy = point_new();
        point_t *dummy = point_new();
    {% endif %}

    point_t *q = point_copy(curve->neutral);
	for (long i = naf->length - 1; i >= 0; i--) {
		point_dbl(q, curve, q);
		{% if scalarmult.always %}
            point_set(q, q_copy);
        {% endif %}

		if (naf->data[i] == 1) {
			point_accumulate(q, point, curve, q);
			{% if scalarmult.always %}
                point_accumulate(q_copy, neg, curve, dummy);
            {% endif %}
		} else if (naf->data[i] == -1) {
			point_accumulate(q, neg, curve, q);
			{% if scalarmult.always %}
                point_accumulate(q_copy, point, curve, dummy);
            {% endif %}
		}
	}
	{% if scalarmult.always %}
        point_free(q_copy);
        point_free(dummy);
    {% endif %}
    return q;
}

point_t* scalar_mult_rtl(point_t *point, point_t *neg, curve_t *curve, wnaf_t *naf) {
    {% if scalarmult.always %}
        point_t *r_copy = point_new();
        point_t *dummy = point_new();
    {% endif %}

    point_t *q = point_copy(point);
    point_t *r = point_copy(curve->neutral);
    point_t *q_neg = point_new();
    for (long i = 0; i < naf->length; i++) {
        {% if scalarmult.always %}
            point_set(r, r_copy);
        {% endif %}
        if (naf->data[i] == 1) {
            point_accumulate(r, q, curve, r);
            {% if scalarmult.always %}
                point_neg(q, curve, q_neg);
                point_accumulate(r_copy, q_neg, curve, dummy);
            {% endif %}
        } else if (naf->data[i] == -1) {
            point_neg(q, curve, q_neg);
            point_accumulate(r, q_neg, curve, r);
            {% if scalarmult.always %}
                point_accumulate(r_copy, q, curve, dummy);
            {% endif %}
        }
        point_dbl(q, curve, q);
    }
    point_free(q_neg);
    point_free(q);

    {% if scalarmult.always %}
        point_free(r_copy);
        point_free(dummy);
    {% endif %}
    return r;
}

static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *neg = point_new();
	point_neg(point, curve, neg);
	wnaf_t *naf = bn_bnaf(scalar);

	{# TODO: Handle the ".complete" option #}

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