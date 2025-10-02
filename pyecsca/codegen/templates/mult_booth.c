#include "mult.h"
#include "point.h"



static void scalar_mult_inner(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
    point_t *points[{{ 2 ** (scalarmult.width - 1) }}];
    {% if scalarmult.precompute_negation %}
        point_t *points_neg[{{ 2 ** (scalarmult.width - 1) }}];
    {% endif %}

    point_t *current = point_copy(point);
    point_t *dbl = point_new();
    point_dbl(current, curve, dbl);
    points[0] = point_copy(current);
    {% if scalarmult.precompute_negation %}
        points_neg[0] = point_new();
        point_neg(points[0], curve, points_neg[0]);
    {% endif %}
    {% if scalarmult.width > 1 %}
        points[1] = point_copy(dbl);
        {% if scalarmult.precompute_negation %}
            points_neg[1] = point_new();
            point_neg(points[1], curve, points_neg[1]);
        {% endif %}
    {% endif %}

    point_set(dbl, current);
    {% if scalarmult.width > 2 %}
        for (long i = 2; i < {{ 2 ** (scalarmult.width - 1) }}; i++) {
            point_add(current, point, curve, current);
            points[i] = point_copy(current);
            {% if scalarmult.precompute_negation %}
                points_neg[i] = point_new();
                point_neg(points[i], curve, points_neg[i]);
            {% endif %}
        }
    {% endif %}
    point_free(current);
    point_free(dbl);

    size_t bits = bn_bit_length(&curve->n);

    booth_t *bs = bn_booth(scalar, {{ scalarmult.width }}, bits);

    point_t *q = point_copy(curve->neutral);
    point_t *neg = point_new();
    for (long i = 0; i < bs->length; i++) {
        for (long j = 0; j < {{ scalarmult.width }}; j++) {
            point_dbl(q, curve, q);
        }
        int32_t val = bs->data[i];
        if (val > 0) {
            point_accumulate(q, points[val - 1], curve, q);
        } else if (val < 0) {
            {% if scalarmult.precompute_negation %}
                point_accumulate(q, points_neg[-val - 1], curve, q);
            {% else %}
                point_neg(points[-val - 1], curve, neg);
                point_accumulate(q, neg, curve, q);
            {% endif %}
        }
    }
    bn_booth_clear(bs);
    point_free(neg);

    {%- if "scl" in scalarmult.formulas %}
        point_scl(q, curve, q);
    {%- endif %}
    point_set(q, out);
    for (long i = 0; i < {{ 2 ** (scalarmult.width - 1) }}; i++) {
        point_free(points[i]);
        {% if scalarmult.precompute_negation %}
            point_free(points_neg[i]);
        {% endif %}
    }
    point_free(q);
}