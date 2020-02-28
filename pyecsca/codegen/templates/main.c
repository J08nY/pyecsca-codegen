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
#include "formulas.h"
#include "action.h"
#include "rand.h"

#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>

{% from "action.c" import start_action, end_action %}

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

static uint8_t cmd_init_prng(uint8_t *data, uint16_t len) {
    prng_seed(data, len);
    return 0;
}

static void parse_set_params(const char *path, const uint8_t *data, size_t len, void *arg) {
	{%- for param in curve_parameters + ["p", "n", "h"] %}
	if (strcmp(path, "{{ param }}") == 0) {
		bn_from_bin(data, len, &curve->{{ param }});
		return;
	}
	{%- endfor %}

	fat_t *affine = (fat_t *) arg;
	if (strcmp(path, "gx") == 0) {
		affine[0].len = len;
		affine[0].value = malloc(len);
		memcpy(affine[0].value, data, len);
		return;
	}
	if (strcmp(path, "gy") == 0) {
		affine[1].len = len;
		affine[1].value = malloc(len);
		memcpy(affine[1].value, data, len);
		return;
	}

	if (strcmp(path, "in") == 0) {
		curve->neutral->infinity = *data;
		return;
	}
	{%- for variable in curve_variables %}
	if (strcmp(path, "i{{ variable }}") == 0) {
		bn_from_bin(data, len, &curve->neutral->{{ variable }});
		return;
	}
	{%- endfor %}
}

static uint8_t cmd_set_params(uint8_t *data, uint16_t len) {
	// need p, [params], n, h, g[xy], i[variables]
	fat_t affine[2] = {fat_empty, fat_empty};
	parse_data(data, len, "", parse_set_params, (void *) affine);
	bn_t x; bn_init(&x);
	bn_t y; bn_init(&y);
	bn_from_bin(affine[0].value, affine[0].len, &x);
	bn_from_bin(affine[1].value, affine[1].len, &y);

	point_from_affine(&x, &y, curve, curve->generator);
	bn_clear(&x);
	bn_clear(&y);
	free(affine[0].value);
	free(affine[1].value);
	return 0;
}

static uint8_t cmd_generate(uint8_t *data, uint16_t len) {
	// generate a keypair, export privkey and affine pubkey
	{{ start_action("keygen") }}
	bn_rand_mod(&privkey, &curve->n);
	size_t priv_size = bn_to_bin_size(&privkey);
	size_t coord_size = bn_to_bin_size(&curve->p);

	scalar_mult(&privkey, curve->generator, curve, pubkey);

	uint8_t priv[priv_size];
	bn_to_bin(&privkey, priv);

	bn_t x; bn_init(&x);
	bn_t y; bn_init(&y);

	point_to_affine(pubkey, curve, &x, &y);

	uint8_t pub[coord_size * 2];
	bn_to_binpad(&x, pub, coord_size);
	bn_to_binpad(&y, pub + coord_size, coord_size);
	bn_clear(&x);
	bn_clear(&y);
	{{ end_action("keygen") }}

	simpleserial_put('s', priv_size, priv);
	simpleserial_put('w', coord_size * 2, pub);
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
	fat_t *affine = (fat_t *) arg;
	if (strcmp(path, "wx") == 0) {
		affine[0].len = len;
		affine[0].value = malloc(len);
		memcpy(affine[0].value, data, len);
		return;
	}
	if (strcmp(path, "wy") == 0) {
		affine[1].len = len;
		affine[1].value = malloc(len);
		memcpy(affine[1].value, data, len);
		return;
	}
}

static uint8_t cmd_set_pubkey(uint8_t *data, uint16_t len) {
	// set the current pubkey
	fat_t affine[2] = {fat_empty, fat_empty};
	parse_data(data, len, "", parse_set_pubkey, (void *) affine);
	bn_t x; bn_init(&x);
	bn_t y; bn_init(&y);
	bn_from_bin(affine[0].value, affine[0].len, &x);
	bn_from_bin(affine[1].value, affine[1].len, &y);

	point_from_affine(&x, &y, curve, pubkey);
	bn_clear(&x);
	bn_clear(&y);
	free(affine[0].value);
	free(affine[1].value);
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
	bn_clear(&scalar);
	point_free(result);

	simpleserial_put('w', coord_size * {{ curve_variables | length }}, res);
	return 0;
}

