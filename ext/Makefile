export

all: help

help:
	@echo "Build the tommath library for use with targets."

clean:
	$(MAKE) -C libtommath clean

tommath_dir:
	mkdir -p ../pyecsca/codegen/tommath

host: LIBNAME=libtommath-HOST.a
host: CFLAGS=-DMP_NO_DEV_URANDOM -DMP_LOW_MEM -DMP_PREC=10
host: tommath_dir
	$(MAKE) -C libtommath clean
	$(MAKE) -C libtommath
	cp libtommath/$(LIBNAME) ../pyecsca/codegen/tommath/$(LIBNAME)

stm32f0: CROSS_COMPILE=arm-none-eabi-
stm32f0: CFLAGS=-mcpu=cortex-m0 -mthumb -mfloat-abi=soft -ffunction-sections -DMP_NO_DEV_URANDOM -DMP_32BIT -DMP_LOW_MEM -DMP_PREC=10
stm32f0: LDFLAGS=--specs=nano.specs --specs=nosys.specs -T ../pyecsca/codegen/hal/stm32f0/LinkerScript.ld -Wl,--gc-sections -lm -mthumb -mcpu=cortex-m0
stm32f0: COMPILE_SIZE=1
stm32f0: LIBNAME=libtommath-CW308_STM32F0.a
stm32f0: tommath_dir
	$(MAKE) -C libtommath clean
	$(MAKE) -C libtommath
	cp libtommath/$(LIBNAME) ../pyecsca/codegen/tommath/$(LIBNAME)

stm32f3: CROSS_COMPILE=arm-none-eabi-
stm32f3: CFLAGS=-mcpu=cortex-m4 -mthumb -mfloat-abi=soft -mfpu=fpv4-sp-d16 -fmessage-length=0 -ffunction-sections -DMP_NO_DEV_URANDOM -DMP_32BIT -DMP_LOW_MEM -DMP_PREC=10
stm32f3: LDFLAGS=--specs=nano.specs -T ../pyecsca/codegen/hal/stm32f3/LinkerScript.ld -Wl,--gc-sections -lm -mthumb -mcpu=cortex-m4
stm32f3: COMPILE_SIZE=1
stm32f3: LIBNAME=libtommath-CW308_STM32F3.a
stm32f3: tommath_dir
	$(MAKE) -C libtommath clean
	$(MAKE) -C libtommath
	cp libtommath/$(LIBNAME) ../pyecsca/codegen/tommath/$(LIBNAME)

.PHONY: all host stm32f0 stm32f3 xmega tommath_dir help clean