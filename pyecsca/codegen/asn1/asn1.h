#ifndef ASN1_H_
#define ASN1_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "bn.h"

uint8_t *asn1_der_encode(const bn_t *r, const bn_t *s, size_t *result_len);

bool asn1_der_decode(const uint8_t *sig, size_t sig_len, bn_t *r, bn_t *s);

#endif //ASN1_H_