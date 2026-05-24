#!/bin/bash

#Create a virtual environment
python3 -m venv .venv

#Activate the virtual environment
source .venv/bin/activate

#Install libraries
pip install nicegui requests opencv-python

#Run the script
python3 gui.py
