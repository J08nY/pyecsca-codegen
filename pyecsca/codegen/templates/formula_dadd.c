#include "point.h"
{% import "ops.c" as ops %}

{{ ops.render_static_init(allocations, initializations, formula.shortname) }}

{{ ops.render_static_clear(frees, formula.shortname) }}

void point_dadd(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out_one) {
	// TODO: short-circuits
	{{ ops.render_ops(operations) }}
	{{ ops.render_returns(returns) }}
}
