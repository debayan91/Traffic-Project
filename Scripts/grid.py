import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BACKGROUND_COLOR = (255, 255, 255)
ROAD_COLOR = (0, 0, 0)

# Create the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Traffic Simulation")

# Define classes for traffic lights, vehicles, roads, and intersections

class TrafficLight:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = "red"  # Initialize as red
        self.last_switch_time = time.time()
        self.switch_interval = random.randint(2, 10)

    def switch_state(self):
        if time.time() - self.last_switch_time >= self.switch_interval:
            if self.state == "red":
                self.state = "green"
            else:
                self.state = "red"
            self.last_switch_time = time.time()
            self.switch_interval = random.randint(2, 10)

    def draw(self):
        pygame.draw.circle(screen, (255, 0, 0) if self.state == "red" else (0, 255, 0), (self.x, self.y), 15)

class Vehicle:
    def __init__(self, x, y, shape, speed_range):
        self.x = x
        self.y = y
        self.shape = shape
        self.speed = random.uniform(speed_range[0], speed_range[1])
        self.direction = random.choice(["up", "down", "left", "right"])
        self.stopped = False

    def move(self):
        if not self.stopped:
            if self.direction == "up":
                self.y -= self.speed
            elif self.direction == "down":
                self.y += self.speed
            elif self.direction == "left":
                self.x -= self.speed
            elif self.direction == "right":
                self.x += self.speed

    def draw(self):
        if self.shape == "car":
            pygame.draw.rect(screen, (0, 0, 255), (self.x, self.y, 20, 20))
        elif self.shape == "motorcycle":
            pygame.draw.polygon(screen, (0, 255, 0), [(self.x, self.y), (self.x + 10, self.y - 20), (self.x + 20, self.y)])
        elif self.shape == "truck":
            pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, 30, 20))

class Intersection:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.traffic_light = TrafficLight(x, y)

    def draw(self):
        self.traffic_light.switch_state()
        self.traffic_light.draw()

# Ask the user for the size of the grid
GRID_SIZE = int(input("Enter the size of the grid: "))

# Create a grid-based road network
ROAD_WIDTH = WINDOW_WIDTH // GRID_SIZE
ROAD_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

roads = []
intersections = []

for i in range(GRID_SIZE):
    for j in range(GRID_SIZE):
        if i < GRID_SIZE - 1:
            if random.random() > 0.2:  # Randomly remove some road sections
                # Main road
                roads.append((i * ROAD_WIDTH, (j + 1) * ROAD_HEIGHT, ROAD_WIDTH, 10))
                intersections.append(Intersection(i * ROAD_WIDTH + ROAD_WIDTH, (j + 1) * ROAD_HEIGHT + 10))
                # Reverse lane
                roads.append((i * ROAD_WIDTH, (j + 1) * ROAD_HEIGHT - 10, ROAD_WIDTH, 10))

        if j < GRID_SIZE - 1:
            if random.random() > 0.2:  # Randomly remove some road sections
                # Main road
                roads.append(((i + 1) * ROAD_WIDTH, j * ROAD_HEIGHT, 10, ROAD_HEIGHT))
                intersections.append(Intersection((i + 1) * ROAD_WIDTH + 10, j * ROAD_HEIGHT + ROAD_HEIGHT))
                # Reverse lane
                roads.append(((i + 1) * ROAD_WIDTH - 10, j * ROAD_HEIGHT, 10, ROAD_HEIGHT))

# Create vehicles
num_cars = int(input("Enter the number of cars: "))
num_motorcycles = int(input("Enter the number of motorcycles: "))
num_trucks = int(input("Enter the number of trucks: "))

vehicles = []

for _ in range(num_cars):
    vehicles.append(Vehicle(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT), "car", (1, 2)))

for _ in range(num_motorcycles):
    vehicles.append(Vehicle(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT), "motorcycle", (3, 4)))

for _ in range(num_trucks):
    vehicles.append(Vehicle(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT), "truck", (0.5, 1.5)))

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND_COLOR)

    for intersection in intersections:
        intersection.draw()

    for vehicle in vehicles:
        vehicle.move()

        # Check for traffic lights
        for intersection in intersections:
            if (
                intersection.x <= vehicle.x <= intersection.x + 10 and
                intersection.y <= vehicle.y <= intersection.y + 10 and
                intersection.traffic_light.state == "red"
            ):
                vehicle.stopped = True
            else:
                vehicle.stopped = False

        vehicle.draw()

    for road in roads:
        pygame.draw.rect(screen, ROAD_COLOR, road)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()