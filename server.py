import socket
import threading
import logging

logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(message)s')

clients_data = {}
clients_lock = threading.Lock()

MAX_CONNECTIONS_PER_CLIENT = 2


def handle_client(conn, addr):
    try:
        data = conn.recv(1024).decode().strip()
        if not data.startswith('REGISTER'):
            conn.sendall('ERROR Invalid registration format\n'.encode())
            conn.close()
            return

        _, client_id, password = data.split()

        with clients_lock:
            if client_id not in clients_data:
                clients_data[client_id] = {
                    'password': password,
                    'counter': 0,
                    'connections': 1
                }
                conn.sendall('ACK Registration successful\n'.encode())
            else:
                client_info = clients_data[client_id]
                if password != client_info['password']:
                    conn.sendall('ERROR Invalid password\n'.encode())
                    conn.close()
                    return
                elif client_info['connections'] >= MAX_CONNECTIONS_PER_CLIENT:
                    conn.sendall('ERROR Maximum connections reached\n'.encode())
                    conn.close()
                    return
                else:
                    client_info['connections'] += 1
                    conn.sendall('ACK Registration successful\n'.encode())

        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            if data.upper() == 'LOGOUT':
                break
            action, amount = data.split()
            amount = int(amount)

            with clients_lock:
                client_info = clients_data[client_id]
                if action.upper() == 'INCREASE':
                    client_info['counter'] += amount
                elif action.upper() == 'DECREASE':
                    client_info['counter'] -= amount
                else:
                    conn.sendall('ERROR Invalid action\n'.encode())
                    continue

                # Log the counter change
                logging.info(f"Client {client_id} - Counter: {client_info['counter']}")
                conn.sendall(f"ACK Counter updated to {client_info['counter']}\n".encode())

    finally:
        with clients_lock:
            if client_id in clients_data:
                clients_data[client_id]['connections'] -= 1
                if clients_data[client_id]['connections'] == 0:

                    del clients_data[client_id]
        conn.close()


def start_server(host='0.0.0.0', port=5555):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    finally:
        server.close()


if __name__ == "__main__":
    start_server()
