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


armazenamento = {}

versao_global = 0

max_versoes_chaves = {}


MQTT_BROKER = "localhost"  
MQTT_PORT = 1883
MQTT_TOPIC = "kvs/sync"


class MQTTClient:
    def __init__(self, server):
        self.server = server
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Conectado ao broker com código: {rc}")
        client.subscribe(MQTT_TOPIC)

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            chave = data["chave"]
            valor = data["valor"]
            versao = data["versao"]
            max_versao = data.get("max_versao", versao)  
            
            
            with lock:
                if chave in max_versoes_chaves:
                    if max_versao > max_versoes_chaves[chave]:
                        max_versoes_chaves[chave] = max_versao
                else:
                    max_versoes_chaves[chave] = max_versao

            if valor == "":
                if chave in armazenamento and versao in armazenamento[chave]:
                    del armazenamento[chave][versao]
                    if not armazenamento[chave]:
                        del armazenamento[chave]
                    print(f"[MQTT] Chave {chave} removida (v{versao})")
            else:
                if chave not in armazenamento:
                    armazenamento[chave] = {}
                if versao not in armazenamento[chave]:
                    armazenamento[chave][versao] = valor
                    print(f"[MQTT] Atualizado via broker: {chave} = {valor} (v{versao})")
        except Exception as e:
            print(f"[MQTT] Erro ao processar JSON: {e}")

    def publicar_mqtt(self, chave, valor, versao):
        with lock:
            current_max = max_versoes_chaves.get(chave, 0)
        payload = json.dumps({
            "chave": chave, 
            "valor": valor, 
            "versao": versao,
            "max_versao": current_max
        })
        self.client.publish(MQTT_TOPIC, payload)

class KVSServicer(kvs_pb2_grpc.KVSServicer):
    def __init__(self):
        self.mqtt_client = MQTTClient(self)

    def Insere(self, request, context):
        if len(request.chave) < 3 or len(request.valor) < 3:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Chave e valor devem ter pelo menos 3 caracteres.")
            return kvs_pb2.Versao(versao=-1)
        
        with lock:
            versao_maxima = max_versoes_chaves.get(request.chave, 0)
            nova_versao = versao_maxima + 1
            
            versoes = armazenamento.setdefault(request.chave, {})
            versoes[nova_versao] = request.valor
            
            max_versoes_chaves[request.chave] = nova_versao
        
        print(f"[INSERIR] {request.chave} = {request.valor} (v{nova_versao})")
        self.mqtt_client.publicar_mqtt(request.chave, request.valor, nova_versao)
        return kvs_pb2.Versao(versao=nova_versao)

    def Consulta(self, request, context):
        if request.chave in armazenamento:
            versoes = armazenamento[request.chave]
            
            if request.versao == -1 or request.versao == 0:
                versao = max(versoes)
            elif request.versao in versoes:
                versao = request.versao
            else:
                versao = max(versoes)
                
            valor = versoes[versao]
            return kvs_pb2.Tupla(chave=request.chave, valor=valor, versao=versao)
        
        return kvs_pb2.Tupla(chave=request.chave, valor="", versao=0)

    def Remove(self, request, context):
        chave = request.chave
        versao_req = request.versao

        if chave not in armazenamento:
            return kvs_pb2.Versao(versao=-1)

        versoes = armazenamento[chave]

        if versao_req == 0:
            if versoes:
                max_versoes_chaves[chave] = max(versoes.keys())
            
            print(f"[REMOVER TODAS] {chave} (versões: {list(versoes.keys())}")
            
            for versao in versoes:
                self.mqtt_client.publicar_mqtt(chave, "", versao)
                print(f"[REMOVER] {chave} (v{versao})")
            
            del armazenamento[chave]
            
            return kvs_pb2.Versao(versao=0)

        if versao_req not in versoes:
            return kvs_pb2.Versao(versao=-1)

        valor = versoes.pop(versao_req)
        print(f"[REMOVER] {chave} (v{versao_req})")
        self.mqtt_client.publicar_mqtt(chave, "", versao_req)

        if not versoes:
            del armazenamento[chave]

        return kvs_pb2.Versao(versao=versao_req)

    def Snapshot(self, request, context):
        print(f"[SNAPSHOT] Requisitado snapshot até a versão {request.versao}")
        
        if request.versao < 0:
            yield kvs_pb2.Tupla(chave="", valor="", versao=0)
            return

        if request.versao == 0:
            for chave, versoes in armazenamento.items():
                if versoes:
                    ultima_versao = max(versoes)
                    yield kvs_pb2.Tupla(
                        chave=chave,
                        valor=versoes[ultima_versao],
                        versao=ultima_versao
                    )
        else:
            for chave, versoes in armazenamento.items():
                versoes_validas = [v for v in versoes if v <= request.versao]
                if versoes_validas:
                    versao_snapshot = max(versoes_validas)
                    yield kvs_pb2.Tupla(
                        chave=chave,
                        valor=versoes[versao_snapshot],
                        versao=versao_snapshot
                    )


    def InsereVarias(self, request_iterator, context):
        for req in request_iterator:
            if len(req.chave) < 3 or len(req.valor) < 3:
                yield kvs_pb2.Versao(versao=-1)
                continue
                
            with lock:
                versao_maxima = max_versoes_chaves.get(req.chave, 0)
                nova_versao = versao_maxima + 1
                
                versoes = armazenamento.setdefault(req.chave, {})
                versoes[nova_versao] = req.valor
                
                max_versoes_chaves[req.chave] = nova_versao
            
            print(f"[INSERIR VÁRIAS] {req.chave} = {req.valor} (v{nova_versao})")
            
            self.mqtt_client.publicar_mqtt(req.chave, req.valor, nova_versao)
            
            yield kvs_pb2.Versao(versao=nova_versao)

    def RemoveVarias(self, request_iterator, context):
        for req in request_iterator:
            chave = req.chave
            versao_req = req.versao

            if chave not in armazenamento:
                yield kvs_pb2.Versao(versao=-1)
                continue

            versoes = armazenamento[chave]

            if versao_req == 0: 
                if versoes:
                    max_versoes_chaves[chave] = max(versoes.keys())
                
                for versao in versoes:
                    self.mqtt_client.publicar_mqtt(chave, "", versao)
                
                del armazenamento[chave]
                
                yield kvs_pb2.Versao(versao=0)
                continue

            if versao_req not in versoes:
                yield kvs_pb2.Versao(versao=-1)
                continue

            versoes.pop(versao_req)
            self.mqtt_client.publicar_mqtt(chave, "", versao_req)

            if not versoes:
                del armazenamento[chave]

            yield kvs_pb2.Versao(versao=versao_req)

    def ConsultaVarias(self, request_iterator, context):
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
