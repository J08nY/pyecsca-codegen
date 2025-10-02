#include <stdio.h>
#include <stdlib.h>
#include "bn/bn.h"

int test_wsliding_ltr() {
    printf("test_wsliding_ltr: ");
    int failed = 0;
    struct {
        const char *value;
        int w;
        int expected_len;
        uint8_t expected[100]; // max expected length
    } cases[] = {
        // sliding_window_ltr begin
        {"181", 3, 6, {5, 0, 0, 5, 0, 1}},
        {"1", 3, 1, {1}},
        {"1234", 2, 11, {1, 0, 0, 0, 3, 0, 1, 0, 0, 1, 0}},
        {"170", 4, 6, {5, 0, 0, 0, 5, 0}},
        {"554", 5, 6, {17, 0, 0, 0, 5, 0}},
        {"123456789123456789123456789", 5, 83, {25, 1, 0, 0, 0, 0, 0, 0, 0, 15, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0, 23, 0, 0, 0, 0, 25, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 29, 0, 0, 0, 0, 17, 0, 0, 0, 0, 19, 0, 0, 0, 0, 29, 0, 0, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 17, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0, 0, 0, 0, 21}}
        // sliding_window_ltr end
    };
    int num_cases = sizeof(cases) / sizeof(cases[0]);
    for (int t = 0; t < num_cases; t++) {
        bn_t bn;
        bn_init(&bn);
        bn_from_dec(cases[t].value, &bn);
        wsliding_t *ws = bn_wsliding_ltr(&bn, cases[t].w);
        if (ws == NULL) {
            printf("Case %d: NULL\n", t);
            failed++;
            bn_clear(&bn);
            continue;
        }
        if (ws->length != cases[t].expected_len) {
            printf("Case %d: Bad length (%li instead of %i)\n", t, ws->length, cases[t].expected_len);
            failed++;
        }
        for (int i = 0; i < cases[t].expected_len; i++) {
            if (ws->data[i] != cases[t].expected[i]) {
                printf("Case %d: Bad data at %d (%i instead of %i)\n", t, i, ws->data[i], cases[t].expected[i]);
                failed++;
                break;
            }
        }
        bn_clear(&bn);
        free(ws->data);
        free(ws);
    }
    if (failed == 0) {
        printf("OK\n");
    } else {
        printf("FAILED (%d cases)\n", failed);
    }
    return failed;
}

int test_wsliding_rtl() {
    printf("test_wsliding_rtl: ");
    int failed = 0;
    struct {
        const char *value;
        int w;
        int expected_len;
        uint8_t expected[100]; // max expected length
    } cases[] = {
        // sliding_window_rtl begin
        {"181", 3, 8, {1, 0, 0, 3, 0, 0, 0, 5}},
        {"1", 3, 1, {1}},
        {"1234", 2, 11, {1, 0, 0, 0, 3, 0, 1, 0, 0, 1, 0}},
        {"170", 4, 6, {5, 0, 0, 0, 5, 0}},
        {"554", 5, 10, {1, 0, 0, 0, 0, 0, 0, 0, 21, 0}},
        {"123456789123456789123456789",5, 87, {1, 0, 0, 0, 0, 19, 0, 0, 0, 0, 1, 0, 0, 0, 0, 29, 0, 0, 0, 0, 31, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0, 0, 11, 0, 0, 0, 0, 17, 0, 0, 0, 0, 27, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 17, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0, 0, 0, 0, 21}}
        // sliding_window_rtl end
    };
    int num_cases = sizeof(cases) / sizeof(cases[0]);
    for (int t = 0; t < num_cases; t++) {
        bn_t bn;
        bn_init(&bn);
        bn_from_dec(cases[t].value, &bn);
        wsliding_t *ws = bn_wsliding_rtl(&bn, cases[t].w);
        if (ws == NULL) {
            printf("Case %d: NULL\n", t);
            failed++;
            bn_clear(&bn);
            continue;
        }
        if (ws->length != cases[t].expected_len) {
            printf("Case %d: Bad length (%li instead of %i)\n", t, ws->length, cases[t].expected_len);
            failed++;
        }
        for (int i = 0; i < cases[t].expected_len; i++) {
            if (ws->data[i] != cases[t].expected[i]) {
                printf("Case %d: Bad data at %d (%i instead of %i)\n", t, i, ws->data[i], cases[t].expected[i]);
                failed++;
                break;
            }
        }
        bn_clear(&bn);
        free(ws->data);
        free(ws);
    }
    if (failed == 0) {
        printf("OK\n");
    } else {
        printf("FAILED (%d cases)\n", failed);
    }
    return failed;
}

