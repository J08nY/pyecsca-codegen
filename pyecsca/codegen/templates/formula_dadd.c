#include "point.h"
#include "action.h"
#include "hal/hal.h"
{% import "ops.c" as ops %}
{% from "action.c" import start_action, end_action %}

{{ ops.render_static_init(allocations, formula.shortname) }}

{{ ops.render_static_zero(allocations, formula.shortname) }}

{{ ops.render_static_clear(frees, formula.shortname) }}

__attribute__((noinline)) void point_dadd(const point_t *one, const point_t *other, const point_t *diff, const curve_t *curve, point_t *out_one) {
	{{ start_action("dadd") }}
	//NOP_128();
	// TODO: short-circuits
	{{ ops.render_initializations(initializations) }}
	{{ ops.render_ops(operations) }}
	{{ ops.render_returns(returns) }}
	//NOP_128();
	{{ end_action("dadd") }}
}
