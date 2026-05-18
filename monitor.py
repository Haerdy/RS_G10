import paho.mqtt.client as mqtt
import json
import time
import subprocess
import threading

# Dicionário global para armazenar o mapa de saúde da rede
# Chave: container_id -> Valor: {ip, port, status, last_seen, rtt}
network_health_map = {}
TIMEOUT_LIMIT = 12  # Se não houver atualizações em X segundos, passa a DOWN

def calculate_rtt(ip):
    """Executa um ping rápido para medir a latência (RTT) até o contentor."""
    if ip == "127.0.0.1":
        return "0.0 ms"
    try:
        # Executa 1 envio de ping com timeout de 1 segundo
        start = time.time()
        output = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        end = time.time()
        if output.returncode == 0:
            rtt = (end - start) * 1000
            return f"{rtt:.2f} ms"
        return "N/A (Inalcançável)"
    except Exception:
        return "Error"

def on_connect(client, userdata, flags, rc):
    print("Monitor de Telemetria iniciado. Subscrevendo tópicos...")
    # Subscreve os status de todos os nós dinamicamente
    client.subscribe("docker/nodes/+/status")

def on_message(client, userdata, msg):
    print("MENSAGEM RECEBIDA")
    print(msg.payload.decode())    
    try:
        payload = json.loads(msg.payload.decode())
        container_id = payload.get("id")
        status = payload.get("status")
        
        if not container_id:
            return

        if status == "UP":
            ip = payload.get("ip")
            port = payload.get("port")
            # Calcula o RTT em tempo real ao receber a telemetria
            rtt ="0 ms"
            
            network_health_map[container_id] = {
                "ip": ip,
                "port": port,
                "status": "UP",
                "last_seen": time.time(),
                "rtt": rtt
            }
        elif status == "DOWN":
            # Atualiza o estado para DOWN se explicitamente enviado ou via LWT
            if container_id in network_health_map:
                network_health_map[container_id]["status"] = "DOWN"
                network_health_map[container_id]["rtt"] = "N/A"
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

# Thread responsável por verificar timeouts (Deadman Switch)
def monitor_timeout_checker():
    while True:
        now = time.time()
        for container_id, info in network_health_map.items():
            if info["status"] == "UP" and (now - info["last_seen"]) > TIMEOUT_LIMIT:
                info["status"] = "DOWN"
                info["rtt"] = "TIMEOUT"
        time.sleep(2)

if __name__ == "__main__":
# Configuração do Cliente MQTT do monitor
    client = mqtt.Client(client_id="main-docker-monitor")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("localhost", 1883, keepalive=60)
    client.loop_start()

    # Inicia a verificação ativa de timeout numa thread separada
    checker_thread = threading.Thread(target=monitor_timeout_checker, daemon=True)
    checker_thread.start()

    # Mantém o monitor ativo
    while True:
        time.sleep(1)