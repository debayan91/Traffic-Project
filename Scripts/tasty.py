
from tkinter import Tk
Tk().withdraw()  
import random
import time
import threading
import pygame
import sys
import math
import cv2
from tkinter import Tk, filedialog
try:
    from ultralytics import YOLO
except ImportError:
    print("YOLO not available - using default vehicle detection")
from pyfirmata2 import ArduinoMega


PORT = "/dev/tty.usbserial-1130"  
board = ArduinoMega(PORT)


LED_PINS = {
    0: {'red': 22, 'yellow': 23, 'green': 24}, 
    1: {'red': 25, 'yellow': 26, 'green': 27},  
    2: {'red': 28, 'yellow': 29, 'green': 30},  
    3: {'red': 31, 'yellow': 32, 'green': 33}  
}


for signal in LED_PINS.values():
    for pin in signal.values():
        board.digital[pin].mode = 1 
        board.digital[pin].write(0)  

def set_leds(signal_num, red, yellow, green):
    """Control all traffic signals with safety checks"""
    if signal_num not in LED_PINS:
        return
        

    pins = LED_PINS[signal_num]
    board.digital[pins['red']].write(red)
    board.digital[pins['yellow']].write(yellow)
    board.digital[pins['green']].write(green)
    
    # Ensure other signals show red
    for sig in LED_PINS:
        if sig != signal_num:
            other_pins = LED_PINS[sig]
            board.digital[other_pins['red']].write(1)  # Red ON
            board.digital[other_pins['yellow']].write(0)
            board.digital[other_pins['green']].write(0)

def test_all_leds():
    """Test sequence for all LEDs before starting"""
    for color in ['red', 'yellow', 'green']:
        for sig in LED_PINS:
            set_leds(sig, 
                   1 if color == 'red' else 0,
                   1 if color == 'yellow' else 0,
                   1 if color == 'green' else 0)
            time.sleep(0.5)
            set_leds(sig, 0, 0, 0)
    print("LED test complete")

# Initialize pygame with Mac-specific adjustments
pygame.init()

# Screen dimensions - adjusted for typical Mac display
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Intelligent Traffic Simulation")

# Signal control variables
noOfSignals = 4
currentGreen = 0
nextGreen = (currentGreen + 1) % noOfSignals
currentYellow = 0
signals = []

# Timing configuration
defaultGreen = {0: 15, 1: 15, 2: 15, 3: 15}
defaultRed = 150
defaultYellow = 3

# Vehicle configuration
speeds = {'car': 3.5, 'bus': 2.8, 'truck': 2.5, 'bike': 4, 'ambulance': 5}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike', 4: 'ambulance'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}
weights = {'car': 2, 'bus': 4, 'truck': 6, 'bike': 1, 'ambulance': 1000}

# Updated road alignment coordinates - 2 lanes per direction
x = {
    'right': [0, 0],  # 2 lanes
    'down': [730, 690], 
    'left': [1400, 1400], 
    'up': [610, 650]
}
y = {
    'right': [360, 395], 
    'down': [0, 0], 
    'left': [480, 440], 
    'up': [800, 800]
}

# Save the initial positions for vehicle generation
initial_x = x.copy()
initial_y = y.copy()

# Vehicle storage - updated for 2 lanes
vehicles = {
    'right': {0: [], 1: [], 'crossed': 0},
    'down': {0: [], 1: [], 'crossed': 0},
    'left': {0: [], 1: [], 'crossed': 0},
    'up': {0: [], 1: [], 'crossed': 0}
}

# Signal positions
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

# Stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Vehicle spacing
stoppingGap = 15
movingGap = 15

