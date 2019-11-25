#include "bn.h"

bn_err bn_init(bn_t *bn) {
    return mp_init(bn);
}

void bn_clear(bn_t *bn) {
    mp_clear(bn);
}