TARGET = pyecsca-codegen

SRC += main.c ecdh.c ecdsa.c hash/hash.c

CDEFS += -DHASH=HASH_SHA1

MKDIR_LIST += hash

EXTRAINCDIRS += hash

include simpleserial/Makefile.simpleserial

FIRMWAREPATH = .
include Makefile.inc
