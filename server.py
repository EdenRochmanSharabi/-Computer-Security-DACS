import os
import pathlib
import socket
import ssl
import threading
import logging
import bcrypt


from support_methods import is_valid_password

MAX_CLIENT_CONNECTIONS = 2
MAX_INT_VALUE = 2 ** 31 - 1 # limiting value for integer
DEBUG = True

ssl_context = None # create global ssl context

def generate_ssl_certificates():
    """
    Generate self-signed SSL certificates for secure communication.
    In a production environment, use properly signed certificates.
    """

    # Ensure certificates directory exists
    cert_dir = pathlib.Path('certificates')
    cert_dir.mkdir(exist_ok=True)

    # Generate server private key
    os.system('openssl genrsa -out certificates/server.key 2048')

    # Generate self-signed certificate
    os.system(f'openssl req -new -x509 -key certificates/server.key -out certificates/server.crt -days 365 \
        -subj "/C=US/ST=YourState/L=YourCity/O=YourOrganization/OU=YourUnit/CN=localhost"')


    global ssl_context # use ssl context from outer scope
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # Configure server-side SSL
    ssl_context.load_cert_chain(
        certfile="certificates/server.crt",
        keyfile="certificates/server.key",
    )

def register_client(client_id: str, password: str) -> str:
    # Check password validity
    if not is_valid_password(password):
        logging.error(f"{client_id if DEBUG else ''}: Password doesn't fulfill requirements. Registration refused")
        return f"ERROR: Password doesn't fulfill requirements. Registration refused"

    # Register new client if not presented in the database
    if client_id not in client_database:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        client_database[client_id] = {
            'password': hashed_password,
            'counter': 0,
            'connections': 1
        }

        logging.info(f"Registered client {client_id if DEBUG else ''}")
        return f"ACK Client registered."

    if not bcrypt.checkpw(password.encode(), client_database[client_id]['password'].encode()):
        logging.error(f"{client_id if DEBUG else ''}: Client password mismatch. Registration refused")
        return f"ERROR:  Client password mismatch. Registration refused"

    # Update already existing client data
    if client_database[client_id]["connections"] == MAX_CLIENT_CONNECTIONS:
        logging.warning(f"Client {client_id if DEBUG else ''} is already registered. Connection refused, as limit per client is reached")
        return f"ACK Client is already registered. Connection refused, as limit per client is reached"

    client_database[client_id]["connections"] += 1
    logging.info(f"Client {client_id if DEBUG else ''} is already registered. Connection added instead")
    return f"ACK Client is already registered. Connection added instead"


def disconnect_client(client_id: str) -> str:
    # Reduce amount of connected instances
    client_database[client_id]['connections'] -= 1

    # Erase all data about client if no instances are present
    if client_database[client_id]['connections'] == 0:
        client_database.pop(client_id)
        return f"ACK Last instance of client {client_id if DEBUG else ''} disconnected. All data erased"

    return f"ACK Instance of client disconnected. All data erased"


def execute_action(client_id: str, action: str) -> str:
    try:
        action_type = action.split(" ")[0]
        print(action.split(" ")[1].strip("[]"))
        amount = min(int(action.split(" ")[1].strip("[]")), MAX_INT_VALUE)
    except ValueError: # Catch incorrect action values
        logging.warning(f"{client_id if DEBUG else ''}: Action ignored. Action value is not supported. Should be int")
        return f"WARNING: Action ignored. Action value is not supported. Should be int"

    except IndexError:
        logging.warning(f"{client_id if DEBUG else ''}: Action ignored. Missing action value")
        return f"WARNING: Action ignored. Missing action value"

    if action_type.upper() == "INCREASE":
        client_database[client_id]['counter'] += amount

    elif action_type.upper() == "DECREASE":
        client_database[client_id]['counter'] -= amount

    else:
        logging.warning(f"{client_id if DEBUG else ''}: Action ignored. Action type {action_type} not supported")
        return f"WARNING: Action ignored. Action type {action_type} not supported"

    if DEBUG:
        logging.info(f"{client_id} {action_type.lower()}d counter by {amount}. New value: {client_database[client_id]['counter']}\n")

    return f"ACK counter updated"


def handle_client(client_socket):
    try:
        msg = client_socket.recv(1024).decode().strip()

        if not msg.startswith("REGISTER"):
            client_socket.sendall("ERROR: Handling rejected. Registration format violated".encode())
            return

        _, client_id, password = msg.split(" ")

        response = register_client(client_id, password)
        client_socket.sendall(response.encode())

        while not response.startswith("ERROR"):
            print(client_database)
            msg = client_socket.recv(1024).decode().strip()

            if msg.startswith("EXECUTE"):
                response = execute_action(client_id, msg[8:])
                client_socket.sendall(response.encode())

            elif msg.startswith("DISCONNECT"):
                response = disconnect_client(client_id)
                client_socket.sendall(response.encode())

                break
        else:
            logging.error(response)


    except ssl.SSLError as ssl_err:
        logging.error(f"SSL Error in client handling: {ssl_err}")
    finally:
        client_socket.close()



if __name__ == '__main__':
    generate_ssl_certificates()

    # Create database and config
    client_database = dict()
    logging.basicConfig(filename='server.log', encoding='utf-8', level=logging.DEBUG)
    # Clear config
    open("server.log", "w").close()

    # create an INET, STREAMing socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind the socket to a public host, and a well-known port
    server_socket.bind(('localhost', 5000))
    # become a server socket
    server_socket.listen(5)

    # Wrap socket with SSL
    server_socket = ssl_context.wrap_socket(
        server_socket,
        server_side=True
    )

    while True:
        # accept connections from outside
        (client_socket, address) = server_socket.accept()

        # Process client socket. Assign thread to it and pro
        logging.info(f"Connection from: {address}")

        threading.Thread(target=handle_client, args=(client_socket,)).start()

