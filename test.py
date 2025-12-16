import pygame
from sys import exit
import os
import math

# =====================
# INIT
# =====================
pygame.init()
os.chdir(os.path.dirname(__file__))
clock = pygame.time.Clock()

# =====================
# SETTINGS
# =====================
SCREEN_SIZE = (1024, 768)
PLAYER_SPEED = 5

ELLIPSE_SIZE = 3000
ELLIPSE_BORDER_THICKNESS = 8
ELLIPSE_COLOR = (180, 0, 255)

# =====================
# SCREEN
# =====================
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Ellipse Border World")

# =====================
# IMAGES
# =====================
# 👉 PAS PATHS AAN
background = pygame.Surface((ELLIPSE_SIZE, ELLIPSE_SIZE))
background.fill((20, 20, 20))

player_image = pygame.image.load("images\Kerstman-def.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (64, 64))

WORLD_WIDTH = ELLIPSE_SIZE
WORLD_HEIGHT = ELLIPSE_SIZE

# =====================
# ELLIPSE DATA
# =====================
ellipse_center = pygame.Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
ellipse_rx = ELLIPSE_SIZE // 2
ellipse_ry = ELLIPSE_SIZE // 2

# =====================
# PLAYER
# =====================
class Player:
    def __init__(self):
        self.rect = player_image.get_rect(center=ellipse_center)

    def move(self, dx, dy):
        old_center = self.rect.center

        self.rect.x += dx * PLAYER_SPEED
        self.rect.y += dy * PLAYER_SPEED

        if not point_inside_ellipse(self.rect.center):
            self.rect.center = old_center

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

    camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_SIZE[0]))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_SIZE[1]))

# =====================
# INPUT
# =====================
def handle_input():
    keys = pygame.key.get_pressed()
    dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
    dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
    player.move(dx, dy)

# =====================
# ELLIPSE CHECK
# =====================
def point_inside_ellipse(point):
    px, py = point
    cx, cy = ellipse_center

    return (
        ((px - cx) ** 2) / (ellipse_rx ** 2)
        + ((py - cy) ** 2) / (ellipse_ry ** 2)
    ) <= 1

# =====================
# RENDER
# =====================
def render():
    screen.fill((10, 10, 10))

    # Draw ellipse border (world border)
    pygame.draw.ellipse(
        screen,
        ELLIPSE_COLOR,
        pygame.Rect(
            ellipse_center.x - ellipse_rx - camera_x,
            ellipse_center.y - ellipse_ry - camera_y,
            ellipse_rx * 2,
            ellipse_ry * 2
        ),
        ELLIPSE_BORDER_THICKNESS
    )

    # Draw player
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
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        handle_input()
        update_camera()
        render()
        clock.tick(60)

main()
