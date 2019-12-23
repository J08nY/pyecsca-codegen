#ifndef POINT_H_
#define POINT_H_

#include "defs.h"

point_t *point_new(void);

point_t *point_copy(const point_t *from);

void point_set(const point_t *from, point_t *out);

void point_free(point_t *point);

bool point_equals(const point_t *one, const point_t *other);

void point_to_affine(point_t *point, curve_t *curve, bn_t *out_x, bn_t *out_y);

void point_from_affine(bn_t *x, bn_t *y, curve_t *curve, point_t *out);

void point_add(const point_t *one, const point_t *other, const curve_t *curve, point_t *out_one);

void point_dbl(const point_t *one, const curve_t *curve, point_t *out_one);

void point_tpl(const point_t *one, const curve_t *curve, point_t *out_one);

void point_neg(const point_t *one, const curve_t *curve, point_t *out_one);

void point_scl(const point_t *one, const curve_t *curve, point_t *out_one);

void point_dadd(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out_one);

void point_ladd(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out_one, point_t *out_other);

#endif //POINT_H_