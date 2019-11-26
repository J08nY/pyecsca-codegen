point_t *point_new(void) {
	point_t *result = malloc(sizeof(point_t));
	{%- for variable in variables %}
	bn_init(&result->{{ variable }});
	{%- endfor %}

	return result;
}

point_t *point_copy(const point_t *from) {
	point_t *result = point_new();
	point_set(from, result);
	return result;
}

void point_set(const point_t *from, point_t *out) {
	{%- for variable in variables %}
	bn_copy(&from->{{ variable }}, &out->{{ variable }});
	{%- endfor %}
}

void point_free(point_t *point) {
	{%- for variable in variables %}
	bn_clear(&point->{{ variable }});
	{%- endfor %}
	free(point);
}

int point_to_affine(point_t *point, const char coord, curve_t *curve, bn_t *out) {
	
}

int point_from_affine(bn_t *x, bn_t *y, curve_t *curve, point_t *out) {

}
