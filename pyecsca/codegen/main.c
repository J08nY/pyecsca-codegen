#include <stdint.h>
#include <stdlib.h>

#include "hal/hal.h"
#include "simpleserial/simpleserial.h"
#include "hash/hash.h"

uint8_t cmd_set_curve(uint8_t *data, uint16_t len) {
    return 0;
}

int main(void) {
    platform_init();
    init_uart();
    trigger_setup();
    simpleserial_init();
    void *ctx = hash_new_ctx();
    uint8_t thing[10] = {1,2,3,4,5,6,7,8,9,10};
    uint8_t out[hash_size(10)];
    hash_init(ctx);
    hash_final(ctx, 10, thing, out);
    simpleserial_addcmd('a', 256, cmd_set_curve);
    while(1)
        simpleserial_get();
    return 0;
}