"""
SCRIPT: dashboard.py
RESUMO: Central de Monitorização Ativa (Serviço de Dashboard). Subscreve os 
        tópicos de telemetria de todos os nós, calcula métricas de latência (RTT) 
        em tempo real e gere de forma concorrente os estados de vivacidade (UP, 
        DELAYED, DOWN) dos contentores através de um mecanismo de timeout.
"""

import paho.mqtt.client as mqtt
import json
import time
import os
import threading
from datetime import datetime

# Estrutura de dados global que armazena a tabela de saúde da infraestrutura
network_health_map = {}

# Tempo máximo sem heartbeat
TIMEOUT_LIMIT = 12

# [IMPORTANTE] Thread Lock (Mutex)
# Evita condições de corrida (Race Conditions) ao manipular o 'network_health_map',
lock = threading.Lock()

# conexão MQTT
"""
    RESUMO: Callback disparado quando o dashboard se liga ao broker MQTT.
        Responsável por efetuar a subscrição dinâmica através de wildcards (+).
"""
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[DASHBOARD] Conectado ao broker MQTT.")
        # [IMPORTANTE] Subscrição com Single-Level Wildcard (+) para capturar eventos de qualquer ID
        client.subscribe("docker/nodes/+/status")
    else:
        print(f"[ERRO] Falha ao conectar MQTT. Código: {rc}")

"""
RESUMO: Callback executado sempre que uma mensagem de telemetria chega ao broker.
        Efetua o parsing dos dados do agente e calcula o RTT da mensagem.
"""
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        cid = payload.get("id")
        if not cid:
            return
        
        current_time = time.time()

        # [IMPORTANTE] Cálculo de Latência Unidirecional / RTT aproximado
        # Subtrai o timestamp de envio do agente ao tempo de receção do dashboard
        sent_time = payload.get("timestamp", current_time)
        latency = round((current_time - sent_time) * 1000, 2)
        rtt_str = f"{latency} ms" if payload.get("status") == "UP" else "N/A"

        # [IMPORTANTE] Escrita segura usando exclusão mútua
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

"""
RESUMO: Avalia o diferencial de tempo decorrido desde o último heartbeat recebido, 
        atualizando o estado do mapa para DELAYED ou DOWN se exceder os limites.
"""
def update_timeout_status():
    
    current_time = time.time()

    # [IMPORTANTE] Lock para leitura e modificação segura do dicionário
    with lock:
        # Conversão para list() essencial para evitar erros de mutação de dicionário durante a iteração
        for cid, info in list(network_health_map.items()):
            elapsed = current_time - info["last_seen"]

            # [IMPORTANTE] Máquina de Estados de Disponibilidade
            if elapsed > TIMEOUT_LIMIT:
                if info["status"] != "DOWN":
                    info["status"] = "DOWN"
                    info["rtt"] = "N/A"
                    print(f"[TIMEOUT] {cid[:12]} ficou OFFLINE.")
            elif elapsed > 5 and info["status"] == "UP":
                info["status"] = "DELAYED"

"""
RESUMO: Loop de renderização visual da Interface de Linha de Comando (CLI). 
        Limpa o terminal periodicamente e imprime a matriz de saúde formatada.
"""
def display_dashboard():
    while True:
        # Executa a verificação lógica de vitalidade antes de desenhar
        update_timeout_status()
        # Limpar o terminal
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

        # [IMPORTANTE] Bloqueio de concorrência para leitura e renderização consistente dos dados
        with lock:
            if not network_health_map:
                print("Nenhum contentor Docker registado.")
            else:
                for cid, info in network_health_map.items():
                    elapsed = int(time.time() - info["last_seen"])

                    # Cor para gerar um indicador visual do estado dos contentores
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
        # Inicializa o loop de processamento de rede do MQTT numa thread secundária nativa
        client.loop_start()
        # Inicia a renderização do Dashboard (bloqueia o fluxo principal)
        display_dashboard()
    except KeyboardInterrupt:
        print("\n[DASHBOARD] Encerrando dashboard...")
    except Exception as e:
        print(f"[ERRO CRÍTICO INESPERADO] {e}")