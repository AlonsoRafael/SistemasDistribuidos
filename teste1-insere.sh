#!/bin/bash

echo "insere 1: deve retornar versao igual a 1"
./client.sh --port 9000 -o insere -k chave1 -v valor1
sleep 2

echo "insere 2: deve retornar versao igual a 2"
./client.sh --port 9002 -o insere -k chave1 -v valor2
sleep 2


echo "insere 3: deve retornar versao igual a 3"
./client.sh --port 9001 -o insere -k chave1 -v valor3
sleep 2


echo "insere 4: deve retornar versao igual a 4"
./client.sh --port 9001 -o insere -k chave1 -v valor4
sleep 2


echo "insere 5: deve retornar versao igual a 1"
./client.sh --port 9000 -o insere -k chave99 -v valor111
sleep 2


echo "insere 6: deve retornar versao igual a 2"
./client.sh --port 9001 -o insere -k chave99 -v valor222
sleep 2


echo "insere 7: deve retornar versao igual a 3"
./client.sh --port 9002 -o insere -k chave99 -v valor333
sleep 2

echo "insere varias: deve retornar versoes 5 4 1 1"
./client.sh --port 9001 -o insere-v -k chave1 -v valor5 -k chave99 -v valor444 -k chave-aaa -v valor-aaa -k chave-bbb -v valor-bbb

