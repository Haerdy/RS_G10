import paho.mqtt.client as mqtt
import json
import time
import threading

network_health_map = {}
# Tempo máximo sem heartbeat
TIMEOUT_LIMIT = 12

# CONEXÃO MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MONITOR] Conectado ao broker MQTT.")
        client.subscribe("docker/nodes/+/status")
        print("[MONITOR] Subscrevendo tópico: docker/nodes/+/status")
    else:
        print(f"[ERRO] Falha na conexão MQTT. Código: {rc}")


# recibe mensagens de status dos contentores e atualiza o mapa de saúde da rede
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        container_id = payload.get("id")
        status = payload.get("status")

        if not container_id:
            return

        # Atualiza ou cria entrada no mapa
        network_health_map[container_id] = {
            "ip": payload.get("ip"),
            "port": payload.get("port"),
            "status": status,
            "last_seen": time.time(),
            "rtt": "0 ms"
        }
        print(f"[HEARTBEAT] {container_id[:12]} -> {status}")
    except Exception as e:
        print(f"[ERRO] Falha ao processar mensagem MQTT: {e}")

# deteção de timeout para marcar contentores como DOWN se não receberem heartbeat dentro do limite
def monitor_timeout_checker():
    while True:
        current_time = time.time()
        for container_id, info in list(network_health_map.items()):
            elapsed = current_time - info["last_seen"]
            if info["status"] == "UP" and elapsed > TIMEOUT_LIMIT:
                info["status"] = "DOWN"
                print(f"[TIMEOUT] Container {container_id[:12]} marcado como DOWN.")
        time.sleep(2)
if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,client_id="main-docker-monitor")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect("localhost", 1883, keepalive=60)
        client.loop_start()
        print("[MONITOR] Sistema de monitorização iniciado.")
        # Thread do timeout
        threading.Thread(
            target=monitor_timeout_checker,
            daemon=True
        ).start()

        # Mantém processo vivo
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[MONITOR] Encerrando monitor...")

    except Exception as e:
        print(f"[ERRO CRÍTICO] {e}")