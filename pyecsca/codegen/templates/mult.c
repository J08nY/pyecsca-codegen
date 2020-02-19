
#include "mult.h"

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
{%- endif -%}
