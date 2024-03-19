import socket

from config import PORT, HOST


class Client:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.host, self.port))

    def send(self, message):
        self.socket.send(message.encode('ascii'))

    def receive(self):
        return self.socket.recv(1024).decode('ascii')

    def close(self):
        self.socket.close()

    def execute(self):
        self.connect()
        try:
            while True:
                command = input("Enter command: ")
                self.send(command)
                if command == "exit":
                    print("Exiting.")
                    break
                response = self.receive()
                print("Response:", response)
        finally:
            self.close()


if __name__ == "__main__":
    client = Client()
    client.execute()
