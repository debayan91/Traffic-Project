import random
import time
import threading
import pygame
import sys
import math
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
    if signal_num not in LED_PINS:
        return

    pins = LED_PINS[signal_num]
    board.digital[pins['red']].write(red)
    board.digital[pins['yellow']].write(yellow)
    board.digital[pins['green']].write(green)

    for sig in LED_PINS:
        if sig != signal_num:
            other_pins = LED_PINS[sig]
            board.digital[other_pins['red']].write(1)
            board.digital[other_pins['yellow']].write(0)
            board.digital[other_pins['green']].write(0)

defaultGreen = {0: 0, 1: 0, 2: 0, 3: 0}
defaultRed = 150
defaultYellow = 3

carTime = 2+1
busTime = 3+1
truckTime = 4+1
bikeTime = 1+1
ambulanceTime = 1.5+1

signals = []
noOfSignals = 4
currentGreen = 0
nextGreen = (currentGreen + 1) % noOfSignals
currentYellow = 0

speeds = {'car': 4.5-1, 'bus': 3-1, 'truck': 2.25-1, 'bike': 4-1, 'ambulance': 4.3-1}

x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0}, 'up': {0: [], 1: [], 2: [], 'crossed': 0}}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike', 4: 'ambulance'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}
weights = {'car': 2, 'bus': 4, 'truck': 6, 'bike': 1, 'ambulance': 1000}

signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

stoppingGap = 15
movingGap = 15

pygame.init()
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
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

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

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if (self.direction == 'right'):
            if (self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]):
                self.crossed = 1
            if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (
                    currentGreen == 0 and currentYellow == 0)) and (
                    self.index == 0 or self.x + self.image.get_rect().width < (
                    vehicles[self.direction][self.lane][self.index - 1].x - movingGap))):
                self.x += self.speed
        elif (self.direction == 'down'):
            if (self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]):
                self.crossed = 1
            if ((self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or (
                    currentGreen == 1 and currentYellow == 0)) and (
                    self.index == 0 or self.y + self.image.get_rect().height < (
                    vehicles[self.direction][self.lane][self.index - 1].y - movingGap))):
                self.y += self.speed
        elif (self.direction == 'left'):
            if (self.crossed == 0 and self.x < stopLines[self.direction]):
                self.crossed = 1
            if ((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0)) and (
                    self.index == 0 or self.x > (
                    vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][
                self.index - 1].image.get_rect().width + movingGap))):
                self.x -= self.speed
        elif (self.direction == 'up'):
            if (self.crossed == 0 and self.y < stopLines[self.direction]):
                self.crossed = 1
            if ((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0)) and (
                    self.index == 0 or self.y > (
                    vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][
                self.index - 1].image.get_rect().height + movingGap))):
                self.y -= self.speed

def countVehicles():
    counts = [0, 0, 0, 0]
    noOfCars = [0, 0, 0, 0]
    noOfBuses = [0, 0, 0, 0]
    noOfTrucks = [0, 0, 0, 0]
    noOfBikes = [0, 0, 0, 0]
    noOfAmbulances = [0, 0, 0, 0]

    for i in range(noOfSignals):
        direction = directionNumbers[i]
        for lane in [0, 1, 2]:
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
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, defaultGreen[1])
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
    signals.append(ts4)
    repeat()

def repeat():
    global currentGreen, currentYellow, nextGreen
    while True:
        counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes, noOfAmbulances, weighted = countVehicles()

        total_vehicles = noOfCars[currentGreen] + noOfBuses[currentGreen] + noOfTrucks[currentGreen] + noOfBikes[currentGreen] + noOfAmbulances[currentGreen]
        greenTime = max(weighted)
        maxIndex = weighted.index(greenTime)
        greenTime = greenTime - noOfAmbulances[maxIndex] * weights['ambulance']
        greenTime = max(5, min(60, greenTime))

        currentGreen = maxIndex
        signals[currentGreen].green = math.ceil(greenTime / 3.68)

        set_leds(currentGreen, 0, 0, 1)

        while (signals[currentGreen].green > 0):
            updateValues()
            time.sleep(1)

        if counts[currentGreen] > 0:
            signals[currentGreen].yellow = min(3, max(1, counts[currentGreen] // 5))
        else:
            signals[currentGreen].yellow = 0

        currentYellow = 1
        set_leds(currentGreen, 0, 1, 0)

        for i in range(0, 3):
            for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen]]

        while (signals[currentGreen].yellow > 0):
            updateValues()
            time.sleep(1)

        currentYellow = 0
        set_leds(currentGreen, 1, 0, 0)

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

def generateVehicles():
    while True:
        vehicle_type = random.randint(0, 3)
        x = 5
        if x == random.randint(0, 20):
            vehicle_type = 4
        lane_number = random.randint(1, 2)
        temp = random.randint(0, 99)
        direction_number = 0
        dist = [25, 50, 75, 100]
        if temp < dist[0]:
            direction_number = 0
        elif temp < dist[1]:
            direction_number = 1
        elif temp < dist[2]:
            direction_number = 2
        elif temp < dist[3]:
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number])
        time.sleep(1)

def test_all_leds():
    for color in ['red', 'yellow', 'green']:
        for sig in LED_PINS:
            set_leds(sig,
                     1 if color == 'red' else 0,
                     1 if color == 'yellow' else 0,
                     1 if color == 'green' else 0)
            time.sleep(0.5)
            set_leds(sig, 0, 0, 0)
    print("LED test complete")

class Main:
    test_all_leds()

    black = (0, 0, 0)
    white = (255, 255, 255)

    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    background = pygame.image.load('images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    traffic_thread = threading.Thread(target=initialize)
    traffic_thread.daemon = True
    traffic_thread.start()

    vehicle_thread = threading.Thread(target=generateVehicles)
    vehicle_thread.daemon = True
    vehicle_thread.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                for sig in LED_PINS:
                    set_leds(sig, 0, 0, 0)
                board.exit()
                pygame.quit()
                sys.exit()

        screen.blit(background, (0, 0))
        counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes, noOfAmbulances, weighted = countVehicles()

        for i in range(0, noOfSignals):
            if i == currentGreen:
                if currentYellow == 1:
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if signals[i].red <= 10:
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])

        signalTexts = ["", "", "", ""]
        for i in range(0, noOfSignals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], signalTimerCoods[i])

        for i in range(0, noOfSignals):
            countText = font.render(f"Vehicles: {counts[i]}", True, white, black)
            if i == 0:
                screen.blit(countText, (50, 50))
            elif i == 1:
                screen.blit(countText, (1250, 50))
            elif i == 2:
                screen.blit(countText, (1250, 750))
            elif i == 3:
                screen.blit(countText, (50, 750))

        for i in range(0, noOfSignals):
            w = font.render(f"Weight: {weighted[i]}", True, white, black)
            if i == 0:
                screen.blit(w, (50, 75))
            elif i == 1:
                screen.blit(w, (1250, 75))
            elif i == 2:
                screen.blit(w, (1250, 775))
            elif i == 3:
                screen.blit(w, (50, 775))

        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()

        pygame.display.update()

if __name__ == "__main__":
    Main()