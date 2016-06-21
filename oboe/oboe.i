%module oboe
%{
#include "oboe.hpp"
%}

%include std_string.i

%newobject Context::startTrace();
%newobject Context::createEvent();
%newobject Context::copy();

%newobject Metadata::copy();
%newobject Metadata::fromString(std::string s);
%newobject Metadata::createEvent();
%newobject Metadata::makeRandom();

%newobject Event::startTrace();
%newobject Event::startTrace(const oboe_metadata_t *md);
%newobject Event::getMetadata();

%include "oboe.hpp"
