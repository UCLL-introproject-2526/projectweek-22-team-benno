import pygame
from pygame.display import flip
from sys import exit
import os

pygame.init()
os.chdir(os.path.dirname(__file__))

clock = pygame.time.Clock()

# =====================
# SETTINGS
# =====================
SCREEN_SIZE = (1024, 768)
TILE_SIZE = 64
player_speed = 5

scroll_speed = 0.7  # how fast the camera scrolls upward
SHOW_GRID = True    # True = show grid, False = hide grid

# =====================
# LEVEL (EASIER TO EDIT + CAN BE REALLY LONG)
# Last line = bottom of the map
#   # = wall
#   . = empty
# =====================
LEVEL_TEXT = """
################
#..............#
#..............#
#..............#
#..............#
#....####......#
#..............#
#..............#
#..######......#
#..............#
#..............#
#..............#
#..............#
#..............#
#..............#
##.............#
##............#
###............#
###............#
####........####
###..........###
##.............#
#..............#
#..............#
#..............#
################
"""

LEVEL_MAP = [row for row in LEVEL_TEXT.strip().splitlines()]
walls = []

# =====================
# PLAYER
# =====================
class Player:
    def __init__(self):
        self.xpos = 200
        self.ypos = 0

    def move(self, x, y):
        self.xpos += x * player_speed
        self.ypos += y * player_speed

    

player = Player()

# =====================
# SCREEN
# =====================
def create_main_surface():
    return pygame.display.set_mode(SCREEN_SIZE)

surface = create_main_surface()

# =====================
# IMAGE
# =====================
mario = pygame.image.load("images/kerstman-def.png").convert_alpha()
mario = pygame.transform.scale(mario, (64, 64))
mario_rect = mario.get_rect(topleft=(player.xpos, player.ypos))

# =====================
# WORLD SIZE + CAMERA
# =====================
map_width_tiles = len(LEVEL_MAP[0])
map_height_tiles = len(LEVEL_MAP)

WORLD_WIDTH = map_width_tiles * TILE_SIZE
WORLD_HEIGHT = map_height_tiles * TILE_SIZE

camera_y = max(0, WORLD_HEIGHT - SCREEN_SIZE[1])
camera_x = SCREEN_SIZE[0] / 2

player.ypos = WORLD_HEIGHT - TILE_SIZE * 2
mario_rect.topleft = (player.xpos, player.ypos)

# =====================
# WALLS
# =====================
def build_walls():
    walls.clear()
    for row_i, row in enumerate(LEVEL_MAP):
        for col_i, tile in enumerate(row):
            if tile == "#":
                walls.append(
                    pygame.Rect(
                        col_i * TILE_SIZE,
                        row_i * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE
                    )
                )

build_walls()

# =====================
# MOVEMENT + COLLISION
# =====================
def handle_player_movement():
    keys = pygame.key.get_pressed()
    dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
    dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]

    player.move(dx, 0)
    mario_rect.topleft = (player.xpos, player.ypos)
    for wall in walls:
        if mario_rect.colliderect(wall):
            player.move(-dx, 0)
            mario_rect.topleft = (player.xpos, player.ypos)
            break

    player.move(0, dy)
    mario_rect.topleft = (player.xpos, player.ypos)
    for wall in walls:
        if mario_rect.colliderect(wall):
            player.move(0, -dy)
            mario_rect.topleft = (player.xpos, player.ypos)
            break

    mario_rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
    player.xpos, player.ypos = mario_rect.topleft

# =====================
# CAMERA SCROLL
# =====================
def update_camera():
    global camera_x, camera_y

    camera_x = player.xpos - SCREEN_SIZE[0] // 2 + TILE_SIZE // 2
    camera_y = player.ypos - SCREEN_SIZE[1] // 2 + TILE_SIZE // 2

    # Clamp camera binnen wereld
    camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_SIZE[0]))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_SIZE[1]))


# =====================
# GRID DRAW
# =====================
def draw_grid(surface):
    if not SHOW_GRID:
        return

    w, h = surface.get_size()
    start_y = -(camera_y % TILE_SIZE)

    x = 0
    while x <= w:
        pygame.draw.line(surface, (50, 50, 50), (x, 0), (x, h))
        x += TILE_SIZE

    y = start_y
    while y <= h:
        pygame.draw.line(surface, (50, 50, 50), (0, y), (w, y))
        y += TILE_SIZE

# =====================
# RENDERING
# =====================
def clear_surface(surface):
    surface.fill((0, 0, 0))

def render_frame(surface):
    clear_surface(surface)

    for wall in walls:
        screen_rect = wall.move(-camera_x, -camera_y)
        if screen_rect.bottom >= 0 and screen_rect.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surface, (120, 120, 120), screen_rect)

    draw_grid(surface)

    mario_screen_pos = (
    mario_rect.x - camera_x,
    mario_rect.y - camera_y
)

    surface.blit(mario, mario_screen_pos)

    flip()

# =====================
# MAIN LOOP
# =====================
def main():
    global SHOW_GRID

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    SHOW_GRID = not SHOW_GRID

        handle_player_movement()
        update_camera()
        render_frame(surface)
        clock.tick(60)

main()
