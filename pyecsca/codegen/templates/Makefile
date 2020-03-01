TARGET = pyecsca-codegen

SRC += main.c bn/bn.c asn1/asn1.c hash/hash.c prng/prng.c $(wildcard gen/*.c)

PLATFORM = {{ platform }}

CDEFS += -DHASH={{ hash_type }} -DMOD_RAND={{ mod_rand }} -DREDUCTION={{ reduction }}

MKDIR_LIST += hash prng asn1 bn gen

EXTRAINCDIRS += hash prng asn1 bn gen tommath

LDFLAGS += tommath/libtommath-{{ platform }}.a

ifeq ($(PLATFORM),CW308_XMEGA)

else ifeq ($(PLATFORM),CW308_STM32F0)
CFLAGS += -DMP_NO_DEV_URANDOM -DMP_32BIT -DMP_LOW_MEM -DMP_PREC=10
else ifeq ($(PLATFORM),CW308_STM32F3)
CFLAGS += -DMP_NO_DEV_URANDOM -DMP_32BIT -DMP_LOW_MEM -DMP_PREC=10
else ifeq ($(PLATFORM),HOST)
CFLAGS += -DMP_NO_DEV_URANDOM -DMP_LOW_MEM -DMP_PREC=10
else
  $(error Invalid or empty PLATFORM: $(PLATFORM). Known platforms: $(KNOWN_PLATFORMS))
endif
include simpleserial/Makefile.simpleserial

FIRMWAREPATH = .
include Makefile.inc
