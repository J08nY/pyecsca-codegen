#include "point.h"
#include "formulas.h"


void formulas_init(void) {
	{%- for name in names %}
	point_{{ name }}_init();
	{%- endfor %}
}

void formulas_clear(void) {
	{%- for name in names %}
	point_{{ name }}_clear();
	{%- endfor %}
}