int test_convert_base_small() {
    printf("test_convert_base_small: ");
    int failed = 0;
    struct {
        const char *value;
        int base;
        int expected_len;
        uint8_t expected[100]; // max expected length
    } cases[] = {
        // convert_base_small begin
        {"11", 2, 4, {1, 1, 0, 1}},
        {"255", 2, 8, {1, 1, 1, 1, 1, 1, 1, 1}},
        {"1234", 10, 4, {4, 3, 2, 1}},
        {"0", 2, 1, {0}},
        {"1", 2, 1, {1}},
        {"123456789123456789123456789", 16, 22, {5, 1, 15, 5, 4, 0, 12, 7, 15, 9, 1, 11, 3, 14, 2, 15, 13, 15, 14, 1, 6, 6}}
        // convert_base_small end
    };
    int num_cases = sizeof(cases) / sizeof(cases[0]);
    for (int t = 0; t < num_cases; t++) {
        bn_t bn;
        bn_init(&bn);
        bn_from_dec(cases[t].value, &bn);
        small_base_t *bs = bn_convert_base_small(&bn, cases[t].base);
        if (bs == NULL) {
            printf("Case %d: NULL\n", t);
            failed++;
            bn_clear(&bn);
            continue;
        }
        if (bs->length != cases[t].expected_len) {
            printf("Case %d: Bad length (%li instead of %i)\n", t, bs->length, cases[t].expected_len);
            failed++;
        }
        for (int i = 0; i < cases[t].expected_len; i++) {
            if (bs->data[i] != cases[t].expected[i]) {
                printf("Case %d: Bad data at %d (%i instead of %i)\n", t, i, bs->data[i], cases[t].expected[i]);
                failed++;
                break;
            }
        }
        bn_clear(&bn);
        free(bs->data);
        free(bs);
    }
    if (failed == 0) {
        printf("OK\n");
    } else {
        printf("FAILED (%d cases)\n", failed);
    }
    return failed;
}

int test_convert_base_large() {
    printf("test_convert_base_large: ");
    int failed = 0;
    struct {
        const char *value;
        const char *base;
        int expected_len;
        const char *expected[100]; // max expected length
    } cases[] = {
        // convert_base_large begin
        {"123456789123456", "2", 47, {"0", "0", "0", "0", "0", "0", "0", "1", "1", "0", "0", "0", "1", "0", "0", "1", "1", "1", "1", "1", "0", "0", "0", "0", "0", "1", "1", "0", "0", "0", "0", "1", "0", "0", "0", "1", "0", "0", "1", "0", "0", "0", "0", "0", "1", "1", "1"}},
        {"123456789123456789123456789", "123456", 6, {"104661", "75537", "83120", "74172", "37630", "4"}},
        {"352099265818416392997042486274568094251", "18446744073709551616", 3, {"12367597952119210539", "640595372834356666", "1"}}
        // convert_base_large end
    };
    int num_cases = sizeof(cases) / sizeof(cases[0]);
    for (int t = 0; t < num_cases; t++) {
        bn_t bn, base;
        bn_init(&bn);
        bn_init(&base);
        bn_from_dec(cases[t].value, &bn);
        bn_from_dec(cases[t].base, &base);
        large_base_t *bs = bn_convert_base_large(&bn, &base);
        if (bs == NULL) {
            printf("Case %d: NULL\n", t);
            failed++;
            bn_clear(&bn);
            bn_clear(&base);
            continue;
        }
        if (bs->length != cases[t].expected_len) {
            printf("Case %d: Bad length (%li instead of %i)\n", t, bs->length, cases[t].expected_len);
            failed++;
        }
        for (int i = 0; i < cases[t].expected_len; i++) {
            bn_t exp;
            bn_init(&exp);
            bn_from_dec(cases[t].expected[i], &exp);
            if (!bn_eq(&bs->data[i], &exp)) {
                printf("Case %d: Bad data at %d\n", t, i);
                failed++;
                bn_clear(&exp);
                break;
            }
            bn_clear(&exp);
        }
        for (int i = 0; i < bs->length; i++) {
            bn_clear(&bs->data[i]);
        }
        bn_clear(&bs->m);
        bn_clear(&bn);
        bn_clear(&base);
        free(bs->data);
        free(bs);
    }
    if (failed == 0) {
        printf("OK\n");
    } else {
        printf("FAILED (%d cases)\n", failed);
    }
    return failed;
}

