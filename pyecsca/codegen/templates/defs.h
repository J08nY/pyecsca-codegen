#ifndef DEFS_H_
#define DEFS_H_

#include <stdlib.h>
#include "bn.h"

typedef struct {
	{%- for variable in variables %}
	bn_t {{ variable }};
	{%- endfor %}
	bool infinity;
} point_t;

typedef struct {
	bn_t p;
	red_t p_red;
    {%- for param in params %}
    bn_t {{ param }};
    {%- endfor %}
    bn_t n;
    red_t n_red;
    bn_t h;
    point_t *generator;
    point_t *neutral;
} curve_t;

#endif //DEFS_H_