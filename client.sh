#!/bin/bash

if [ -z "$1" ]; then
  echo "Uso: ./cliente.sh <porta>"
  exit 1
fi
python3 cliente.py localhost $1