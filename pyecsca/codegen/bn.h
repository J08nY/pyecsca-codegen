#ifndef BN_H_
#define BN_H_

//bn_t definition is variable
//BN_SIZE definition is variable

typedef struct {
	char name;
	bn_t value;
} named_bn_t;

//heap based
bn_t *bn_new();
void bn_free(bn_t *bn);)

int bn_from_hex(const char *data, bn_t *out);
int bn_from_int(uint64_t value, bn_t *out);
void bn_mod_add(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_sub(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_mul(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_div(bn_t *one, bn_t *other, bn_t *mod, bn_t *out);
void bn_mod_inv(bn_t *one, bn_t *mod, bn_t *out);
int bn_get_bit(bn_t *bn, int which);
void bn_set_bit(bn_t *bn, int which, int value);

#endif //BN_H_