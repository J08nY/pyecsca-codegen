#ifndef HOST_HAL_H_
#define HOST_HAL_H_

#include "uart.h"

#define trigger_setup()
#define trigger_high()
#define trigger_low()

#define init_uart init_uart0
#define putch output_ch_0
#define getch input_ch_0
#define flush flush_ch_0

#define led_error(X)
#define led_ok(X)

#endif //HOST_HAL_H_
