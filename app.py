import pygame

#main root function
def main():
    #pygame init
    
    pygame.init()
    create_main_surface()
    #SCHERM AANHOUDEN
    while True:
        pass

def create_main_surface():
    #SCHERM AANMAKEN 
    screen_size = (1024, 768)
    pygame.display.set_mode(screen_size)


main()