# Sprite group
simulation = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        
        # Add vehicle to appropriate data structure
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        
        # Load vehicle image with fallback - Mac path handling
        try:
            path = f"images/{direction}/{vehicleClass}.png"
            self.image = pygame.image.load(path)
        except pygame.error:
            try:
                path = f"images/{direction}/car.png"
                self.image = pygame.image.load(path)
            except pygame.error:
                # Create a colored rectangle as fallback
                colors = {'car': (255,0,0), 'bus': (0,255,0), 'truck': (0,0,255), 
                         'bike': (255,255,0), 'ambulance': (255,0,255)}
                color = colors.get(vehicleClass, (255,255,255))
                size = (30, 20) if vehicleClass != 'bike' else (20, 10)
                self.image = pygame.Surface(size)
                self.image.fill(color)
        
        # Calculate stop position based on vehicles ahead
        if (len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0):
            if (direction == 'right'):
                self.stop = vehicles[direction][lane][self.index - 1].stop - \
                            vehicles[direction][lane][self.index - 1].image.get_rect().width - stoppingGap
            elif (direction == 'left'):
                self.stop = vehicles[direction][lane][self.index - 1].stop + \
                            vehicles[direction][lane][self.index - 1].image.get_rect().width + stoppingGap
            elif (direction == 'down'):
                self.stop = vehicles[direction][lane][self.index - 1].stop - \
                            vehicles[direction][lane][self.index - 1].image.get_rect().height - stoppingGap
            elif (direction == 'up'):
                self.stop = vehicles[direction][lane][self.index - 1].stop + \
                            vehicles[direction][lane][self.index - 1].image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Set new starting position for next vehicle
        if (direction == 'right'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] -= temp
        elif (direction == 'left'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif (direction == 'down'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif (direction == 'up'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        
        simulation.add(self)

    def move(self):
        # Movement logic
        if (self.direction == 'right'):
            if (self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (
                    currentGreen == 0 and currentYellow == 0)) and (
                    self.index == 0 or self.x + self.image.get_rect().width < (
                    vehicles[self.direction][self.lane][self.index - 1].x - movingGap))):
                self.x += self.speed
        elif (self.direction == 'down'):
            if (self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if ((self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or (
                    currentGreen == 1 and currentYellow == 0)) and (
                    self.index == 0 or self.y + self.image.get_rect().height < (
                    vehicles[self.direction][self.lane][self.index - 1].y - movingGap))):
                self.y += self.speed
        elif (self.direction == 'left'):
            if (self.crossed == 0 and self.x < stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if ((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0)) and (
                    self.index == 0 or self.x > (
                    vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][
                self.index - 1].image.get_rect().width + movingGap))):
                self.x -= self.speed
        elif (self.direction == 'up'):
            if (self.crossed == 0 and self.y < stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if ((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0)) and (
                    self.index == 0 or self.y > (
                    vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][
                self.index - 1].image.get_rect().height + movingGap))):
                self.y -= self.speed

def countVehicles():
    counts = [0, 0, 0, 0]  # Total vehicles per direction
    noOfCars = [0, 0, 0, 0]
    noOfBuses = [0, 0, 0, 0]
    noOfTrucks = [0, 0, 0, 0]
    noOfBikes = [0, 0, 0, 0]
    noOfAmbulances = [0, 0, 0, 0]

    for i in range(noOfSignals):
        direction = directionNumbers[i]
        for lane in [0, 1]:  # Updated to 2 lanes
            for vehicle in vehicles[direction][lane]:
                if not vehicle.crossed:
                    if hasattr(vehicle, 'image'):
                        rect = vehicle.image.get_rect()
                        if direction == 'right':
                            if (vehicle.x + rect.width > stopLines[direction] - 330 and vehicle.x + rect.width < stopLines[direction]):
                                counts[i] += 1
                                if vehicle.vehicleClass == 'car':
                                    noOfCars[i] += 1
                                elif vehicle.vehicleClass == 'bus':
                                    noOfBuses[i] += 1
                                elif vehicle.vehicleClass == 'truck':
                                    noOfTrucks[i] += 1
                                elif vehicle.vehicleClass == 'bike':
                                    noOfBikes[i] += 1
                                elif vehicle.vehicleClass == 'ambulance':
                                    noOfAmbulances[i] += 1
                        elif direction == 'left':
                            if (vehicle.x < stopLines[direction] + 330 and vehicle.x > stopLines[direction]):
                                counts[i] += 1
                                if vehicle.vehicleClass == 'car':
                                    noOfCars[i] += 1
                                elif vehicle.vehicleClass == 'bus':
                                    noOfBuses[i] += 1
                                elif vehicle.vehicleClass == 'truck':
                                    noOfTrucks[i] += 1
                                elif vehicle.vehicleClass == 'bike':
                                    noOfBikes[i] += 1
                                elif vehicle.vehicleClass == 'ambulance':
                                    noOfAmbulances[i] += 1
                        elif direction == 'down':
                            if (vehicle.y + rect.height > stopLines[direction] - 330 and vehicle.y + rect.height < stopLines[direction]):
                                counts[i] += 1
                                if vehicle.vehicleClass == 'car':
                                    noOfCars[i] += 1
                                elif vehicle.vehicleClass == 'bus':
                                    noOfBuses[i] += 1
                                elif vehicle.vehicleClass == 'truck':
                                    noOfTrucks[i] += 1
                                elif vehicle.vehicleClass == 'bike':
                                    noOfBikes[i] += 1
                                elif vehicle.vehicleClass == 'ambulance':
                                    noOfAmbulances[i] += 1
                        elif direction == 'up':
                            if (vehicle.y < stopLines[direction] + 250 and vehicle.y > stopLines[direction]):
                                counts[i] += 1
                                if vehicle.vehicleClass == 'car':
                                    noOfCars[i] += 1
                                elif vehicle.vehicleClass == 'bus':
                                    noOfBuses[i] += 1
                                elif vehicle.vehicleClass == 'truck':
                                    noOfTrucks[i] += 1
                                elif vehicle.vehicleClass == 'bike':
                                    noOfBikes[i] += 1
                                elif vehicle.vehicleClass == 'ambulance':
                                    noOfAmbulances[i] += 1

    weighted = [0, 0, 0, 0]
    for i in range(4):
        weighted[i] = noOfCars[i] * weights['car'] + noOfBikes[i] * weights['bike'] + noOfBuses[i] * weights['bus'] + noOfTrucks[i] * weights['truck'] + noOfAmbulances[i] * weights['ambulance']
    
    return counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes, noOfAmbulances, weighted

def initialize():
    # Initialize traffic signals
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, defaultGreen[1])
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
    signals.append(ts4)
    
    # Start traffic control loop
    repeat()

