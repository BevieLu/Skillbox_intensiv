"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                
                
                i = 0
                for client in self.server.clients:
                    #self.transport.write(client.login)
                    if client.login == self.login:
                        i += 1
                if i >= 2:
                    self.transport.write(
                        f"Имя, {self.login} уже занято\n".encode()
                    )
                    self.login = None
                    #self.server.clients.remove(self)
                else:
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.send_history()
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"{self.login}: {message}"
        encoded = format_string.encode()
        self.save_history(format_string)
        
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)
    
    def save_history(self, message):
        self.server.history.append(message)
    
    def send_history(self):
        self.transport.write(
            f"10 последних сообщений!".encode()
        )
        if len(self.server.history) >= 1:
            for mes in self.server.history[-10::1]:
                self.transport.write(
                    f"> {mes} ".encode()
                )
        else:
            self.transport.write(
                f"Сообщений после перезапуска сервера нет\n".encode()
            )
    
    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.transport.write(
            f"Список Участников чата: \n".encode()
        )
        for client in self.server.clients:
            if client.login != None:
                self.transport.write(
                    f"> {client.login} \n".encode()
                )
        self.server.clients.append(self)
        self.transport.write(
                        f"Введи логин\n".encode()
                    )
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
