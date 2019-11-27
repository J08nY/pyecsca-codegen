#include "asn1.h"

#include <stdlib.h>

uint8_t *asn1_der_encode(const bn_t *r, const bn_t *s, size_t *result_len) {
    uint8_t r_len = (uint8_t) bn_to_bin_size(r);
    uint8_t s_len = (uint8_t) bn_to_bin_size(s);

	// Pad with one zero byte in case most-significant bit of top byte is one.
    uint8_t r_length = r_len + (bn_get_bit(r, r_len * 8) ? 1 : 0);
    uint8_t s_length = s_len + (bn_get_bit(s, s_len * 8) ? 1 : 0);

    // R and S are < 128 bytes, so 1 byte tag + 1 byte len + len bytes value
    size_t seq_value_len = 2 + r_length + 2 + s_length;
    size_t whole_len = seq_value_len;

    // The SEQUENCE length might be >= 128, so more bytes of length
    size_t seq_len_len = 0;
    if (seq_value_len >= 128) {
        size_t s = seq_value_len;
        do {
            seq_len_len++;
        } while ((s = s >> 8));
    }
    // seq_len_len bytes for length and one for length of length
    whole_len += seq_len_len + 1;

    // 1 byte tag for SEQUENCE
    whole_len += 1;

    uint8_t *data = malloc(whole_len);
    size_t i = 0;
    data[i++] = 0x30; // SEQUENCE
    if (seq_value_len < 128) {
        data[i++] = (uint8_t) seq_value_len;
    } else {
        data[i++] = (uint8_t) (seq_len_len | (1 << 7));
        for (size_t j = 0; j < seq_len_len; ++j) {
            data[i++] = (uint8_t) (seq_value_len & (0xff << (8 * (seq_len_len - j - 1))));
        }
    }
    data[i++] = 0x02; //INTEGER
    data[i++] = r_length;
    if (bn_get_bit(r, r_len * 8)) {
        data[i++] = 0;
    }
    bn_to_bin(r, data + i);
    i += r_len;
    data[i++] = 0x02; //INTEGER
    data[i++] = s_length;
    if (bn_get_bit(s, s_len * 8)) {
        data[i++] = 0;
    }
    bn_to_bin(s, data + i);
    i += s_len;

    return data;
}

bool asn1_der_decode(const uint8_t *sig, size_t sig_len, bn_t *r, bn_t *s) {
    size_t i = 0;
    if (sig[i++] != 0x30) {//SEQUENCE
        return false;
    }
    size_t seq_value_len = 0;
    if (!(sig[i] & 0x80)) {
        seq_value_len = sig[i++];
    } else {
        size_t seq_len_len = sig[i++] & 0x7f;
        while (seq_len_len > 0) {
            seq_value_len |= (sig[i++] << (seq_len_len - 1));
            seq_len_len--;
        }
    }

    if (sig[i++] != 0x02) {//INTEGER
        return false;
    }
    size_t r_length = sig[i++];
    size_t r_offset = i;
    i += r_length;

    if (sig[i++] != 0x02) {//INTEGER
        return false;
    }
    size_t s_length = sig[i++];
    size_t s_offset = i;
    i += s_length;

    if (i != sig_len) {
        return false;
    }

    bn_from_bin(sig + r_offset, r_length, r);
	bn_from_bin(sig + s_offset, s_length, s);
    return true;
}