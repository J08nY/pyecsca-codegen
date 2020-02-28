#ifndef ACTION_H_
#define ACTION_H_

#include <stdlib.h>

extern uint32_t action_vector;

void action_start(uint32_t action);

void action_end(uint32_t action);

void action_set(uint32_t new_vector);

#endif //ACTION_H_