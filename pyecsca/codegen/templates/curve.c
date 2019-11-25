curve_t* curve_new(const named_bn_t **params, int num_params) {
	curve_t *result = malloc(sizeof(curve_t));
	{%- for param in params %}
	bn_init(&result->{{ param }});
	{%- endfor %}
	bn_init(&result->n);

	for (int i = 0; i < num_params; ++i) {
		switch (params[i]->name) {
			{%- for param in params %}
			case '{{ param }}': bn_copy(params[i]->value, result->{{ param }});
								break;
			{%- endfor %}
			default:
				curve_free(result);
				return NULL;
		}
	}
	return result;
}

void curve_free(curve_t *curve) {
	{%- for param in params %}
	bn_clear(&curve->{{ param }});
	{%- endfor %}
	bn_clear(&curve->n);
	free(curve);
}