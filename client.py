import socket
import json
import time
import re

def validate_config(config):

    required_keys = ['id', 'password', 'server_ip', 'server_port', 'actions']
    num_actions = 100

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")

    if not re.match(r'^[a-zA-Z0-9_]{3,50}$', config['id']):
        raise ValueError("Invalid client ID. Must be 3-50 alphanumeric characters")

    if not is_valid_password(config['password']):
        raise ValueError("Invalid password. Must be 8-100 characters with uppercase, lowercase, and digit")

    if not is_valid_ip(config['server_ip']):
        raise ValueError("Invalid server IP address")

    if not isinstance(config['server_port'], int) or config['server_port'] < 1 or config['server_port'] > 65535:
        raise ValueError("Invalid server port. Must be between 1 and 65535")

    if not config['actions'] or not isinstance(config['actions'], list):
        raise ValueError("Actions must be a non-empty list")

    for action in config['actions']:
        validate_action(action)

    if len(config['actions']) > num_actions:
        raise ValueError(f"Too many actions. Maximum allowed: {num_actions}")


def is_valid_password(password):

    if len(password) < 8 or len(password) > 50:
        return False

    has_upper = False
    has_lower = False
    has_digit = False

    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True

    return has_upper and has_lower and has_digit

def is_valid_ip(ip):

    parts = ip.split('.')
    if len(parts) != 4:
        return False

    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def validate_action(action):

    max_delay = 60

    required_action_keys = ['action', 'amount', 'delay']
    for key in required_action_keys:
        if key not in action:
            raise ValueError(f"Missing required action key: {key}")

    if action['delay'] > max_delay:
        raise ValueError(f"Delay too long. Maximum allowed: {max_delay} seconds")

    if action['action'].upper() not in ['INCREASE', 'DECREASE']:
        raise ValueError(f"Invalid action type: {action['action']}. Must be INCREASE or DECREASE")

    if not isinstance(action['amount'], int) or action['amount'] <= 0:
        raise ValueError(f"Invalid amount: {action['amount']}. Must be a positive integer")

    if not isinstance(action['delay'], (int, float)) or action['delay'] < 0:
        raise ValueError(f"Invalid delay: {action['delay']}. Must be a non-negative number")

    try:
        if action['amount'] > 2**31 - 1:  # Max 32-bit signed integer
            raise ValueError(f"Amount too large, potential integer overflow: {action['amount']}")
    except OverflowError:
        raise ValueError(f"Integer overflow detected for amount: {action['amount']}")

def load_config(config_file):

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        validate_config(config)
        return config
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in configuration file")
    except Exception as e:
        raise ValueError(f"Configuration validation error: {e}")

def start_client(config):
    client_id = config['id']
    password = config['password']
    server_ip = config['server_ip']
    server_port = config['server_port']
    actions = config['actions']

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conn.connect((server_ip, server_port))

        # Registration
        conn.sendall(f"REGISTER {client_id} {password}\n".encode())
        response = conn.recv(1024).decode().strip()

        if not response.startswith('ACK'):
            print(f"Registration failed: {response}")
            return

        print(f"Registered successfully as {client_id}")

        # Perform actions
        for act in actions:
            time.sleep(act['delay'])
            action_msg = f"{act['action']} {act['amount']}\n"

            try:
                conn.sendall(action_msg.encode())
                response = conn.recv(1024).decode().strip()

                if not response.startswith('ACK'):
                    print(f"Action failed: {response}")
                    # Optional: break or continue based on error handling strategy
                else:
                    print(f"Server response: {response}")

            except Exception as e:
                print(f"Error sending action: {e}")
                break

        # Logout
        conn.sendall("LOGOUT\n".encode())

    except ConnectionRefusedError:
        print(f"Could not connect to server at {server_ip}:{server_port}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        config = load_config('client_config.json')
        start_client(config)
    except ValueError as e:
        print(f"Configuration error: {e}")