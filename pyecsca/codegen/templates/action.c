{% macro start_action(action) %}
	{% if action == "add" %}
		action_start((uint32_t) (1 << 0));
	{% elif action == "dadd" %}
		action_start((uint32_t) (1 << 1));
	{% elif action == "dbl" %}
		action_start((uint32_t) (1 << 2));
	{% elif action == "ladd" %}
		action_start((uint32_t) (1 << 3));
	{% elif action == "neg" %}
		action_start((uint32_t) (1 << 4));
	{% elif action == "scl" %}
		action_start((uint32_t) (1 << 5));
	{% elif action == "tpl" %}
		action_start((uint32_t) (1 << 6));
	{% elif action == "mult" %}
		action_start((uint32_t) (1 << 7));
	{% elif action == "keygen" %}
		action_start((uint32_t) (1 << 8));
	{% elif action == "ecdh" %}
		action_start((uint32_t) (1 << 9));
	{% elif action == "ecdsa_sign" %}
		action_start((uint32_t) (1 << 10));
	{% elif action == "ecdsa_verify" %}
		action_start((uint32_t) (1 << 11));
	{% elif action == "coord_map" %}
		action_start((uint32_t) (1 << 12));
	{% elif action == "random_mod" %}
		action_start((uint32_t) (1 << 13));
	{% endif %}
{%- endmacro %}

{% macro end_action(action) %}
	{% if action == "add" %}
		action_end((uint32_t) (1 << 0));
	{% elif action == "dadd" %}
		action_end((uint32_t) (1 << 1));
	{% elif action == "dbl" %}
		action_end((uint32_t) (1 << 2));
	{% elif action == "ladd" %}
		action_end((uint32_t) (1 << 3));
	{% elif action == "neg" %}
		action_end((uint32_t) (1 << 4));
	{% elif action == "scl" %}
		action_end((uint32_t) (1 << 5));
	{% elif action == "tpl" %}
		action_end((uint32_t) (1 << 6));
	{% elif action == "mult" %}
		action_end((uint32_t) (1 << 7));
	{% elif action == "keygen" %}
		action_end((uint32_t) (1 << 8));
	{% elif action == "ecdh" %}
		action_end((uint32_t) (1 << 9));
	{% elif action == "ecdsa_sign" %}
		action_end((uint32_t) (1 << 10));
	{% elif action == "ecdsa_verify" %}
		action_end((uint32_t) (1 << 11));
	{% elif action == "coord_map" %}
		action_end((uint32_t) (1 << 12));
	{% elif action == "random_mod" %}
		action_end((uint32_t) (1 << 13));
	{% endif %}
{%- endmacro %}

#include "hal/hal.h"
#include <stdint.h>

uint32_t action_vector = 0;

void action_start(uint32_t action) {
	if (action_vector & action) {
		trigger_flip();
	}
}

void action_end(uint32_t action) {
	if (action_vector & action) {
		trigger_flip();
	}
}

void action_set(uint32_t new_vector) {
	action_vector = new_vector;
}
