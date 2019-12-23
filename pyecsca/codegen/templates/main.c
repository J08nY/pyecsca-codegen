#include "hal/hal.h"
#include "simpleserial/simpleserial.h"
#include "asn1/asn1.h"
#include "hash/hash.h"
#include "bn/bn.h"
#include "prng/prng.h"
#include "gen/defs.h"
#include "mult.h"
#include "point.h"
#include "curve.h"
#include "fat.h"
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>

static point_t *pubkey;
static bn_t privkey;

static curve_t *curve;

static size_t parse_data(const uint8_t *data, size_t len, const char *path, void(*callback)(const char *path, const uint8_t *data, size_t len, void *arg), void *callback_arg) {
	size_t parsed = 0;
	while (parsed < len) {
		char name = (char) data[parsed];
		bool recurse = false;
		if (name & 0x80) {
			name = name & 0x7f;
			recurse = true;
		}

		uint8_t value_len = data[parsed + 1];
		size_t path_len = strlen(path);
		char new_path[path_len + 1 + 1];
		strcpy(new_path, path);
		new_path[path_len] = name;
		new_path[path_len + 1] = '\0';

		if (recurse) {
			parsed += parse_data(data + parsed + 2, value_len, new_path, callback, callback_arg) + 2;
		} else {
			if (callback)
				callback(new_path, data + parsed + 2, value_len, callback_arg);
			parsed += value_len + 2;
		}
	}
	return parsed;
}

static void parse_init_prng(const char *path, const uint8_t *data, size_t len, void *arg) {
	prng_seed(data, len);
}

static uint8_t cmd_init_prng(uint8_t *data, uint16_t len) {
    parse_data(data, len, "", parse_init_prng, NULL);
    return 0;
}

static void parse_set_curve(const char *path, const uint8_t *data, size_t len, void *arg) {
	{%- for param in curve_parameters + ["p", "n", "h"] %}
	if (strcmp(path, "{{ param }}") == 0) {
		bn_from_bin(data, len, &curve->{{ param }});
		return;
	}
	{%- endfor %}
	{%- for variable in curve_variables %}
	if (strcmp(path, "g{{ variable }}") == 0) {
		bn_from_bin(data, len, &curve->generator->{{ variable }});
		return;
	}
	if (strcmp(path, "i{{ variable }}") == 0) {
		bn_from_bin(data, len, &curve->neutral->{{ variable }});
		return;
	}
	{%- endfor %}
}

static uint8_t cmd_set_curve(uint8_t *data, uint16_t len) {
	// need p, [params], n, h, g[variables], i[variables]
	parse_data(data, len, "", parse_set_curve, NULL);
	return 0;
}

static uint8_t cmd_generate(uint8_t *data, uint16_t len) {
	// generate a keypair, export privkey and affine pubkey
	bn_init(&privkey);
	bn_rand_mod(&privkey, &curve->n);
	size_t priv_size = bn_to_bin_size(&privkey);
	size_t coord_size = bn_to_bin_size(&curve->p);

	scalar_mult(&privkey, curve->generator, curve, pubkey);

	uint8_t priv[priv_size];
	bn_to_bin(&privkey, priv);
	simpleserial_put('s', priv_size, priv);
	uint8_t pub[coord_size * {{ curve_variables | length }}];
	{%- for variable in curve_variables %}
	bn_to_binpad(&pubkey->{{ variable }}, pub + coord_size * {{ loop.index0 }}, coord_size);
	{%- endfor %}
	simpleserial_put('w', coord_size * {{ curve_variables | length }}, pub);
	return 0;
}

static void parse_set_privkey(const char *path, const uint8_t *data, size_t len, void *arg) {
	if (strcmp(path, "s") == 0) {
		bn_from_bin(data, len, &privkey);
		return;
	}
}

static uint8_t cmd_set_privkey(uint8_t *data, uint16_t len) {
	// set the current privkey
	parse_data(data, len, "", parse_set_privkey, NULL);
	return 0;
}

static void parse_set_pubkey(const char *path, const uint8_t *data, size_t len, void *arg) {
	{%- for variable in curve_variables %}
	if (strcmp(path, "w{{ variable }}") == 0) {
		bn_from_bin(data, len, &pubkey->{{ variable }});
		return;
	}
	{%- endfor %}
}

