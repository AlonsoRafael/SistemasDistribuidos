#!/bin/bash

echo "remove 1: deve retornar versao 1"
./client.sh --port 9000 -o remove -k chave1 -e 1
sleep 2


echo "remove 2: deve retornar versao -1"
./client.sh --port 9001 -o remove -k chave1 -e 1
sleep 2


echo "remove 3: deve retornar versao 0"
./client.sh --port 9002 -o remove -k chave99
sleep 2


echo "remove 4: deve retornar versao -1"
./client.sh --port 9001 -o remove -k chave99 -e 1000
sleep 2


echo "remove 5: deve retornar versoes 2 e -1"
./client.sh --port 9001 -o remove-v -k chave1 -e 2 -k chave-aaa -e 2
sleep 2


echo "consulta 1: versao 1 para chave 1 não existe mais"
./client.sh --port 9002 -o consulta -k chave1 -e 1
sleep 2


echo "snapshot 1: chave99 e chave1 não possuem valor para versao 2"
./client.sh --port 9000 -o snapshot -e 2
sleep 2