int test_bn_wnaf() {
    printf("test_bn_wnaf: ");
    int failed = 0;
    struct {
        const char *value;
        int w;
        int expected_len;
        int8_t expected[100]; // max expected length
    } cases[] = {
        // wnaf begin
        {"19", 2, 5, {1, 0, 1, 0, -1}},
        {"45", 3, 5, {3, 0, 0, 0, -3}},
        {"0", 3, 0, {}},
        {"1", 2, 1, {1}},
        {"21", 4, 5, {1, 0, 0, 0, 5}},
        {"123456789", 3, 28, {1, 0, 0, -1, 0, 0, 3, 0, 0, -1, 0, 0, 0, 0, 0, -3, 0, 0, 0, -3, 0, 0, 0, 0, 3, 0, 0, -3}},
        {"123456789123456789123456789", 5, 84, {13, 0, 0, 0, 0, 0, -15, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, -13, 0, 0, 0, 0, 0, -7, 0, 0, 0, 0, 0, -5, 0, 0, 0, 0, 0, 0, 13, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, -7, 0, 0, 0, 0, -11}}
        // wnaf end
    };
    int num_cases = sizeof(cases) / sizeof(cases[0]);
    for (int t = 0; t < num_cases; t++) {
        bn_t bn;
        bn_init(&bn);
        bn_from_dec(cases[t].value, &bn);
        wnaf_t *naf = bn_wnaf(&bn, cases[t].w);
        if (naf == NULL) {
            printf("Case %d: NULL\n", t);
            failed++;
            bn_clear(&bn);
            continue;
        }
        if (naf->length != cases[t].expected_len) {
            printf("Case %d: Bad length (%li instead of %i)\n", t, naf->length, cases[t].expected_len);
            failed++;
        }
        for (int i = 0; i < cases[t].expected_len; i++) {
            if (naf->data[i] != cases[t].expected[i]) {
                printf("Case %d: Bad data at %d (%i instead of %i)\n", t, i, naf->data[i], cases[t].expected[i]);
                failed++;
                break;
            }
        }
        bn_clear(&bn);
        free(naf->data);
        free(naf);
    }
    if (failed == 0) {
        printf("OK\n");
    } else {
        printf("FAILED (%d cases)\n", failed);
    }
    return failed;
}

int test_bn_wnaf_manipulation() {
    printf("test_bn_wnaf_manipulation: ");
    bn_t bn;
    bn_init(&bn);
    bn_from_dec("123456789", &bn);
    wnaf_t *naf = bn_wnaf(&bn, 3);
    bn_clear(&bn);
    if (naf->length != 28) {
        printf("FAILED (bad length %li instead of 28)\n", naf->length);
        return 1;
    }
    bn_naf_pad_left(naf, 0, 5);
    if (naf->length != 33) {
        printf("FAILED (bad length after pad left %li instead of 33)\n", naf->length);
        return 1;
    }
    for (int i = 0; i < 5; i++) {
        if (naf->data[i] != 0) {
            printf("FAILED (bad data after pad left at %d (%i instead of 0))\n", i, naf->data[i]);
            return 1;
        }
    }
    bn_naf_strip_left(naf, 0);
    if (naf->length != 28) {
        printf("FAILED (bad length after strip left %li instead of 28)\n", naf->length);
        return 1;
    }
    bn_naf_pad_right(naf, 0, 3);
    if (naf->length != 31) {
        printf("FAILED (bad length after pad right %li instead of 31)\n", naf->length);
        return 1;
    }
    for (int i = 28; i < 31; i++) {
        if (naf->data[i] != 0) {
            printf("FAILED (bad data after pad right at %d (%i instead of 0))\n", i, naf->data[i]);
            return 1;
        }
    }
    bn_naf_strip_right(naf, 0);
    if (naf->length != 28) {
        printf("FAILED (bad length after strip right %li instead of 28)\n", naf->length);
        return 1;
    }
    int8_t rev[28] = {-3, 0, 0, 3, 0, 0, 0, 0, -3, 0, 0, 0, -3, 0, 0, 0, 0, 0, -1, 0, 0, 3, 0, 0, -1, 0, 0, 1};
    bn_naf_reverse(naf);
    for (int i = 0; i < 28; i++) {
        if (naf->data[i] != rev[i]) {
            printf("FAILED (bad data after reverse at %d (%i instead of %i))\n", i, naf->data[i], rev[i]);
            return 1;
        }
    }

    free(naf->data);
    free(naf);
    printf("OK\n");
    return 0;
}

