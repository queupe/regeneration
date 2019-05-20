#!/bin/bash

python3 run_sim.py --config-json ./config/test_prime.json
#TEXINPUTS=./latex
python3 create_graph.py

filename=`cat latex_name.txt`
cd latex
pdflatex $filename
cd ../
#cat test_prime.log.txt 
#rm test_prime.log.txt 