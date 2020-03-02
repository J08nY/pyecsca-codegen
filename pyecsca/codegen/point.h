#ifndef POINT_H_
#define POINT_H_

#include "defs.h"

point_t *point_new(void);

point_t *point_copy(const point_t *from);

void point_set(const point_t *from, point_t *out);

void point_free(point_t *point);

bool point_equals(const point_t *one, const point_t *other);

bool point_equals_affine(const point_t *one, const point_t *other, const curve_t *curve);

void point_red_encode(point_t *point, const curve_t *curve);

void point_red_decode(point_t *point, const curve_t *curve);

void point_to_affine(const point_t *point, const curve_t *curve, bn_t *out_x, bn_t *out_y);

void point_from_affine(bn_t *x, bn_t *y, const curve_t *curve, point_t *out);

void point_add(const point_t *one, const point_t *other, const curve_t *curve, point_t *out_one);
bool point_add_init(void);
void point_add_clear(void);

void point_dbl(const point_t *one, const curve_t *curve, point_t *out_one);
bool point_dbl_init(void);
void point_dbl_clear(void);

void point_tpl(const point_t *one, const curve_t *curve, point_t *out_one);
bool point_tpl_init(void);
void point_tpl_clear(void);

void point_neg(const point_t *one, const curve_t *curve, point_t *out_one);
bool point_neg_init(void);
void point_neg_clear(void);

void point_scl(const point_t *one, const curve_t *curve, point_t *out_one);
bool point_scl_init(void);
void point_scl_clear(void);

void point_dadd(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out_one);
bool point_dadd_init(void);
void point_dadd_clear(void);

void point_ladd(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out_one, point_t *out_other);
bool point_ladd_init(void);
void point_ladd_clear(void);

#endif //POINT_H_