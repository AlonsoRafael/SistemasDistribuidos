# KVS Distribuído - Sistema de Armazenamento Chave-Valor com gRPC + MQTT

Este projeto implementa um sistema **distribuído de armazenamento chave-valor (Key-Value Store - KVS)** usando comunicação **gRPC** com clientes e **MQTT (pub/sub)** entre servidores. Foi desenvolvido como parte da disciplina **GBC074 - Sistemas Distribuídos**, conforme especificações fornecidas.

---

## Visão Geral

- Comunicação cliente-servidor via **gRPC**
- Comunicação entre servidores via **MQTT (Mosquitto Broker)**
- Suporte a **múltiplos servidores**
- Sincronização automática entre servidores
- Operações: inserção, consulta, remoção, snapshot e operações em lote
- Armazenamento em memória usando **tabelas hash**
- Interface **CLI** para execução do servidor
- Dados propagados via MQTT no formato **JSON**

---

## Estrutura de Dados

O armazenamento em cada servidor é feito via dicionário Python:

```python
self.kvs = {
    "chave1": [
        {"valor": "valor1", "versao": 1},
        {"valor": "valor2", "versao": 2}
    ],
    "chave2": [
        {"valor": "outro", "versao": 1}
    ]
}

self.last_versions = {
    "chave1": 2,
    "chave2": 1
}
```

---

## Instalação

1. Instalar o broker Mosquitto (Linux)
   sudo apt update
   sudo apt install mosquitto mosquitto-clients

2. Instalar dependências Python

chmod +x compile.sh
./compile.sh

O script instala:

-grpcio

-grpcio-tools

-paho-mqtt

---

## Compilação do .proto

python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. kvs.proto

---

## Execução servidor

chmod +x server.sh
./server.sh 50051
ou
entra na pasta src
python server.py 50051

---

## Execução cliente

chmod +x client.sh
./client.sh 50051
ou
entrar na pasta src
python cliente.py 50051
