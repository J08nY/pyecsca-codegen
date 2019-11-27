typedef struct {
	size_t len;
	void *value;
} fat_t;

#define fat_empty {0, NULL}