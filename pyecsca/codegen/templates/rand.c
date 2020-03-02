#include "rand.h"
#include "action.h"
{% from "action.c" import start_action, end_action %}

bn_err bn_rand_mod(bn_t *out, const bn_t *mod) {
	{{ start_action("random_mod") }}

	#if MOD_RAND == MOD_RAND_SAMPLE
		bn_err err = bn_rand_mod_sample(out, mod);
	#elif MOD_RAND == MOD_RAND_REDUCE
		bn_err err = bn_rand_mod_reduce(out, mod);
	#endif

	{{ end_action("random_mod") }}
	return err;
}