int test_booth() {
    printf("test_booth: ");
    for (int i = 0; i < (1 << 6); i++) {
        int32_t bw = bn_booth_word(i, 5);
        if (i <= 31) {
            if (bw != (i + 1) / 2) {
                printf("FAILED (bad booth for %d: %d instead of %d)\n", i, bw, (i + 1) / 2);
                return 1;
            }
        } else {
            if (bw != -((64 - i) / 2)) {
                printf("FAILED (bad booth for %d: %d instead of %d)\n", i, bw, -((64 - i) / 2));
                return 1;
            }
        }
    }
    int failed = 0;
    struct {
        const char *value;
        int w;
        size_t bits;
        int expected_len;
        int32_t expected[256]; // max expected length
    } cases[] = {
        // booth begin
        {"12345678123456781234567812345678123456781234567812345678", 1, 224, 225, {0, 0, 0, 1, -1, 0, 1, -1, 0, 0, 1, 0, -1, 1, -1, 0, 0, 1, -1, 1, -1, 1, 0, -1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 1, -1, 0, 0, 1, 0, -1, 1, -1, 0, 0, 1, -1, 1, -1, 1, 0, -1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 1, -1, 0, 0, 1, 0, -1, 1, -1, 0, 0, 1, -1, 1, -1, 1, 0, -1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 1, -1, 0, 0, 1, 0, -1, 1, -1, 0, 0, 1, -1, 1, -1, 1, 0, -1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 1, -1, 0, 0, 1, 0, -1, 1, -1, 0, 0, 1, -1, 1, -1, 1, 0, -1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 1, -1, 0, 0, 1, 0, -1, 1, -1, 0, 0, 1, -1, 1, -1, 1, 0, -1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 1, -1, 0, 0, 1, 0, -1, 1, -1, 0, 0, 1, -1, 1, -1, 1, 0, -1, 0, 1, 0, 0, 0, -1, 0, 0, 0}},
        {"12345678123456781234567812345678123456781234567812345678", 2, 224, 113, {0, 0, 1, 1, -2, 1, -1, 1, 0, 1, 1, 2, -2, 2, 0, -2, 0, 0, 1, 1, -2, 1, -1, 1, 0, 1, 1, 2, -2, 2, 0, -2, 0, 0, 1, 1, -2, 1, -1, 1, 0, 1, 1, 2, -2, 2, 0, -2, 0, 0, 1, 1, -2, 1, -1, 1, 0, 1, 1, 2, -2, 2, 0, -2, 0, 0, 1, 1, -2, 1, -1, 1, 0, 1, 1, 2, -2, 2, 0, -2, 0, 0, 1, 1, -2, 1, -1, 1, 0, 1, 1, 2, -2, 2, 0, -2, 0, 0, 1, 1, -2, 1, -1, 1, 0, 1, 1, 2, -2, 2, 0, -2, 0}},
        {"12345678123456781234567812345678123456781234567812345678", 5, 224, 45, {1, 4, 13, 3, -10, 15, 0, 9, 3, 9, -10, -12, -8, 2, 9, -6, 5, 13, -2, 1, -14, 7, -15, 11, 8, -16, 5, -14, -12, 11, -6, -4, 1, 4, 13, 3, -10, 15, 0, 9, 3, 9, -10, -12, -8}},
        {"12345678123456781234567812345678123456781234567812345678", 16, 224, 15, {0, 4660, 22136, 4660, 22136, 4660, 22136, 4660, 22136, 4660, 22136, 4660, 22136, 4660, 22136}},
        {"12345678123456781234567812345678123456781234567812345678", 24, 224, 10, {18, 3430008, 1193046, 7868980, 5666834, 3430008, 1193046, 7868980, 5666834, 3430008}},
        {"12345678123456781234567812345678123456781234567812345678", 30, 224, 0, {}}
        // booth end
    };
    int num_cases = sizeof(cases) / sizeof(cases[0]);
    for (int t = 0; t < num_cases; t++) {
        bn_t bn;
        bn_init(&bn);
        bn_from_hex(cases[t].value, &bn);
        booth_t *booth = bn_booth(&bn, cases[t].w, cases[t].bits);
        if (booth == NULL && cases[t].expected_len != 0) {
            printf("Case %d: NULL\n", t);
            failed++;
            bn_clear(&bn);
            continue;
        }
        if (cases[t].expected_len != 0) {
            if (booth->length != cases[t].expected_len) {
                printf("Case %d: Bad length (%li instead of %i)\n", t, booth->length, cases[t].expected_len);
                failed++;
            }
            for (int i = 0; i < cases[t].expected_len; i++) {
                if (booth->data[i] != cases[t].expected[i]) {
                    printf("FAILED (bad booth data at %d: %d instead of %d)\n", i, booth->data[i], cases[t].expected[i]);
                    failed++;
                    break;
                }
            }
        }
        bn_clear(&bn);
        bn_booth_clear(booth);
    }
    printf("OK\n");
    return 0;
}

int main(void) {
    return test_wsliding_ltr() + test_wsliding_rtl() + test_convert_base_small() + test_convert_base_large() + test_bn_wnaf() + test_bn_wnaf_manipulation() + test_booth();
}
