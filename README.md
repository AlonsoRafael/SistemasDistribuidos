# Sistema Distribuído de Armazenamento Chave-Valor (KVS)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Rust](https://img.shields.io/badge/Rust-1.70%2B-orange)
![gRPC](https://img.shields.io/badge/gRPC-1.60%2B-lightgrey)
![MQTT](https://img.shields.io/badge/MQTT-5.0-green)

## Índice

- [Pré-requisitos](#-pré-requisitos)
- [Compilação](#-instruções-de-compilação)
- [Uso](#-uso-do-servidor)
- [Estrutura de Dados](#-organização-dos-dados)
- [Testes](#-como-testar)
- [Limitações](#-limitações)
- [Dificuldades](#-dificuldades-encontradas)

## Trabalho de Sistemas Distribuídos

**Dupla:** - Gabriel Luiz de Lima Soares - Rafael Alonso Marques
**Curso:** Ciência da Computação  
**Ano:** 2025

---

## Vídeo de Apresentação (3:42 min)

[Demonstração do Sistema KVS](https://youtu.be/nP5gAX4Nfb4)

<a href="https://youtu.be/nP5gAX4Nfb4" target="_blank">
  <img src="https://img.youtube.com/vi/nP5gAX4Nfb4/0.jpg" alt="Vídeo de Demonstração" width="400">
</a>

---

## Descrição do Projeto

Este projeto implementa um sistema de **armazenamento chave-valor distribuído** com arquitetura **híbrida**, combinando:

- Comunicação **cliente-servidor via gRPC**
- Sincronização entre servidores via **MQTT (Mosquitto)** no modelo **publish/subscribe**

O sistema suporta **múltiplas versões por chave**, **tabelas hash em memória**, e possui scripts auxiliares para **compilação e execução automatizadas**.

Cliente Rust
│
▼ (gRPC)
Servidor Python ────(MQTT)───┤
▲ Broker Mosquitto
│ │
└─────────────────────────┘

---

## Estrutura do Repositório

```
.
├── proto/
│   ├── kvs.proto
├── src/                  # Arquivos gerados para gRPC, implementação do cliente em Rust e do Servidor em Python
│   ├── kvs_pb2.py
│   ├── kvs_pb2_grpc.py
│   ├── main.rs
│   ├── server.py
├── compile.sh             # Script para setup do ambiente e compilação
├── server.sh              # Script para execução do servidor
├── teste.sh               # Script de testes
└── README.md              # Este arquivo
```

---

## Instruções de Compilação

No terminal (Linux ou WSL):

```bash
chmod +x compile.sh
./compile.sh
```

Esse script:

- Instala o Mosquitto e cliente MQTT
- Cria e ativa o ambiente virtual Python
- Instala as dependências Python
- Instala o compilador Rust e dependências do cliente
- Gera os arquivos do gRPC a partir do `.proto`
- Cria os scripts `server.sh` e `teste.sh`

---

## Detalhes de Instalação e Configuração (Python)

O servidor é implementado em **Python 3.10+** e requer:

- `grpcio`
- `grpcio-tools`
- `paho-mqtt`

Todos são instalados automaticamente via `compile.sh`.

---

## Uso do Servidor

Para executar o servidor em uma porta específica:

```bash
./server.sh <porta>
```

Exemplo:

```bash
./server.sh 50051
```

O servidor inicia o gRPC e se conecta ao broker Mosquitto local.

---

## Uso do Cliente (Rust)

Para executar ações com o cliente, execute o comando no terminal bash:

```bash
./client.sh --port <porta> -o <ação> -k <chave> -v <valor> -e <versao>
```

Exemplos:

```bash
./client.sh --port 9000 -o insere -k chave1 -v valor1
```

Também pode ser usado os scripts de teste para verificar o funcionamento da implementação, executando (por exemplo):

```bash
chmod +x teste1-insere.sh
./teste1-insere.sh
```

---

## Organização dos Dados

- Cada servidor mantém uma **tabela hash em memória** com estrutura:

```python
Dict[str, Dict[int, str]]
```

Ou seja, cada chave (`str`) possui um dicionário de versões (`int`) com valores (`str`).

- Versões são incrementais, começando em 1 por chave.

---

## Como Testar

Após compilar:

1. Abra 3 terminais e rode 3 instâncias do servidor:

```bash
./server.sh 9000
./server.sh 9001
./server.sh 9002
```

2. No terminal do cliente (Rust), teste com comandos:

```bash
./client.sh --port 9000 -o insere -k chave1 -v valor1
./client.sh --port 9002 -o insere -k chave1 -v valor2
./client.sh --port 9000 -o consulta -k chave1 -e 1
```

Você verá que o dado é replicado via MQTT entre servidores.

3. Ou execute:

```bash
./teste.sh
```

Esse script faz operações automáticas via cliente Rust.

---

## Dificuldades Encontradas

- Integração entre gRPC (Python) e cliente Rust exigiu cuidados com tipos e serialização.
- Configuração do MQTT para múltiplas instâncias em paralelo sem conflitos.
- Garantir que a sincronização via publish/subscribe não causasse redundância ou conflitos de versão.

---

## Requisitos Não Implementados

- Persistência em disco dos dados (o armazenamento é apenas em memória).
- Tolerância a falhas de servidor (ex: reconexão automática após falha).
- Balanceamento de carga entre servidores.
- Autenticação entre servidores
- Criptografia das comunicações

---

## Requisitos Implementados

- [x] Cliente e Servidor com gRPC
- [x] Múltiplas versões por chave
- [x] Hash table em memória
- [x] Sincronização entre servidores com MQTT
- [x] Scripts automatizados (`compile.sh`, `server.sh`, `teste.sh`)
- [x] Testes via cliente Rust em múltiplos servidores
