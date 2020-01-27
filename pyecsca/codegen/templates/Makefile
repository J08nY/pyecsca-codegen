TARGET = pyecsca-codegen

SRC += main.c bn/bn.c asn1/asn1.c hash/hash.c prng/prng.c gen/point.c gen/curve.c gen/mult.c

PLATFORM = {{ platform }}

CDEFS += -DHASH={{ hash_type }} -DMOD_RAND={{ mod_rand }}

MKDIR_LIST += hash prng asn1 bn gen

EXTRAINCDIRS += hash prng asn1 bn gen tommath

LDFLAGS += tommath/libtommath-{{ platform }}.a

include simpleserial/Makefile.simpleserial

FIRMWAREPATH = .
include Makefile.inc