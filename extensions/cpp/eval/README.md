# ast.literal
implemented with cpp to get high efficiency.
uses only the basic types: str, bool, int, float, list, tuple, dict, set.

## compile
```shell
# shared library
c++ -std=c++11 -DLIB py-to-pickle.cpp -shared -fPIC -o libpytopickle.so
# bin
c++ -std=c++11 literal_eval.cpp -o literal_eval.bin
# literal_eval.py
```

## bench mark
```
python time-read.py
```
Gunzip + read time: 0.1663219928741455
Size: 22540270
py_to_pickle: 0.539439306
pickle.loads+py_to_pickle: 0.7234611099999999
compile: 3.3440755870000003
parse: 3.6302585899999995
eval: 3.306765757000001
ast.literal_eval: 4.056752016000003
json.loads: 0.3230752619999997
pickle.loads: 0.1351051709999993
marshal.loads: 0.10351717500000035