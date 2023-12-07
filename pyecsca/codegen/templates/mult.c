
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

{%- elif isinstance(scalarmult, FullPrecompMultiplier) -%}

    {% include "mult_precomp.c" %}

{%- elif isinstance(scalarmult, BGMWMultiplier) -%}

    {% include "mult_bgmw.c" %}

{%- elif isinstance(scalarmult, CombMultiplier) -%}

    {% include "mult_comb.c" %}

{%- endif %}

#include "formulas.h"
#include "action.h"
{% from "action.c" import start_action, end_action %}

void scalar_mult(bn_t *scalar, point_t *point, curve_t *curve, point_t *out) {
	{{ start_action("mult") }}
	formulas_zero();
	scalar_mult_inner(scalar, point, curve, out);
	{{ end_action("mult") }}
}