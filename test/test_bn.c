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
    bn_t bn;
    bn_init(&bn);
    bn_from_int(181, &bn);
    wsliding_t *ws = bn_wsliding_rtl(&bn, 3);
    if (ws == NULL) {
        printf("NULL\n");
        return 1;
    }
    if (ws->length != 8) {
        printf("Bad length (%li instead of 8)\n", ws->length);
        return 1;
    }
    uint8_t expected[8] = {1, 0, 0, 3, 0, 0, 0, 5};
    for (int i = 0; i < 8; i++) {
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

int test_convert_base() {
    printf("test_convert-base: ");
    bn_t bn;
    bn_init(&bn);
    bn_from_int(5, &bn);
    base_t *bs = bn_convert_base(&bn, 2);
    if (bs == NULL) {
        printf("NULL\n");
        return 1;
    }
    if (bs->length != 3) {
        printf("Bad length (%li instead of 3)\n", bs->length);
        return 1;
    }
    uint8_t expected[3] = {1, 0, 1};
    for (int i = 0; i < 3; i++) {
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
