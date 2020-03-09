#include "bn.h"
#include <string.h>
#include <stdlib.h>
#include <limits.h>

void math_init(void) {
	#if MUL == MUL_TOOM_COOK
		MP_MUL_TOOM_CUTOFF = 4;
		MP_MUL_KARATSUBA_CUTOFF = INT_MAX;
	#elif MUL == MUL_KARATSUBA
		MP_MUL_TOOM_CUTOFF = INT_MAX;
		MP_MUL_KARATSUBA_CUTOFF = 2;
	#else
		MP_MUL_TOOM_CUTOFF = INT_MAX;
		MP_MUL_KARATSUBA_CUTOFF = INT_MAX;
	#endif //TODO: COMBA
	
	#if SQR == SQR_TOOM_COOK
		MP_SQR_TOOM_CUTOFF = 4;
		MP_SQR_KARATSUBA_CUTOFF = INT_MAX;
	#elif SQR == SQR_KARATSUBA
		MP_SQR_TOOM_CUTOFF = INT_MAX;
		MP_SQR_KARATSUBA_CUTOFF = 2;
	#else
		MP_SQR_TOOM_CUTOFF = INT_MAX;
		MP_SQR_KARATSUBA_CUTOFF = INT_MAX;
	#endif //TODO: COMBA
}

bn_err bn_init(bn_t *bn) {
	return mp_init(bn);
}

bn_err bn_copy(const bn_t *from, bn_t *to) {
	return mp_copy(from, to);
}

void bn_clear(bn_t *bn) {
	mp_clear(bn);
}

bn_err bn_from_bin(const uint8_t *data, size_t size, bn_t *out) {
	return mp_from_ubin(out, data, size);
}

bn_err bn_from_hex(const char *data, bn_t *out) {
	return mp_read_radix(out, data, 16);
}

bn_err bn_from_int(unsigned int value, bn_t *out) {
	if (sizeof(unsigned int) == 8) {
		mp_set_u64(out, value);
	} else {
		mp_set_u32(out, value);
	}
	return MP_OKAY;
}

bn_err bn_to_binpad(const bn_t *one, uint8_t *data, size_t size) {
	size_t ubin_size = mp_ubin_size(one);
	size_t offset = size - ubin_size;
	memset(data, 0, offset);
	return mp_to_ubin(one, data + offset, ubin_size, NULL);
}

bn_err bn_to_bin(const bn_t *one, uint8_t *data) {
	return mp_to_ubin(one, data, mp_ubin_size(one), NULL);
}

size_t bn_to_bin_size(const bn_t *one) {
	return mp_ubin_size(one);
}

bn_err bn_rand_mod_sample(bn_t *out, const bn_t *mod) {
	int mod_len = bn_bit_length(mod);

	bn_err err = BN_OKAY;
	bn_t mask; bn_init(&mask);
	if ((err = mp_2expt(&mask, mod_len + 1)) != BN_OKAY) {
		goto out;
	}
	if ((err = mp_decr(&mask)) != BN_OKAY) {
		goto out;
	}
	while (1) {
		if ((err = mp_rand(out, (mod_len / (sizeof(mp_digit) * 8)) + 1)) != BN_OKAY) {
			break;
		}
		if ((err = mp_and(out, &mask, out)) != BN_OKAY) {
			break;
		}
		if (mp_cmp_mag(out, mod) == MP_LT) {
			break;
		}
	}
	out:
	bn_clear(&mask);
	return err;
}

bn_err bn_rand_mod_reduce(bn_t *out, const bn_t *mod) {
	int mod_len = bn_bit_length(mod);
	bn_err err = BN_OKAY;
	if ((err = mp_rand(out, (mod_len / MP_DIGIT_BIT) + 2)) != BN_OKAY) {
		return err;
	}
	return mp_mod(out, mod, out);
}

bn_err bn_mod_add(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	return mp_addmod(one, other, mod, out);
}

bn_err bn_mod_sub(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	return mp_submod(one, other, mod, out);
}

bn_err bn_mod_neg(const bn_t *one, const bn_t *mod, bn_t *out) {
	bn_err err = BN_OKAY;
	if ((err = mp_neg(one, out)) != BN_OKAY) {
		return err;
	}
	return mp_mod(out, mod, out);
}

bn_err bn_mod_mul(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	return mp_mulmod(one, other, mod, out);
}

bn_err bn_mod_sqr(const bn_t *one, const bn_t *mod, bn_t *out) {
	return mp_sqrmod(one, mod, out);
}

bn_err bn_mod_div(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	bn_t inv;
	bn_err err = BN_OKAY;
	if ((err = mp_init(&inv)) != BN_OKAY) {
		return err;
	}
	if ((err = mp_invmod(other, mod, &inv)) != BN_OKAY) {
		goto out;
	}
	if ((err = mp_mulmod(one, &inv, mod, out)) != BN_OKAY) {
		goto out;
	}
out:
	mp_clear(&inv);
	return err;
}

