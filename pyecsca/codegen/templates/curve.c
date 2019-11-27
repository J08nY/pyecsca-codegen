#include "curve.h"
#include "point.h"
#include <stdlib.h>

curve_t* curve_new(void) {
	curve_t *result = malloc(sizeof(curve_t));
	{%- for param in params + ["p", "n", "h"] %}
	bn_init(&result->{{ param }});
	{%- endfor %}
	result->generator = point_new();
	result->neutral = point_new();

	return result;
}

void curve_free(curve_t *curve) {
	{%- for param in params + ["p", "n", "h"] %}
	bn_clear(&curve->{{ param }});
	{%- endfor %}
	if (curve->generator) {
		point_free(curve->generator);
	}
	if (curve->neutral) {
		point_free(curve->neutral);
	}
	free(curve);
}

void curve_set_param(curve_t *curve, char name, const bn_t *value) {
	switch (name) {
	{%- for param in params + ["p", "n", "h"] %}
		case '{{ param }}': bn_copy(value, &curve->{{ param }});
							break;
	{%- endfor %}
	}
}