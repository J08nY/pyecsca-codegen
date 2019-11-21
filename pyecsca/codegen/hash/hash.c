
#include "hash.h"

#if HASH == HASH_NONE
#include "none.c"
#elif HASH == HASH_SHA1
#include "sha1.c"
#elif HASH == HASH_SHA224 || HASH == HASH_SHA256 || HASH == HASH_SHA384 || HASH == HASH_SHA512
#include "sha2.c"
#endif