bn_err bn_mod_inv(const bn_t *one, const bn_t *mod, bn_t *out) {
	return mp_invmod(one, mod, out);
}

bn_err bn_mod_pow(const bn_t *one, const bn_t *exp, const bn_t *mod, bn_t *out) {
	return mp_exptmod(one, exp, mod, out);
}

bn_err bn_mod(const bn_t *one, const bn_t *mod, bn_t *out) {
	return mp_mod(one, mod, out);
}

bn_err bn_red_init(red_t *out) {
	#if REDUCTION == RED_MONTGOMERY
		return bn_init(&out->montgomery_renorm);
	#elif REDUCTION == RED_BARRETT
		return bn_init(&out->barrett);
	#endif
		return BN_OKAY;
}

bn_err bn_red_setup(const bn_t *mod, red_t *out) {
	#if REDUCTION == RED_MONTGOMERY
		bn_err err;
		if ((err = mp_montgomery_setup(mod, &out->montgomery_digit)) != BN_OKAY) {
			return err;
		}
		if ((err = mp_montgomery_calc_normalization(&out->montgomery_renorm, mod)) != BN_OKAY) {
			return err;
		}
		return mp_sqrmod(&out->montgomery_renorm, mod, &out->montgomery_renorm_sqr);
	#elif REDUCTION == RED_BARRETT
		return mp_reduce_setup(&out->barrett, mod);
	#endif
		return BN_OKAY;
}

bn_err bn_red_encode(bn_t *one, const bn_t *mod, const red_t *red) {
	#if REDUCTION == RED_MONTGOMERY
		return mp_mulmod(one, &red->montgomery_renorm, mod, one);
	#else
		return BN_OKAY;
	#endif
}

bn_err bn_red_decode(bn_t *one, const bn_t *mod, const red_t *red) {
	#if REDUCTION == RED_MONTGOMERY
		return mp_montgomery_reduce(one, mod, red->montgomery_digit);
	#else
		return BN_OKAY;
	#endif
}

bn_err bn_red_add(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out) {
#ifdef BN_NON_CONST
	bn_err err;
	if ((err = mp_add(one, other, out)) != BN_OKAY) {
		return err;
	}
	if (mp_cmp(out, mod) == MP_GT) {
		return mp_sub(out, mod, out);
	} else {
		return err;
	}
#else
	return mp_addmod(one, other, mod, out);
#endif
}

bn_err bn_red_sub(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out) {
#ifdef BN_NON_CONST
	bn_err err;
	if ((err = mp_sub(one, other, out)) != BN_OKAY) {
		return err;
	}
	if (mp_cmp_d(out, 0) == MP_LT) {
		return mp_add(out, mod, out);
	}
	if (mp_cmp(out, mod) == MP_GT) {
		return mp_sub(out, mod, out);
	}
	return err;
#else
	return mp_submod(one, other, mod, out);
#endif
}

bn_err bn_red_neg(const bn_t *one, const bn_t *mod, const red_t *red, bn_t *out) {
	bn_err err;
	if ((err = mp_neg(one, out)) != BN_OKAY) {
		return err;
	}
	if (mp_cmp_d(out, 0) == MP_LT) {
		return mp_add(out, mod, out);
	}
	return err;
}

bn_err bn_red_mul(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out) {
	bn_err err;
	if ((err = mp_mul(one, other, out)) != BN_OKAY) {
		return err;
	}
	return bn_red_reduce(mod, red, out);
}

bn_err bn_red_sqr(const bn_t *one, const bn_t *mod, const red_t *red, bn_t *out) {
	bn_err err;
	if ((err = mp_sqr(one, out)) != BN_OKAY) {
		return err;
	}
	return bn_red_reduce(mod, red, out);
}

bn_err bn_red_inv(const bn_t *one, const bn_t *mod, const red_t *red, bn_t *out) {
	bn_err err;
	if ((err = mp_invmod(one, mod, out)) != BN_OKAY) {
		return err;
	}
	#if REDUCTION == RED_MONTGOMERY
		return mp_mulmod(out, &red->montgomery_renorm_sqr, mod, out);
	#else
		return err;
	#endif
}

bn_err bn_red_div(const bn_t *one, const bn_t *other, const bn_t *mod, const red_t *red, bn_t *out) {
	bn_t inv;
	bn_err err;
	if ((err = mp_init(&inv)) != BN_OKAY) {
		return err;
	}
	if ((err = mp_copy(other, &inv)) != BN_OKAY) {
		goto out;
	}
	#if REDUCTION == RED_MONTGOMERY
		if ((err = mp_montgomery_reduce(&inv, mod, red->montgomery_digit)) != BN_OKAY) {
			goto out;
		}
	#endif
	if ((err = mp_invmod(&inv, mod, &inv)) != BN_OKAY) {
		goto out;
	}
	if ((err = mp_mulmod(one, &inv, mod, out)) != BN_OKAY) {
		goto out;
	}
out:
	mp_clear(&inv);
	return err;
}

