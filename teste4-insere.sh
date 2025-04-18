#!/bin/bash

echo "insere 1: deve retornar versao igual a 6"
./client.sh --port 9002 -o insere -k chave1 -v valor6
sleep 2


echo "insere 2: deve retornar versao igual a 5"
./client.sh --port 9001 -o insere -k chave99 -v valor555
sleep 2


echo "insere 3: deve retornar versao igual a 2"
./client.sh --port 9000 -o insere -k chave-aaa -v valor-aaa2
sleep 2


echo "snapshot 1: deve retornar última versao de cada chave"
./client.sh --port 9001 -o snapshot -e 0
sleep 2


echo "snapshot 2: deve retornar valor-aaa2 e valor-bbb"
./client.sh --port 9000 -o snapshot -e 2
sleep 2

