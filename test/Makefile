
test_bn: test_bn.c ../pyecsca/codegen/bn/bn.c
	gcc -g -o $@ $^ -fsanitize=address -fsanitize=undefined -I ../pyecsca/codegen/ -I ../pyecsca/codegen/tommath/ -L ../pyecsca/codegen/tommath/ -l:libtommath-HOST.a
