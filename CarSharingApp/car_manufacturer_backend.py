import socket
import threading

from config import MANUFACTURER_HOST, MANUFACTURER_PORT


class ManufacturerServer:
    def __init__(self, host=MANUFACTURER_HOST, port=MANUFACTURER_PORT):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))

    def send_message_to_car(self, host, port, message_id, message):
        payload = f"{message_id},{message}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, int(port)))
            sock.send(payload.encode('utf-8'))
            response = sock.recv(1024).decode('utf-8')
            print(f"Response from car at {host}:{port}: {response}")
            return response
        except ConnectionError:
            print(f"Failed to connect to car at {host}:{port}")
        finally:
            sock.close()

    def post_car(self, client_id, payload):
        id, host, port = payload.split(',')
        with open('car_list.txt', 'r') as file:
            lines = file.readlines()

        with open('car_list.txt', 'w') as file:
            for line in lines:
                car_id, _, _ = line.strip().split(',')
                if car_id == id:
                    file.write(f"{id},{host},{port}\n")
                else:
                    file.write(line)

            if id not in [line.strip().split(',')[0] for line in lines]:
                file.write(f"{id},{host},{port}\n")

        return self.send_message_to_car(host, port, '0', client_id)

    def look_for_car_in_file(self, car_id):
        with open('car_list.txt', 'r') as file:
            for line in file:
                id, host, port = line.strip().split(',')
                if id == car_id:
                    return host, port
        return None, None

    def get_all_available_cars(self):
        available_cars = []
        print('test123123')
        with open('car_list.txt', 'r') as file:
            print('testststst')
            for line in file:
                car_id, host, port = line.strip().split(',')
                if host and port:
                    response = self.command_to_car('test', car_id, '4')
                    print(response)
                if response == 'Good':
                    print('arrived here')
                    available_cars.append(car_id)

        if not available_cars:
            return 'No cars available'

        return ','.join(available_cars)

    def command_to_car(self, client_id, payload, message_id):
        car_id = payload

        host, port = self.look_for_car_in_file(car_id)
        if host and port:
            return self.send_message_to_car(host, port, message_id, client_id)
        else:
            return f"Car {car_id} not found"

    def handle_connection(self, client_socket, address):
        print(f"Connection from {address} has been established.")
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                print(message)

                client_id, client_type, message_id, payload = message.split(',', 3)

                if message_id == '2' and client_type == '0':
                    response = self.post_car(client_id, payload)
                elif message_id == '3' and client_type == '1':
                    response = self.command_to_car(client_id, payload, '1')
                elif message_id == '4' and client_type == '0':
                    response = self.command_to_car(client_id, payload, '2')
                elif message_id == '5' and client_type == '1':
                    response = self.command_to_car(client_id, payload, '3')
                elif message_id == '6' and client_type == '1':
                    response = self.get_all_available_cars()
                else:
                    response = "Invalid message ID"
                print(f"Message from {address}: {message}")
                client_socket.send(response.encode('utf-8'))
            except ConnectionResetError:
                break
        client_socket.close()

    def start(self):
        self.socket.listen(5)
        print(f"Manufacturer server listening on {self.host}:{self.port}")
        while True:
            client_socket, address = self.socket.accept()
            thread = threading.Thread(target=self.handle_connection, args=(client_socket, address))
            thread.start()


if __name__ == "__main__":
    server = ManufacturerServer()
    server.start()
