#ifndef BN_H_
#define BN_H_

#include <tommath.h>

#define RED_MONTGOMERY   1
#define RED_BARRET 		 2
#define RED_BASE		 3

#define MUL_TOOM_COOK 1
#define MUL_KARATSUBA 2
#define MUL_COMBA	  3
#define MUL_BASE	  4

#define SQR_TOOM_COOK 1
#define SQR_KARATSUBA 2
#define SQR_COMBA	  3
#define SQR_BASE	  4

#define bn_t mp_int
#define bn_digit mp_digit
#define bn_err mp_err
#define bn_sign mp_sign

#define BN_OKAY MP_OKAY /* no error */
#define BN_ERR MP_ERR   /* unknown error */
#define BN_MEM MP_MEM   /* out of mem */
#define BN_VAL MP_VAL   /* invalid input */
#define BN_ITER MP_ITER /* maximum iterations reached */
#define BN_BUF MP_BUF   /* buffer overflow, supplied buffer too small */
#define BN_OVF MP_OVF   /* mp_int overflow, too many digits */

#define BN_ZPOS MP_ZPOS
#define BN_NEG MP_NEG

#define BN_LT MP_LT /* less than */
#define BN_EQ MP_EQ /* equal */
#define BN_GT MP_GT /* greater than */

typedef struct {
	#if REDUCTION == RED_MONTGOMERY
		bn_digit montgomery_digit;
		bn_t montgomery_renorm;
		bn_t montgomery_renorm_sqr;
	#elif REDUCTION == RED_BARRETT
		bn_t barrett;
	#endif
} red_t;

typedef struct {
	char name;
	bn_t value;
} named_bn_t;

typedef struct {
	int8_t *data;
	size_t length;
	int w;
} wnaf_t;

typedef struct {
    uint8_t *data;
    size_t length;
    int w;
} wsliding_t;

typedef struct {
    int *data;
    size_t length;
    int m;
} small_base_t;

typedef struct {
    bn_t *data;
    size_t length;
    bn_t m;
} large_base_t;

void math_init(void);

extern const int bn_digit_bits;

bn_err  bn_init(bn_t *bn);
#define bn_init_multi mp_init_multi
bn_err  bn_copy(const bn_t *from, bn_t *to);
void    bn_clear(bn_t *bn);
#define bn_clear_multi mp_clear_multi

bn_err bn_from_bin(const uint8_t *data, size_t size, bn_t *out);
bn_err bn_from_hex(const char *data, bn_t *out);
bn_err bn_from_int(unsigned int value, bn_t *out);

bn_err bn_to_binpad(const bn_t *one, uint8_t *data, size_t size);
bn_err bn_to_bin(const bn_t *one, uint8_t *data);
size_t bn_to_bin_size(const bn_t *one);
unsigned int bn_to_int(const bn_t *one);

bn_err bn_rand_mod_sample(bn_t *out, const bn_t *mod);
bn_err bn_rand_mod_reduce(bn_t *out, const bn_t *mod);

bn_err bn_mod_add(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
bn_err bn_mod_sub(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
bn_err bn_mod_neg(const bn_t *one, const bn_t *mod, bn_t *out);
bn_err bn_mod_mul(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
bn_err bn_mod_sqr(const bn_t *one, const bn_t *mod, bn_t *out);
bn_err bn_mod_div(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out);
bn_err bn_mod_inv(const bn_t *one, const bn_t *mod, bn_t *out);
bn_err bn_mod_pow(const bn_t *one, const bn_t *exp, const bn_t *mod, bn_t *out);
bn_err bn_mod(const bn_t *one, const bn_t *mod, bn_t *out);

bn_err bn_red_init(red_t *out);
bn_err bn_red_setup(const bn_t *mod, red_t *out);
bn_err bn_red_encode(bn_t *one, const bn_t *mod, const red_t *red);
bn_err bn_red_decode(bn_t *one, const bn_t *mod, const red_t *red);
bn_err bn_red_add(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_sub(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_neg(const bn_t *one, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_mul(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_sqr(const bn_t *one, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_inv(const bn_t *one, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_div(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_pow(const bn_t *base, const bn_t *exp, const bn_t *mod, const red_t *red, bn_t *out);
bn_err bn_red_reduce(const bn_t *mod, const red_t *red, bn_t *what);
void   bn_red_clear(red_t *out);

bn_err bn_lsh(const bn_t *one, int amount, bn_t *out);
bn_err bn_rsh(const bn_t *one, int amount, bn_t *out);
bn_err bn_and(const bn_t *one, const bn_t *other, bn_t *out);

bool    bn_eq(const bn_t *one, const bn_t *other);
bool    bn_is_0(const bn_t *one);
bool    bn_is_1(const bn_t *one);
bn_sign bn_get_sign(const bn_t *one);

int     bn_get_bit(const bn_t *bn, int which);
int     bn_bit_length(const bn_t *bn);

wnaf_t *bn_wnaf(const bn_t *bn, int w);
wnaf_t *bn_bnaf(const bn_t *bn);

wsliding_t *bn_wsliding_ltr(const bn_t *bn, int w);
wsliding_t *bn_wsliding_rtl(const bn_t *bn, int w);

small_base_t *bn_convert_base_small(const bn_t *bn, int m);
large_base_t *bn_convert_base_large(const bn_t *bn, const bn_t *m);

#endif //BN_H_