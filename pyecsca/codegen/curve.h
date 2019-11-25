#ifndef CURVE_H_
#define CURVE_H_

#include "defs.h"

curve_t* curve_new(const named_bn_t **params, int num_params);

void curve_free(curve_t *curve);

#endif //CURVE_H_