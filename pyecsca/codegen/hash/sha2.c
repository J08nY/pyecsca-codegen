/* sha2.c */
/*
    This file was part of the AVR-Crypto-Lib.
    Copyright (C) 2011 Daniel Otte (daniel.otte@rub.de)
    Copyright (C) 2019 Jan Jancar

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

#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include "sha2.h"

#if HASH == HASH_SHA224
    static const uint32_t init_vector[] = {
        0xc1059ed8, 0x367cd507, 0x3070dd17, 0xf70e5939,
        0xffc00b31, 0x68581511, 0x64f98fa7, 0xbefa4fa4
        };
#elif HASH == HASH_SHA256
    static const uint32_t init_vector[] = {
        0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
        0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19
        };
#elif HASH == HASH_SHA384
    static const uint64_t init_vector[8] = {
        0xcbbb9d5dc1059ed8, 0x629a292a367cd507, 0x9159015a3070dd17, 0x152fecd8f70e5939,
        0x67332667ffc00b31, 0x8eb44a8768581511, 0xdb0c2e0d64f98fa7, 0x47b5481dbefa4fa4
        };
#elif HASH == HASH_SHA512
    static const uint64_t init_vector[8] = {
        0x6a09e667f3bcc908, 0xbb67ae8584caa73b, 0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1,
        0x510e527fade682d1, 0x9b05688c2b3e6c1f, 0x1f83d9abfb41bd6b, 0x5be0cd19137e2179
        };
#endif

#define CH(x,y,z)  (((x)&(y)) ^ ((~(x))&(z)))
#define MAJ(x,y,z) (((x)&(y)) ^ ((x)&(z)) ^ ((y)&(z)))

#define LITTLE_ENDIAN

#if HASH == HASH_SHA224 || HASH == HASH_SHA256
    #define SIGMA_0(x) (rotr32((x), 2) ^ rotr32((x),13) ^ rotl32((x),10))
    #define SIGMA_1(x) (rotr32((x), 6) ^ rotr32((x),11) ^ rotl32((x),7))
    #define SIGMA_a(x) (rotr32((x), 7) ^ rotl32((x),14) ^ ((x)>>3))
    #define SIGMA_b(x) (rotl32((x),15) ^ rotl32((x),13) ^ ((x)>>10))
#elif HASH == HASH_SHA384 || HASH == HASH_SHA512
    #define SIGMA_0(x) (rotr64((x), 28) ^ rotl64((x), 30) ^ rotl64((x), 25))
    #define SIGMA_1(x) (rotr64((x), 14) ^ rotr64((x), 18) ^ rotl64((x), 23))
    #define SIGMA_a(x) (rotr64((x),  1) ^ rotr64((x),  8) ^ ((x)>>7))
    #define SIGMA_b(x) (rotr64((x), 19) ^ rotl64((x),  3) ^ ((x)>>6))
#endif

static void sha2_init(sha2_ctx_t* ctx){
	ctx->length = 0;
	memcpy(ctx->h, init_vector, SHA2_STATE_BYTES);
}

/**************************************************************************************************/

