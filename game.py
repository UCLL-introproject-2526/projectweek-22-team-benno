import pygame
from pygame.display import flip
from sys import exit
pygame.init()

class Keyboard:
    def update(self):
        #Bijhouden van keypress
        self._held = pygame.key.get_pressed()
    
    def move_with_arrows(self, cord, amount=1):
        #Movement
        if self._held[pygame.K_RIGHT]:
            cord.incrementx(amount)
        if self._held[pygame.K_LEFT]:
            cord.incrementx(-amount)
        if self._held[pygame.K_UP]:
            cord.incrementy(-amount)
        if self._held[pygame.K_DOWN]:
            cord.incrementy(amount)

class State:
    def __init__(self):
        self.x = 0
        self.y = 0

    def incrementx(self, amount):
        self.x += amount

    def incrementy(self, amount):
        self.y += amount

def create_main_surface():
    #SCHERM AANMAKEN 
    screen_size = (1024, 768)
    return pygame.display.set_mode(screen_size)

surface = create_main_surface()

def main():
    create_main_surface()
    #While loop voor alles rendering
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.display.update()
        render_frame(surface)



def render_frame(surface):
        clear_surface(surface)
        #alle dingen dat moeten worden gerendered 
        flip()

def clear_surface(surface):
    surface.fill((0, 0, 0))

main()