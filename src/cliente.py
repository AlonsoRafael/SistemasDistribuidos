import grpc
import sys
import kvs_pb2
import kvs_pb2_grpc

def run_client(porta):
    canal = grpc.insecure_channel(f'localhost:{porta}')
    stub = kvs_pb2_grpc.KVSStub(canal)

    print("Cliente iniciado. Comandos disponíveis:")
    print("insere <chave> <valor>")
    print("consulta <chave> [versao]")
    print("remove <chave> [versao]")
    print("snapshot <versao>")
    print("insere_varias <chave1> <valor1> <chave2> <valor2> ...")
    print("consulta_varias <chave1> [versao1] <chave2> [versao2] ...")
    print("remove_varias <chave1> [versao1] <chave2> [versao2] ...")
    print("fim")

    while True:
        try:
            entrada = input("> ").strip()
            if not entrada:
                continue

            comando, *args = entrada.split()

            if comando == "fim":
                break

            elif comando == "insere" and len(args) == 2:
                resposta = stub.Insere(kvs_pb2.ChaveValor(chave=args[0], valor=args[1]))
                print("Versão inserida:", resposta.versao)

            elif comando == "consulta" and len(args) >= 1:
                chave = args[0]
                versao = int(args[1]) if len(args) > 1 else 0
                resposta = stub.Consulta(kvs_pb2.ChaveVersao(chave=chave, versao=versao))
                print(f"{resposta.chave} = {resposta.valor} (v{resposta.versao})")

            elif comando == "remove" and len(args) >= 1:
                chave = args[0]
                versao = int(args[1]) if len(args) > 1 else 0
                resposta = stub.Remove(kvs_pb2.ChaveVersao(chave=chave, versao=versao))
                print("Versão removida:", resposta.versao)

            elif comando == "snapshot" and len(args) == 1:
                versao = int(args[0])
                respostas = stub.Snapshot(kvs_pb2.Versao(versao=versao))
                for r in respostas:
                    print(f"{r.chave} = {r.valor} (v{r.versao})")

            elif comando == "insere_varias" and len(args) % 2 == 0:
                def gerar():
                    for i in range(0, len(args), 2):
                        yield kvs_pb2.ChaveValor(chave=args[i], valor=args[i+1])
                respostas = stub.InsereVarias(gerar())
                for r in respostas:
                    print("Versão inserida:", r.versao)

            elif comando == "consulta_varias" and len(args) >= 1:
                def gerar():
                    i = 0
                    while i < len(args):
                        chave = args[i]
                        i += 1
                        versao = int(args[i]) if i < len(args) and args[i].isdigit() else 0
                        if i < len(args) and args[i].isdigit():
                            i += 1
                        yield kvs_pb2.ChaveVersao(chave=chave, versao=versao)
                respostas = stub.ConsultaVarias(gerar())
                for r in respostas:
                    print(f"{r.chave} = {r.valor} (v{r.versao})")

            elif comando == "remove_varias" and len(args) >= 1:
                def gerar():
                    i = 0
                    while i < len(args):
                        chave = args[i]
                        i += 1
                        versao = int(args[i]) if i < len(args) and args[i].isdigit() else 0
                        if i < len(args) and args[i].isdigit():
                            i += 1
                        yield kvs_pb2.ChaveVersao(chave=chave, versao=versao)
                respostas = stub.RemoveVarias(gerar())
                for r in respostas:
                    print("Versão removida:", r.versao)

            else:
                print("Comando inválido ou parâmetros incorretos.")

        except grpc.RpcError as e:
            print("Erro na comunicação com o servidor:", e)
        except Exception as e:
            print("Erro:", e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cliente.py <porta>")
        sys.exit(1)
    run_client(sys.argv[1])