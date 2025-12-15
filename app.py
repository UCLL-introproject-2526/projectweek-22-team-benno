import pygame
from pygame.display import flip
from sys import exit

class State:
    def __init__(self):
        self.x = 0

    def increment(self, amount):
        self.x += amount

class Keyboard:
    def __init__(self):
        self.game_running = True
        
    def is_key_down(key):
        while self.game_running:
            if keyboard.is_key_down(RIGHT_ARROW):
                player_x_position += 1
      



def create_main_surface():
    #SCHERM AANMAKEN 
    screen_size = (1024, 768)
    return pygame.display.set_mode(screen_size)

clock = pygame.time.Clock()

#main root function
def main():
    cord = State()

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

        #geeft 60 fps
        
        cord.increment(1)
        render_frame(surface, cord)

        
  

        
       
surface = create_main_surface()

def render_frame(surface, cord):
        #render een frame
        clear_surface(surface)
        pygame.draw.circle(surface, (255,255,255), (cord.x, 300), 50)
        flip()

def clear_surface(surface):
    surface.fill((0, 0, 0))

main()