static uint8_t cmd_set_pubkey(uint8_t *data, uint16_t len) {
	// set the current pubkey
	parse_data(data, len, "", parse_set_pubkey, NULL);
	return 0;
}

static void parse_scalar_mult(const char *path, const uint8_t *data, size_t len, void *arg) {
	bn_t *scalar = (bn_t *)arg;
	if (strcmp(path, "s") == 0) {
		bn_from_bin(data, len, scalar);
		return;
	}
}

static uint8_t cmd_scalar_mult(uint8_t *data, uint16_t len) {
	// perform base point scalar mult with supplied scalar.
	bn_t scalar; bn_init(&scalar);
	parse_data(data, len, "", parse_scalar_mult, (void *) &scalar);
	size_t coord_size = bn_to_bin_size(&curve->p);

	point_t *result = point_new();

	scalar_mult(&scalar, curve->generator, curve, result);

	uint8_t res[coord_size * {{ curve_variables | length }}];
	{%- for variable in curve_variables %}
	bn_to_binpad(&result->{{ variable }}, res + coord_size * {{ loop.index0 }}, coord_size);
	{%- endfor %}
	simpleserial_put('w', coord_size * {{ curve_variables | length }}, res);
	bn_clear(&scalar);
	point_free(result);
	return 0;
}

static void parse_ecdh(const char *path, const uint8_t *data, size_t len, void *arg) {
	point_t *other = (point_t *) arg;
	{%- for variable in curve_variables %}
	if (strcmp(path, "w{{ variable }}") == 0) {
		bn_from_bin(data, len, &other->{{ variable }});
		return;
	}
	{%- endfor %}
}

static uint8_t cmd_ecdh(uint8_t *data, uint16_t len) {
	//perform ECDH with provided point (and current privkey), output shared secret
	point_t *other = point_new();
	parse_data(data, len, "", parse_ecdh, (void *) other);

	point_t *result = point_new();

	scalar_mult(&privkey, other, curve, result);

	bn_t x; bn_init(&x);
	bn_t y; bn_init(&y);

	point_to_affine(result, curve, &x, &y);

	size_t size = bn_to_bin_size(&curve->p);

	uint8_t x_raw[size];
	bn_to_binpad(&x, x_raw, size);

	size_t h_size = hash_size(size);
	void *h_ctx = hash_new_ctx();
	hash_init(h_ctx);
	uint8_t h_out[h_size];
	hash_final(h_ctx, size, x_raw, h_out);
	hash_free_ctx(h_ctx);

	simpleserial_put('r', h_size, h_out);
	bn_clear(&x);
	bn_clear(&y);
	point_free(result);
	point_free(other);
	return 0;
}

static void parse_ecdsa_msg(const char *path, const uint8_t *data, size_t len, void *arg) {
	fat_t *dest = (fat_t *)arg;
	if (strcmp(path, "d") == 0) {
		dest->len = len;
		dest->value = malloc(len);
		memcpy(dest->value, data, len);
		return;
	}
}

static void parse_ecdsa_sig(const char *path, const uint8_t *data, size_t len, void *arg) {
	fat_t *dest = (fat_t *)arg;
	if (strcmp(path, "s") == 0) {
		dest->len = len;
		dest->value = malloc(len);
		memcpy(dest->value, data, len);
		return;
	}
}

static uint8_t cmd_ecdsa_sign(uint8_t *data, uint16_t len) {
	//perform ECDSA signature on supplied data, output signature
	fat_t msg = fat_empty;
	parse_data(data, len, "", parse_ecdsa_msg, (void *) &msg);

	size_t h_size = hash_size(msg.len);
	void *h_ctx = hash_new_ctx();
	hash_init(h_ctx);
	uint8_t h_out[h_size];
	hash_final(h_ctx, msg.len, msg.value, h_out);
	hash_free_ctx(h_ctx);
	free(msg.value);

	bn_t h; bn_init(&h);
	bn_from_bin(h_out, h_size, &h);

	int mod_len = bn_bit_length(&curve->n);

	if (h_size * 8 > mod_len) {
		bn_rsh(&h, (h_size * 8) - mod_len, &h);
	}

	bn_t k; bn_init(&k);
	bn_rand_mod(&k, &curve->n);

	point_t *p = point_new();

	scalar_mult(&k, curve->generator, curve, p);

	bn_t r; bn_init(&r);
	point_to_affine(p, curve, &r, NULL);
	bn_mod(&r, &curve->n, &r);

	bn_t s; bn_init(&s);
	bn_copy(&privkey, &s);
	bn_mod_mul(&s, &r, &curve->n, &s);
	bn_mod_add(&s, &h, &curve->n, &s);
	bn_mod_div(&s, &k, &curve->n, &s);

	size_t result_len = 0;
	uint8_t *result = asn1_der_encode(&r, &s, &result_len);

	simpleserial_put('s', result_len, result);
	free(result);
	point_free(p);
	bn_clear(&r);
	bn_clear(&s);
	bn_clear(&k);
	bn_clear(&h);
	return 0;
}

