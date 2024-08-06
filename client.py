try:
    import pygame
except ImportError: print("Unless you are using a raspberry pi, please run \"pip install pygame\"")
import socket
import json
from time import sleep
from threading import Thread
try:
    from sense_hat import SenseHat
except ImportError: pass

class main:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mode = input("Mode (pygame/sense): ").lower() or "pygame"
        self.mac = (20, 190, 50)
        self.oac = (255, 255, 255)
        self.bac = (0, 0, 0)
        self.dac = (120, 20, 20)
        self.pbc = (30, 30, 100)
        self.rules = {}
        self.run = True
        self.id = 0

        self.fps = 20
        self.x = 0
        self.y = 0
        self.opindex = 0
        self.players = []
        self.hazards = []
        self.oldplayers = []
        self.point_blocks = []

        self.kdown = False
        self.moved = False

        match self.mode:
            case "pygame":
                pygame.init()
                self.window = pygame.display.set_mode((800, 800))
                self.clock = pygame.time.Clock()
                self.key = pygame.key.get_pressed()
            case "sense":
                self.sense = SenseHat()
            case _:
                exit(f"Unkown mode \"{self.mode}\"")
    def recv(self):
        try: return json.loads(self.sock.recv(1024).decode())
        except: return False
    def send(self, d):
        try:
            self.sock.send(json.dumps(d).encode())
            return True
        except json.JSONDecodeError:
            print(f"Failed to send {d} to server")
            return False
    def handle_conn(self):
        print("Starting connection loop...")
        while True:
            if not self.send({"op": "update", "d": {"pos": [self.x, self.y]}}):
                break
            else:
                self.x = 0
                self.y = 0
                self.moved = False

            d = self.recv()

            if d:
                self.players = d['d']['players']
                self.hazards = d['d']['hazards']
                self.point_blocks = d['d']['point_blocks']

                sleep(1/self.fps)
            else:
                exit("There was an error trying trying to recieve data from the server.")
    def pygame_draw(self):
        self.window.fill(self.bac)

        self.opindex = 0

        for player in self.players:
            if player['exists']:
                if player['id'] == self.id:
                    c = self.mac
                else:
                    c = self.oac
                try:
                    if player['points'] != self.oldplayers[self.opindex]['points']:
                        print(f"{player['username']} Has {player['points']} points")
                except KeyError:
                    print("There was a key error whilst comparing scores, it should be fixed in a moment. If it doesn't fix, please restart the server.")

                pygame.draw.rect(self.window, c, (player['pos'][0]*100, player['pos'][1]*100, 100, 100))
            
            self.opindex += 1
        
        self.oldplayers = self.players

        for pb in self.point_blocks:
            pygame.draw.rect(self.window, self.pbc, (pb['pos'][0]*100, pb['pos'][1]*100, 100, 100))

        for hazard in self.hazards:
            pygame.draw.rect(self.window, self.dac, (hazard['pos'][0]*100, hazard['pos'][1]*100, 100, 100))
    def main_pygame(self):
        while self.run:
            self.key = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                if event.type == pygame.KEYUP:
                    self.moved = False

            if not self.moved:
                if self.key[pygame.K_UP]:
                    self.y = -1
                    self.moved = True
                elif self.key[pygame.K_DOWN]:
                    self.y = 1
                    self.moved = True
                elif self.key[pygame.K_LEFT]:
                    self.x = -1
                    self.moved = True
                elif self.key[pygame.K_RIGHT]:
                    self.x = 1
                    self.moved = True

            self.pygame_draw()
            pygame.display.update()
            self.clock.tick(self.fps)

        pygame.quit()
    def he_sense(self):
        print("started listening for events...")
        while True:
            event = self.sense.stick.wait_for_event()
            
            if event.action == "pressed":
                if event.direction == "up":
                    self.y = -1
                    self.moved = True
                elif event.direction == "down":
                    self.y = 1
                    self.moved = True
                elif event.direction == "left":
                    self.x = -1
                    self.moved = True
                elif event.direction == "right":
                    self.x = 1
                    self.moved = True
            else:
                self.x = 0
                self.y = 0
    def main_sense(self):
        Thread(target=self.he_sense, daemon=True).start()
        try:
            while True:
                self.sense.clear(self.bac)
                self.opindex = 0
                
                try:
                    for hazard in self.hazards:
                        self.sense.set_pixel(hazard['pos'][0], hazard['pos'][1], self.dac)
                    for pb in self.point_blocks:
                        self.sense.set_pixel(pb['pos'][0], pb['pos'][1], self.pbc)
                    for player in self.players:
                        if player['exists']:
                            if player['id'] == self.id:
                                c = self.mac
                            else:
                                c = self.oac

                            try:
                                if player['points'] != self.oldplayers[self.opindex]['points']:
                                    print(f"{player['username']} Has {player['points']} points")
                            except KeyError:
                                print("There was a key error whilst comparing scores, it should be fixed in a moment. If it doesn't fix, please restart the server.", end="\r")

                            self.sense.set_pixel(player['pos'][0], player['pos'][1], c)
                        self.opindex += 1
        
                    self.oldplayers = self.players

                except ValueError:
                    print("Pixel out of range", end="\r")
                sleep(1/self.fps)
        except KeyboardInterrupt:
            self.sense.clear()
    def main(self):
        self.sock.connect((input("IP: ") or "127.0.0.1", int(input("PORT: ") or "25565")))

        if not self.send({"op": "auth", "d": input("Successfully connected\nUsername for auth: ")}):
            exit("There's a problem with the server")

        data = self.recv()

        if data:
            print(data)
            Thread(target=self.handle_conn, daemon=True).start()

            self.id = data['d']['index']
            self.players = data['d']['players']
            self.oldplayers = data['d']['players']

            if self.mode == "pygame":
                self.main_pygame()
            else:
                self.main_sense()
        else:
            print("There was an error trying to recieve data from the server.")

if __name__ == "__main__":
    main().main()