lib: literal_eval.cpp
	c++ -std=c++11 -DLIB $< -shared -fPIC -o libliteraleval.so

bin: literal_eval.cpp
	c++ -std=c++11 $< -o literal_eval.bin
