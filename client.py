import socket
import json
import time

from support_methods import validate_config


class Client:

    def __init__(self):
        # Create socket

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

        # Use data from the config to connect to the server
        self.socket.connect((self.host_ip, self.port))
        # Register in the server
        self.send(f"REGISTER {self.id} {self.password}\n")

        print(self.receive())

    def send(self, msg: str):
        # Send the message to the server
        try:
            self.socket.sendall(msg.encode())
        except socket.error as err:
            print(f"{self.id}: Message {msg} was not sent. The following error occurred: {err}")


    def receive(self, buffer_size = 1024) -> str:
        # Save message received from the server
        try:
            received_msg = self.socket.recv(buffer_size).decode()

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
    # It's expected that some errors occur, while executing following code. I was testing how does it handle password mismatch
    # and such things
    client1 = Client()
    client1.load_config(json.loads(open("./configs/client1.json").read()))
    client1.connect()

    # client2 = Client()
    # client2.load_config(json.loads(open("./configs/client2.json").read()))
    # client2.connect()
    #
    # client3 = Client()
    # client3.load_config(json.loads(open("./configs/client3.json").read()))
    # client3.connect()
    # client3.execute_routines()

    client1.execute_routines()
    client1.close()
    # client2.close()
    # client3.close()