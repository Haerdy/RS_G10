import paho.mqtt.client as mqtt
import json
import time
import os
import random
import socket

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("SERVICE_PORT", 8080))

heartbeat_interval = 5

container_id = socket.gethostname()
ip = socket.gethostbyname(socket.gethostname())
topic = f"docker/nodes/{container_id}/status"

client = mqtt.Client(client_id=container_id)

# Last Will
will_payload = json.dumps({
    "id": container_id,
    "status": "DOWN"
})

client.will_set(topic, will_payload, qos=1, retain=True) #QOS = 1 para receber um acknowledgment

client.connect(BROKER, 1883, keepalive=60)
client.loop_start()

print(f"[{container_id}] conectado ao broker MQTT")

try:
    while True:

        payload = json.dumps({
            "id": container_id,
            "ip": ip,
            "port": PORT,
            "status": "UP",
            "timestamp": time.time()
        })

        print(f"[{container_id}] enviando heartbeat")
        print(payload)

        client.publish(topic, payload, qos=1, retain=False) #heartbeat
        delay = random.randint(1, 8)
        # simular um delay
        time.sleep(heartbeat_interval + delay)

except Exception as e:
    # desconecta caso ocorra um erro
    client.publish(topic, json.dumps({"id": container_id, "status": "DOWN"}), qos=1, retain=True)
    client.disconnect()