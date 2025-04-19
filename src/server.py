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
# Versão máxima já vista para cada chave (mesmo após remoção)
max_versoes_chaves = {}

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
            max_versao = data.get("max_versao", versao)  # Usa o max_versao se disponível
            
            # Atualiza a versão máxima conhecida para esta chave
            with lock:
                if chave in max_versoes_chaves:
                    if max_versao > max_versoes_chaves[chave]:
                        max_versoes_chaves[chave] = max_versao
                else:
                    max_versoes_chaves[chave] = max_versao

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
        with lock:
            current_max = max_versoes_chaves.get(chave, 0)
        payload = json.dumps({
            "chave": chave, 
            "valor": valor, 
            "versao": versao,
            "max_versao": current_max
        })
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
            # Verifica a versão máxima já usada para esta chave
            versao_maxima = max_versoes_chaves.get(request.chave, 0)
            nova_versao = versao_maxima + 1
            
            # Atualiza o armazenamento
            versoes = armazenamento.setdefault(request.chave, {})
            versoes[nova_versao] = request.valor
            
            # Atualiza a versão máxima conhecida
            max_versoes_chaves[request.chave] = nova_versao
        
        print(f"[INSERIR] {request.chave} = {request.valor} (v{nova_versao})")
        self.mqtt_client.publicar_mqtt(request.chave, request.valor, nova_versao)
        return kvs_pb2.Versao(versao=nova_versao)

    def Consulta(self, request, context):
        """Consulta a versão mais recente ou uma versão específica da chave"""
        if request.chave in armazenamento:
            versoes = armazenamento[request.chave]
            
            if request.versao == -1 or request.versao == 0:
                versao = max(versoes)  # Retorna a versão mais recente, caso versao seja -1 ou 0
            elif request.versao in versoes:
                versao = request.versao
            else:
                # Retorna a versão mais recente se a versão solicitada não existir
                versao = max(versoes)
                
            valor = versoes[versao]
            return kvs_pb2.Tupla(chave=request.chave, valor=valor, versao=versao)
        
        return kvs_pb2.Tupla(chave=request.chave, valor="", versao=0)

    def Remove(self, request, context):
        """Remove uma versão específica ou todas as versões de uma chave"""
        chave = request.chave
        versao_req = request.versao

        if chave not in armazenamento:
            return kvs_pb2.Versao(versao=-1)  # chave inexistente

        versoes = armazenamento[chave]

        if versao_req == 0:  # Remover todas as versões
            # Atualiza a versão máxima antes de remover
            if versoes:
                max_versoes_chaves[chave] = max(versoes.keys())
            
            # Log local da remoção
            print(f"[REMOVER TODAS] {chave} (versões: {list(versoes.keys())}")
            
            # Remove todas as versões e sincroniza via MQTT
            for versao in versoes:
                self.mqtt_client.publicar_mqtt(chave, "", versao)
                print(f"[REMOVER] {chave} (v{versao})")  # Log local
            
            del armazenamento[chave]  # Remove a chave completamente
            
            return kvs_pb2.Versao(versao=0)

        if versao_req not in versoes:
            return kvs_pb2.Versao(versao=-1)  # versão não encontrada

        # Remoção de uma versão específica
        valor = versoes.pop(versao_req)
        print(f"[REMOVER] {chave} (v{versao_req})")  # Log local
        self.mqtt_client.publicar_mqtt(chave, "", versao_req)

        if not versoes:  # Se não restar nenhuma versão, remove a chave
            del armazenamento[chave]

        return kvs_pb2.Versao(versao=versao_req)

    def Snapshot(self, request, context):
        """Retorna todas as versões até a versão informada"""
        print(f"[SNAPSHOT] Requisitado snapshot até a versão {request.versao}")
        
        if request.versao < 0:  # Versão inválida
            yield kvs_pb2.Tupla(chave="", valor="", versao=0)
            return

        if request.versao == 0:  # Retorna versões mais recentes
            for chave, versoes in armazenamento.items():
                if versoes:  # Se existirem versões
                    ultima_versao = max(versoes)
                    yield kvs_pb2.Tupla(
                        chave=chave,
                        valor=versoes[ultima_versao],
                        versao=ultima_versao
                    )
        else:  # Versão específica
            for chave, versoes in armazenamento.items():
                # Encontra a maior versão que seja <= request.versao
                versoes_validas = [v for v in versoes if v <= request.versao]
                if versoes_validas:
                    versao_snapshot = max(versoes_validas)
                    yield kvs_pb2.Tupla(
                        chave=chave,
                        valor=versoes[versao_snapshot],
                        versao=versao_snapshot
                    )


    def InsereVarias(self, request_iterator, context):
        """Insere múltiplas chaves mantendo a consistência entre servidores"""
        for req in request_iterator:
            # Validação do tamanho mínimo da chave e valor
            if len(req.chave) < 3 or len(req.valor) < 3:
                yield kvs_pb2.Versao(versao=-1)
                continue
                
            with lock:
                # Obtém a versão máxima conhecida (local ou recebida via MQTT)
                versao_maxima = max_versoes_chaves.get(req.chave, 0)
                nova_versao = versao_maxima + 1
                
                # Atualiza o armazenamento local
                versoes = armazenamento.setdefault(req.chave, {})
                versoes[nova_versao] = req.valor
                
                # Atualiza a versão máxima conhecida
                max_versoes_chaves[req.chave] = nova_versao
            
            # Log da operação
            print(f"[INSERIR VÁRIAS] {req.chave} = {req.valor} (v{nova_versao})")
            
            # Publica a inserção no MQTT incluindo a versão máxima atual
            self.mqtt_client.publicar_mqtt(req.chave, req.valor, nova_versao)
            
            # Retorna a versão criada
            yield kvs_pb2.Versao(versao=nova_versao)

    def RemoveVarias(self, request_iterator, context):
        """Remove múltiplas chaves e versões"""
        for req in request_iterator:
            chave = req.chave
            versao_req = req.versao

            if chave not in armazenamento:
                yield kvs_pb2.Versao(versao=-1)  # chave inexistente
                continue

            versoes = armazenamento[chave]

            if versao_req == 0:  # Se versão não for especificada (ou é 0), remover todas as versões
                # Atualiza a versão máxima antes de remover
                if versoes:
                    max_versoes_chaves[chave] = max(versoes.keys())
                
                # Remove todas as versões e sincroniza via MQTT
                for versao in versoes:
                    self.mqtt_client.publicar_mqtt(chave, "", versao)
                
                del armazenamento[chave]  # Remove a chave completamente
                
                yield kvs_pb2.Versao(versao=0)
                continue

            if versao_req not in versoes:
                yield kvs_pb2.Versao(versao=-1)  # versão não encontrada
                continue

            # Remoção de uma versão específica
            versoes.pop(versao_req)
            self.mqtt_client.publicar_mqtt(chave, "", versao_req)

            if not versoes:  # Se não restar nenhuma versão, remove a chave
                del armazenamento[chave]

            yield kvs_pb2.Versao(versao=versao_req)

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
