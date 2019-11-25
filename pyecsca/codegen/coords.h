#ifndef COORDS_H_
#define COORDS_H_

#include "bn.h"
#include "defs.h"

point_t *point_new(void);

point_t *point_copy(const point_t *from);

void point_set(const point_t *from, point_t *out);

void point_free(point_t *point);

int point_to_affine(point_t *point, const char coord, curve_t *curve, bn_t *out);

int point_from_affine(bn_t *x, bn_t *y, curve_t *curve, point_t *out);

#endif //COORDS_H_