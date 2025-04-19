#!/bin/bash
source venv/bin/activate
./teste1-insere.sh
sleep 2
./teste2-consulta.sh
sleep 2
./teste3-remove.sh
sleep 2
./teste4-insere.sh
