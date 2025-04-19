import grpc
from concurrent import futures
import time
import sys
import json
import paho.mqtt.client as mqtt
import kvs_pb2
import kvs_pb2_grpc
from threading import Lock
lock = Lock()
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
                # A versão foi removida
                if chave in armazenamento and versao in armazenamento[chave]:
                    del armazenamento[chave][versao]
                    if not armazenamento[chave]:
                        del armazenamento[chave]
                    print(f"[MQTT] Chave {chave} removida (v{versao})")
            else:
                # Atualiza ou insere a chave
                if chave not in armazenamento:
                    armazenamento[chave] = {}
                # Só insere se ainda não existir essa versão
                if versao not in armazenamento[chave]:
                    armazenamento[chave][versao] = valor
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
        """Insere uma nova versão da chave-valor"""
        if len(request.chave) < 3 or len(request.valor) < 3:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Chave e valor devem ter pelo menos 3 caracteres.")
            return kvs_pb2.Versao(versao=-1)
        with lock:
            versoes = armazenamento.setdefault(request.chave, {})
            nova_versao = max(versoes.keys(), default=0) + 1
            versoes[nova_versao] = request.valor
        print(f"[INSERIR] {request.chave} = {request.valor} (v{nova_versao})")
        self.mqtt_client.publicar_mqtt(request.chave, request.valor, nova_versao)
        return kvs_pb2.Versao(versao=nova_versao)

    def Consulta(self, request, context):
        """Consulta a versão mais recente ou uma versão específica da chave"""
        if request.chave in armazenamento:
            versoes = armazenamento[request.chave]
            
            # Se versao é -1, retorna a última versão (max(versoes))
            if request.versao == -1:
                versao = max(versoes)
            elif request.versao == 0:
                # Última versão (sem versão especificada, padrão para última)
                versao = max(versoes)
            elif request.versao in versoes:
                versao = request.versao
            else:
                return kvs_pb2.Tupla(chave=request.chave, valor="", versao=0)

            valor = versoes[versao]
            return kvs_pb2.Tupla(chave=request.chave, valor=valor, versao=versao)
        
        return kvs_pb2.Tupla(chave=request.chave, valor="", versao=0)

    def Remove(self, request, context):
        """Remove uma versão específica ou a mais recente da chave"""
        if request.chave in armazenamento:
            versoes = armazenamento[request.chave]
            if request.versao == 0:
                versao = max(versoes)
            elif request.versao in versoes:
                versao = request.versao
            else:
                return kvs_pb2.Versao(versao=0)

            valor = versoes.pop(versao)
            if not versoes:
                del armazenamento[request.chave]  # remove chave se ficou vazia

            self.mqtt_client.publicar_mqtt(request.chave, "", versao)
            return kvs_pb2.Versao(versao=versao)
        return kvs_pb2.Versao(versao=0)

    def Snapshot(self, request, context):
        """Retorna todas as versões até a versão informada"""
        print(f"[SNAPSHOT] Requisitado snapshot até a versão {request.versao}")
        if request.versao <= 0:
            # Retorna versões mais recentes de todas as chaves
            for chave, versoes in armazenamento.items():
                ultima_versao = max(versoes)
                yield kvs_pb2.Tupla(
                    chave=chave,
                    valor=versoes[ultima_versao],
                    versao=ultima_versao
                )
        else:
            for chave, versoes in armazenamento.items():
                for versao, valor in versoes.items():
                    if versao <= request.versao:
                        print(f"[SNAPSHOT] {chave} = {valor} (v{versao})")
                        yield kvs_pb2.Tupla(chave=chave, valor=valor, versao=versao)


    def InsereVarias(self, request_iterator, context):
        """Insere múltiplas chaves"""
        for req in request_iterator:
            versoes = armazenamento.setdefault(req.chave, {})
            nova_versao = max(versoes.keys(), default=0) + 1
            versoes[nova_versao] = req.valor
            print(f"[INSERIR VÁRIAS] {req.chave} = {req.valor} (v{nova_versao})")
            self.mqtt_client.publicar_mqtt(req.chave, req.valor, nova_versao)
            yield kvs_pb2.Versao(versao=nova_versao)

    def RemoveVarias(self, request_iterator, context):
        """Remove múltiplas chaves"""
        for req in request_iterator:
            chave = req.chave
            versao = req.versao

            if chave not in armazenamento:
                yield kvs_pb2.Versao(versao=0)
                continue

            versoes = armazenamento[chave]

            # Determina qual versão remover
            if versao == 0:
                versao_alvo = max(versoes)
            elif versao in versoes:
                versao_alvo = versao
            else:
                yield kvs_pb2.Versao(versao=0)
                continue

            # Remove a versão
            valor = versoes.pop(versao_alvo)
            if not versoes:
                del armazenamento[chave]

            # Sincroniza via MQTT
            self.mqtt_client.publicar_mqtt(chave, "", versao_alvo)

            # Retorna a versão removida
            yield kvs_pb2.Versao(versao=versao_alvo)

    def ConsultaVarias(self, request_iterator, context):
        """Consulta múltiplas chaves"""
        for req in request_iterator:
            chave = req.chave
            versao = req.versao
            if chave in armazenamento:
                versoes = armazenamento[chave]
                if versao == 0:
                    versao_real = max(versoes)
                elif versao in versoes:
                    versao_real = versao
                else:
                    yield kvs_pb2.Tupla(chave=chave, valor="", versao=0)
                    continue
                valor = versoes[versao_real]
                yield kvs_pb2.Tupla(chave=chave, valor=valor, versao=versao_real)
            else:
                yield kvs_pb2.Tupla(chave=chave, valor="", versao=0)


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
