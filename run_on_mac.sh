#!/bin/bash

rm -rf .env
virtualenv -p python3 .env
source .env/bin/activate
pip install -r requirements.txt
python3 resulaj.py