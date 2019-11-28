#ifndef FAT_H_
#define FAT_H_

typedef struct {
	size_t len;
	void *value;
} fat_t;

#define fat_empty {0, NULL}

#endif //FAT_H_