TARGET = pyecsca-codegen

SRC += main.c bn/bn.c asn1/asn1.c hash/hash.c mult/mult.c prng/prng.c

CDEFS += -DHASH=HASH_SHA224 -DMOD_RAND=MOD_RAND_SAMPLE

MKDIR_LIST += hash prng mult asn1 bn

EXTRAINCDIRS += hash prng mult asn1 bn ../../ext/libtommath/

LDFLAGS += ../../ext/libtommath/libtommath.a

include simpleserial/Makefile.simpleserial

FIRMWAREPATH = .
include Makefile.inc
