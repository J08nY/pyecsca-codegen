
test_bn_san: test_bn.c ../pyecsca/codegen/bn/bn.c
	gcc -g -o $@ $^ -fsanitize=address -fsanitize=undefined -I ../pyecsca/codegen/ -I ../pyecsca/codegen/tommath/ -L ../pyecsca/codegen/tommath/ -l:libtommath-HOST.a

test_bn_val: test_bn.c ../pyecsca/codegen/bn/bn.c
	gcc -g -o $@ $^ -I ../pyecsca/codegen/ -I ../pyecsca/codegen/tommath/ -L ../pyecsca/codegen/tommath/ -l:libtommath-HOST.a


test: test_bn_san test_bn_val
	./test_bn_san
	valgrind -q ./test_bn_val

.PHONY: test