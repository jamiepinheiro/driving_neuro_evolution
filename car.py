import pygame
from pygame.locals import *
from neat import nn, population, statistics
import random
import time
import math

###################################################################################################################################

#global variables
FPS, WIDTH, HEIGHT = 60, 1920, 1080
IMAGES = {}
obstacles = []
generation = 0;
xTimer = 0
xOffset = 0

###################################################################################################################################

#car class
class Car:
    #initialize car object
    def __init__(self, genome):
        self.x = WIDTH/5 + 20
        self.y = HEIGHT/2
        self.genome = genome
        self.nn = nn.create_feed_forward_phenotype(genome)
        self.alive = True
        self.speed = 2
        self.direction = 0
        self.rect = pygame.Rect(self.x + xOffset, self.y, 8, 8)

    #get image to be drawn
    def image(self):
        self.rect = pygame.Rect(self.x + xOffset, self.y, 8, 8)
        return pygame.transform.rotate(IMAGES["car"], -self.direction * 57.3 - 90)

    #decide on direction of steering
    def decision(self):
        inputs = [1000, 1000] #[left, right]
        xDis = 1000;

        xRounded = round(self.rect.x/8) * 8
        yRounded = round(self.rect.y/8) * 8

        closestX1, closestX2 = 1000, 1000;
        closest1, closest2 = None, None

        #find distance to top and bottom block
        for obstacle in obstacles:
            disX = abs(self.rect.x - obstacle.rect.x)
            obstacle.triggered = False

            if(disX < closestX1 and obstacle.rect.y < self.rect.y):
                if closest1 is not None:
                    closest1.triggered = False
                closestX1 = disX
                closest1 = obstacle
                closest1.triggered = True
            elif(disX < closestX2 and obstacle.rect.y > self.rect.y):
                if closest2 is not None:
                    closest2.triggered = False
                closestX2 = disX 
                closest2 = obstacle
                closest2.triggered = True

        if(closest1 is not None and closest2 is not None):
            inputs[0] = abs(closest1.rect.y - self.rect.y)
            inputs[1] = abs(closest2.rect.y - self.rect.y)

        #send inputs to neural network and get outputs
        outputs = self.nn.serial_activate(inputs)

        #steer based on outputs
        if(outputs[0] > 0.5):
            self.direction += 0.05
        if(outputs[0] < 0.5):
            self.direction -= 0.05
        
    #move based on steering direction
    def move(self):
        self.x += math.ceil(self.speed * math.cos(self.direction))
        self.y += math.ceil(self.speed * math.sin(self.direction))
      
    #check if car is in a crash 
    def inCollision(self, obstacles):
        #check each obstacle rect to see if in collision
        for obstacle in obstacles:
            if(math.sqrt((self.rect.x + self.rect.width/2 - obstacle.rect.x + obstacle.rect.width/2) ** 2 + (self.rect.y + self.rect.height/2 - obstacle.rect.y + obstacle.rect.height/2) ** 2) < 15):
                return True
        return False

###################################################################################################################################

#obstacle class
class Obstacle:

    #initialize obstacle object
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x + xOffset, self.y, 8, 8)
        self.triggered = False

    #get image to be drawn
    def image(self):
        #check if obstacle is triggered right now 
        if(self.triggered):
            return IMAGES["obstacle_triggered"]
        else:
            return IMAGES["obstacle"]

    #offset based on xOffset
    def offset(self):
        self.rect = pygame.Rect(self.x + xOffset, self.y, 8, 8)

###################################################################################################################################

#main game loop for 1 generation
def eval_fitness(genomes):

    #access variables
    global generation, obstacles, xOffset

    #create random winding road for generation
    obstacles = []
    min, max, changeFreq = -0.5, 0.5, 1
    currentY = HEIGHT/2

    #generate 1000m of road
    for x in range(1000):
        if(x == 0):
            for y in range(135):
                obstacles.append(Obstacle(WIDTH/5, y * 8))
        if(x == 999):
            for y in range(135):
                obstacles.append(Obstacle(WIDTH/5 + x * 8, y * 8))
        obstacles.append(Obstacle(WIDTH/5 + x * 8, currentY + 48))
        obstacles.append(Obstacle(WIDTH/5 + x * 8, currentY - 48))

        if(currentY < 150):
            min = 0
            max = 10
        elif(currentY > 930):
            min = -10
            max = 0
        else:
            if(x % changeFreq == 0):
                currentY += random.uniform(min, max)
            if(x % 100 == 0):
                min = round(random.uniform(-10, -1))
                max = round(random.uniform(1, 10))
                changeFreq = round(random.uniform(2, 3))

    #generate cars for the generation         
    cars = []
    for genome in genomes:
        cars.append(Car(genome))

    cars_alive = len(cars)

    #reset control variables
    offsetStart = time.time()
    lifespanStart = time.time()
    done = False
    xOffset = 0
    offsetTime = 0.02

    #loop until all cars have crashed
    while cars_alive and done == False:

        #close button action control
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True 
                break

        #update timer
        xTimer = (time.time() - offsetStart)

        #draw white background
        SCREEN.fill(pygame.Color(255, 255, 255, 255))

        #draw obstacles and offset obstacles
        for obstacle in obstacles:
            obstacle.offset()
            SCREEN.blit(obstacle.image(), (obstacle.rect.x , obstacle.rect.y))

        #draw cars, offset cars, check collisions, make decisions for cars and move cars
        for car in cars:
            if not car.alive:
                continue
            if car.inCollision(obstacles):
                car.alive = False
                cars_alive -= 1
                lifespan = float(time.time() - lifespanStart)
                car.genome.fitness = car.x/1000
            car.decision()
            car.move()
            SCREEN.blit(car.image(), (car.rect.x , car.rect.y))

        #offset screen to keep up with cars moving right
        if(xTimer > offsetTime):
            for car in cars:
                if car.rect.x > WIDTH/2:
                    offsetTime -= 0.01

            if(len(cars) != 1):
                xOffset -= 2
                offsetStart = time.time()

        #print stats on screen
        SCREEN.blit(FONT.render("ALIVE: " + str(cars_alive), 2, (0,0,0)), (20, 80))
        SCREEN.blit(FONT.render("TIME: " + str(round(time.time() - lifespanStart, 2)) + " s", 2, (0,0,0)), (20, 120))
        SCREEN.blit(FONT.render("GENERATION: " + str(generation), 2, (0,0,0)), (20, 160))

        #draw distance markers
        for x in range(10):
            label = FONT.render(str(x * 100) + "m", 10, (0,0,0))
            SCREEN.blit(label, (WIDTH/2 + x * 800 + xOffset, 1000))

        # update the screen and tick the clock
        pygame.display.update()
        pygame.display.flip()
        FPSCLOCK.tick(FPS)

    #increment generation
    generation += 1

###################################################################################################################################

#access variables
global FPSCLOCK, SCREEN, FONT

#pygame setup
pygame.init()
FONT = pygame.font.SysFont("arial", 30)
FPSCLOCK = pygame.time.Clock()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car NeuroEvolution")

#get images
IMAGES['car'] = pygame.image.load("pics/car.png").convert()
IMAGES['obstacle']  = pygame.image.load("pics/obstacle.png").convert()
IMAGES['obstacle_triggered']  = pygame.image.load("pics/obstacle_triggered.png").convert()

#create population and begin Neuro Evolution
pop = population.Population('car_config')
pop.run(eval_fitness, 10000)

#log stats
statistics.save_stats(pop.statistics)
statistics.save_species_count(pop.statistics)
statistics.save_species_fitness(pop.statistics)

###################################################################################################################################