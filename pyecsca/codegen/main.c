#include <stdint.h>
#include <stdlib.h>

#include "hal/hal.h"
#include "simpleserial/simpleserial.h"
#include "hash/hash.h"
#include "bn.h"
#include "prng.h"
#include <string.h>

uint8_t cmd_init_prng(uint8_t *data, uint16_t len) {
    prng_seed(data, len);
    return 0;
}

int main(void) {
    platform_init();
    prng_init();
    init_uart();
    trigger_setup();
    simpleserial_init();
    simpleserial_addcmd('i', 4, cmd_init_prng);
    while(1)
        simpleserial_get();
    return 0;
}