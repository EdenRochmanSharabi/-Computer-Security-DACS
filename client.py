import os
import pathlib
import socket
import json
import ssl
import subprocess
import time

from server import ssl_context
from support_methods import validate_config


def verify_ssl_certificates():
    """
    Verify SSL certificates exist, otherwise create them.
    For production, replace this with proper certificate management.
    """
    cert_path = pathlib.Path('certificates/server.crt')

    if not cert_path.exists():
        print("Warning: Server certificate not found. Generating self-signed certificate.")
        os.system('''
        mkdir -p certificates
        openssl req -x509 -newkey rsa:4096 -keyout certificates/server.key -out certificates/server.crt \
        -days 365 -nodes -subj "/CN=localhost"
        ''')


class Client:

    def __init__(self, cert_path):
        if cert_path is not None:
            # Create SSL context
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            # Load CA certificates (for verifying server)
            self.ssl_context.load_verify_locations(cert_path)

            # Disable hostname checking for local development (remove in production)
            self.ssl_context.check_hostname = False

        else:
            raise ValueError("Certificate path is required.")

            # Create base socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.config = None
        self.action_steps = None
        self.action_delay = None
        self.port = None
        self.host_ip = None
        self.password = None
        self.id = None

    def load_config(self, config: dict):
        self.config = config

        # unpack the config
        try:
            self.id = config['id']
            self.password = config['password']
            self.host_ip = config['server']['ip']
            self.port = config['server']['port']
            self.action_delay = config['actions']['delay']
            self.action_steps = config['actions']['steps']
        except KeyError as key:
            self.config = None # reset config as it was not loaded correctly
            print(f"ERROR: Config loading failed. Key '{key.args[-1]}' not found")
            return

        try:
            validate_config(config)
        except ValueError as err:
            self.config = None
            print(f"ERROR: Config loading failed. Invalid configuration: {err}")
            return

        print("Config was loaded successfully")

    def connect(self):
        # Check whether config is set up
        if not self.config:
            print("Client is not configured. Please load the config file first!")
            return

        self.socket = self.ssl_context.wrap_socket(
            self.socket,
            server_hostname=self.host_ip
        )

        # Use data from the config to connect to the server
        self.socket.connect((self.host_ip, self.port))
        # Register in the server
        self.send(f"REGISTER {self.id} {self.password}\n")

        print(self.receive())

    def send(self, msg: str):
        # Send the message to the server
        try:
            self.socket.sendall(msg.encode())
        except ssl.SSLError as e:
            print(f"Message was not sent. SSL Error: {e}")
        except socket.error as err:
            print(f"{self.id}: Message {msg} was not sent. The following error occurred: {err}")


    def receive(self, buffer_size = 1024) -> str:
        # Save message received from the server
        try:
            received_msg = self.socket.recv(buffer_size).decode()
        except ssl.SSLError as e:
            print(f"Message was not sent. SSL Error: {e}")
            return ""
        except socket.error as err:
            print(f"{self.id}: Message was not received. The following error occurred: {err}")
            return ""

        return received_msg


    def close(self):
        if not self.config:
            print("Client is not configured. Please load the config file first!")
            return

        # Send notification to the server that client is being disconnected
        self.send(f"DISCONNECT")

        # Reset config
        self.config = None

        self.socket.close()

    def execute_routines(self):
        if not self.config:
            print("Client is not configured. Please load the config file first!")
            return

        if self.action_delay <= 0 or self.action_delay >= 10:
            print("WARNING: Incorrect action delay value. Default value 1 is used")
            self.action_delay = 1

        # Make a call to execute each step of the client's routine
        for step in self.action_steps:
            self.send(f"EXECUTE {step}")
            time.sleep(self.action_delay)

            print(self.receive())




if __name__ == "__main__":
    client1 = Client("certificates/server.crt")
    verify_ssl_certificates()
    client1.load_config(json.loads(open("./configs/client3.json").read())) # change here which client JSON file you would like to run : client1, client2, client3 are available 
    client1.connect()

    client1.execute_routines()
    client1.close()