bn_err bn_red_pow(const bn_t *base, const bn_t *exp, const bn_t *mod, const red_t *red, bn_t *out) {
	int blen = bn_bit_length(exp);
	bn_t result;
	bn_err err;
	if ((err = bn_init(&result)) != BN_OKAY) {
		return err;
	}
	if ((err = bn_copy(base, &result)) != BN_OKAY) {
		bn_clear(&result);
		return err;
	}
	for (int i = blen - 2; i >= 0; --i) {
		bn_red_sqr(&result, mod, red, &result);
		if (bn_get_bit(exp, i)) {
			bn_red_mul(&result, base, mod, red, &result);
		}
	}
	bn_copy(&result, out);
	bn_clear(&result);
	return BN_OKAY;
}

bn_err bn_red_reduce(const bn_t *mod, const red_t *red, bn_t *what) {
	#if REDUCTION == RED_MONTGOMERY
		return mp_montgomery_reduce(what, mod, red->montgomery_digit);
	#elif REDUCTION == RED_BARRETT
		return mp_reduce(what, mod, &red->barrett);
	#endif
		return mp_mod(what, mod, what);
}

void bn_red_clear(red_t *out) {
	#if REDUCTION == RED_MONTGOMERY
		bn_clear(&out->montgomery_renorm);
	#elif REDUCTION == RED_BARRETT
		bn_clear(&out->barrett);
	#endif
}

bn_err bn_lsh(const bn_t *one, int amount, bn_t *out) {
	return mp_mul_2d(one, amount, out);
}

bn_err bn_rsh(const bn_t *one, int amount, bn_t *out) {
	return mp_div_2d(one, amount, out, NULL);
}

bool bn_eq(const bn_t *one, const bn_t *other) {
	return mp_cmp_mag(one, other) == MP_EQ;
}

bool bn_is_0(const bn_t *one) {
	return mp_cmp_d(one, 0) == MP_EQ;
}

bool bn_is_1(const bn_t *one) {
	return mp_cmp_d(one, 1) == MP_EQ;
}

bn_sign bn_get_sign(const bn_t *one) {
	return one->sign;
}

int bn_get_bit(const bn_t *bn, int which) {
	int which_digit = which / MP_DIGIT_BIT;
	int which_bit = which % MP_DIGIT_BIT;
	if (bn->used <= which_digit) {
		return 0;
	}
	return (bn->dp[which_digit] >> which_bit) & 1;
}

int bn_bit_length(const bn_t *bn) {
	return mp_count_bits(bn);
}

wnaf_t *bn_wnaf(const bn_t *bn, int w) {
	if (w > 8 || w < 2) {
		return NULL;
	}
	wnaf_t *result = NULL;

	bn_t half_width;
	if (mp_init(&half_width) != BN_OKAY) {
		return NULL;
	}
	bn_from_int(1, &half_width);
	bn_lsh(&half_width, w - 1, &half_width);
	bn_t full_width;
	if (mp_init(&full_width) != BN_OKAY) {
		goto exit_full_width;
	}
	bn_from_int(1, &full_width);
	bn_lsh(&full_width, w, &full_width);

	bn_t k;
	if (mp_init(&k) != BN_OKAY) {
		goto exit_k;
	}
	bn_copy(bn, &k);

	bn_t val_mod;
	if (mp_init(&val_mod) != BN_OKAY) {
		goto exit_val_mod;
	}

	result = malloc(sizeof(wnaf_t));
	result->w = w;
	result->length = bn_bit_length(bn) + 1;
	result->data = calloc(result->length, sizeof(int8_t));

	size_t i = 0;
	while (!bn_is_0(&k) && !(bn_get_sign(&k) == BN_NEG)) {
		if (bn_get_bit(&k, 0) == 1) {
			bn_mod(&k, &full_width, &val_mod);
			if (mp_cmp(&val_mod, &half_width) == MP_GT) {
				if (mp_sub(&val_mod, &full_width, &val_mod) != BN_OKAY) {
					free(result->data);
					free(result);
					result = NULL;
					break;
				}
			}
			int8_t val = (int8_t) mp_get_i32(&val_mod);
			result->data[i++] = val;
			if (mp_sub(&k, &val_mod, &k) != BN_OKAY) {
				free(result->data);
				free(result);
				result = NULL;
				break;
			}
		} else {
			result->data[i++] = 0;
		}
		bn_rsh(&k, 1, &k);
	}
	bn_clear(&val_mod);

exit_val_mod:
	bn_clear(&k);
exit_k:
	bn_clear(&full_width);
exit_full_width:
	bn_clear(&half_width);
	return result;
}

wnaf_t *bn_bnaf(const bn_t *bn) {
	return bn_wnaf(bn, 2);
}