#ifndef CURVE_H_
#define CURVE_H_

#include "defs.h"

curve_t* curve_new(void);

void curve_free(curve_t *curve);

void curve_set_param(curve_t *curve, char name, const bn_t *value);

#endif //CURVE_H_