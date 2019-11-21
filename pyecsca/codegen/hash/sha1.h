/* sha1.h */
/*
    This file was part of the AVR-Crypto-Lib.
    Copyright (C) 2008  Daniel Otte (daniel.otte@rub.de)
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
 
#ifndef SHA1_H_
#define SHA1_H_

#include <stdint.h>
#define SHA1_HASH_BITS  160
#define SHA1_HASH_BYTES (SHA1_HASH_BITS/8)
#define SHA1_BLOCK_BITS 512
#define SHA1_BLOCK_BYTES (SHA1_BLOCK_BITS/8)

/** \typedef sha1_ctx_t
 * \brief SHA-1 context type
 * 
 * A vatiable of this type may hold the state of a SHA-1 hashing process
 */
typedef struct {
	uint32_t h[5];
	uint64_t length;
} sha1_ctx_t;

#endif /*SHA1_H_*/
