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
    0: {'red': 22, 'yellow': 23, 'green': 24},
    1: {'red': 25, 'yellow': 26, 'green': 27},
    2: {'red': 28, 'yellow': 29, 'green': 30},
    3: {'red': 31, 'yellow': 32, 'green': 33}
}
for signal in SIGNAL_PINS.values():
    for pin in signal.values():
        board.digital[pin].mode = 1
        board.digital[pin].write(0)

def set_signal(signal_id, state):
    if signal_id not in SIGNAL_PINS:
        return
    pins = SIGNAL_PINS[signal_id]
    board.digital[pins['red']].write(1 if state == 'red' else 0)
    board.digital[pins['yellow']].write(1 if state == 'yellow' else 0)
    board.digital[pins['green']].write(1 if state == 'green' else 0)
    for sig in SIGNAL_PINS:
        if sig != signal_id:
            other_pins = SIGNAL_PINS[sig]
            board.digital[other_pins['red']].write(1)
            board.digital[other_pins['yellow']].write(0)
            board.digital[other_pins['green']].write(0)

class TrafficSystem:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1600, 900))
        pygame.display.set_caption("4-Lane Traffic System")
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.video_surfaces = {
            0: pygame.Surface((400, 300)),
            1: pygame.Surface((400, 300)),
            2: pygame.Surface((400, 300)),
            3: pygame.Surface((400, 300))
        }
        self.current_signal = 0
        self.previous_signal = -1
        self.next_change = time.time() + 5
        self.base_delays = {0: 5, 1: 5, 2: 5, 3: 5}
        self.adjusted_delays = {0: 5, 1: 5, 2: 5, 3: 5}
        self.weights = {0: 0, 1: 0, 2: 0, 3: 0}
        self.vehicle_counts = {0: {}, 1: {}, 2: {}, 3: {}}
        self.video_paused = {0: False, 1: True, 2: True, 3: True}
        self.caps = {0: None, 1: None, 2: None, 3: None}
        self.current_frames = {0: None, 1: None, 2: None, 3: None}
        self.calibration_mode = True
        self.calibration_start = time.time()
        self.calibration_duration = 5
        self.pause_overlays = {
            i: pygame.Surface((400, 300), pygame.SRCALPHA) for i in range(4)
        }
        for lane in range(4):
            self.pause_overlays[lane].fill((0, 0, 0, 128))
            pause_text = self.font.render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(200, 150))
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
            if (self.current_signal == lane_id or self.calibration_mode) and not self.video_paused[lane_id]:
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
                self.base_delays[lane_id] = max(5, math.ceil(weighted / 3.68))
                self.adjusted_delays[lane_id] = max(1, math.ceil(self.base_delays[lane_id] / 5))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.video_surfaces[lane_id] = pygame.transform.scale(frame, (400, 300))
            time.sleep(0.01)

    def get_next_lane(self):
        available_lanes = [i for i in range(4) if i != self.current_signal]
        available_weights = {lane: self.weights[lane] for lane in available_lanes}
        return max(available_weights.items(), key=lambda x: x[1])[0]

    def update_signals(self):
        now = time.time()
        if self.calibration_mode:
            if now - self.calibration_start >= self.calibration_duration:
                self.calibration_mode = False
                next_lane = max(self.weights.items(), key=lambda x: x[1])[0]
                self.switch_to_lane(next_lane)
            return
        if now >= self.next_change:
            set_signal(self.current_signal, 'yellow')
            self.next_change = now + 2
            for i in range(4):
                self.video_paused[i] = True
            next_lane = self.get_next_lane()
            self.next_change = now + 2
            self.switch_to_lane(next_lane)

    def switch_to_lane(self, lane_id):
        set_signal(self.current_signal, 'red')
        self.current_signal = lane_id
        set_signal(lane_id, 'green')
        self.next_change = time.time() + self.adjusted_delays[lane_id]
        for i in range(4):
            self.video_paused[i] = (i != lane_id)

    def draw_vehicle_info(self, lane_id, x, y):
        text_y = y
        weight_text = self.font.render(f"Lane {lane_id+1} Weight: {self.weights[lane_id]:.1f}", True, (255, 255, 255))
        self.screen.blit(weight_text, (x, text_y))
        text_y += 40
        original_delay_text = self.font.render(f"Original Delay: {self.base_delays[lane_id]}s", True, (200, 200, 255))
        self.screen.blit(original_delay_text, (x, text_y))
        text_y += 40
        adjusted_delay_text = self.font.render(f"Adjusted Delay: {self.adjusted_delays[lane_id]}s (÷5)", True, (255, 255, 0))
        self.screen.blit(adjusted_delay_text, (x, text_y))
        text_y += 40
        status_text = "Status: "
        if self.current_signal == lane_id:
            status_text += "Green"
            status_color = (0, 255, 0)
        else:
            status_text += "Red"
            status_color = (255, 0, 0)
        status_render = self.font.render(status_text, True, status_color)
        self.screen.blit(status_render, (x, text_y))
        text_y += 40
        count_title = self.small_font.render("Vehicle Counts:", True, (200, 200, 200))
        self.screen.blit(count_title, (x, text_y))
        text_y += 30
        for vehicle, count in self.vehicle_counts[lane_id].items():
            count_text = self.small_font.render(f"{vehicle}: {count}", True, (200, 200, 200))
            self.screen.blit(count_text, (x, text_y))
            text_y += 20
        if self.calibration_mode:
            calib_text = self.small_font.render("CALIBRATING...", True, (255, 165, 0))
            self.screen.blit(calib_text, (x, text_y))

    def draw_signal_status(self, lane_id, x, y):
        if 0 <= lane_id <= 3:
            if self.current_signal == lane_id:
                state = 'green'
            else:
                state = 'red'
        pygame.draw.rect(self.screen, (70, 70, 70), (x-30, y-100, 60, 200))
        colors = ['red', 'yellow', 'green']
        for i, color in enumerate(colors):
            light_color = (255, 0, 0) if color == 'red' else (255, 255, 0) if color == 'yellow' else (0, 255, 0)
            pygame.draw.circle(self.screen,
                             light_color if state == color else (40, 40, 40),
                             (x, y - 50 + i*60), 20)

    def run(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.submit(self.process_video, "vecteezy_busy-traffic-on-the-highway_6434705.mp4", 0)
            executor.submit(self.process_video, "donka.mp4", 1)
            executor.submit(self.process_video, "donka.mp4", 2)
            executor.submit(self.process_video, "vecteezy_busy-traffic-on-the-highway_6434705.mp4", 3)
            set_signal(0, 'green')
            for i in range(1, 4):
                set_signal(i, 'red')
            for i in range(4):
                self.video_paused[i] = False
            clock = pygame.time.Clock()
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                self.update_signals()
                self.screen.fill((50, 50, 50))
                self.screen.blit(self.video_surfaces[0], (600, 50))
                self.screen.blit(self.video_surfaces[1], (1000, 300))
                self.screen.blit(self.video_surfaces[2], (600, 550))
                self.screen.blit(self.video_surfaces[3], (200, 300))
                for lane in range(4):
                    if self.video_paused[lane]:
                        if lane == 0:
                            self.screen.blit(self.pause_overlays[lane], (600, 50))
                        elif lane == 1:
                            self.screen.blit(self.pause_overlays[lane], (1000, 300))
                        elif lane == 2:
                            self.screen.blit(self.pause_overlays[lane], (600, 550))
                        elif lane == 3:
                            self.screen.blit(self.pause_overlays[lane], (200, 300))
                self.draw_signal_status(0, 700, 400)
                self.draw_signal_status(1, 900, 400)
                self.draw_signal_status(2, 700, 600)
                self.draw_signal_status(3, 500, 400)
                self.draw_vehicle_info(0, 600, 370)
                self.draw_vehicle_info(1, 1000, 620)
                self.draw_vehicle_info(2, 600, 870)
                self.draw_vehicle_info(3, 200, 620)
                pygame.display.flip()
                clock.tick(60)
            for i in range(4):
                set_signal(i, 'red')
                if self.caps[i] is not None:
                    self.caps[i].release()
            board.exit()
            pygame.quit()

def test_all_leds():
    for color in ['red', 'yellow', 'green']:
        for sig in SIGNAL_PINS:
            set_signal(sig, color)
            time.sleep(0.5)
            set_signal(sig, 'red')
    print("LED test complete")

if __name__ == "__main__":
    test_all_leds()
    system = TrafficSystem()
    system.run()