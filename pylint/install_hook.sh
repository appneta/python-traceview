#!/bin/bash

ROOT_DIR=$(git rev-parse --show-toplevel)
SRC="${ROOT_DIR}/pylint/pre-commit"
DEST="${ROOT_DIR}/.git/hooks/pre-commit"

cp $SRC $DEST
chmod +x $DEST
