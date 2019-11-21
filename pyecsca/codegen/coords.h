#ifndef COORDS_H_
#define COORDS_H_

//point_t definition is variable
/*
typedef struct {
	bn_t X;
	bn_t Y;
	bn_t Z;
} point_t;
*/

int point_to_affine(point_t *point, const char coord, curve_t *curve, bn_t *out);

int point_from_affine(bn_t *x, bn_t *y, curve_t *curve, point_t *out);

#endif //COORDS_H_