static uint8_t cmd_ecdsa_verify(uint8_t *data, uint16_t len) {
	//perform ECDSA verification on supplied data and signature (and current pubkey), output status
	fat_t msg = fat_empty;
	parse_data(data, len, "", parse_ecdsa_msg, (void *) &msg);
	fat_t sig = fat_empty;
	parse_data(data, len, "", parse_ecdsa_sig, (void *) &sig);

	size_t h_size = hash_size(msg.len);
	void *h_ctx = hash_new_ctx();
	hash_init(h_ctx);
	uint8_t h_out[h_size];
	hash_final(h_ctx, msg.len, msg.value, h_out);
	hash_free_ctx(h_ctx);
	free(msg.value);

	bn_t h; bn_init(&h);
	bn_from_bin(h_out, h_size, &h);

	int mod_len = bn_bit_length(&curve->n);

	if (h_size * 8 > mod_len) {
		bn_rsh(&h, (h_size * 8) - mod_len, &h);
	}

	bn_t r; bn_init(&r);
	bn_t s; bn_init(&s);
	if (!asn1_der_decode(sig.value, sig.len, &r, &s)) {
		simpleserial_put('v', 1, (uint8_t *) "\0");
		bn_clear(&r);
		bn_clear(&s);
		bn_clear(&h);
		free(sig.value);
		return 0;
	}
	bn_t orig_r; bn_init(&orig_r);
	bn_copy(&r, &orig_r);

	bn_mod_inv(&s, &curve->n, &s);
	bn_mod_mul(&r, &s, &curve->n, &r); //r = u2
	bn_mod_mul(&h, &s, &curve->n, &h); //h = u1

	point_t *p1 = point_new();
	point_t *p2 = point_new();
	scalar_mult(&h, curve->generator, curve, p1);
	scalar_mult(&r, pubkey, curve, p2);

	point_add(p1, p2, curve, p1);
	bn_t x; bn_init(&x);
	point_to_affine(p1, curve, &x, NULL);
	bn_mod(&x, &curve->n, &x);

	bool result = bn_eq(&orig_r, &x);
	uint8_t res_data[1] = {(uint8_t) result};

	simpleserial_put('v', 1, res_data);
	point_free(p1);
	point_free(p2);
	bn_clear(&x);
	bn_clear(&orig_r);
	bn_clear(&h);
	bn_clear(&r);
	bn_clear(&s);
	free(sig.value);
	return 0;
}

int main(void) {
    platform_init();
    prng_init();
    init_uart();
    trigger_setup();

    curve = curve_new();
    pubkey = point_new();
    bn_init(&privkey);

    simpleserial_init();
    simpleserial_addcmd('i', MAX_SS_LEN, cmd_init_prng);
    simpleserial_addcmd('c', MAX_SS_LEN, cmd_set_curve);
    simpleserial_addcmd('g', 0, cmd_generate);
    simpleserial_addcmd('s', MAX_SS_LEN, cmd_set_privkey);
    simpleserial_addcmd('w', MAX_SS_LEN, cmd_set_pubkey);
    simpleserial_addcmd('m', MAX_SS_LEN, cmd_scalar_mult);
    simpleserial_addcmd('e', MAX_SS_LEN, cmd_ecdh);
    simpleserial_addcmd('a', MAX_SS_LEN, cmd_ecdsa_sign);
    simpleserial_addcmd('v', MAX_SS_LEN, cmd_ecdsa_verify);
    while(simpleserial_get());
    return 0;
}