def repeat():
    global currentGreen, currentYellow, nextGreen
    while True:
        counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes, noOfAmbulances, weighted = countVehicles()
        
        # Calculate green time based on vehicle counts and their average crossing times
        greenTime = max(weighted)
        maxIndex = weighted.index(greenTime)
        # Subtract ambulance weight to avoid disruption
        greenTime = greenTime - noOfAmbulances[maxIndex] * weights['ambulance']
        greenTime = max(5, min(60, greenTime))  # Minimum 5 seconds, maximum 60 seconds

        currentGreen = maxIndex
        signals[currentGreen].green = math.ceil(greenTime / 3.68)
        
        # Set Arduino lights to green for current signal
        set_leds(currentGreen, 0, 0, 1)
        
        # Green phase
        while (signals[currentGreen].green > 0):
            updateValues()
            time.sleep(1)
        
        # Yellow phase handling
        if counts[currentGreen] > 0:
            signals[currentGreen].yellow = min(3, max(1, counts[currentGreen] // 5))
        else:
            signals[currentGreen].yellow = 0
            
        currentYellow = 1
        
        # Set Arduino lights to yellow for current signal
        set_leds(currentGreen, 0, 1, 0)
        
        # Reset stop coordinates of lanes and vehicles
        for i in range(0, 2):  # Updated for 2 lanes
            for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen]]
        
        while (signals[currentGreen].yellow > 0):
            updateValues()
            time.sleep(1)
            
        # Switch to next signal
        currentYellow = 0

        # Set Arduino lights to red for current signal (next will be set to green)
        set_leds(currentGreen, 1, 0, 0)

        # Reset all signal times of current signal to default times
        signals[currentGreen].green = defaultGreen[currentGreen]
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed

        currentGreen = nextGreen
        nextGreen = (currentGreen + 1) % noOfSignals
        signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green

