/* sha1.c */
/*
    This file was part of the AVR-Crypto-Lib.
    Copyright (C) 2008, 2009  Daniel Otte (daniel.otte@rub.de)
    Copyright (C) 2019  Jan Jancar

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "hash.h"

#include <string.h> /* memcpy & co */
#include <stdint.h>
#include <stdlib.h>
#include "sha1.h"

#ifndef LITTLE_ENDIAN
#define LITTLE_ENDIAN
#endif

/********************************************************************************************************/

static void sha1_init(sha1_ctx_t *state){
	state->h[0] = 0x67452301;
	state->h[1] = 0xefcdab89;
	state->h[2] = 0x98badcfe;
	state->h[3] = 0x10325476;
	state->h[4] = 0xc3d2e1f0;
	state->length = 0;
}

/********************************************************************************************************/
/* some helping functions */
static uint32_t rotl32(uint32_t n, uint8_t bits){
	return ((n<<bits) | (n>>(32-bits)));
}

static uint32_t change_endian32(uint32_t x){
	return (((x)<<24) | ((x)>>24) | (((x)& 0x0000ff00)<<8) | (((x)& 0x00ff0000)>>8));
}

/* three SHA-1 inner functions */
static uint32_t ch(uint32_t x, uint32_t y, uint32_t z){
	return ((x&y)^((~x)&z));
}

static uint32_t maj(uint32_t x, uint32_t y, uint32_t z){
	return ((x&y)^(x&z)^(y&z));
}

uint32_t parity(uint32_t x, uint32_t y, uint32_t z){
	return ((x^y)^z);
}

/********************************************************************************************************/

#define MASK 0x0000000f

typedef uint32_t (*pf_t)(uint32_t x, uint32_t y, uint32_t z);

static void sha1_nextBlock(sha1_ctx_t *state, const void* block){
	uint32_t a[5];
	uint32_t w[16];
	uint32_t temp;
	uint8_t t,s,fi, fib;
	pf_t f[] = {ch,parity,maj,parity};
	uint32_t k[4]={	0x5a827999,
					0x6ed9eba1,
					0x8f1bbcdc,
					0xca62c1d6};

	/* load the w array (changing the endian and so) */
	for(t=0; t<16; ++t){
		w[t] = change_endian32(((uint32_t*)block)[t]);
	}
	/* load the state */
	memcpy(a, state->h, 5*sizeof(uint32_t));


	/* the fun stuff */
	for(fi=0,fib=0,t=0; t<=79; ++t){
		s = t & MASK;
		if(t>=16){
			w[s] = rotl32( w[(s+13)&MASK] ^ w[(s+8)&MASK] ^ w[(s+ 2)&MASK] ^ w[s] ,1);
		}

		uint32_t dtemp;
		temp = rotl32(a[0],5) + (dtemp=f[fi](a[1],a[2],a[3])) + a[4] + k[fi] + w[s];
		memmove(&(a[1]), &(a[0]), 4*sizeof(uint32_t)); /* e=d; d=c; c=b; b=a; */
		a[0] = temp;
		a[2] = rotl32(a[2],30); /* we might also do rotr32(c,2) */
		fib++;
		if(fib==20){
			fib=0;
			fi = (fi+1)%4;
		}
	}

	/* update the state */
	for(t=0; t<5; ++t){
		state->h[t] += a[t];
	}
	state->length += 512;
}

/********************************************************************************************************/

static void sha1_lastBlock(sha1_ctx_t *state, const void* block, uint16_t length){
	uint8_t lb[SHA1_BLOCK_BYTES]; /* local block */
	while(length>=SHA1_BLOCK_BITS){
		sha1_nextBlock(state, block);
		length -= SHA1_BLOCK_BITS;
		block = (uint8_t*)block + SHA1_BLOCK_BYTES;
	}
	state->length += length;
	memset(lb, 0, SHA1_BLOCK_BYTES);
	memcpy (lb, block, (length+7)>>3);

	/* set the final one bit */
	lb[length>>3] |= 0x80>>(length & 0x07);

	if (length>512-64-1){ /* not enouth space for 64bit length value */
		sha1_nextBlock(state, lb);
		state->length -= 512;
		memset(lb, 0, SHA1_BLOCK_BYTES);
	}
	/* store the 64bit length value */
#if defined LITTLE_ENDIAN
	 	/* this is now rolled up */
	uint8_t i;
	for (i=0; i<8; ++i){
		lb[56+i] = ((uint8_t*)&(state->length))[7-i];
	}
#elif defined BIG_ENDIAN
	*((uint64_t)&(lb[56])) = state->length;
#endif
	sha1_nextBlock(state, lb);
}

/********************************************************************************************************/

static void sha1_ctx2hash (void *dest, sha1_ctx_t *state){
#if defined LITTLE_ENDIAN
	uint8_t i;
	for(i=0; i<5; ++i){
		((uint32_t*)dest)[i] = change_endian32(state->h[i]);
	}
#elif BIG_ENDIAN
	if (dest != state->h)
		memcpy(dest, state->h, SHA1_HASH_BITS/8);
#else
# error unsupported endian type!
#endif
}

/********************************************************************************************************/

int hash_size(int input_size) {
    return 20;
}

void *hash_new_ctx(void) {
    return malloc(sizeof(sha1_ctx_t));
}

void hash_init(void *ctx) {
	sha1_init((sha1_ctx_t*) ctx);
}

void hash_final(void *ctx, int size, const uint8_t *msg, uint8_t *digest) {
	uint32_t length = size * 8;
	while(length & (~0x0001ff)){ /* length>=512 */
		sha1_nextBlock(ctx, msg);
		msg = (uint8_t*)msg + SHA1_BLOCK_BITS/8; /* increment pointer to next block */
		length -= SHA1_BLOCK_BITS;
	}
	sha1_lastBlock(ctx, msg, length);
	sha1_ctx2hash(digest, ctx);
}

void hash_free_ctx(void *ctx) {
	free(ctx);
}
