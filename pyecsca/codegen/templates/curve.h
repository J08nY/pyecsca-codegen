#ifndef CURVE_H_
#define CURVE_H_

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

curve_t* curve_new();

void curve_free(curve_t *curve);

void curve_set_param(curve_t *curve, char name, const bn_t *value);

#endif //CURVE_H_