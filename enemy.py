import random
import math
import pygame
from main import screen_height
from main import screen_width

red = (255, 50, 50)

class Enemy:
    def __init__(self,player_pos):
        self.hp = 50
        self.speed = 0.5
        self.width = 6
        self.height = 6


        edge = random.choice(["top", "bottom", "left", "right"])

        if edge == "top":
            self.x = random.randint(0, screen_width)
            self.y = -5
        elif edge == "bottom":
            self.x = random.randint(0, screen_width)
            self.y = screen_height + 5
        elif edge == "left":
            self.x = -5
            self.y = random.randint(0, screen_height)
        else:  # right
            self.x = screen_width + 5
            self.y = random.randint(0, screen_height)

        px, py = player_pos
        dx = px - self.x
        dy = py - self.y

        distance = math.hypot(dx, dy)

        self.vx = dx / distance * self.speed
        
        self.vy = dy / distance * self.speed

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.topleft = (round(self.x), round(self.y))

    def draw(self, screen):
        pygame.draw.rect(screen, red, self.rect)