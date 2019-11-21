#include "hash.h"

#include <string.h>
#include <stdint.h>

int hash_size(int input_size) {
    return input_size;
}

void *hash_new_ctx(void) {
    return NULL;
}

void hash_init(void *ctx) {

}

void hash_final(void *ctx, int size, const uint8_t *msg, uint8_t *digest) {
    memcpy(digest, msg, size);
}