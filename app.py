import pygame
from pygame.display import flip
from sys import exit
import pygame

#variabele initialisatie

clock = pygame.time.Clock()


#movement
class Keyboard:
    def update(self):
        self._held = pygame.key.get_pressed()

    def move_with_arrows(self, cord, amount=1):
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



#main root function
def main():
    cord = State()
    keyboard = Keyboard()

    #pygame init
    
    pygame.init()
    create_main_surface()
    #SCHERM AANHOUDEN
    while True:
        #Alle render functies in while loop!
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.display.update()
        keyboard.update()
        keyboard.move_with_arrows(cord)
        render_frame(surface, cord)



def render_frame(surface, cord):
        clear_surface(surface)
        pygame.draw.circle(surface, (255,255,255), (cord.x, cord.y), 30)
        
        flip()

def clear_surface(surface):
    surface.fill((0, 0, 0))

main()
