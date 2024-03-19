import hashlib
import socket
import threading

from config import PORT, HOST, MANUFACTURER_HOST, MANUFACTURER_PORT


class MobileAppServer:
    def __init__(self, host=HOST, port=PORT, manufacturer_host=MANUFACTURER_HOST, manufacturer_port=MANUFACTURER_PORT):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.users_file = 'users.txt'

        self.manufacturer_host = manufacturer_host
        self.manufacturer_port = manufacturer_port

        self.authenticated_clients = {}

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, *args):
        if len(args) != 3:
            raise ValueError('Invalid number of arguments')

        username, password, role = args

        if not username.isalnum() or not password.isalnum():
            raise ValueError('Invalid input, only letters and digits are allowed')

        if role not in ('owner', 'renter'):
            raise ValueError('Invalid role')

        with open(self.users_file, 'r') as f:
            for line in f:
                stored_username, _, _ = line.strip().split(',')
                if stored_username == username:
                    raise ValueError('Username already exists')

        hashed_password = self.hash_password(password)

        with open(self.users_file, 'a') as f:
            f.write(f'{username},{hashed_password},{role}\n')

    def authenticate_user(self, *args):
        if len(args) != 2:
            raise ValueError('Invalid number of arguments')

        username, password = args

        if not username.isalnum() or not password.isalnum():
            raise ValueError('Invalid input, only letters and digits are allowed')

        hashed_password = self.hash_password(password)

        with open(self.users_file, 'r') as f:
            for line in f:
                stored_username, stored_password, _ = line.strip().split(',')

                if stored_username == username and stored_password == hashed_password:
                    return True

        return False

    def send_to_manufacturer(self, client_id, client_type, message_id, payload):
        message = f"{client_id},{client_type},{message_id},{payload}"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.manufacturer_host, self.manufacturer_port))
                sock.sendall(message.encode('utf-8'))
                response = sock.recv(1024).decode('utf-8')
                print("teeeeessst", response)
                print(f"Response from manufacturer: {response}")
                return response
        except Exception as e:
            print(f"Failed to send message to manufacturer: {e}")

    def get_username_by_address(self, client_address):
        if client_address in self.authenticated_clients:
            return self.authenticated_clients[client_address]['username']
        else:
            return None

    def post_car(self, username, car_id, car_host, car_port):
        payload = f"{car_id},{car_host},{car_port}"
        response = self.send_to_manufacturer(username, '0', '2', payload)
        print(f"Car posted by {username}: {car_id}")
        return response

    def start_rent(self, username, car_id):
        payload = f"{car_id}"
        response = self.send_to_manufacturer(username, '0', '4', payload)
        print(f"Rental started by {username} for car {car_id}")
        return response

    def rent_car(self, username, car_id):
        payload = f"{car_id}"
        response = self.send_to_manufacturer(username, '1', '3', payload)
        print(f"Car requested by {username}: {car_id}")
        return response

    def end_rent(self, username, car_id):
        payload = f"{car_id}"
        response = self.send_to_manufacturer(username, '1', '5', payload)
        print(f"Rental ended by {username} with rental ID {car_id}")
        return response

    def handle_client(self, client_socket, client_address):
        print('Got a connection from', client_address)
        user_role = None

        try:
            while True:
                data = client_socket.recv(1024).decode('ascii')
                if not data:
                    break

                command, *args = data.split()

                if command == 'register':
                    try:
                        self.register_user(*args)
                        client_socket.send('User registered successfully.'.encode('ascii'))
                        if args[2] == 'renter':
                            message_id = '0'
                        elif args[2] == 'owner':
                            message_id = '1'
                        self.send_to_manufacturer(args[0], 'NA', message_id, 'hello')
                    except ValueError as e:
                        client_socket.send(f'Error: {str(e)}'.encode('ascii'))

                elif command == 'login':
                    if self.authenticate_user(*args):
                        with open(self.users_file, 'r') as f:
                            for line in f:
                                username, _, role = line.strip().split(',')
                                if username == args[0]:
                                    user_role = role
                                    break
                        self.authenticated_clients[client_address] = {'username': args[0], 'role': user_role}
                        client_socket.send('Login successful.'.encode('ascii'))
                    else:
                        client_socket.send('Login failed.'.encode('ascii'))

                elif client_address in self.authenticated_clients:
                    username = self.get_username_by_address(client_address)
                    if user_role == "owner":
                        if command == 'postcar':
                            if len(args) != 3:
                                client_socket.send('Invalid number of arguments.'.encode('ascii'))
                                continue
                            response = self.post_car(username, *args)
                            client_socket.send(response.encode('ascii'))
                        elif command == 'startrent':
                            response = self.start_rent(username, *args)
                            client_socket.send(response.encode('ascii'))
                        else:
                            client_socket.send('Invalid command or insufficient permissions.'.encode('ascii'))
                    elif user_role == "renter":
                        if command == 'rentcar':
                            response = self.rent_car(username, *args)
                            client_socket.send(response.encode('ascii'))
                        elif command == 'endrent':
                            response = self.end_rent(username, *args)
                            client_socket.send(response.encode('ascii'))
                        elif command == 'listcars':
                            response = self.send_to_manufacturer(username, '1', '6', 'hello')
                            client_socket.send(response.encode('ascii'))
                        else:
                            client_socket.send('Invalid command or insufficient permissions.'.encode('ascii'))
                    else:
                        client_socket.send('Invalid command or insufficient permissions.'.encode('ascii'))

                if data == 'exit':
                    if client_address in self.authenticated_clients:
                        del self.authenticated_clients[client_address]
                    print('Client requested to exit.')
                    break

        finally:
            client_socket.close()

    def start(self):
        self.server_socket.listen(5)
        print('Server listening on port:', self.port)

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                client_address = f"{addr[0]}:{addr[1]}"

                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.start()

        except KeyboardInterrupt:
            print("Server is shutting down.")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    server = MobileAppServer()
    server.start()
