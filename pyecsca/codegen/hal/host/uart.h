#ifndef UART_H_
#define UART_H_

#include <stdio.h>


void init_uart0(void);

int input_ch_0(void);

void output_ch_0(char data);

void flush_ch_0(void);

#endif //UART_H_