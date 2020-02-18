#include "uart.h"

void init_uart0(void) {}

int input_ch_0(void) { return getchar(); }

void output_ch_0(char data) { putchar(data); }

void flush_ch_0(void) { fflush(stdout); }