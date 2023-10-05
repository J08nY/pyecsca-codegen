
{%- if isinstance(scalarmult, LTRMultiplier) -%}

	{% include "mult_ltr.c" %}

{%- elif isinstance(scalarmult, RTLMultiplier) -%}

	{% include "mult_rtl.c" %}

{%- elif isinstance(scalarmult, CoronMultiplier) -%}

	{% include "mult_coron.c" %}

{%- elif isinstance(scalarmult, LadderMultiplier) -%}

	{% include "mult_ldr.c" %}

{%- elif isinstance(scalarmult, SimpleLadderMultiplier) -%}

	{% include "mult_simple_ldr.c" %}

{%- elif isinstance(scalarmult, DifferentialLadderMultiplier) -%}

	{% include "mult_diff_ldr.c" %}

{%- elif isinstance(scalarmult, BinaryNAFMultiplier) -%}

	{% include "mult_bnaf.c" %}

{%- elif isinstance(scalarmult, WindowNAFMultiplier) -%}

    {% include "mult_wnaf.c" %}

{%- elif isinstance(scalarmult, SlidingWindowMultiplier) -%}

    {% include "mult_sliding_w.c" %}

{%- elif isinstance(scalarmult, FixedWindowLTRMultiplier) -%}

    {% include "mult_fixed_w.c" %}

{%- endif %}


#include "action.h"
{% from "action.c" import start_action, end_action %}

void scalar_mult(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	{{ start_action("mult") }}
	scalar_mult_inner(scalar, point, curve, out);
	{{ end_action("mult") }}
}