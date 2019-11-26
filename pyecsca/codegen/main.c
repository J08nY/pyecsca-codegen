#include <stdint.h>
#include <stdlib.h>

#include "hal/hal.h"
#include "simpleserial/simpleserial.h"
#include "hash/hash.h"
#include "bn.h"
#include "prng.h"
#include "defs.h"
#include <stdlib.h>

static point_t *pubkey;
static bn_t privkey;

static curve_t *curve;

static uint8_t cmd_init_prng(uint8_t *data, uint16_t len) {
    prng_seed(data, len);
    return 0;
}

static uint8_t cmd_set_curve(uint8_t *data, uint16_t len) {
	// need p, [params], gx, gy, n
	return 0;
}

static uint8_t cmd_generate(uint8_t *data, uint16_t len) {
	// generate a keypair, export privkey and affine pubkey
	return 0;
}

static uint8_t cmd_set_privkey(uint8_t *data, uint16_t len) {
	// set the current privkey
	return 0;
}

static uint8_t cmd_set_pubkey(uint8_t *data, uint16_t len) {
	// set the current pubkey
	return 0;
}

static uint8_t cmd_scalar_mult(uint8_t *data, uint16_t len) {
	// perform base point scalar mult with supplied scalar, return affine point.
	return 0;
}

static uint8_t cmd_ecdh(uint8_t *data, uint16_t len) {
	//perform ECDH with provided point (and current privkey), output shared secret
	return 0;
}

static uint8_t cmd_ecdsa_sign(uint8_t *data, uint16_t len) {
	//perform ECDSA signature on supplied data, output signature
	return 0;
}

static uint8_t cmd_ecdsa_verify(uint8_t *data, uint16_t len) {
	//perform ECDSA verification on supplied data (and current pubkey), output status
	return 0;
}

int main(void) {
    platform_init();
    prng_init();
    init_uart();
    trigger_setup();
    simpleserial_init();
    simpleserial_addcmd('i', 32, cmd_init_prng);
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