#if HASH == HASH_SHA224 || HASH == HASH_SHA256

    /**
     * rotate x right by n positions
     */
    static uint32_t rotr32( uint32_t x, uint8_t n){
        return ((x>>n) | (x<<(32-n)));
    }

    static uint32_t rotl32( uint32_t x, uint8_t n){
        return ((x<<n) | (x>>(32-n)));
    }

    static uint32_t change_endian32(uint32_t x){
        return (((x)<<24) | ((x)>>24) | (((x)& 0x0000ff00)<<8) | (((x)& 0x00ff0000)>>8));
    }

    /* sha256 functions as macros for speed and size, cause they are called only once */

    static const uint32_t sha2_small_common_const[] = {
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    };


    static void sha2_nextBlock(sha2_small_common_ctx_t *state, const void* block){
        uint32_t w[16], wx;
        uint8_t  i;
        uint32_t a[8],t1,t2;

        /* init w */
    #if defined LITTLE_ENDIAN
        for (i=0; i<16; ++i){
            w[i]= change_endian32(((uint32_t*)block)[i]);
        }
    #elif defined BIG_ENDIAN
            memcpy((void*)w, block, 64);
    #endif
	    /*
	        for (i=16; i<64; ++i){
	            w[i] = SIGMA_b(w[i-2]) + w[i-7] + SIGMA_a(w[i-15]) + w[i-16];
	        }
	    */
	    /* init working variables */
        memcpy((void*)a,(void*)(state->h), 8*4);

	    /* do the, fun stuff, */
        for (i=0; i<64; ++i){
            if(i<16){
                wx = w[i];
            }else{
                wx = SIGMA_b(w[14]) + w[9] + SIGMA_a(w[1]) + w[0];
                memmove(&(w[0]), &(w[1]), 15*4);
                w[15] = wx;
            }
            t1 = a[7] + SIGMA_1(a[4]) + CH(a[4],a[5],a[6]) + sha2_small_common_const[i] + wx;
            t2 = SIGMA_0(a[0]) + MAJ(a[0],a[1],a[2]);
            memmove(&(a[1]), &(a[0]), 7*4); 	/* a[7]=a[6]; a[6]=a[5]; a[5]=a[4]; a[4]=a[3]; a[3]=a[2]; a[2]=a[1]; a[1]=a[0]; */
            a[4] += t1;
            a[0] = t1 + t2;
        }

	    /* update, the, state, */
        for (i=0; i<8; ++i){
            state->h[i] += a[i];
        }
        state->length += 1;
    }

    static void sha2_lastBlock(sha2_small_common_ctx_t *state, const void* block, uint16_t length_b){
        uint8_t lb[512/8]; /* local block */
        uint64_t len;
        while(length_b>=512){
            sha2_nextBlock(state, block);
            length_b -= 512;
            block = (uint8_t*)block+64;
        }
        len = state->length*512 + length_b;
        memset(lb, 0, 64);
        memcpy(lb, block, (length_b+7)/8);

        /* set the final one bit */
        lb[length_b/8] |= 0x80>>(length_b & 0x7);
        /* pad with zeros */
        if (length_b>=512-64){ /* not enouth space for 64bit length value */
            sha2_nextBlock(state, lb);
            memset(lb, 0, 64);
        }
        /* store the 64bit length value */
    #if defined LITTLE_ENDIAN
        /* this is now rolled up */
        uint8_t i;
        i=7;
        do{
            lb[63-i] = ((uint8_t*)&len)[i];
        }while(i--);
    #elif defined BIG_ENDIAN
        *((uint64_t)&(lb[56])) = len;
    #endif
        sha2_nextBlock(state, lb);
    }

    static void sha2_ctx2hash(void* dest, const sha2_small_common_ctx_t *state){
    #if defined LITTLE_ENDIAN
        uint8_t i, j, *s=(uint8_t*)(state->h);
        i=SHA2_j;
        do{
            j=3;
            do{
                *((uint8_t*)dest) = s[j];
                dest = (uint8_t*)dest + 1;
            }while(j--);
            s += 4;
        }while(--i);
    #elif BIG_ENDIAN
        memcpy(dest, state->h, SHA2_SIZE);
    #else
    # error unsupported endian type!
    #endif
    }

