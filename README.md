# Redes e Serviços - Tema 3 – Serviço de monitoria de Docker com MQTT

## Apresentação do projeto

### 1. Objetivos:

Este projeto foi desenvolvido na unidade curricular Redes e Serviços no curso de Engenharia Informática na Universidade de Aveiro com o âmbito de desenvolver um produto que seja capaz de monitorar um broker MQTT através do docker que satisfaça os seguintes requisitos:

* Criar um sistema de monitorização ativa para infraestruturas Docker, focando-se no ciclo de vida dos serviços.
* Cada serviço Docker deve ter um pequeno "agente" (script) que, ao arrancar, publica as suas coordenadas de rede (IP, Porta, ID) num tópico MQTT.
* O agente deve enviar sinais de "presença" periódicos (Heartbeat/Keepalive). Se o broker deixar de receber o sinal de um agente após X segundos, o serviço deve ser marcado como DOWN.
* Devem desenvolver um serviço que subscreva os tópicos de metadados e imprima em tempo real o mapa de saúde da rede de contentores (que contentores existem, quais as coordenadas, se estão down/up, qual o RTT do servidor para eles, etc.)
* O objetivo não é o dado do sensor, mas sim a telemetria do estado da rede e a gestão de disponibilidade dos serviços.

---

### 2. Autores e Responsabilidades

* Arthur Haerdy [@Haerdy](https://github.com/Haerdy)
    * role 1
    * role 2
* Geovana Mayer [@seuUsuario](seulink)
    * role 1
    * role 2
* Judy Chemane [@seuUsuario](seulink)
    * role 1
    * role 2

## 3. Estrutura do projeto

### 3.1 Baixando o projeto

1.  **Clonar o repositório:**
    ```sh
    git clone [https://github.com/(...))]([https://github.com/YourUsername/YourProject.git](https://github.com/(...)))
    ```
2.  **Navegar até a estrutura do projeto:**
    ```sh
    cd nextcloud
    ```

### 3.2 Estrutura do projeto
Ao inicializar o projeto pela primeira vez esta é a estrutura esperada:

```
adicionar quando estiver concluído.
```

### 3.3 inicializando o projeto

Para inicializar o projeto corretamente será necessário 3 instancias do terminal com suporte bash.

1. No primeiro terminal(1), insira os seguintes comandos para inicializar o container do docker:

   ```sh
   $ docker-compose up -d mosquitto
   ```

2. No mesmo terminal(1), instale o Mosquitto, inicie um ambiente virtual python (venv) e baixe a livraria python:
    ```sh
    $ sudo apt install mosquitto-clients
    $ python3 -m venv venv && source venv/bin/activate
    $ pip install "paho-mqtt==1.6.1"
    ```
3. E em seguida, ainda no terminal(1), inicie o arquivo dashboard.py, que será responsável por monitorizar as instâncias dos agentes:

    ```sh
    $ python3 dashboard.py
    ```
4. em outro terminal(2), entre no ambiente virtual e execute o seguinte comando para simular contentores:

    ```sh
    $ python3 -m venv venv && source venv/bin/activate
    $ MQTT_BROKER=localhost SERVICE_PORT=8081 python device.py
    ```

---
            _
        .__(.)< (quak)
        \___)