import pygame

class Keyboard:
    def __init__(self):
        pass

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