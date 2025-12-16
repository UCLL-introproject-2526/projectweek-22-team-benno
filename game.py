import pygame
from pygame.display import flip
from sys import exit
import os
import random

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

# ENEMIES
ENEMY_SIZE = 48
ENEMY_SPEED = 2.2
SPAWN_INTERVAL_MS = 1500
MAX_ENEMIES = 30

enemies = []
NEXT_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(NEXT_SPAWN_EVENT, SPAWN_INTERVAL_MS)

# =====================
# LEVEL
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
#..............#
#..............#
#..............#
#..............#
#..............#
#..............#
##.............#
##.............#
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
mario = pygame.transform.scale(mario, (55, 55))
mario_rect = mario.get_rect(topleft=(player.xpos, player.ypos))

# =====================
# WORLD SIZE + CAMERA
# =====================
map_width_tiles = len(LEVEL_MAP[0])
map_height_tiles = len(LEVEL_MAP)

WORLD_WIDTH = map_width_tiles * TILE_SIZE
WORLD_HEIGHT = map_height_tiles * TILE_SIZE

camera_y = max(0, WORLD_HEIGHT - SCREEN_SIZE[1])

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
# ENEMY
# =====================
class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)

    def move_and_collide(self, dx, dy):
        # Move X then resolve
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0:
                    self.rect.right = wall.left
                elif dx < 0:
                    self.rect.left = wall.right

        # Move Y then resolve
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0:
                    self.rect.bottom = wall.top
                elif dy < 0:
                    self.rect.top = wall.bottom

        # Can't cross world boundaries
        self.rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))

    def update(self, target_pos):
        tx, ty = target_pos
        cx, cy = self.rect.centerx, self.rect.centery

        vx = tx - cx
        vy = ty - cy
        dist = (vx * vx + vy * vy) ** 0.5

        if dist > 0.0001:
            vx /= dist
            vy /= dist

        dx = int(round(vx * ENEMY_SPEED))
        dy = int(round(vy * ENEMY_SPEED))

        self.move_and_collide(dx, dy)

def spawn_enemy():
    # Spawn near the top of the camera view (world coords)
    spawn_y = max(0, int(camera_y) - TILE_SIZE)

    tries = 80
    while tries > 0:
        tries -= 1

        x = random.randint(0, WORLD_WIDTH - ENEMY_SIZE)
        y_low = spawn_y
        y_high = min(spawn_y + TILE_SIZE * 2, WORLD_HEIGHT - ENEMY_SIZE)
        if y_high < y_low:
            y_low, y_high = 0, WORLD_HEIGHT - ENEMY_SIZE

        y = random.randint(y_low, y_high)

        e = Enemy(x, y)

        # Don't spawn inside walls
        if any(e.rect.colliderect(w) for w in walls):
            continue

        enemies.append(e)
        return

def update_enemies():
    player_center = mario_rect.center
    for e in enemies:
        e.update(player_center)

# =====================
# MOVEMENT + COLLISION (PLAYER)
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
    global camera_y
    camera_y -= scroll_speed
    if camera_y < 0:
        camera_y = 0

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

    # Walls
    for wall in walls:
        screen_rect = wall.move(0, -camera_y)
        if screen_rect.bottom >= 0 and screen_rect.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surface, (120, 120, 120), screen_rect)

    draw_grid(surface)

    # Enemies
    for e in enemies:
        enemy_screen = e.rect.move(0, -camera_y)
        if enemy_screen.bottom >= 0 and enemy_screen.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surface, (200, 60, 60), enemy_screen)

    # Player
    mario_screen_pos = (mario_rect.x, mario_rect.y - camera_y)
    surface.blit(mario, mario_screen_pos)

    flip()

# =====================
# MAIN LOOP
# =====================
def main():
    global SHOW_GRID

    pygame.display.set_caption("Pygame Scroller")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    SHOW_GRID = not SHOW_GRID

            if event.type == NEXT_SPAWN_EVENT:
                if len(enemies) < MAX_ENEMIES:
                    spawn_enemy()

        handle_player_movement()
        update_camera()
        update_enemies()
        render_frame(surface)
        clock.tick(60)

main()
