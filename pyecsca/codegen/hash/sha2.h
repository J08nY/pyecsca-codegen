/* sha2.h */
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

#ifndef SHA2_H_
#define SHA2_H_

typedef struct {
	uint64_t h[8];
	uint32_t length;
} sha2_large_common_ctx_t;

typedef struct {
	uint32_t h[8];
	uint32_t length;
} sha2_small_common_ctx_t;

#if HASH == HASH_SHA224
    #define SHA2_SIZE 28
    #define SHA2_j 7
    #define SHA2_HASH_BITS  224
    #define SHA2_HASH_BYTES (SHA2_HASH_BITS/8)
    #define SHA2_BLOCK_BITS 512
    #define SHA2_BLOCK_BYTES (SHA2_BLOCK_BITS/8)
    #define sha2_ctx_t sha2_small_common_ctx_t
    #define SHA2_STATE_BYTES 32
#elif HASH == HASH_SHA256
    #define SHA2_SIZE 32
    #define SHA2_j 8
    #define SHA2_HASH_BITS  256
    #define SHA2_HASH_BYTES (SHA2_HASH_BITS/8)
    #define SHA2_BLOCK_BITS 512
    #define SHA2_BLOCK_BYTES (SHA2_BLOCK_BITS/8)
    #define sha2_ctx_t sha2_small_common_ctx_t
    #define SHA2_STATE_BYTES 32
#elif HASH == HASH_SHA384
    #define SHA2_SIZE 48
    #define SHA2_i 6
    #define SHA2_HASH_BITS  384
    #define SHA2_HASH_BYTES (SHA2_HASH_BITS/8)
    #define SHA2_BLOCK_BITS 1024
    #define SHA2_BLOCK_BYTES (SHA2_BLOCK_BITS/8)
    #define sha2_ctx_t sha2_large_common_ctx_t
    #define SHA2_STATE_BYTES 64
#elif HASH == HASH_SHA512
    #define SHA2_SIZE 64
    #define SHA2_i 8
    #define SHA2_HASH_BITS  512
    #define SHA2_HASH_BYTES (SHA2_HASH_BITS/8)
    #define SHA2_BLOCK_BITS 1024
    #define SHA2_BLOCK_BYTES (SHA2_BLOCK_BITS/8)
    #define sha2_ctx_t sha2_large_common_ctx_t
    #define SHA2_STATE_BYTES 64
#endif

#endif /* SHA2_H_ */
