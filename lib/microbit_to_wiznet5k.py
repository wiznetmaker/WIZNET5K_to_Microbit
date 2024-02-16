from umqttsimple import MQTTClient
from usocket import socket

    
class Microbit_to_wiznet5k:
    def __init__(self, uart):
        self._uart = uart
        self.mb_mqtt= Microbit_to_wiznet5k_Mqtt(uart)

    def do_process(self):
        self.check_uart_form_microbit()
        #self.recv_data_from_ethernet()
        
    def check_uart_form_microbit(self):
        if not self._uart.any():
            return
        
        full_message = ''
        while self._uart.any():
            message_segment = self._uart.read(1)
            full_message += message_segment.decode('utf-8')
    
        full_message = full_message.strip()
        print("recv data from microbit:", full_message)
        self.parse_command(full_message)
        
    def recv_data_from_ethernet (self):
        self.mb_mqtt.mqtt_subscribe_message()
        #http
        #tcp 
        
    def send_data_to_uart(self, data):
        print("send data to uart:", data)
        self.uart.write(data)

    def parse_command(self, message):
        parts = message.split('=', 1)  # '='를 기준으로 최대 1번 분할
        if len(parts) >= 1:
            command_part = parts[0]
            data = parts[1] if len(parts) == 2 else None  # 데이터가 없는 경우 None 할당
            
            if command_part.startswith('AT+'):
                self.handle_command(command_part[3:], data)  # 'AT+' 제거 후 명령어 처리
            else:
                print("Invalid command format:", command_part)
        else:
            print("Invalid message format:", message)
    
    def handle_command(self, command, data):
        ignore_commands = { 'RST','RESTORE',
                            'CWMODE','CWLAPOPT', 'CWLAP', 'CWJAP',
                            'SYSTIMESTAMP', 'CIPSNTPCFG'}
        
        if command == 'MQTTUSERCFG': 
            self.mb_mqtt.mqtt_set_user_config(data)
        elif command == 'MQTTCONN':
            self.mb_mqtt.mqtt_connect_broker(data)
        elif command == 'MQTTPUB':
            self.mb_mqtt.mqtt_publish_message(data)                     
        elif command in ignore_commands:
            return
        else:
            print("Unknown command:", command)
        return

class Microbit_to_wiznet5k_Mqtt:
    def __init__(self, uart, sub_cb= None):
        self.uart= uart
        self.mqtt_client= None
        
        if sub_cb is None:
            self.sub_callback= self.mqtt_subscribe_default_cb
        else:            
            self.sub_callback= sub_cb
    
    def mqtt_is_client_null():
        if self.mqtt_client is None:
            return False
        else:
            return True
    
    def mqtt_set_user_config (self, data):
        parts = data.split(',')
        
        #LinkID = int(parts[0])
        #scheme = int(parts[1])
        self.mqtt_cli_id = parts[2].replace('"', "'")
        self.username = parts[3].replace('"', "'")
        self.password = parts[4].replace('"', "'")
        #cert_key_ID = int(parts[5])
        #CA_ID = int(parts[6])
        #path = parts[7].strip('"')
        print(f"user_config: Client ID: {self.mqtt_cli_id}, Username: {self.username}, Password: {self.password}")

    def mqtt_subscribe_message(self, topic = '#'): # Subscribe to all topics using '#' wildcard
        if self.mqtt_client is None:
            return        
        self.mqtt_client.subscribe(topic)
        
    def mqtt_subscribe_default_cb(self, topic, msg):
        full_message= topic+msg
        self.uart.write(full_message)        

    def mqtt_connect_broker(self, data):
        if self.mqtt_client is not None:            
            print("mqtt_client is initialized already.")
            return
        
        parts = data.split(',')
        if len(parts) != 4:
            print("Invalid number of arguments")
            return
            
        #client_id = parts[0]
        server_IP = parts[1].strip('"')
        port = int(parts[2])
        #reconnect = parts[3]
    
        print(f"connect_broker: Client ID: {self.mqtt_cli_id}, Server IP: {server_IP}, Port: {port}")

        self.mqtt_client = MQTTClient(self.mqtt_cli_id, server_IP, port, user= self.username, password= self.password, keepalive =60)
        self.mqtt_client.set_callback(self.sub_callback)
        self.mqtt_client.connect()
        
        print('Connected to %s MQTT Broker'%(server_IP))
        self.uart.write(b"OK")

    def mqtt_publish_message(self, data):      
        if self.mqtt_client is None:
            print("Error: mqtt_client is not initialized.")
            return
        
        parts = []
        while data:
            if data[0] == '"':
                end_quote_index = data.find('",')
                if end_quote_index != -1:
                    parts.append(data[1:end_quote_index])
                    data = data[end_quote_index+2:]
                else:
                    
                    end_quote_index = data.rfind('"')
                    if end_quote_index == -1 or end_quote_index == 0:
                        print("Invalid data format")
                        return None
                    parts.append(data[1:end_quote_index])
                    break  
            else:
                comma_index = data.find(',')
                if comma_index == -1:  
                    parts.append(data)
                    break
                parts.append(data[:comma_index])
                data = data[comma_index+1:]  

        if len(parts) != 5:
            print("Invalid number of arguments")
            return None

        #LinkID = int(parts[0])
        pub_topic = parts[1]
        pub_data = parts[2]
        #qos = int(parts[3])
        #retain = int(parts[4])
    
        print(f"Publish Topic: {pub_topic}, Publish Data: {pub_data}")
        self.mqtt_client.publish(pub_topic, pub_data)
