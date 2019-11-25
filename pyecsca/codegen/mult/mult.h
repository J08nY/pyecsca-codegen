#ifndef MULT_H_
#define MULT_H_

#include "defs.h"

#define MULT_NONE			  0
#define MULT_DOUBLE_AND_ADD   1

void scalar_mult(bn_t *scalar, point_t *point, curve_t *curve, point_t *out);

#endif //MULT_H_