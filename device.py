import time
import os
from monitor import network_health_map  # Importa o mapa de saúde atualizado pelo monitor

def display_dashboard():
    while True:
        # Limpa o terminal para efeito "Real-Time"
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 80)
        print("          MAPA DE SAÚDE DA REDE DE CONTENTORES DOCKER (MQTT)           ")
        print("=" * 80)
        print(f"{'CONTAINER ID':<15} | {'IP COORD':<15} | {'PORTA':<6} | {'ESTADO':<8} | {'RTT LATÊNCIA':<15}")
        print("-" * 80)
        
        if not network_health_map:
            print("Nenhum contentor Docker registado no ecossistema até ao momento.")
        else:
            for c_id, info in list(network_health_map.items()):
                status_color = "\033[92mUP\033[0m" if info['status'] == "UP" else "\033[91mDOWN\033[0m"
                print(f"{c_id:<15} | {info['ip']:<15} | {info['port']:<6} | {status_color:<17} | {info['rtt']:<15}")
                
        print("=" * 80)
        print("Pressione Ctrl+C para sair do Dashboard.")
        time.sleep(2)

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\nDashboard encerrado.")