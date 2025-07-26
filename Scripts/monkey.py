import random
import time
import threading
import pygame
import sys
import math

# Default values of signal timers
defaultGreen = {0: 0, 1: 0, 2: 0, 3: 0}  # Default green time for each signal
defaultRed = 150
defaultYellow = 3

# Average times for vehicles to pass the intersection
carTime = 2
busTime = 3
truckTime = 4
bikeTime = 1
ambulanceTime=1.5

signals = []
noOfSignals = 4
currentGreen = 0  # Indicates which signal is green currently
nextGreen = (currentGreen + 1) % noOfSignals  # Indicates which signal will turn green next
currentYellow = 0  # Indicates whether yellow signal is on or off

speeds = {'car': 4.5, 'bus': 3, 'truck': 2.25, 'bike': 4, 'ambulance':4.3}  # average speeds of vehicles

# Coordinates of vehicles' start
x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0}, 'up': {0: [], 1: [], 2: [], 'crossed': 0}}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike',4:'ambulance'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}
weights = {'car': 2, 'bus': 4, 'truck': 6, 'bike': 1,'ambulance':1000}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
stoppingGap = 15  # stopping gap
movingGap = 15  # moving gap

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
        self.image = pygame.image.load(path)  # Ensure image is loaded here

        if (len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][
            self.index - 1].crossed == 0):  # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
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

        # Set new starting and stopping coordinate
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
            if (self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[
                self.direction]):  # if the image has crossed stop line now
                self.crossed = 1
            if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (
                    currentGreen == 0 and currentYellow == 0)) and (
                    self.index == 0 or self.x + self.image.get_rect().width < (
                    vehicles[self.direction][self.lane][self.index - 1].x - movingGap))):
                self.x += self.speed  # move the vehicle
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
    counts = [0, 0, 0, 0]  # Total vehicles per direction
    noOfCars = [0, 0, 0, 0]
    noOfBuses = [0, 0, 0, 0]
    noOfTrucks = [0, 0, 0, 0]
    noOfBikes = [0, 0, 0, 0]
    noOfAmbulances=[0,0,0,0]

    for i in range(noOfSignals):
        direction = directionNumbers[i]
        for lane in [0, 1, 2]:
            for vehicle in vehicles[direction][lane]:
                if not vehicle.crossed:
                    if hasattr(vehicle, 'image'):  # Check if the vehicle has the 'image' attribute
                        rect = vehicle.image.get_rect()
                        # Check if the vehicle is within a certain distance from the stop line
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
                                elif vehicle.vehicleClass=='ambulance':
                                    noOfAmbulances[i]+=1
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
                                elif vehicle.vehicleClass=='ambulance':
                                    noOfAmbulances[i]+=1
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
                                elif vehicle.vehicleClass=='ambulance':
                                    noOfAmbulances[i]+=1
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
                                elif vehicle.vehicleClass=='ambulance':
                                    noOfAmbulances[i]+=1

    print(f"Vehicle Counts: {counts} (Cars: {noOfCars}, Buses: {noOfBuses}, Trucks: {noOfTrucks}, Bikes: {noOfBikes}, Ambulances:{noOfAmbulances})")
    weighted = [0, 0, 0, 0]
    for i in range(4):
        weighted[i] = noOfCars[i] * weights['car'] + noOfBikes[i] * weights['bike'] + noOfBuses[i] * weights['bus'] + noOfTrucks[i] * weights['truck']+noOfAmbulances[i]*weights['ambulance']
    return counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes, noOfAmbulances, weighted


