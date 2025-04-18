#!/bin/bash

echo "consulta 1: deve retornar valor1"
./client.sh --port 9000 -o consulta -k chave1 -e 1
sleep 2


echo "consulta 2: deve retornar valor5"
./client.sh --port 9002 -o consulta -k chave1 --ver=-1
sleep 2


echo "consulta 3: deve retornar valor444"
./client.sh --port 9000 -o consulta -k chave99
sleep 2


echo "consulta 4: deve retornar valor444"
./client.sh --port 9001 -o consulta -k chave99 -e 1000
sleep 2


echo "consulta 5: deve retornar valor333 valor-aaa"
./client.sh --port 9001 -o consulta-v -k chave99 -e 3 -k chave-aaa -e 0
sleep 2


echo "snapshot 1: deve retornar ultimo valor de cada chave"
./client.sh --port 9001 -o snapshot -e 0
sleep 2

echo "snapshot 2: deve retornar valor com versão 2 ou menor para cada chave"
./client.sh --port 9002 -o snapshot -e 2
sleep 2
