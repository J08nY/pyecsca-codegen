export

all: help

help:
	@echo "Build the tommath library for use with targets."

clean:
	$(MAKE) -C libtommath clean

TOMMATH_DIR?=../pyecsca/codegen/tommath

tommath_dir:
	mkdir -p $(TOMMATH_DIR)

tommath_headers: tommath_dir
	cp -u libtommath/*.h $(TOMMATH_DIR)

host: LIBNAME=libtommath-HOST.a
host: CFLAGS=-DMP_NO_DEV_URANDOM -DMP_LOW_MEM -DMP_DEFAULT_DIGIT_COUNT=10 -DMP_MIN_DIGIT_COUNT=10
host: COMPILE_SIZE=1
host: COMPILE_LTO=1
host: tommath_dir tommath_headers
	$(MAKE) -C libtommath clean
	$(MAKE) -C libtommath
	cp -u libtommath/$(LIBNAME) $(TOMMATH_DIR)/$(LIBNAME)

nano: CROSS_COMPILE=arm-none-eabi-
nano: CFLAGS=-mcpu=cortex-m0 -mthumb -mfloat-abi=soft -ffunction-sections -DMP_NO_DEV_URANDOM -DMP_32BIT -DMP_LOW_MEM -DMP_DEFAULT_DIGIT_COUNT=10 -DMP_MIN_DIGIT_COUNT=10
nano: LDFLAGS=--specs=nano.specs --specs=nosys.specs -T ../pyecsca/codegen/hal/stm32f0_nano/LinkerScript.ld -Wl,--gc-sections -lm -mthumb -mcpu=cortex-m0
nano: COMPILE_SIZE=1
nano: COMPILE_LTO=1
nano: LIBNAME=libtommath-CWNANO.a
nano: tommath_dir tommath_headers
	$(MAKE) -C libtommath clean
	$(MAKE) -C libtommath
	cp -u libtommath/$(LIBNAME) $(TOMMATH_DIR)/$(LIBNAME)

stm32f0: CROSS_COMPILE=arm-none-eabi-
stm32f0: CFLAGS=-mcpu=cortex-m0 -mthumb -mfloat-abi=soft -ffunction-sections -DMP_NO_DEV_URANDOM -DMP_32BIT -DMP_LOW_MEM -DMP_DEFAULT_DIGIT_COUNT=10 -DMP_MIN_DIGIT_COUNT=10
stm32f0: LDFLAGS=--specs=nano.specs --specs=nosys.specs -T ../pyecsca/codegen/hal/stm32f0/LinkerScript.ld -Wl,--gc-sections -lm -mthumb -mcpu=cortex-m0
stm32f0: COMPILE_SIZE=1
stm32f0: COMPILE_LTO=1
stm32f0: LIBNAME=libtommath-CW308_STM32F0.a
stm32f0: tommath_dir tommath_headers
	$(MAKE) -C libtommath clean
	$(MAKE) -C libtommath
	cp -u libtommath/$(LIBNAME) $(TOMMATH_DIR)/$(LIBNAME)

stm32f3: CROSS_COMPILE=arm-none-eabi-
stm32f3: CFLAGS=-mcpu=cortex-m4 -mthumb -mfloat-abi=soft -mfpu=fpv4-sp-d16 -fmessage-length=0 -ffunction-sections -DMP_NO_DEV_URANDOM -DMP_32BIT -DMP_LOW_MEM -DMP_DEFAULT_DIGIT_COUNT=10 -DMP_MIN_DIGIT_COUNT=10
stm32f3: LDFLAGS=--specs=nano.specs -T ../pyecsca/codegen/hal/stm32f3/LinkerScript.ld -Wl,--gc-sections -lm -mthumb -mcpu=cortex-m4
stm32f3: COMPILE_SIZE=1
stm32f3: COMPILE_LTO=1
stm32f3: LIBNAME=libtommath-CW308_STM32F3.a
stm32f3: tommath_dir tommath_headers
	$(MAKE) -C libtommath clean
	$(MAKE) -C libtommath
	cp -u libtommath/$(LIBNAME) $(TOMMATH_DIR)/$(LIBNAME)

.PHONY: all host nano stm32f0 stm32f3 tommath_dir tommath_headers help clean
