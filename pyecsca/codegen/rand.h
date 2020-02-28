#ifndef RAND_H_
#define RAND_H_

#include "bn/bn.h"

bn_err bn_rand_mod(bn_t *out, const bn_t *mod);

#endif //RAND_H_