# Initialization of signals with default values
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
    while (True):
        counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes, noOfAmbulances, weighted = countVehicles()
        # Calculate green time based on vehicle counts and their average crossing times
        total_vehicles = noOfCars[currentGreen] + noOfBuses[currentGreen] + noOfTrucks[currentGreen] + noOfBikes[currentGreen]+noOfAmbulances[currentGreen]
        greenTime = max(weighted)
        maxIndex = weighted.index(greenTime)
        greenTime=greenTime-noOfAmbulances[maxIndex]*weights['ambulance']
        greenTime = max(5, min(60, greenTime))  # Minimum 10 seconds, maximum 60 seconds

        currentGreen = maxIndex
        signals[currentGreen].green = math.ceil(greenTime / 3.68)

        while (signals[currentGreen].green > 0):  # while the timer of current green signal is not zero
            updateValues()
            time.sleep(1)

        # Dynamic yellow signal timing
        if counts[currentGreen] > 0:
            signals[currentGreen].yellow = min(3, max(1, counts[currentGreen] // 5))  # 1-3 seconds based on vehicle count
        else:
            signals[currentGreen].yellow = 0  # No vehicles, no yellow signal

        currentYellow = 1  # set yellow signal on
        # reset stop coordinates of lanes and vehicles
        for i in range(0, 3):
            for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen]]
        while (signals[currentGreen].yellow > 0):  # while the timer of current yellow signal is not zero
            updateValues()
            time.sleep(1)
        currentYellow = 0  # set yellow signal off

        # reset all signal times of current signal to default times
        signals[currentGreen].green = defaultGreen[currentGreen]
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed

        currentGreen = nextGreen  # set next signal as green signal
        nextGreen = (currentGreen + 1) % noOfSignals  # set next green signal
        signals[nextGreen].red = signals[currentGreen].yellow + signals[
            currentGreen].green  # set the red time of next to next signal as (yellow time + green time) of next signal


# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            # Calculate the time remaining for the red signal to turn green
            if i == nextGreen:
                signals[i].red = signals[currentGreen].yellow + signals[currentGreen].green
            else:
                # Ensure red signal does not go negative
                signals[i].red = max(0, signals[i].red - 1)


# Generating vehicles in the simulation
def generateVehicles():
    while (True):
        vehicle_type = random.randint(0, 3)
        x=5
        if(x==random.randint(0,20)):
            vehicle_type=4
        lane_number = random.randint(1, 2)
        temp = random.randint(0, 99)
        direction_number = 0
        dist = [25, 50, 75, 100]
        if (temp < dist[0]):
            direction_number = 0
        elif (temp < dist[1]):
            direction_number = 1
        elif (temp < dist[2]):
            direction_number = 2
        elif (temp < dist[3]):
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number])
        time.sleep(1)


class Main:
    thread1 = threading.Thread(name="initialization", target=initialize, args=())  # initialization
    thread1.daemon = True
    thread1.start()

    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    thread2 = threading.Thread(name="generateVehicles", target=generateVehicles, args=())  # Generating vehicles
    thread2.daemon = True
    thread2.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background, (0, 0))  # display background in simulation
        counts, noOfCars, noOfBuses, noOfTrucks, noOfBikes,noOfAmbulances,weighted = countVehicles()
        for i in range(0, noOfSignals):  # display signal and set timer according to current status: green, yellow, or red
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

        # display signal timer
        for i in range(0, noOfSignals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], signalTimerCoods[i])

        # display vehicle count beside the signal
        for i in range(0, noOfSignals):
            countText = font.render(f"Vehicles: {counts[i]}", True, white, black)
            if i == 0:  # Right signal (top-left corner)
                screen.blit(countText, (50, 50))  # Top-left corner
            elif i == 1:  # Down signal (top-right corner)
                screen.blit(countText, (screenWidth - 150, 50))  # Top-right corner
            elif i == 2:  # Left signal (bottom-left corner)
                screen.blit(countText, (screenWidth - 150, screenHeight - 50))  # Bottom-left corner
            elif i == 3:  # Up signal (bottom-right corner)
                screen.blit(countText, (50, screenHeight - 50))  # Bottom-right corner
        
        for i in range(0, noOfSignals):
            w = font.render(f"Weight: {weighted[i]}", True, white, black)
            if i == 0:  # Right signal (top-left corner)
                screen.blit(w, (50, 75))  # Top-left corner
            elif i == 1:  # Down signal (top-right corner)
                screen.blit(w, (screenWidth - 150, 75))  # Top-right corner
            elif i == 2:  # Left signal (bottom-left corner)
                screen.blit(w, (screenWidth - 150, screenHeight - 75))  # Bottom-left corner
            elif i == 3:  # Up signal (bottom-right corner)
                screen.blit(w, (50, screenHeight - 75))  # Bottom-right corner
                

        # display the vehicles
        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
        pygame.display.update()


Main()