def updateValues():
    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            if i == nextGreen:
                signals[i].red = signals[currentGreen].yellow + signals[currentGreen].green
            else:
                signals[i].red = max(0, signals[i].red - 1)

class VehicleDetector:
    def __init__(self):
        self.model = None
        self.class_map = {
            'car': 'car', 'bus': 'bus', 'truck': 'truck',
            'motorcycle': 'bike', 'bicycle': 'bike', 'ambulance': 'ambulance'
        }
        try:
            # Try to load YOLO model
            self.model = YOLO('yolov8n.pt')
        except Exception as e:
            print(f"Could not initialize YOLO model: {e}")
            print("Using default vehicle detection instead")
    
    def detect_vehicles(self, image_path):
        if not image_path:
            return ['car', 'car', 'bus', 'truck']
            
        # If no model available, return default vehicles
        if not self.model:
            return ['car', 'car', 'bus', 'truck']
            
        try:
            img = cv2.imread(image_path)
            if img is None:
                print(f"Failed to load image: {image_path}")
                return ['car', 'car', 'bus']
                
            results = self.model(img)
            vehicles = []
            
            for box in results[0].boxes:
                cls = int(box.cls[0])
                name = results[0].names[cls]
                if name in self.class_map:
                    vehicles.append(self.class_map[name])
                    print(f"Detected {name} in {image_path}")
            
            # If no vehicles detected, return some default vehicles
            if not vehicles:
                return ['car', 'car', 'bus']
                
            print(f"Total vehicles detected in {image_path}: {len(vehicles)}")
            return vehicles
        except Exception as e:
            print(f"Error during detection: {e}")
            return ['car', 'car', 'bus']

def generate_vehicles(detections):
    # Reset the x and y positions to their initial values
    for direction in ['right', 'down', 'left', 'up']:
        x[direction] = initial_x[direction].copy()
        y[direction] = initial_y[direction].copy()
    
    # Process each direction's detections
    for dir_index, direction in enumerate(['right', 'down', 'left', 'up']):
        detected_vehicles = detections.get(direction, [])
        
        # Print what's been detected
        print(f"Detected in {direction} direction: {detected_vehicles}")
        
        # Generate detected vehicles across both lanes
        for i, vehicle_type in enumerate(detected_vehicles):
            # Ensure vehicle type is valid
            if vehicle_type not in speeds:
                vehicle_type = 'car'  # Default to car if unknown type
                
            # Alternate between lanes
            lane = i % 2
            
            # Create vehicle
            Vehicle(lane, vehicle_type, dir_index, direction)
            
            # Small delay to prevent vehicle overlap issues
            time.sleep(0.1)

