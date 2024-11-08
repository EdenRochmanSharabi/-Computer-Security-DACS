import socket
import json
import time

def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)

def start_client(config):
    client_id = config['id']
    password = config['password']
    server_ip = config['server_ip']
    server_port = config['server_port']
    actions = config['actions']
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((server_ip, server_port))

    try:
        conn.sendall(f"REGISTER {client_id} {password}\n".encode())
        response = conn.recv(1024).decode()
        if not response.startswith('ACK'):
            print(f"Registration failed: {response}")
            return

        print(f"Registered successfully as {client_id}")

        for act in actions:
            time.sleep(act['delay'])
            action_msg = f"{act['action']} {act['amount']}\n"
            conn.sendall(action_msg.encode())
            response = conn.recv(1024).decode()
            print(f"Server response: {response.strip()}")

        conn.sendall("LOGOUT\n".encode())

    finally:
        conn.close()

if __name__ == "__main__":
    config = load_config('client_config.json')
    start_client(config)
