import paho.mqtt.client as mqtt
import json
import time
import os
import socket

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("SERVICE_PORT", 8080))

container_id = socket.gethostname()
ip ="127.0.0.1"

topic = f"docker/nodes/{container_id}/status"

client = mqtt.Client(client_id=container_id)

# Last Will
will_payload = json.dumps({
    "id": container_id,
    "status": "DOWN"
})

client.will_set(topic, will_payload, qos=1, retain=True)

client.connect(BROKER, 1883, keepalive=60)

client.loop_start()

print(f"[{container_id}] conectado ao broker MQTT")
try:
    while True:

        payload = json.dumps({
            "id": container_id,
            "ip": ip,
            "port": PORT,
            "status": "UP"
        })

        print(f"[{container_id}] enviando heartbeat")
        print(payload)

        client.publish(topic, payload, qos=1, retain=True)

        time.sleep(5)
except Exception as e:
    print("ERRO:")
    print(e)