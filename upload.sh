#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

fname=$1
echo "Name:"
read name
echo "Authors:"
read authors


python3 $DIR/upload.py "$(cat $DIR/key)" "$fname" "$name" "$authors" "@article{,title={$name}}" dataset "" ""
