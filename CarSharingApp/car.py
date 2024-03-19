import socket
import threading


class Car:
    def __init__(self, id, host, port):
        self.id = id
        self.is_requested = False
        self.rented_by = None
        self.owner = None

        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))

    def handle_connection(self, client_socket, address):
        print(f"Connection from {address} has been established.")
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                command_id, payload = message.split(',')
                if command_id == '0':
                    if not self.owner:
                        self.owner = payload
                        client_socket.send('Car registered'.encode('utf-8'))
                    else:
                        client_socket.send('Car already registered'.encode('utf-8'))
                elif command_id == '1':
                    if self.is_requested or self.rented_by:
                        client_socket.send('Car already rented'.encode('utf-8'))
                    else:
                        self.is_requested = True
                        client_socket.send('Car requested'.encode('utf-8'))
                elif command_id == '2':
                    if self.is_requested:
                        self.is_requested = False
                        self.rented_by = payload
                        client_socket.send('Rental started'.encode('utf-8'))
                    else:
                        client_socket.send('Car not requested'.encode('utf-8'))
                elif command_id == '3':
                    if self.rented_by:
                        self.rented_by = None
                        client_socket.send('Rental ended'.encode('utf-8'))
                    else:
                        client_socket.send('Car not rented'.encode('utf-8'))
                elif command_id == '4':
                    if self.is_requested or self.rented_by:
                        client_socket.send('NA'.encode('utf-8'))
                    else:
                        client_socket.send('Good'.encode('utf-8'))
                else:
                    client_socket.send('Invalid command'.encode('utf-8'))
            except ConnectionResetError:
                break
        client_socket.close()

    def start(self):
        self.socket.listen(1)
        print(f"Car server listening on {self.host}:{self.port}")
        while True:
            client_socket, address = self.socket.accept()
            thread = threading.Thread(target=self.handle_connection, args=(client_socket, address))
            thread.start()


if __name__ == "__main__":
    car = Car(69, 'localhost', 50000)
    car.start()
