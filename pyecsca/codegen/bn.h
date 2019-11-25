#ifndef BN_H_
#define BN_H_

#include <tommath.h>

#define bn_t mp_int
#define bn_err mp_err

typedef struct {
	char name;
	bn_t value;
} named_bn_t;

bn_err bn_init(bn_t *bn);
void bn_copy(bn_t *from, bn_t *to);
void bn_clear(bn_t *bn);

int bn_from_hex(const char *data, bn_t *out);
int bn_from_int(uint64_t value, bn_t *out);
void bn_mod_add(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_sub(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_mul(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_sqr(bn_t *one, bn_t *mod, bn_t *out);
void bn_mod_div(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_inv(bn_t *one, bn_t *mod, bn_t *out);
int bn_get_bit(bn_t *bn, int which);
int bn_bit_length(bn_t *bn);

#endif //BN_H_