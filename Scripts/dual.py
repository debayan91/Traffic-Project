import cv2
import numpy as np
from ultralytics import YOLO
import math
import time
import pygame
from concurrent.futures import ThreadPoolExecutor
from pyfirmata2 import ArduinoMega

model = YOLO("yolov8n.pt")

board = ArduinoMega("/dev/tty.usbserial-1130")

SIGNAL_PINS = {
    1: {'red': 22, 'yellow': 23, 'green': 24},
    2: {'red': 25, 'yellow': 26, 'green': 27}
}

for signal in SIGNAL_PINS.values():
    for pin in signal.values():
        board.digital[pin].mode = 1
        board.digital[pin].write(0)

def set_signal(signal_id, state):
    for color, pin in SIGNAL_PINS[signal_id].items():
        board.digital[pin].write(1 if color == state else 0)

class TrafficSystem:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1600, 900))
        pygame.display.set_caption("Dual Traffic System")
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.video_surfaces = {
            1: pygame.Surface((500, 375)),
            2: pygame.Surface((500, 375))
        }
        
        self.current_signal = 1  # 1 or 2 for green, 0 or 3 for yellow
        self.next_change = time.time() + 5
        self.base_delays = {1: 0, 2: 0}  # Original calculated delays
        self.adjusted_delays = {1: 5, 2: 5}  # Delays divided by 5
        self.weights = {1: 0, 2: 0}
        self.vehicle_counts = {1: {}, 2: {}}
        self.video_paused = {1: False, 2: False}
        self.caps = {1: None, 2: None}
        self.current_frames = {1: None, 2: None}
        
        # Create pause overlays
        self.pause_overlays = {
            1: pygame.Surface((500, 375), pygame.SRCALPHA),
            2: pygame.Surface((500, 375), pygame.SRCALPHA)
        }
        for lane in [1, 2]:
            self.pause_overlays[lane].fill((0, 0, 0, 128))
            pause_text = self.font.render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(250, 187))
            self.pause_overlays[lane].blit(pause_text, text_rect)

    def process_video(self, video_path, lane_id):
        classNames = [
            'ambulance', 'army vehicle', 'auto rickshaw', 'bicycle', 'bus',
            'car', 'garbagevan', 'human hauler', 'minibus', 'minivan',
            'motorbike', 'pickup', 'policecar', 'rickshaw', 'scooter',
            'suv', 'taxi', 'three wheelers -CNG-', 'truck', 'van', 'wheelbarrow'
        ]
        
        weights = {
            'ambulance': 10, 'army vehicle': 6, 'bus': 5, 'truck': 4,
            'car': 2, 'van': 3, 'suv': 3, 'motorbike': 1, 'scooter': 1,
            'bicycle': 0.5, 'auto rickshaw': 1.5, 'rickshaw': 1.5
        }

        self.caps[lane_id] = cv2.VideoCapture(video_path)
        cap = self.caps[lane_id]
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            self.current_frames[lane_id] = frame.copy()
            
            # Only process and update weights if this is the active lane
            if self.current_signal == lane_id and not self.video_paused[lane_id]:
                results = model(frame)[0]
                weighted = 0
                vehicle_count = {}
                
                for r in results:
                    for box in r.boxes:
                        cls = int(box.cls[0])
                        name = classNames[cls]
                        weighted += weights.get(name, 1)
                        vehicle_count[name] = vehicle_count.get(name, 0) + 1
                
                self.weights[lane_id] = weighted
                self.vehicle_counts[lane_id] = vehicle_count
                
                # Calculate original delay (from weight)
                self.base_delays[lane_id] = max(5, math.ceil(weighted / 3.68))
                # Calculate adjusted delay (divided by 5)
                self.adjusted_delays[lane_id] = max(1, math.ceil(self.base_delays[lane_id] / 5))
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.video_surfaces[lane_id] = pygame.transform.scale(frame, (500, 375))
            
            time.sleep(0.01)

    def update_signals(self):
        now = time.time()
        if now >= self.next_change:
            if self.current_signal == 1:  # Lane 1 green -> switch to yellow
                set_signal(1, 'yellow')
                set_signal(2, 'red')
                self.next_change = now + 2  # Fixed 2-second yellow duration
                self.current_signal = 0  # Transition state
                self.video_paused[1] = True
                self.video_paused[2] = True
            elif self.current_signal == 0:  # Lane 1 yellow -> switch to lane 2 green
                set_signal(1, 'red')
                set_signal(2, 'green')
                self.next_change = now + self.adjusted_delays[2]  # Use adjusted delay
                self.current_signal = 2
                self.video_paused[1] = True
                self.video_paused[2] = False
            elif self.current_signal == 2:  # Lane 2 green -> switch to yellow
                set_signal(2, 'yellow')
                set_signal(1, 'red')
                self.next_change = now + 2  # Fixed 2-second yellow duration
                self.current_signal = 3  # Transition state
                self.video_paused[1] = True
                self.video_paused[2] = True
            else:  # Lane 2 yellow -> switch to lane 1 green
                set_signal(2, 'red')
                set_signal(1, 'green')
                self.next_change = now + self.adjusted_delays[1]  # Use adjusted delay
                self.current_signal = 1
                self.video_paused[1] = False
                self.video_paused[2] = True

    def draw_vehicle_info(self, lane_id, x, y):
        text_y = y
        
        # Display weight information
        weight_text = self.font.render(f"Lane {lane_id} Weight: {self.weights[lane_id]:.1f}", True, (255, 255, 255))
        self.screen.blit(weight_text, (x, text_y))
        text_y += 40
        
        # Display original and adjusted delays
        original_delay_text = self.font.render(f"Original Delay: {self.base_delays[lane_id]}s", True, (200, 200, 255))
        self.screen.blit(original_delay_text, (x, text_y))
        text_y += 40
        
        adjusted_delay_text = self.font.render(f"Adjusted Delay: {self.adjusted_delays[lane_id]}s (÷5)", True, (255, 255, 0))
        self.screen.blit(adjusted_delay_text, (x, text_y))
        text_y += 40
        
        # Display signal status
        status_text = "Status: " + ("Green" if self.current_signal == lane_id else 
                                  "Yellow" if self.current_signal in [0, 3] and 
                                  ((lane_id == 1 and self.current_signal == 0) or 
                                   (lane_id == 2 and self.current_signal == 3)) else "Red")
        status_color = (0, 255, 0) if "Green" in status_text else (255, 255, 0) if "Yellow" in status_text else (255, 0, 0)
        status_render = self.font.render(status_text, True, status_color)
        self.screen.blit(status_render, (x, text_y))
        text_y += 40
        
        # Display vehicle counts
        count_title = self.small_font.render("Vehicle Counts:", True, (200, 200, 200))
        self.screen.blit(count_title, (x, text_y))
        text_y += 30
        
        for vehicle, count in self.vehicle_counts[lane_id].items():
            count_text = self.small_font.render(f"{vehicle}: {count}", True, (200, 200, 200))
            self.screen.blit(count_text, (x, text_y))
            text_y += 20

    def run(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.process_video, "vecteezy_busy-traffic-on-the-highway_6434705.mp4", 1)
            executor.submit(self.process_video, "vecteezy_busy-traffic-on-the-highway_6434705.mp4", 2)
            
            clock = pygame.time.Clock()
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                
                self.update_signals()
                
                self.screen.fill((50, 50, 50))
                
                # Display video feeds
                for lane in [1, 2]:
                    self.screen.blit(self.video_surfaces[lane], (50 if lane == 1 else 850, 50))
                    if self.video_paused[lane]:
                        self.screen.blit(self.pause_overlays[lane], (50 if lane == 1 else 850, 50))
                
                # Draw signal lights
                self.draw_signal_status(1, 350, 500)
                self.draw_signal_status(2, 1150, 500)
                
                # Draw vehicle information
                self.draw_vehicle_info(1, 50, 450)
                self.draw_vehicle_info(2, 850, 450)
                
                pygame.display.flip()
                clock.tick(60)
            
            # Cleanup
            set_signal(1, 'red')
            set_signal(2, 'red')
            for cap in self.caps.values():
                if cap is not None:
                    cap.release()
            board.exit()
            pygame.quit()

    def draw_signal_status(self, lane_id, x, y):
        if lane_id == 1:
            state = ('green' if self.current_signal == 1 else 
                    'yellow' if self.current_signal == 0 else 'red')
        else:
            state = ('green' if self.current_signal == 2 else 
                    'yellow' if self.current_signal == 3 else 'red')
        
        pygame.draw.rect(self.screen, (70, 70, 70), (x-30, y-100, 60, 200))
        
        colors = ['red', 'yellow', 'green']
        for i, color in enumerate(colors):
            light_color = (255, 0, 0) if color == 'red' else (255, 255, 0) if color == 'yellow' else (0, 255, 0)
            pygame.draw.circle(self.screen, 
                             light_color if state == color else (40, 40, 40),
                             (x, y - 50 + i*60), 20)

if __name__ == "__main__":
    system = TrafficSystem()
    system.run()