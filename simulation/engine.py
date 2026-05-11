import os
import sys
import random
import math
import time
import subprocess
import requests
import threading
import collections
import pygame
from network.protocols import PROTOCOLS
from ui.dashboard import Dashboard
from analytics.stats import AnalyticsReport

try:
    import traci
    from sumolib import checkBinary
except ImportError:
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
        import traci
        from sumolib import checkBinary
    else:
        print("Error: SUMO_HOME not found in environment.")

class Packet:
    def __init__(self, start_pos, end_pos, color):
        self.start = start_pos
        self.end = end_pos
        self.pos = list(start_pos)
        self.color = color
        self.speed = 0.08
        self.progress = 0
        self.finished = False

    def move(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            self.finished = True
        self.pos[0] = self.start[0] + (self.end[0] - self.start[0]) * self.progress
        self.pos[1] = self.start[1] + (self.end[1] - self.start[1]) * self.progress

class SimulationEngine:
    def __init__(self, config_path):
        self.config_path = config_path
        self.running = False
        self.paused = False
        self.width, self.height = 1280, 720
        self.zoom = 0.8
        self.offset = [0, 0]
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        
        self.vehicles = {}
        self.rsus = []
        self.packets = []
        self.current_protocol = "DSRC"
        self.step_count = 0
        self.total_packets_sent = 0
        self.total_packets_received = 0
        self.weather = "clear" # options: "clear", "rain", "fog"
        self.rain_drops = [(random.randint(0, self.width), random.randint(0, self.height)) for _ in range(100)]
        
        # Sliding window for dynamic, responsive PDR
        self.window_size = 200
        self.proto_history = {
            "DSRC": collections.deque(maxlen=self.window_size),
            "C-V2X": collections.deque(maxlen=self.window_size),
            "5G-V2X": collections.deque(maxlen=self.window_size)
        }
        
        self.color_bg = (10, 10, 15)
        self.color_road = (40, 45, 55)
        self.color_grid = (20, 25, 30)
        self.color_accent = (0, 242, 255)
        
        try:
            pygame.init()
            # Font initialization is delayed to init_fonts() to avoid circular import crash
            self.font_main = None
            self.font_bold = None
        except Exception as e:
            print(f"Pygame Init Warning: {e}")
            
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("CyberVANET | Research Command")
        self.clock = pygame.time.Clock()
        
        self.dashboard = Dashboard(self.screen)
        self.analytics = AnalyticsReport()
        self.road_shapes = []

    def init_fonts(self):
        if self.font_main is not None: return
        try:
            # Check if font module is ready
            if not pygame.font.get_init():
                pygame.font.init()
            font_path = "/System/Library/Fonts/Geneva.ttf"
            if os.path.exists(font_path):
                self.font_main = pygame.font.Font(font_path, 12)
                self.font_bold = pygame.font.Font(font_path, 14)
            else:
                self.font_main = pygame.font.SysFont("Arial", 12)
                self.font_bold = pygame.font.SysFont("Arial", 14, bold=True)
        except:
            # Silent fail to keep simulation running without labels if font is broken
            pass

    def start_traci(self):
        sumo_binary = "sumo-gui" 
        traci.start([sumo_binary, "-c", self.config_path, "--step-length", "0.1", "--start"])
        
        for edge_id in traci.edge.getIDList():
            shape = traci.lane.getShape(edge_id + "_0")
            self.road_shapes.append(shape)
            
        self.rsus = [
            RSU((500, 500), 400),
            RSU((1500, 1500), 400),
            RSU((1000, 0), 400)
        ]

    def run(self):
        self.start_traci()
        self.running = True
        threading.Thread(target=self.report_loop, daemon=True).start()
        
        while self.running:
            self.init_fonts() # Safe initialization during loop
            self.handle_events()
            if not self.paused:
                self.update()
            self.render()
            self.clock.tick(30)
            
        traci.close()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_1: self.current_protocol = "DSRC"
                elif event.key == pygame.K_2: self.current_protocol = "C-V2X"
                elif event.key == pygame.K_3: self.current_protocol = "5G-V2X"
                elif event.key == pygame.K_r: self.weather = "rain" if self.weather != "rain" else "clear"
                elif event.key == pygame.K_f: self.weather = "fog" if self.weather != "fog" else "clear"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:
                    self.zoom *= 1.1
                elif event.button == 5:
                    self.zoom /= 1.1
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx = (event.pos[0] - self.last_mouse_pos[0]) / self.zoom
                    dy = (event.pos[1] - self.last_mouse_pos[1]) / self.zoom
                    self.offset[0] += dx
                    self.offset[1] -= dy
                    self.last_mouse_pos = event.pos
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

    def update(self):
        traci.simulationStep()
        self.step_count += 1
        active_veh_ids = traci.vehicle.getIDList()
        if len(active_veh_ids) < 10:
            self.spawn_vehicle()

        for vid in active_veh_ids:
            pos = traci.vehicle.getPosition(vid)
            angle = traci.vehicle.getAngle(vid)
            speed = traci.vehicle.getSpeed(vid)
            
            if vid not in self.vehicles:
                from .vehicle import Vehicle
                self.vehicles[vid] = Vehicle(vid, pos, angle, self.current_protocol)
            else:
                self.vehicles[vid].update(pos, angle, speed)
            
            if self.step_count % 20 == 0:
                self.simulate_v2x(self.vehicles[vid])

        self.vehicles = {vid: v for vid, v in self.vehicles.items() if vid in active_veh_ids}
        for p in self.packets[:]:
            p.move()
            if p.finished:
                self.packets.remove(p)

    def spawn_vehicle(self):
        try:
            vid = f"veh_{self.step_count}_{random.randint(0,1000)}"
            routes = traci.route.getIDList()
            if routes:
                traci.vehicle.add(vid, random.choice(routes))
        except:
            pass

    def simulate_v2x(self, sender):
        proto = PROTOCOLS[self.current_protocol]
        
        for vid, receiver in self.vehicles.items():
            if vid == sender.vid: continue
            dist = math.sqrt((sender.pos[0]-receiver.pos[0])**2 + (sender.pos[1]-receiver.pos[1])**2)
            
            # Distance Attenuation (Inverse Square Law approximation)
            dist_factor = max(0.1, 1.0 - (dist / proto.range_m)**2)
            
            if dist < proto.range_m:
                # Signal noise + Weather
                noise = random.uniform(-0.03, 0.03)
                rel = (proto.reliability * dist_factor) + noise
                if self.weather == "rain": rel *= 0.80
                elif self.weather == "fog": rel *= 0.60

                success = random.random() < rel
                self.proto_history[self.current_protocol].append(1 if success else 0)
                
                if success:
                    self.packets.append(Packet(sender.pos, receiver.pos, proto.packet_color))
                    sender.signal_wave_radius = 1
            else:
                # Count out-of-range as a missed attempt for the window
                self.proto_history[self.current_protocol].append(0)

    def report_loop(self):
        while self.running:
            try:
                report_data = {}
                for p_name, protocol in PROTOCOLS.items():
                    history = self.proto_history[p_name]
                    pdr = (sum(history) / len(history) * 100) if len(history) > 0 else 0
                    
                    stability = self.calculate_stability_score(pdr, p_name)
                    
                    key = p_name.replace("-V2X", "").replace("-", "")
                    if key == "C": key = "CV2X"
                    
                    report_data[key] = {
                        "vehicle_count": len(self.vehicles),
                        "pdr": pdr,
                        "packets_sent": len(history),
                        "packets_received": sum(history),
                        "stability": stability,
                        "latency": protocol.latency_ms + random.uniform(-1, 1) # Jitter
                    }
                
                if "5GV2X" in report_data: report_data["5G"] = report_data["5GV2X"]
                
                # Send weather state
                report_data["weather"] = self.weather
                
                requests.post(f"http://127.0.0.1:5001/update_stats?active={self.current_protocol.replace('-V2X','')}", json=report_data)
            except:
                pass
            time.sleep(1)

    def calculate_stability_score(self, pdr, proto):
        # Dynamic Stability Factor based on congestion and noise
        veh_count = len(self.vehicles)
        congestion_factor = max(0.6, 1.0 - (veh_count / 100.0))
        
        vr = 0.8 * congestion_factor
        ds = 0.7 + random.uniform(-0.1, 0.1) # Distance noise
        ld = 1.0 - (PROTOCOLS[proto].latency_ms / 50.0)
        df = pdr / 100.0
        
        score = (0.2 * vr + 0.2 * ds + 0.3 * ld + 0.3 * df) * 100
        return min(100, max(10, score)) # Minimum 10% stability

    def traci_to_pygame(self, x, y):
        px = (x + self.offset[0]) * self.zoom + self.width / 2
        py = (-y + self.offset[1]) * self.zoom + self.height / 2
        return int(px), int(py)

    def render(self):
        self.screen.fill(self.color_bg)
        
        grid_size = int(100 * self.zoom)
        if grid_size > 5:
            for x in range(0, self.width, grid_size):
                pygame.draw.line(self.screen, self.color_grid, (x, 0), (x, self.height))
            for y in range(0, self.height, grid_size):
                pygame.draw.line(self.screen, self.color_grid, (0, y), (self.width, y))

        for shape in self.road_shapes:
            points = [self.traci_to_pygame(p[0], p[1]) for p in shape]
            if len(points) > 1:
                pygame.draw.lines(self.screen, self.color_road, False, points, max(1, int(8 * self.zoom)))

        self.draw_weather_effects()

        for p in self.packets:
            px, py = self.traci_to_pygame(*p.pos)
            pygame.draw.circle(self.screen, p.color, (px, py), max(2, int(5 * self.zoom)))

        for vid, veh in self.vehicles.items():
            px, py = self.traci_to_pygame(veh.pos[0], veh.pos[1])
            color = PROTOCOLS[veh.protocol].packet_color
            
            car_w, car_h = int(14 * self.zoom), int(28 * self.zoom)
            car_surf = pygame.Surface((car_w, car_h), pygame.SRCALPHA)
            pygame.draw.rect(car_surf, color, (0, 0, car_w, car_h), border_radius=int(4*self.zoom))
            pygame.draw.rect(car_surf, (20, 20, 20), (int(2*self.zoom), int(4*self.zoom), car_w - int(4*self.zoom), int(5*self.zoom)))
            
            rotated_car = pygame.transform.rotate(car_surf, -veh.angle + 90)
            rect = rotated_car.get_rect(center=(px, py))
            self.screen.blit(rotated_car, rect)
            
            if self.zoom > 0.5:
                label_y = py - car_h - 5
                self.draw_text(f"{veh.vid}", px - 15, label_y, (200, 200, 200), self.font_main)

            if veh.signal_wave_radius > 0:
                alpha = int((1 - veh.signal_wave_radius/PROTOCOLS[veh.protocol].range_m) * 150)
                if alpha > 0:
                    pygame.draw.circle(self.screen, (*color, alpha), (px, py), int(veh.signal_wave_radius * self.zoom), 1)
                veh.signal_wave_radius += 12
                if veh.signal_wave_radius > PROTOCOLS[veh.protocol].range_m:
                    veh.signal_wave_radius = 0

        pygame.display.flip()

    def draw_weather_effects(self):
        if self.weather == "rain":
            for i in range(len(self.rain_drops)):
                x, y = self.rain_drops[i]
                pygame.draw.line(self.screen, (100, 150, 255, 150), (x, y), (x - 3, y + 10), 1)
                self.rain_drops[i] = (x - 2, (y + 12) % self.height)
                if self.rain_drops[i][0] < 0: self.rain_drops[i] = (self.width, self.rain_drops[i][1])
        elif self.weather == "fog":
            fog_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fog_surf.fill((150, 150, 160, 100))
            self.screen.blit(fog_surf, (0, 0))

    def draw_text(self, text, x, y, color=(255, 255, 255), font=None):
        if font:
            img = font.render(str(text), True, color)
            self.screen.blit(img, (x, y))

class RSU:
    def __init__(self, pos, comm_range):
        self.pos = pos
        self.comm_range = comm_range
        self.pulse = 0
