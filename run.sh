#!/bin/bash

case "$1" in
	"2")	VER=2.7;;
	*)	VER=3.4;;
esac

rm -rf aqua.log aquaclasses.py out.txt *.pyc __pycache__

echo python$VER aqua_launcher.py -m generico.py -i input.txt -o out.txt -c classdefs.txt -l aqua.log

python$VER aqua_launcher.py -m generico.py -i input.txt -o out.txt -c classdefs.txt -l aqua.log
[[ $? -ne 0 ]] && cat aqua.log && exit 1

exit 0
