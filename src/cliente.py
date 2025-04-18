import grpc
import sys

import kvs_pb2
import kvs_pb2_grpc

def insere(stub, chave, valor):
    response = stub.Insere(kvs_pb2.ChaveValor(chave=chave, valor=valor))
    if response.versao > 0:
        print(f" Inserido com versão {response.versao}")
    else:
        print(" Falha na inserção")

def consulta(stub, chave, versao=None):
    if versao:
        request = kvs_pb2.ChaveVersao(chave=chave, versao=int(versao))
    else:
        request = kvs_pb2.ChaveVersao(chave=chave)
    response = stub.Consulta(request)
    if response.valor:
        print(f" Resultado: chave={response.chave}, valor={response.valor}, versao={response.versao}")
    else:
        print(" Chave ou versão não encontrada")

def remove(stub, chave, versao=None):
    if versao:
        request = kvs_pb2.ChaveVersao(chave=chave, versao=int(versao))
    else:
        request = kvs_pb2.ChaveVersao(chave=chave)
    response = stub.Remove(request)
    if response.versao > 0:
        print(f" Removido com versão {response.versao}")
    else:
        print(" Falha na remoção")

def snapshot(stub, versao):
    versao = int(versao)
    request = kvs_pb2.Versao(versao=versao)
    responses = stub.Snapshot(request)
    print(f" Snapshot versão {versao}")
    for r in responses:
        if r.chave:
            print(f" - {r.chave}: {r.valor} (v{r.versao})")

def main():
    if len(sys.argv) != 3:
        print("Uso: python client.py <host> <porta>")
        sys.exit(1)

    host = sys.argv[1]
    porta = sys.argv[2]

    with grpc.insecure_channel(f"{host}:{porta}") as channel:
        stub = kvs_pb2_grpc.KVSStub(channel)
        print("🔌 Conectado ao servidor. Digite um comando (ou 'sair'):")

        while True:
            try:
                comando = input("> ").strip().split()
                if not comando:
                    continue
                if comando[0] == "sair":
                    break
                elif comando[0] == "insere" and len(comando) == 3:
                    insere(stub, comando[1], comando[2])
                elif comando[0] == "consulta":
                    consulta(stub, comando[1], comando[2] if len(comando) > 2 else None)
                elif comando[0] == "remove":
                    remove(stub, comando[1], comando[2] if len(comando) > 2 else None)
                elif comando[0] == "snapshot" and len(comando) == 2:
                    snapshot(stub, comando[1])
                else:
                    print(" Comando inválido.")
            except KeyboardInterrupt:
                print("\nEncerrando...")
                break

if __name__ == "__main__":
    main()
