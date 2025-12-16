import pygame
from pygame.display import flip
from sys import exit
import os
import random
import math

pygame.init()
os.chdir(os.path.dirname(__file__))

clock = pygame.time.Clock()

# =====================
# SETTINGS
# =====================
SCREEN_SIZE = (1024, 768)
TILE_SIZE = 64
player_speed = 5

scroll_speed = 0.7
SHOW_GRID = True

# ENEMIES
ENEMY_SIZE = 44
ENEMY_SPEED = 2.2
ENEMY_WANDER_JITTER = 0.35
ENEMY_SHOOT_COOLDOWN_MS = 900

SPAWN_INTERVAL_MS = 1200
MAX_ENEMIES = 5  # <= your requested max

# BULLETS
BULLET_RADIUS = 5
BULLET_SPEED = 7.0
BULLET_LIFETIME_MS = 2600

PLAYER_SHOOT_COOLDOWN_MS = 250

enemies = []
enemy_bullets = []
player_bullets = []

NEXT_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(NEXT_SPAWN_EVENT, SPAWN_INTERVAL_MS)

# =====================
# LEVEL
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
        self.hp = 5
        self.last_shot = 0

    def move(self, x, y):
        self.xpos += x * player_speed
        self.ypos += y * player_speed

player = Player()

# =====================
# SCREEN
# =====================
surface = pygame.display.set_mode(SCREEN_SIZE)

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

WORLD_RECT = pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT)

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
                walls.append(pygame.Rect(col_i * TILE_SIZE, row_i * TILE_SIZE, TILE_SIZE, TILE_SIZE))

build_walls()

# =====================
# HELPERS
# =====================
def normalize(vx, vy):
    d = math.hypot(vx, vy)
    if d < 1e-6:
        return 0.0, 0.0
    return vx / d, vy / d

def draw_text(surf, text, x, y):
    font = pygame.font.SysFont(None, 28)
    img = font.render(text, True, (240, 240, 240))
    surf.blit(img, (x, y))

# =====================
# BULLET
# =====================
class Bullet:
    def __init__(self, x, y, vx, vy, owner):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.spawn_time = pygame.time.get_ticks()
        self.alive = True
        self.owner = owner  # "player" or "enemy"

    def update(self):
        if not self.alive:
            return

        self.x += self.vx
        self.y += self.vy

        # out of bounds
        if self.x < 0 or self.x > WORLD_WIDTH or self.y < 0 or self.y > WORLD_HEIGHT:
            self.alive = False
            return

        # lifetime
        if pygame.time.get_ticks() - self.spawn_time > BULLET_LIFETIME_MS:
            self.alive = False
            return

        # wall collision
        r = BULLET_RADIUS
        bullet_rect = pygame.Rect(int(self.x - r), int(self.y - r), r * 2, r * 2)
        for w in walls:
            if bullet_rect.colliderect(w):
                self.alive = False
                return

    def rect(self):
        r = BULLET_RADIUS
        return pygame.Rect(int(self.x - r), int(self.y - r), r * 2, r * 2)

    def draw(self, surf):
        sx = int(self.x)
        sy = int(self.y - camera_y)
        if -20 <= sy <= SCREEN_SIZE[1] + 20:
            color = (120, 200, 255) if self.owner == "player" else (255, 220, 120)
            pygame.draw.circle(surf, color, (sx, sy), BULLET_RADIUS)

# =====================
# ENEMY
# =====================
class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)

        angle = random.random() * math.tau
        self.vx = math.cos(angle) * ENEMY_SPEED
        self.vy = math.sin(angle) * ENEMY_SPEED

        self.last_shot = pygame.time.get_ticks() + random.randint(0, ENEMY_SHOOT_COOLDOWN_MS)

    def move_and_collide(self, dx, dy):
        # Move X
        self.rect.x += dx
        hit = False
        for w in walls:
            if self.rect.colliderect(w):
                hit = True
                if dx > 0:
                    self.rect.right = w.left
                elif dx < 0:
                    self.rect.left = w.right
        if hit:
            self.vx *= -1

        # Move Y
        self.rect.y += dy
        hit = False
        for w in walls:
            if self.rect.colliderect(w):
                hit = True
                if dy > 0:
                    self.rect.bottom = w.top
                elif dy < 0:
                    self.rect.top = w.bottom
        if hit:
            self.vy *= -1

        self.rect.clamp_ip(WORLD_RECT)

        # bounce at world edges
        if self.rect.left <= 0:
            self.rect.left = 0
            self.vx = abs(self.vx)
        if self.rect.right >= WORLD_WIDTH:
            self.rect.right = WORLD_WIDTH
            self.vx = -abs(self.vx)
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy = abs(self.vy)
        if self.rect.bottom >= WORLD_HEIGHT:
            self.rect.bottom = WORLD_HEIGHT
            self.vy = -abs(self.vy)

    def shoot_at(self, target_pos):
        tx, ty = target_pos
        sx, sy = self.rect.center
        dx, dy = (tx - sx), (ty - sy)
        nx, ny = normalize(dx, dy)
        vx = nx * BULLET_SPEED
        vy = ny * BULLET_SPEED
        enemy_bullets.append(Bullet(sx, sy, vx, vy, owner="enemy"))

    def update(self, target_pos):
        # wander
        self.vx += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)
        self.vy += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)

        # slight drift toward player
        tx, ty = target_pos
        cx, cy = self.rect.center
        to_px, to_py = (tx - cx), (ty - cy)
        nx, ny = normalize(to_px, to_py)
        self.vx += nx * 0.08
        self.vy += ny * 0.08

        # cap speed
        sp = math.hypot(self.vx, self.vy)
        if sp > ENEMY_SPEED:
            self.vx = (self.vx / sp) * ENEMY_SPEED
            self.vy = (self.vy / sp) * ENEMY_SPEED

        self.move_and_collide(int(round(self.vx)), int(round(self.vy)))

        # shoot
        now = pygame.time.get_ticks()
        if now - self.last_shot >= ENEMY_SHOOT_COOLDOWN_MS:
            self.last_shot = now
            self.shoot_at(target_pos)

    def draw(self, surf):
        sr = self.rect.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surf, (200, 60, 60), sr, border_radius=6)

