#!/bin/bash

swig -c++ -python -module oboe_ext oboe.i
sed -i 's/#include <string.h>/#include "oboe.hpp"\n#include <string.h>/g' oboe_wrap.cxx
