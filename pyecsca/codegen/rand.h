#ifndef RAND_H_
#define RAND_H_

#include "bn/bn.h"

#define MOD_RAND_SAMPLE 1
#define MOD_RAND_REDUCE 2

bn_err bn_rand_mod(bn_t *out, const bn_t *mod);

#endif //RAND_H_