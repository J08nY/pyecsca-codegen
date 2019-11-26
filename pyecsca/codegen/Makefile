TARGET = pyecsca-codegen

SRC += main.c bn.c ecdh.c ecdsa.c asn1.c hash/hash.c mult/mult.c prng/prng.c

CDEFS += -DHASH=HASH_SHA224

MKDIR_LIST += hash prng mult

EXTRAINCDIRS += hash prng mult ../../ext/libtommath/

LDFLAGS += ../../ext/libtommath/libtommath.a

include simpleserial/Makefile.simpleserial

FIRMWAREPATH = .
include Makefile.inc
