#include "bn.h"

bn_err bn_init(bn_t *bn) {
	return mp_init(bn);
}

void bn_copy(const bn_t *from, bn_t *to) {
	mp_copy(from, to);
}

void bn_clear(bn_t *bn) {
	mp_clear(bn);
}

int bn_from_bin(const uint8_t *data, size_t size, bn_t *out) {
	return mp_from_ubin(out, data, size);
}

int bn_from_hex(const char *data, bn_t *out) {
	return mp_read_radix(out, data, 16);
}

int bn_from_int(uint64_t value, bn_t *out) {
	mp_set_u64(out, value);
	return MP_OKAY;
}

void bn_to_binpad(const bn_t *one, uint8_t *data, size_t size) {
	size_t ubin_size = mp_ubin_size(one);
	size_t offset = size - ubin_size;
	mp_to_ubin(one, data + offset, ubin_size, NULL);
}

void bn_to_bin(const bn_t *one, uint8_t *data) {
	mp_to_ubin(one, data, mp_ubin_size(one), NULL);
}

size_t bn_to_bin_size(const bn_t *one) {
	return mp_ubin_size(one);
}

void bn_rand_mod_sample(bn_t *out, const bn_t *mod) {
	int mod_len = bn_bit_length(mod);

	bn_t mask; bn_init(&mask);
	mp_2expt(&mask, mod_len + 1);
	mp_decr(&mask);
	while (1) {
		mp_rand(out, (mod_len / (sizeof(mp_digit) * 8)) + 1);
		mp_and(out, &mask, out);
		if (mp_cmp_mag(out, mod) == MP_LT) {
			bn_clear(&mask);
			break;
		}
	}
}

void bn_rand_mod_reduce(bn_t *out, const bn_t *mod) {
	int mod_len = bn_bit_length(mod);
	mp_rand(out, (mod_len / (sizeof(mp_digit) * 8)) + 2);
	mp_mod(out, mod, out);
}

void bn_mod_add(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	mp_addmod(one, other, mod, out);
}

void bn_mod_sub(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	mp_submod(one, other, mod, out);
}

void bn_mod_mul(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	mp_mulmod(one, other, mod, out);
}

void bn_mod_sqr(const bn_t *one, const bn_t *mod, bn_t *out) {
	mp_sqrmod(one, mod, out);
}

void bn_mod_div(const bn_t *one, const bn_t *other, const bn_t *mod, bn_t *out) {
	bn_t inv;
	mp_init(&inv);
	mp_invmod(other, mod, &inv);
	mp_mulmod(one, &inv, mod, out);
	mp_clear(&inv);
}

void bn_mod_inv(const bn_t *one, const bn_t *mod, bn_t *out) {
	mp_invmod(one, mod, out);
}

void bn_mod(const bn_t *one, const bn_t *mod, bn_t *out) {
	mp_mod(one, mod, out);
}

void bn_lsh(const bn_t *one, int amount, bn_t *out) {
	mp_mul_2d(one, amount, out);
}

void bn_rsh(const bn_t *one, int amount, bn_t *out) {
	mp_div_2d(one, amount, out, NULL);
}

bool bn_eq(const bn_t *one, const bn_t *other) {
	return mp_cmp_mag(one, other) == MP_EQ;
}

int bn_get_bit(const bn_t *bn, int which) {
	int which_digit = which / (sizeof(mp_digit) * 8);
	int which_bit = which % (sizeof(mp_digit) * 8);
	if (bn->used <= which_digit) {
		return 0;
	}
	return (bn->dp[which_digit] >> which_bit) & 1;
}

int bn_bit_length(const bn_t *bn) {
	return mp_count_bits(bn);
}