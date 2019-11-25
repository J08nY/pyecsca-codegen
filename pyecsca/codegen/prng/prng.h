#include <stdint.h>

void prng_init(void);

int prng_get(uint8_t *out, size_t size);

void prng_seed(uint8_t *seed, size_t size);

