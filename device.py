"""
SCRIPT: device.py
RESUMO: Atua como o "Agente" de telemetria integrado em cada contentor Docker. 
        Ao inicializar, recolhe metadados da rede local (IP, Porta, Hostname) e 
        estabelece uma ligação contínua com o broker MQTT, enviando heartbeats 
        periódicos com intervalos dinâmicos para simular o comportamento real da rede.
"""

import paho.mqtt.client as mqtt
import json
import time
import os
import random
import socket

# Configurações de rede obtidas dinamicamente do ambiente Docker
BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("SERVICE_PORT", 8080))
heartbeat_interval = 5

# Recolha de dados de identificação e rede do próprio contentor
container_id = socket.gethostname()
ip = socket.gethostbyname(socket.gethostname())
topic = f"docker/nodes/{container_id}/status"

# Inicialização do cliente MQTT
client = mqtt.Client(client_id=container_id)

# [IMPORTANTE] Last Will Testament: envia a mensagem de forma autónoma caso o contentor caia abruptamente
will_payload = json.dumps({
    "id": container_id,
    "status": "DOWN"
})
client.will_set(topic, will_payload, qos=1, retain=True) #QOS = 1 para receber um acknowledgment

# Ativação do ciclo de escuta em background para processar a comunicação com o Broker
client.connect(BROKER, 1883, keepalive=60)
client.loop_start()

print(f"[{container_id}] conectado ao broker MQTT")

try:
    # Ciclo de vida principal do agente (Geração e envio de telemetria)
    while True:
        # [IMPORTANTE] Construção do payload e telemetria
        payload = json.dumps({
            "id": container_id,
            "ip": ip,
            "port": PORT,
            "status": "UP",
            "timestamp": time.time()
        })

        print(f"[{container_id}] enviando heartbeat")
        print(payload)

        # [IMPORTANTE] retain=False para o broker não armazenar em cache estados 'UP' antigos
        client.publish(topic, payload, qos=1, retain=False) #heartbeat
        
        # simular um delay da rede
        delay = random.randint(1, 8)
        time.sleep(heartbeat_interval + delay)

except Exception as e:
    # [IMPORTANTE] Se o script capturar um encerramento voluntário, notifica imediatamente o estado DOWN
    client.publish(topic, json.dumps({"id": container_id, "status": "DOWN"}), qos=1, retain=True)
    client.disconnect()