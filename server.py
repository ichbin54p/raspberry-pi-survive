import socket
import json
from threading import Thread
from time import sleep

class ServerData:
    class server:
        index = 0
        max_players = 5
        players = []
        start = False
    hazards = []

class Conn:
    def __init__(self, s: tuple[socket.socket, tuple], id):
        self.sock = s[0]
        self.ip = s[1]
        self.data = {}
        self.id = id
        self.auth = False
        self.run = True
        if self.id == 0:
            self.oid = 1
        else:
            self.oid = 0
    def recv(self):
        try: return json.loads(self.sock.recv(1024).decode())
        except: 
            print(f"failed to recieve json data from client {self.id} {self.data}")
            return False
    def send(self, d):
        try:
            self.sock.send(json.dumps(d).encode())
            return True
        except ConnectionError:
            print(f"faild to send {d} to client {self.id} {self.data}")
            return False
    def handle(self):
        print(f"Handling client {self.id}")
        while self.run:
            d = self.recv()
            if d:
                if not self.auth:
                    match d['op']:
                        case "auth":
                            self.data = {"username": d['d'], "pos": [0, 0], "exists": True, "id": self.id}
                            print(f"{self.id}: {self.data}")
                            ServerData.server.players[self.id] = self.data

                            if not self.send({"op": "data", "d": {"hazards": ServerData.hazards, "players": ServerData.server.players, "index": self.id}}):
                                self.run = False
                            self.auth = True
                        case _:
                            if not self.send({"op": "error", "d": "Authentication"}):
                                self.run = False
                else:
                    match d['op']:
                        case "update":
                            ServerData.server.players[self.id]['pos'][0] += d['d']['pos'][0]
                            ServerData.server.players[self.id]['pos'][1] += d['d']['pos'][1]

                            if ServerData.server.players[self.id]['pos'][0] > 7:
                                ServerData.server.players[self.id]['pos'][0] = 7
                            elif ServerData.server.players[self.id]['pos'][0] < 0:
                                ServerData.server.players[self.id]['pos'][0] = 0

                            if ServerData.server.players[self.id]['pos'][1] > 7:
                                ServerData.server.players[self.id]['pos'][1] = 7
                            elif ServerData.server.players[self.id]['pos'][1] < 0:
                                ServerData.server.players[self.id]['pos'][1] = 0
                            
                            if not self.send({"op": "update", "d": {"hazards": ServerData.hazards, "players": ServerData.server.players}}):
                                    self.run = False
                    
                    sleep(1/20)
            else:
                print(f"Breaking {self.id} {self.data}, failed to recieve.") 
                break
            
        print(f"Disconnecting client {self.run} {self.id} ({self.data})")
        ServerData.server.players[self.id] = {"exists": False}
        ServerData.server.index -= 1
        self.sock.close()

class main:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def listen(self):
        print("listening...")

        while True:
            Thread(target=Conn(self.sock.accept(), ServerData.server.index).handle, daemon=True).start()
            ServerData.server.index += 1
    def main(self):
        for _ in range(ServerData.server.max_players): ServerData.server.players.append({"exists": False})

        self.sock.bind(("127.0.0.1", 25565))
        self.sock.listen(ServerData.server.max_players)
        Thread(target=self.listen, daemon=True).start()

        try:
            while True:
                for i in range(len(ServerData.hazards)):
                    ServerData.hazards[i]['x'] += ServerData.hazards[i]['v'][0]
                    ServerData.hazards[i]['y'] += ServerData.hazards[i]['v'][1]
                sleep(0.7)
        except KeyboardInterrupt: self.sock.close()
if __name__ == "__main__":
    main().main()