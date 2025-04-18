#!/bin/bash
if [ -z "$1" ]; then
  echo "Uso: ./server.sh <porta>"
  exit 1
fi

python3 server.py $1