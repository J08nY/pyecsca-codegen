TARGET = pyecsca-codegen

SRC += main.c bn/bn.c asn1/asn1.c hash/hash.c mult/mult.c prng/prng.c gen/point.c gen/curve.c

PLATFORM = {{ platform }}

CDEFS += -DHASH={{ hash_type }} -DMULT={{ mult_algo }} -DMOD_RAND={{ mod_rand }}

MKDIR_LIST += hash prng mult asn1 bn gen

EXTRAINCDIRS += hash prng mult asn1 bn gen tommath

LDFLAGS += tommath/libtommath-{{ platform }}.a

include simpleserial/Makefile.simpleserial

FIRMWAREPATH = .
include Makefile.inc
