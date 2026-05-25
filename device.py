import paho.mqtt.client as mqtt
import json
import time
import os
import socket
import random
BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("SERVICE_PORT", 8080))

container_id = socket.gethostname() # Get the container ID
ip = socket.gethostbyname(socket.gethostname()) # Get the IP address

topic = f"docker/nodes/{container_id}/status" # Unique topic for this container's status updates

client = mqtt.Client(client_id=container_id) # Unique client ID based on container ID

# Last Will
will_payload = json.dumps({
    "id": container_id,
    "status": "DOWN"
})
client.will_set(topic, will_payload, qos=1, retain=True) # Set Last Will to mark as DOWN if the container goes offline unexpectedly

client.connect(BROKER, 1883, keepalive=60)# Connect to the MQTT broker

client.loop_start()

print(f"[{container_id}] conectado ao broker MQTT")
try:
    while True:
# Simulate heartbeat with random latency
        payload = json.dumps({
            "id": container_id,
            "ip": ip,
            "port": PORT,
            "status": "UP",
            "timestamp": time.time()
        })

        print(f"[{container_id}] enviando heartbeat")
        print(payload)

        delay = random.randint(1, 8)

        print(f"[{container_id}] latência simulada: {delay}s")

        time.sleep(delay)
#escolheu se qos 1 para garantir que a mensagem seja entregue
#  pelo menos uma vez, e retain=True para que o broker retenha 
# a última mensagem de status do container, permitindo que novos
#  clientes recebam o status atual imediatamente ao se inscreverem.
# n escolheu se qo2 pq é mais complexo e pode resultar em mensagens 
# duplicadas, o que não é necessário para este caso de uso de monitoramento de status.
        client.publish(topic, payload, qos=1, retain=True)
except Exception as e:
    print("ERRO:")
    print(e)