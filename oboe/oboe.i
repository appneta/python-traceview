%module oboe
%{
#include "oboe.hpp"
%}

%include std_string.i

%newobject Context::startTrace();
%newobject Context::createEvent();
%newobject Context::copy();

%newobject Metadata::copy();
%newobject Metadata::fromString();
%newobject Metadata::createEvent();
%newobject Metadata::makeRandom();

%newobject Event::startTrace();
%newobject Event::getMetadata();

%include "oboe.hpp"
