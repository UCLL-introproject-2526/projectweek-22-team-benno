import pygame
from pygame.display import flip

def create_main_surface():
    #SCHERM AANMAKEN 
    screen_size = (1024, 768)
    return pygame.display.set_mode(screen_size)

#main root function
def main():
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
        render_frame(surface)
       
surface = create_main_surface()

def render_frame(surface):
        pygame.draw.circle(surface, (255,255,255), (400, 300), 50)
        flip()

main()