# =====================
# SPAWN
# =====================
def spawn_enemy():
    # spawn near top of the camera view
    spawn_y = max(0, int(camera_y) - TILE_SIZE)

    tries = 120
    while tries > 0:
        tries -= 1
        x = random.randint(0, WORLD_WIDTH - ENEMY_SIZE)
        y_low = spawn_y
        y_high = min(spawn_y + TILE_SIZE * 3, WORLD_HEIGHT - ENEMY_SIZE)
        if y_high < y_low:
            y_low, y_high = 0, WORLD_HEIGHT - ENEMY_SIZE

        y = random.randint(y_low, y_high)
        e = Enemy(x, y)

        if any(e.rect.colliderect(w) for w in walls):
            continue

        enemies.append(e)
        return

# =====================
# PLAYER SHOOT
# =====================
def player_shoot():
    now = pygame.time.get_ticks()
    if now - player.last_shot < PLAYER_SHOOT_COOLDOWN_MS:
        return
    player.last_shot = now

    mx, my = mario_rect.center
    # shoot toward mouse in WORLD coords
    mouse_screen = pygame.mouse.get_pos()
    target_world = (mouse_screen[0], mouse_screen[1] + camera_y)

    dx, dy = (target_world[0] - mx), (target_world[1] - my)
    nx, ny = normalize(dx, dy)
    vx = nx * BULLET_SPEED
    vy = ny * BULLET_SPEED
    player_bullets.append(Bullet(mx, my, vx, vy, owner="player"))

# =====================
# PLAYER MOVEMENT + COLLISION
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

    mario_rect.clamp_ip(WORLD_RECT)
    player.xpos, player.ypos = mario_rect.topleft

# =====================
# CAMERA
# =====================
def update_camera():
    global camera_y
    camera_y -= scroll_speed
    if camera_y < 0:
        camera_y = 0

# =====================
# GRID
# =====================
def draw_grid(surf):
    if not SHOW_GRID:
        return
    w, h = surf.get_size()
    start_y = -(camera_y % TILE_SIZE)

    x = 0
    while x <= w:
        pygame.draw.line(surf, (50, 50, 50), (x, 0), (x, h))
        x += TILE_SIZE

    y = start_y
    while y <= h:
        pygame.draw.line(surf, (50, 50, 50), (0, y), (w, y))
        y += TILE_SIZE

# =====================
# UPDATE ENTITIES
# =====================
def update_enemies_and_bullets():
    player_center = mario_rect.center

    for e in enemies:
        e.update(player_center)

    for b in enemy_bullets:
        b.update()
    for b in player_bullets:
        b.update()

    # collisions: enemy bullets -> player
    p_rect = mario_rect
    for b in enemy_bullets:
        if b.alive and b.rect().colliderect(p_rect):
            b.alive = False
            player.hp -= 1

    # collisions: player bullets -> enemies
    for b in player_bullets:
        if not b.alive:
            continue
        br = b.rect()
        for e in enemies:
            if br.colliderect(e.rect):
                b.alive = False
                enemies.remove(e)
                break

    # cleanup bullets
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    player_bullets[:] = [b for b in player_bullets if b.alive]

# =====================
# RENDER
# =====================
def render_frame(surf):
    surf.fill((0, 0, 0))

    # walls
    for wall in walls:
        screen_rect = wall.move(0, -camera_y)
        if screen_rect.bottom >= 0 and screen_rect.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surf, (120, 120, 120), screen_rect)

    draw_grid(surf)

    # enemies
    for e in enemies:
        e.draw(surf)

    # bullets
    for b in enemy_bullets:
        b.draw(surf)
    for b in player_bullets:
        b.draw(surf)

    # player
    surf.blit(mario, (mario_rect.x, mario_rect.y - camera_y))

    # UI
    draw_text(surf, f"HP: {player.hp}", 12, 12)
    draw_text(surf, f"Enemies: {len(enemies)}/{MAX_ENEMIES}", 12, 36)
    draw_text(surf, "Shoot: SPACE (aim with mouse)", 12, 60)

    flip()

# =====================
# MAIN
# =====================
def main():
    global SHOW_GRID
    pygame.display.set_caption("Pygame Scroller (Shooters)")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    SHOW_GRID = not SHOW_GRID
                if event.key == pygame.K_SPACE:
                    player_shoot()

            if event.type == NEXT_SPAWN_EVENT:
                # spawn UP TO MAX
                if len(enemies) < MAX_ENEMIES:
                    spawn_enemy()

        handle_player_movement()
        update_camera()
        update_enemies_and_bullets()
        render_frame(surface)

        if player.hp <= 0:
            pygame.quit()
            exit()

        clock.tick(60)

main()
