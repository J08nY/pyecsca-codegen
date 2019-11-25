TARGET = pyecsca-codegen

SRC += main.c bn.c ecdh.c ecdsa.c hash/hash.c prng/prng.c

CDEFS += -DHASH=HASH_SHA224

MKDIR_LIST += hash prng

EXTRAINCDIRS += hash prng ../../ext/libtommath/

LDFLAGS += ../../ext/libtommath/libtommath.a

include simpleserial/Makefile.simpleserial

FIRMWAREPATH = .
include Makefile.inc
