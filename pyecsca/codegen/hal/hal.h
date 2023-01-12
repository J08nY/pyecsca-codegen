/*
    This file was taken from the ChipWhisperer Example Target base.
    Copyright (C) 2012-2015 NewAE Technology Inc.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef HAL_H_
#define HAL_H_

void platform_init(void);

#define HAL_xmega   1
#define HAL_stm32f0 2
#define HAL_stm32f0_nano 3
#define HAL_stm32f3 4
#define HAL_host    5

#if HAL == HAL_xmega
    #include <avr/io.h>
    #include <util/delay.h>
    #include "xmega/xmega_hal.h"
    #include "xmega/avr_compiler.h"
#elif HAL == HAL_stm32f0
    #include "stm32f0/stm32f0_hal.h"
#elif HAL == HAL_stm32f0_nano
    #include "stm32f0/stm32f0_hal.h"
#elif HAL == HAL_stm32f3
    #include "stm32f3/stm32f3_hal.h"
#elif HAL == HAL_host
    #include "host/host_hal.h"
#else
    #error "Unsupported HAL Type"
#endif


#ifndef NO_NOP
	#define NOP() __asm__ __volatile__ ("nop");
#else
	#define NOP()
#endif

#define _2(a) a;a
#define NOP_2() _2(NOP())
#define NOP_4() _2(_2(NOP()))
#define NOP_8() _2(_2(_2(NOP())))
#define NOP_16() _2(_2(_2(_2(NOP()))))
#define NOP_32() _2(_2(_2(_2(_2(NOP())))))
#define NOP_64() _2(_2(_2(_2(_2(_2(NOP()))))))
#define NOP_128() _2(_2(_2(_2(_2(_2(_2(NOP())))))))
#define NOP_256() _2(_2(_2(_2(_2(_2(_2(_2(NOP()))))))))
#define NOP_512() _2(_2(_2(_2(_2(_2(_2(_2(_2(NOP())))))))))

#endif //HAL_H_
