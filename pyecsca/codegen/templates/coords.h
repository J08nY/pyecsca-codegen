typedef struct {
	{%- for variable in variables %}
	bn_t {{ variable }};
	{%- endfor %}
} point_t;