class Simulation:
    def __init__(self):
        # Run hardware test first
        test_all_leds()
        
        # Load assets with fallbacks
        try:
            self.background = pygame.image.load('images/intersection.png')
        except:
            # Create a simple intersection background
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill((50, 50, 50))  # Dark gray background
            # Draw roads
            pygame.draw.rect(self.background, (100, 100, 100), (0, 350, SCREEN_WIDTH, 100))  # Horizontal
            pygame.draw.rect(self.background, (100, 100, 100), (650, 0, 100, SCREEN_HEIGHT))  # Vertical
            
        try:
            self.red_signal = pygame.image.load('images/signals/red.png')
        except:
            self.red_signal = pygame.Surface((30, 30))
            self.red_signal.fill((255, 0, 0))
            
        try:
            self.yellow_signal = pygame.image.load('images/signals/yellow.png')
        except:
            self.yellow_signal = pygame.Surface((30, 30))
            self.yellow_signal.fill((255, 255, 0))
            
        try:
            self.green_signal = pygame.image.load('images/signals/green.png')
        except:
            self.green_signal = pygame.Surface((30, 30))
            self.green_signal.fill((0, 255, 0))
            
        self.font = pygame.font.SysFont('Arial', 30)
        
        # Start vehicle detection and generation
        self.detect_vehicles()
        
        # Start simulation
        self.run_simulation()
    
    def detect_vehicles(self):
        # Hide the main Tk window
        root = Tk()
        root.withdraw()
        
        detector = VehicleDetector()
        detections = {}
        
        # Load images for each direction
        for direction in ['right', 'down', 'left', 'up']:
            print(f"Select image for {direction} direction traffic")
            try:
                path = filedialog.askopenfilename(
                    title=f"Select {direction} traffic image",
                    filetypes=[("Image files", "*.jpg *.jpeg *.png")]
                )
            except Exception as e:
                print(f"Error opening file dialog: {e}")
                path = None
                
            if path:
                # Detect vehicles in this image
                detected = detector.detect_vehicles(path)
                detections[direction] = detected
            else:
                # Use defaults if no image selected
                detections[direction] = ['car', 'bus', 'car', 'truck']
                print(f"No image selected for {direction}, using default vehicles")
        
        # Generate vehicles based on detections
        generate_vehicles(detections)
    
    def run_simulation(self):
        # Start traffic control thread
        traffic_thread = threading.Thread(target=initialize, daemon=True)
        traffic_thread.start()
        
        # Main game loop
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Clean shutdown - turn all lights off
                    for sig in LED_PINS:
                        set_leds(sig, 0, 0, 0)
                    board.exit()
                    running = False
            
            # Draw everything
            self.draw_frame()
            pygame.display.flip()
            clock.tick(30)
        
        pygame.quit()
        sys.exit()
    
    def draw_frame(self):
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw signals and info
        counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes, noOfAmbulances, weighted = countVehicles()
        self.draw_signals(counts, weighted)
        
        # Draw vehicles
        for vehicle in simulation:
            screen.blit(vehicle.image, (vehicle.x, vehicle.y))
            vehicle.move()
    
    def draw_signals(self, counts, weighted):
        # Draw signals, timers, and traffic information
        for i in range(4):
            # Draw signal image
            if i == currentGreen:
                if currentYellow:
                    signal_img = self.yellow_signal
                    signals[i].signalText = signals[i].yellow
                else:
                    signal_img = self.green_signal
                    signals[i].signalText = signals[i].green
            else:
                signal_img = self.red_signal
                signals[i].signalText = signals[i].red if signals[i].red <= 10 else "---"
            
            screen.blit(signal_img, signalCoods[i])
            
            # Draw timer text
            text = self.font.render(str(signals[i].signalText), True, (255, 255, 255))
            screen.blit(text, signalTimerCoods[i])
            
            # Draw traffic info
            count_text = self.font.render(f"Vehicles: {counts[i]}", True, (255, 255, 255))
            weight_text = self.font.render(f"Weight: {weighted[i]}", True, (255, 255, 255))
            
            # Position info based on direction
            if i == 0:  # Right
                screen.blit(count_text, (50, 50))
                screen.blit(weight_text, (50, 75))
            elif i == 1:  # Down
                screen.blit(count_text, (1250, 50))
                screen.blit(weight_text, (1250, 75))
            elif i == 2:  # Left
                screen.blit(count_text, (1250, 750))
                screen.blit(weight_text, (1250, 775))
            elif i == 3:  # Up
                screen.blit(count_text, (50, 750))
                screen.blit(weight_text, (50, 775))

if __name__ == "__main__":
    # Check if running on Mac
    if sys.platform == 'darwin':
        # Mac-specific adjustments
        import os
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    
    # Run the simulation
    Simulation()