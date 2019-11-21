#ifndef CURVE_H_
#define CURVE_H_

//curve_t definition is variable
/*
typedef struct {
	bn_t a;
	bn_t b;
} curve_t;
*/

curve_t* curve_new(named_bn_t **params, int num_params);

void curve_free(curve_t *curve);

#endif //CURVE_H_