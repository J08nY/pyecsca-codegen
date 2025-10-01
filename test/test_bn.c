#include <stdio.h>
#include <stdlib.h>
#include "bn/bn.h"

int test_wsliding_ltr() {
    printf("test_wsliding_ltr: ");
    bn_t bn;
    bn_init(&bn);
    bn_from_int(181, &bn);
    wsliding_t *ws = bn_wsliding_ltr(&bn, 3);
    if (ws == NULL) {
        printf("NULL\n");
        return 1;
    }
    if (ws->length != 6) {
        printf("Bad length (%li instead of 6)\n", ws->length);
        return 1;
    }
    uint8_t expected[6] = {5, 0, 0, 5, 0, 1};
    for (int i = 0; i < 6; i++) {
        if (ws->data[i] != expected[i]) {
            printf("Bad data (%i instead of %i)\n", ws->data[i], expected[i]);
            return 1;
        }
    }
    printf("OK\n");
    bn_clear(&bn);
    free(ws->data);
    free(ws);
    return 0;
}

int test_wsliding_rtl() {
    printf("test_wsliding_rtl: ");
    int failed = 0;
    struct {
        int value;
        int w;
        int expected_len;
        uint8_t expected[16]; // max expected length
    } cases[] = {
        // Original test
        {181, 3, 8, {1, 0, 0, 3, 0, 0, 0, 5}},
        // Edge case: 1
        {1, 3, 1, {1}},
        // w = 2, value = 1234
        {1234, 2, 11, {1, 0, 0, 0, 3, 0, 1, 0, 0, 1, 0}},
        // w = 4, value = 0b10101010
        {0b10101010, 4, 6, {5, 0, 0, 0, 5, 0}},
    };
    int num_cases = sizeof(cases) / sizeof(cases[0]);
    for (int t = 0; t < num_cases; t++) {
        bn_t bn;
        bn_init(&bn);
        bn_from_int(cases[t].value, &bn);
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

int test_convert_base() {
    printf("test_convert_base: ");
    bn_t bn;
    bn_init(&bn);
    bn_from_int(11, &bn);
    small_base_t *bs = bn_convert_base_small(&bn, 2);
    if (bs == NULL) {
        printf("NULL\n");
        return 1;
    }
    if (bs->length != 4) {
        printf("Bad length (%li instead of 4)\n", bs->length);
        return 1;
    }
    uint8_t expected[4] = {1, 1, 0, 1};
    for (int i = 0; i < 4; i++) {
        if (bs->data[i] != expected[i]) {
            printf("Bad data (%i insead of %i)\n", bs->data[i], expected[i]);
            return 1;
        }
    }
    printf("OK\n");
    bn_clear(&bn);
    free(bs->data);
    free(bs);
    return 0;
}

int main(void) {
    return test_wsliding_ltr() + test_wsliding_rtl() + test_convert_base();
}