static void parse_ecdh(const char *path, const uint8_t *data, size_t len, void *arg) {
	fat_t *affine = (fat_t *) arg;
	if (strcmp(path, "wx") == 0) {
		affine[0].len = len;
		affine[0].value = malloc(len);
		memcpy(affine[0].value, data, len);
		return;
	}
	if (strcmp(path, "wy") == 0) {
		affine[1].len = len;
		affine[1].value = malloc(len);
		memcpy(affine[1].value, data, len);
		return;
	}
}

static uint8_t cmd_ecdh(uint8_t *data, uint16_t len) {
	//perform ECDH with provided point (and current privkey), output shared secret
	{{ start_action("ecdh") }}
	point_t *other = point_new();
	fat_t affine[2] = {fat_empty, fat_empty};
	parse_data(data, len, "", parse_ecdh, (void *) affine);
	bn_t ox; bn_init(&ox);
	bn_t oy; bn_init(&oy);
	bn_from_bin(affine[0].value, affine[0].len, &ox);
	bn_from_bin(affine[1].value, affine[1].len, &oy);

	point_from_affine(&ox, &oy, curve, other);
	bn_clear(&ox);
	bn_clear(&oy);
	free(affine[0].value);
	free(affine[1].value);

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
	bn_clear(&x);
	bn_clear(&y);
	point_free(result);
	point_free(other);
	{{ end_action("ecdh") }}

	simpleserial_put('r', h_size, h_out);
	return 0;
}

static void parse_ecdsa_msg(const char *path, const uint8_t *data, size_t len, void *arg) {
	fat_t *dest = (fat_t *) arg;
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
	{{ start_action("ecdsa_sign") }}
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
	// r = ([k]G).x mod n

	bn_t s; bn_init(&s);
	bn_copy(&privkey, &s);
	// s = x
	bn_mod_mul(&s, &r, &curve->n, &s);
	// s = rx mod n
	bn_mod_add(&s, &h, &curve->n, &s);
	// s = rx + H(m) mod n
	bn_mod_div(&s, &k, &curve->n, &s);
	// s = k^(-1)*(rx + H(m)) mod n

	size_t result_len = 0;
	uint8_t *result = asn1_der_encode(&r, &s, &result_len);
	{{ end_action("ecdsa_sign") }}

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
	{{ start_action("ecdsa_verify") }}
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
	{{ end_action("ecdsa_verify") }}

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

static uint8_t cmd_debug(uint8_t *data, uint16_t len) {
	char *debug_string = "{{ ','.join((model.shortname, coords.name))}}";
	size_t debug_len = strlen(debug_string);

	simpleserial_put('r', len, data);

	simpleserial_put('d', debug_len, (uint8_t *) debug_string);
	return 0;
}

static uint8_t cmd_set_trigger(uint8_t *data, uint16_t len) {
	uint32_t vector = data[0] | data[1] << 8 | data[2] << 16 | data[3] << 24;
	action_set(vector);

	return 0;
}

int main(void) {
	platform_init();
    init_uart();
    trigger_setup();

    prng_init();
    formulas_init();

    curve = curve_new();
    pubkey = point_new();
    bn_init(&privkey);

    simpleserial_init();
    simpleserial_addcmd('i', MAX_SS_LEN, cmd_init_prng);
    simpleserial_addcmd('c', MAX_SS_LEN, cmd_set_params);
    {%- if keygen %}
    	simpleserial_addcmd('g', 0, cmd_generate);
    {%- endif %}
    simpleserial_addcmd('s', MAX_SS_LEN, cmd_set_privkey);
    simpleserial_addcmd('w', MAX_SS_LEN, cmd_set_pubkey);
    simpleserial_addcmd('m', MAX_SS_LEN, cmd_scalar_mult);
    {%- if ecdh %}
    	simpleserial_addcmd('e', MAX_SS_LEN, cmd_ecdh);
    {%- endif %}
    {%- if ecdsa %}
    	simpleserial_addcmd('a', MAX_SS_LEN, cmd_ecdsa_sign);
    	simpleserial_addcmd('r', MAX_SS_LEN, cmd_ecdsa_verify);
    {%- endif %}
    simpleserial_addcmd('t', MAX_SS_LEN, cmd_set_trigger);
    simpleserial_addcmd('d', MAX_SS_LEN, cmd_debug);

	led_ok(1);
    while(simpleserial_get());
    led_ok(0);

    bn_clear(&privkey);
    curve_free(curve);
    point_free(pubkey);
    formulas_clear();
    return 0;
}