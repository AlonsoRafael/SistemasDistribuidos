# GBC074 - Sistemas Distribuídos - 2024-2

Projeto de um sistema de armazenamento do tipo chave-valor (KVS - _Key-Value Store_).

## Dependências

* protobuf (para uso do binário `protoc`)
* Rust

## Compilação

* `cargo build`

## Uso

* Cliente: `./client.sh -p 9000 --help`, em que 9000 representa a porta do servidor. A opção `--help` lista os possíveis argumentos adicionais.


## Testes

* Os casos de teste assumem 3 servidores aceitando conexões nas portas 9000, 9001 e 9002
* Execute os testes em ordem crescente para obter os resultados esperados
