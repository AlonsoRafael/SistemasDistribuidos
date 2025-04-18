import grpc
from concurrent import futures
import time
import sys
import json
import paho.mqtt.client as mqtt
import kvs_pb2
import kvs_pb2_grpc

# Tabela de armazenamento local (hash table)
armazenamento = {}
# Versão global para controle de versões
versao_global = 0
# Configuração do broker MQTT
MQTT_BROKER = "localhost"  # Pode ser outro broker, mas usar "localhost" é mais comum para testes locais
MQTT_PORT = 1883
MQTT_TOPIC = "kvs/sync"

# Cliente MQTT para comunicação entre os servidores
class MQTTClient:
    def __init__(self, server):
        self.server = server
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        """Quando o servidor MQTT se conecta com sucesso."""
        print(f"[MQTT] Conectado ao broker com código: {rc}")
        client.subscribe(MQTT_TOPIC)

    def on_message(self, client, userdata, msg):
        """Quando uma mensagem MQTT é recebida."""
        try:
            data = json.loads(msg.payload.decode())
            chave = data["chave"]
            valor = data["valor"]
            versao = data["versao"]
            if valor == "":
                # A chave foi removida, então remove da tabela
                if chave in armazenamento:
                    del armazenamento[chave]
                    print(f"[MQTT] Chave {chave} removida (v{versao})")
            else:
                # Atualiza ou insere a chave
                if chave not in armazenamento or armazenamento[chave]["versao"] < versao:
                    armazenamento[chave] = {"valor": valor, "versao": versao}
                    print(f"[MQTT] Atualizado via broker: {chave} = {valor} (v{versao})")
        except Exception as e:
            print(f"[MQTT] Erro ao processar JSON: {e}")

    def publicar_mqtt(self, chave, valor, versao):
        """Publica as mudanças (inserção/remoção) no tópico MQTT para outros servidores."""
        payload = json.dumps({"chave": chave, "valor": valor, "versao": versao})
        self.client.publish(MQTT_TOPIC, payload)

# Classe Servicer implementando os métodos gRPC
class KVSServicer(kvs_pb2_grpc.KVSServicer):
    def __init__(self):
        self.mqtt_client = MQTTClient(self)

    def Insere(self, request, context):
        """Insere uma chave-valor no armazenamento e propaga a atualização via MQTT"""
        global versao_global
        versao_global += 1
        armazenamento[request.chave] = {"valor": request.valor, "versao": versao_global}
        print(f"[INSERIR] {request.chave} = {request.valor} (v{versao_global})")
        self.mqtt_client.publicar_mqtt(request.chave, request.valor, versao_global)
        return kvs_pb2.Versao(versao=versao_global)

    def Consulta(self, request, context):
        """Consulta o valor de uma chave e retorna a versão"""
        if request.chave in armazenamento:
            dados = armazenamento[request.chave]
            if dados["versao"] > request.versao:
                return kvs_pb2.Tupla(chave=request.chave, valor=dados["valor"], versao=dados["versao"])
        # Se não encontrar ou versão for menor, retorna valor vazio (chave não encontrada)
        return kvs_pb2.Tupla(chave=request.chave, valor="", versao=0)

    def Remove(self, request, context):
        """Remove uma chave-valor do armazenamento e propaga a remoção via MQTT"""
        if request.chave in armazenamento:
            dados = armazenamento.pop(request.chave)
            # Publica uma mensagem com valor vazio, indicando que a chave foi removida
            self.mqtt_client.publicar_mqtt(request.chave, "", dados["versao"])
            return kvs_pb2.Versao(versao=dados["versao"])
        return kvs_pb2.Versao(versao=0)

    def Snapshot(self, request, context):
        """Retorna um snapshot do armazenamento até a versão solicitada"""
        print(f"[SNAPSHOT] Obtendo snapshot até a versão {request.versao}")
        for chave, dados in armazenamento.items():
            if dados["versao"] <= request.versao:
                yield kvs_pb2.Tupla(chave=chave, valor=dados["valor"], versao=dados["versao"])

    def InsereVarias(self, request_iterator, context):
        """Insere várias chaves em uma única chamada"""
        global versao_global
        for req in request_iterator:
            versao_global += 1
            armazenamento[req.chave] = {"valor": req.valor, "versao": versao_global}
            print(f"[INSERIR VÁRIAS] {req.chave} = {req.valor} (v{versao_global})")
            self.mqtt_client.publicar_mqtt(req.chave, req.valor, versao_global)
            yield kvs_pb2.Versao(versao=versao_global)

    def RemoveVarias(self, request_iterator, context):
        """Remove várias chaves em uma única chamada"""
        for req in request_iterator:
            if req.chave in armazenamento:
                dados = armazenamento.pop(req.chave)
                # Publica a remoção via MQTT
                self.mqtt_client.publicar_mqtt(req.chave, "", dados["versao"])
                yield kvs_pb2.Versao(versao=dados["versao"])
            else:
                yield kvs_pb2.Versao(versao=0)

# Função para rodar o servidor
def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvs_pb2_grpc.add_KVSServicer_to_server(KVSServicer(), server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"[SERVIDOR] Rodando na porta {port}")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    porta = sys.argv[1] if len(sys.argv) > 1 else "50051"
    serve(porta)
