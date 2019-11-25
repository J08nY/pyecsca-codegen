#ifndef FORMULAS_H_
#define FORMULAS_H_

#include "coords.h"
#include "defs.h"

int point_add(const point_t *one, const point_t *other, const curve_t *curve, point_t *out);

int point_dbl(const point_t *one, const curve_t *curve, point_t *out);

int point_neg(const point_t *one, const curve_t *curve, point_t *out);

int point_scl(const point_t *one, const curve_t *curve, point_t *out);

int point_dadd(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out);

int point_ldr(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out_one, point_t *out_other);

#endif //FORMULAS_H_