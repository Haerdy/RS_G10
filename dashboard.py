import paho.mqtt.client as mqtt
import json
import time
import os
import threading
from datetime import datetime

network_health_map = {}
# Tempo máximo sem heartbeat
TIMEOUT_LIMIT = 12

#proteção contra accessos concorrentes
lock = threading.Lock()

# conexão MQTT
def on_connect(client, userdata, flags, rc):

    if rc == 0:
        print("[DASHBOARD] Conectado ao broker MQTT.")
        client.subscribe("docker/nodes/+/status")
    else:
        print(f"[ERRO] Falha ao conectar MQTT. Código: {rc}")

# recebe mensagens de status dos contentores e atualiza o mapa de saúde da rede
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        cid = payload.get("id")
        if not cid:
            return
        
        current_time = time.time()

        sent_time = payload.get("timestamp", current_time)
        latency = round((current_time - sent_time) * 1000, 2)
        rtt_str = f"{latency} ms" if payload.get("status") == "UP" else "N/A"

        with lock:

            network_health_map[cid] = {
                "ip": payload.get("ip", "N/A"),
                "port": payload.get("port", "N/A"),
                "status": payload.get("status", "UP"),
                "rtt": rtt_str,
                "last_seen": current_time,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
    except Exception as e:
        print(f"[ERRO] {e}")

# deteção de timeout para marcar contentores como DOWN se não receberem heartbeat dentro do limite
def update_timeout_status():
    current_time = time.time()
    with lock:
        for cid, info in list(network_health_map.items()):
            elapsed = current_time - info["last_seen"]
            # Se passou do limite -> DOWN
            if elapsed > TIMEOUT_LIMIT:
                if info["status"] != "DOWN":
                    info["status"] = "DOWN"
                    info["rtt"] = "N/A"
                    print(f"[TIMEOUT] {cid[:12]} ficou OFFLINE.")
            elif elapsed > 5 and info["status"] == "UP":
                info["status"] = "DELAYED"

# exibir o dashboard no terminal

def display_dashboard():

    while True:
        update_timeout_status()
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 120)
        print("          MAPA DE SAÚDE DA REDE DE CONTENTORES DOCKER (MQTT)")
        print("=" * 120)
        print(
            f"{'CONTAINER ID':<15} | "
            f"{'IP':<15} | "
            f"{'PORTA':<8} | "
            f"{'ESTADO':<10} | "
            f"{'LATÊNCIA':<12} | "
            f"{'ÚLTIMO HEARTBEAT':<20} | "
            f"{'TEMPO SEM SINAL':<18}"
        )
        print("-" * 120)

        with lock:
            if not network_health_map:
                print("Nenhum contentor Docker registado.")
            else:
                for cid, info in network_health_map.items():
                    elapsed = int(time.time() - info["last_seen"])

                    # Cor do estado
                    if info["status"] == "UP":
                        status_colored = "\033[92mUP\033[0m"
                    elif info["status"] == "DELAYED":
                        status_colored = "\033[93mDELAYED\033[0m"
                    else:
                        status_colored = "\033[91mDOWN\033[0m"
                    
                    ip = info.get("ip") or "N/A"
                    port = info.get("port") or "N/A"
                    rtt = info.get("rtt") or "N/A"
                    timestamp = info.get("timestamp") or "N/A"

                    print(
                        f"{cid[:15]:<15} | "
                        f"{ip:<15} | "
                        f"{str(port):<8} | "
                        f"{status_colored:<18} | "
                        f"{rtt:<12} | "
                        f"{timestamp:<20} | "
                        f"{str(elapsed) + ' s':<18}"
                    )

        print("=" * 120)
        print("Atualização automática a cada 2 segundos.")
        print("Pressione Ctrl+C para sair.")

        time.sleep(2)

if __name__ == "__main__":

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1,
        client_id="docker-dashboard"
    )

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("localhost", 1883, 60)
        client.loop_start()
        display_dashboard()
    except KeyboardInterrupt:
        print("\n[DASHBOARD] Encerrando dashboard...")
    except Exception as e:
        print(f"[ERRO CRÍTICO INESPERADO] {e}")