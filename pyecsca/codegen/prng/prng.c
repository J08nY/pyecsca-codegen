#include "KeccakPRG.h"
#include "KeccakP-200-compact.c"
#include "KeccakDuplexWidth200.c"
#include "KeccakPRGWidth200.c"
#include "prng.h"
#include <tommath.h>


static KeccakWidth200_SpongePRG_Instance keccak;

mp_err prng_mp_rand(void *out, size_t size) {
    return (prng_get(out, size) == 0) ? MP_OKAY : MP_ERR;
}

void prng_init(void) {
    KeccakWidth200_SpongePRG_Initialize(&keccak, 70);
    mp_rand_source(&prng_mp_rand);
}

int prng_get(uint8_t *out, size_t size) {
    return KeccakWidth200_SpongePRG_Fetch(&keccak, out, size);
}

void prng_seed(const uint8_t *seed, size_t size) {
    KeccakWidth200_SpongePRG_Feed(&keccak, seed, size);
    KeccakWidth200_SpongePRG_Forget(&keccak);
}

