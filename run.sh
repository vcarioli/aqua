#!/bin/bash
rm -rf aqua.log aquaclasses.py out.txt *.pyc __pycache__
echo python aqua_launcher.py -m generico.py -i input.txt -o out.txt -c classdefs.txt -l aqua.log
python3.3 aqua_launcher.py -m generico.py -i input.txt -o out.txt -c classdefs.txt -l aqua.log
[[ $? -ne 0 ]] && cat aqua.log 
