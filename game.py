import pygame
from pygame.display import flip
from sys import exit
pygame.init()

def create_main_surface():
    #SCHERM AANMAKEN 
    screen_size = (1024, 768)
    return pygame.display.set_mode(screen_size)

surface = create_main_surface()

def main():
    create_main_surface()
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