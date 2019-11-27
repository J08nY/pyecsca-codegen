#ifndef DEFS_H_
#define DEFS_H_

#include "bn.h"

typedef struct {
	{%- for variable in variables %}
	bn_t {{ variable }};
	{%- endfor %}
} point_t;

typedef struct {
	bn_t p;
    {%- for param in params %}
    bn_t {{ param }};
    {%- endfor %}
    bn_t n;
    bn_t h;
    point_t *generator;
    point_t *neutral;
} curve_t;

#endif //DEFS_H_