#ifndef DEFS_H_
#define DEFS_H_
#include "bn.h"

//point_t definition is variable
typedef struct {
	bn_t X;
	bn_t Y;
	bn_t Z;
} point_t;

//curve_t definition is variable
typedef struct {
	bn_t n;
	point_t *neutral;
} curve_t;

#endif //DEFS_H_