#ifndef STM32F0_HAL_H
#define STM32F0_HAL_H
#include <stdbool.h>

void init_uart(void);
void putch(char c);
char getch(void);
#define flush()

void trigger_setup(void);
void trigger_low(void);
bool trigger_status(void);
void trigger_flip(void);
void trigger_high(void);

void led_error(unsigned int status);
void led_ok(unsigned int status);

#endif // STM32F0_HAL_H
