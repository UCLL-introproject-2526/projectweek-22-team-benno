import pygame
from sys import exit
import os

# =====================
# INIT
# =====================
pygame.init()
os.chdir(os.path.dirname(__file__))

clock = pygame.time.Clock()
Icon = pygame.image.load('IMAGES/space_invader.png')
Icon = pygame.transform.scale(Icon, (32, 32))

# =====================
# SETTINGS
# =====================
SCREEN_SIZE = (1024, 768)
PLAYER_SPEED = 5

# =====================
# SCREEN
# =====================
def create_main_surface():
    return pygame.display.set_mode(SCREEN_SIZE)

screen = create_main_surface()
pygame.display.set_caption("Open Map Camera Follow")

# =====================
# LOAD IMAGES
# =====================
# 👉 PAS HIER DE PATH AAN
background = pygame.image.load("images/achtergrond.png").convert()

player_image = pygame.image.load("images/kerstman-def.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (64, 64))

WORLD_WIDTH, WORLD_HEIGHT = background.get_size()

# =====================
# PLAYER
# =====================
class Player:
    def __init__(self):
        self.rect = player_image.get_rect(center=(WORLD_WIDTH // 2, WORLD_HEIGHT // 2))

    def move(self, dx, dy):
        self.rect.x += dx * PLAYER_SPEED
        self.rect.y += dy * PLAYER_SPEED

        # Border = rand van de map image
        self.rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))

player = Player()

# =====================
# CAMERA
# =====================
camera_x = 0
camera_y = 0

def update_camera():
    global camera_x, camera_y

    camera_x = player.rect.centerx - SCREEN_SIZE[0] // 2
    camera_y = player.rect.centery - SCREEN_SIZE[1] // 2

    # Camera mag niet buiten de wereld
    camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_SIZE[0]))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_SIZE[1]))

# =====================
# INPUT
# =====================
def handle_player_movement():
    keys = pygame.key.get_pressed()

    dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
    dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]

    player.move(dx, dy)

# =====================
# RENDER
# =====================
def render():
    # Teken juiste stuk van de achtergrond
    screen.blit(
        background,
        (0, 0),
        pygame.Rect(camera_x, camera_y, *SCREEN_SIZE)
    )

    # Teken speler relatief aan camera
    screen.blit(
        player_image,
        (
            player.rect.x - camera_x,
            player.rect.y - camera_y
        )
    )

    pygame.display.flip()

# =====================
# MAIN LOOP
# =====================
def main():

    pygame.display.set_caption('Lucas crackt femboys')
    pygame.display.set_icon(Icon)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        handle_player_movement()
        update_camera()
        render()

        clock.tick(60)

main()
