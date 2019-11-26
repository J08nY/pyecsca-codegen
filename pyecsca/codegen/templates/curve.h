typedef struct {
	bn_t p;
    {%- for param in params %}
    bn_t {{ param }};
    {%- endfor %}
    bn_t n;
    bn_t h;
    point_t neutral;
} curve_t;