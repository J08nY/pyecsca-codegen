#ifndef HASH_H_
#define HASH_H_

#include <stdint.h>

#define HASH_NONE   0
#define HASH_SHA1   1
#define HASH_SHA224 2
#define HASH_SHA256 3
#define HASH_SHA384 4
#define HASH_SHA512 5

int hash_size(int input_size);

void *hash_new_ctx(void);

void hash_init(void *ctx);

void hash_final(void *ctx, int size, const uint8_t *msg, uint8_t *digest);

#endif //HASH_H_