#include "uart.h"

void init_uart0(void) {}

char input_ch_0(void) { return getchar(); }

void output_ch_0(char data) { putchar(data); }