#elif HASH == HASH_SHA384 || HASH == HASH_SHA512

    static const uint64_t sha2_large_common_const[80] = {
	    0x428a2f98d728ae22LL, 0x7137449123ef65cdLL, 0xb5c0fbcfec4d3b2fLL, 0xe9b5dba58189dbbcLL,
	    0x3956c25bf348b538LL, 0x59f111f1b605d019LL, 0x923f82a4af194f9bLL, 0xab1c5ed5da6d8118LL,
	    0xd807aa98a3030242LL, 0x12835b0145706fbeLL, 0x243185be4ee4b28cLL, 0x550c7dc3d5ffb4e2LL,
	    0x72be5d74f27b896fLL, 0x80deb1fe3b1696b1LL, 0x9bdc06a725c71235LL, 0xc19bf174cf692694LL,
	    0xe49b69c19ef14ad2LL, 0xefbe4786384f25e3LL, 0x0fc19dc68b8cd5b5LL, 0x240ca1cc77ac9c65LL,
	    0x2de92c6f592b0275LL, 0x4a7484aa6ea6e483LL, 0x5cb0a9dcbd41fbd4LL, 0x76f988da831153b5LL,
	    0x983e5152ee66dfabLL, 0xa831c66d2db43210LL, 0xb00327c898fb213fLL, 0xbf597fc7beef0ee4LL,
	    0xc6e00bf33da88fc2LL, 0xd5a79147930aa725LL, 0x06ca6351e003826fLL, 0x142929670a0e6e70LL,
	    0x27b70a8546d22ffcLL, 0x2e1b21385c26c926LL, 0x4d2c6dfc5ac42aedLL, 0x53380d139d95b3dfLL,
	    0x650a73548baf63deLL, 0x766a0abb3c77b2a8LL, 0x81c2c92e47edaee6LL, 0x92722c851482353bLL,
	    0xa2bfe8a14cf10364LL, 0xa81a664bbc423001LL, 0xc24b8b70d0f89791LL, 0xc76c51a30654be30LL,
	    0xd192e819d6ef5218LL, 0xd69906245565a910LL, 0xf40e35855771202aLL, 0x106aa07032bbd1b8LL,
	    0x19a4c116b8d2d0c8LL, 0x1e376c085141ab53LL, 0x2748774cdf8eeb99LL, 0x34b0bcb5e19b48a8LL,
	    0x391c0cb3c5c95a63LL, 0x4ed8aa4ae3418acbLL, 0x5b9cca4f7763e373LL, 0x682e6ff3d6b2b8a3LL,
	    0x748f82ee5defb2fcLL, 0x78a5636f43172f60LL, 0x84c87814a1f0ab72LL, 0x8cc702081a6439ecLL,
	    0x90befffa23631e28LL, 0xa4506cebde82bde9LL, 0xbef9a3f7b2c67915LL, 0xc67178f2e372532bLL,
	    0xca273eceea26619cLL, 0xd186b8c721c0c207LL, 0xeada7dd6cde0eb1eLL, 0xf57d4f7fee6ed178LL,
	    0x06f067aa72176fbaLL, 0x0a637dc5a2c898a6LL, 0x113f9804bef90daeLL, 0x1b710b35131c471bLL,
	    0x28db77f523047d84LL, 0x32caab7b40c72493LL, 0x3c9ebe0a15c9bebcLL, 0x431d67c49c100d4cLL,
	    0x4cc5d4becb3e42b6LL, 0x597f299cfc657e2aLL, 0x5fcb6fab3ad6faecLL, 0x6c44198c4a475817LL
    };


    static const uint64_t change_endian64(uint64_t x){
        uint64_t r=0;
        uint8_t i=8;
        do{
            r <<= 8;
            r |= 0xff&x;
            x >>=8;
        }while(--i);
        return r;
    }

    static const uint64_t rotr64(uint64_t x, uint8_t n){
        return (x>>n)|(x<<(64-n));
    }

    static const uint64_t rotl64(uint64_t x, uint8_t n){
        return (x<<n)|(x>>(64-n));
    }

    static void sha2_nextBlock(sha2_large_common_ctx_t *ctx, const void* block){
        uint64_t w[16], wx;
        uint64_t a[8];
        uint64_t t1, t2;
        const uint64_t *k=sha2_large_common_const;
        uint8_t i;
        i=16;
        do{
            w[16-i] = change_endian64(*((const uint64_t*)block));
            block = (uint8_t*)block + 8;
        }while(--i);
        memcpy(a, ctx->h, 8*8);
        for(i=0; i<80; ++i){
            if(i<16){
                wx=w[i];
            }else{
                wx = SIGMA_b(w[14]) + w[9] + SIGMA_a(w[1]) + w[0];
                memmove(&(w[0]), &(w[1]), 15*8);
                w[15] = wx;
            }
            t1 = a[7] + SIGMA_1(a[4]) + CH(a[4], a[5], a[6]) + *k++ + wx;
            t2 = SIGMA_0(a[0]) + MAJ(a[0], a[1], a[2]);
            memmove(&(a[1]), &(a[0]), 7*8);
            a[0] = t1 + t2;
            a[4] += t1;
        }
        i=7;
        do{
            ctx->h[i] += a[i];
        }while(i--);
        ctx->length += 1;
    }

    static void sha2_lastBlock(sha2_large_common_ctx_t *ctx, const void* block, uint16_t length_b){
        while(length_b >= 1024){
            sha2_large_common_nextBlock(ctx, block);
            block = (uint8_t*)block + 1024/8;
            length_b -= 1024;
        }
        uint8_t buffer[1024/8];
        uint64_t len;
        len = ((uint64_t)ctx->length)*1024LL + length_b;
        len = change_endian64(len);
        memset(buffer, 0, 1024/8);
        memcpy(buffer, block, (length_b+7)/8);
        buffer[length_b/8] |= 0x80>>(length_b%8);
        if(length_b>1024-128-1){
            /* length goes into the next block */
            sha2_large_common_nextBlock(ctx, buffer);
            memset(buffer, 0, 120);
        }
        memcpy(&(buffer[128-8]), &len, 8);
        sha2_large_common_nextBlock(ctx, buffer);
    }

    static void sha2_ctx2hash(void* dest, const sha2_large_common_ctx_t* ctx){
        uint8_t i=SHA2_i, j, *s = (uint8_t*)(ctx->h);
        do{
            j=7;
            do{
                *((uint8_t*)dest) = s[j];
                dest = (uint8_t*)dest + 1;
            }while(j--);
            s += 8;
        }while(--i);
    }

#endif

int hash_size(int input_size) {
    return SHA2_SIZE;
}

void* hash_new_ctx(void) {
    return malloc(sizeof(sha2_ctx_t));
}

void hash_init(void* ctx) {
    sha2_init((sha2_ctx_t*)ctx);
}

void hash_final(void* ctx, int size, const uint8_t* msg, uint8_t* digest) {
    int length_b = size * 8;
    while(length_b >= SHA2_BLOCK_BITS){
		sha2_nextBlock(ctx, msg);
		msg = (uint8_t*)msg + SHA2_BLOCK_BYTES;
		length_b -= SHA2_BLOCK_BITS;
	}
	sha2_lastBlock(ctx, msg, length_b);
	sha2_ctx2hash(digest, ctx);
}