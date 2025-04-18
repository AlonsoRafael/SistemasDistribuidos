import grpc
from concurrent import futures
import kvs_pb2
import kvs_pb2_grpc
import json
import paho.mqtt.client as mqtt

class KVSServicer(kvs_pb2_grpc.KVSServicer):
    def __init__(self):
        self.store = {}
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.loop_start()

    def Insere(self, request, context):
        chave = request.chave
        valor = request.valor
        if chave not in self.store:
            self.store[chave] = []
        versao = len(self.store[chave]) + 1
        self.store[chave].append((versao, valor))
        # Publicar no MQTT
        mensagem = json.dumps({"operacao": "insere", "chave": chave, "valor": valor, "versao": versao})
        self.mqtt_client.publish("kvs/atualizacoes", mensagem)
        return kvs_pb2.Versao(versao=versao)

    def Consulta(self, request, context):
        chave = request.chave
        versao = request.versao if request.HasField("versao") else None
        if chave in self.store:
            if versao:
                for v, val in reversed(self.store[chave]):
                    if v <= versao:
                        return kvs_pb2.Tupla(chave=chave, valor=val, versao=v)
            else:
                v, val = self.store[chave][-1]
                return kvs_pb2.Tupla(chave=chave, valor=val, versao=v)
        return kvs_pb2.Tupla(chave="", valor="", versao=0)

    def Remove(self, request, context):
        chave = request.chave
        versao = request.versao if request.HasField("versao") else None
        if chave in self.store:
            if versao:
                for i, (v, _) in enumerate(self.store[chave]):
                    if v == versao:
                        del self.store[chave][i]
                        # Publicar no MQTT
                        mensagem = json.dumps({"operacao": "remove", "chave": chave, "versao": versao})
                        self.mqtt_client.publish("kvs/atualizacoes", mensagem)
                        return kvs_pb2.Versao(versao=versao)
                return kvs_pb2.Versao(versao=-1)
            else:
                del self.store[chave]
                # Publicar no MQTT
                mensagem = json.dumps({"operacao": "remove", "chave": chave})
                self.mqtt_client.publish("kvs/atualizacoes", mensagem)
                return kvs_pb2.Versao(versao=0)
        return kvs_pb2.Versao(versao=-1)

    # Implementar os demais métodos conforme especificações...
    ''''''
def serve():
    print("Iniciando servidor...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvs_pb2_grpc.add_KVSServicer_to_server(KVSServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("servidor iniciado")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
