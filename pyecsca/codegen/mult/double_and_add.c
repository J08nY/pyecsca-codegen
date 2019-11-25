#include "mult.h"
#include "formulas.h"

void scalar_mult(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	point_t *q = point_copy(point);
	point_t *r = point_copy(curve->neutral);

    int nbits = bn_bit_length(&curve->n);
    for (int i = nbits; i >= 0; i--) {
        point_dbl(r, curve, r);
        if (bn_get_bit(scalar, i) == 1) {
            point_add(q, r, curve, r);
        }
    }
    point_scl(r, curve, r);
    point_set(r, out);
    point_free(q);
    point_free(r);
}