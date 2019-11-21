#ifndef FORMULAS_H_
#define FORMULAS_H_

int point_add(point_t *one, point_t *other, curve_t *curve, point_t *out);

int point_dbl(point_t *one, curve_t *curve, point_t *out);

int point_neg(point_t *one, curve_t *curve, point_t *out);

int point_scl(point_t *one, curve_t *curve, point_t *out);

int point_dadd(point_t *one, point_t *other, point_t *diff, curve_t *curve, point_t *out);

int point_ldr(point_t *one, point_t *other, point_t *diff, curve_t *curve, point_t *out_one, point_t *out_other);

#endif //FORMULAS_H_