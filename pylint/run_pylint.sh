#!/bin/bash
#
# Runs PyLint on a given file, emitting warnings from the tracelytics-specific
# options file.

here=$(readlink -f $0 2> /dev/null)
if [ $? -ne 0 ]; then
    # OS X readlink doesn't support -f, greadlink is gnu readlink, available
    # from Homebrew (maybe MacPorts?)
    here=$(greadlink -f $0)
fi

path=$(dirname "$here")

base=$(cd $path && pwd)
venv=/venv/lib/python2.7/site-packages
export PYTHONPATH=$base:$venv:$PYTHONPATH:/usr/lib/python2.7

/venv/bin/pylint --rcfile=$path/.pylintrc $1

exit $?
