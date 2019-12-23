#ifndef BN_H_
#define BN_H_

#include <tommath.h>

#define bn_t mp_int
#define bn_err mp_err
#define bn_sign mp_sign

typedef struct {
	char name;
	bn_t value;
} named_bn_t;

typedef struct {
	int8_t *data;
	size_t length;
	int w;
} wnaf_t;

bn_err bn_init(bn_t *bn);
void bn_copy(const bn_t *from, bn_t *to);
void bn_clear(bn_t *bn);

int bn_from_bin(const uint8_t *data, size_t size, bn_t *out);
int bn_from_hex(const char *data, bn_t *out);
int bn_from_int(uint64_t value, bn_t *out);

void bn_to_binpad(const bn_t *one, uint8_t *data, size_t size);
void bn_to_bin(const bn_t *one, uint8_t *data);
size_t bn_to_bin_size(const bn_t *one);

void bn_rand_mod_sample(bn_t *out, const bn_t *mod);
void bn_rand_mod_reduce(bn_t *out, const bn_t *mod);

#if MOD_RAND == MOD_RAND_SAMPLE
#define bn_rand_mod bn_rand_mod_sample
#elif MOD_RAND == MOD_RAND_REDUCE
#define bn_rand_mod bn_rand_mod_reduce
#endif

void bn_mod_add(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
void bn_mod_sub(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
void bn_mod_mul(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
void bn_mod_sqr(const bn_t *one, const bn_t *mod, bn_t *out);
void bn_mod_div(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
void bn_mod_inv(const bn_t *one, const bn_t *mod, bn_t *out);
void bn_mod_pow(const bn_t *one, const bn_t *exp, const bn_t *mod, bn_t *out);
void bn_mod(const bn_t *one, const bn_t *mod, bn_t *out);

void bn_lsh(const bn_t *one, int amount, bn_t *out);
void bn_rsh(const bn_t *one, int amount, bn_t *out);

bool bn_eq(const bn_t *one, const bn_t *other);
bool bn_is_0(const bn_t *one);
bool bn_is_1(const bn_t *one);
bn_sign bn_get_sign(const bn_t *one);

int bn_get_bit(const bn_t *bn, int which);
int bn_bit_length(const bn_t *bn);
wnaf_t *bn_wnaf(const bn_t *bn, int w);
wnaf_t *bn_bnaf(const bn_t *bn);

#endif //BN_H_