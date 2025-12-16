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
MAX_ENEMIES = 5
ENEMY_SIZE = 44
ENEMY_SPEED = 2.2
ENEMY_WANDER_JITTER = 0.35
ENEMY_SHOOT_COOLDOWN_MS = 900
SPAWN_INTERVAL_MS = 1200

# BULLETS
BULLET_SPEED = 7.0
BULLET_LIFETIME_MS = 2600
PLAYER_SHOOT_COOLDOWN_MS = 250

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
#....###########
#..............#
#..............#
######.........#
#..............#
#..............#
#.....##########
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
# SCREEN
# =====================
surface = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Pygame Shooter")

# =====================
# IMAGES
# =====================
player_img = pygame.image.load("images/kerstman-def.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (55, 55))

player_bullet_img_base = pygame.image.load("images/SNOWBALL.png").convert_alpha()
enemy_bullet_img_base = pygame.image.load("images/SNOWBALL.png").convert_alpha()
player_bullet_img_base = pygame.transform.scale(player_bullet_img_base, (20,20))
enemy_bullet_img_base = pygame.transform.scale(enemy_bullet_img_base, (20,20))

# =====================
# WORLD SIZE + CAMERA
# =====================
map_width_tiles = len(LEVEL_MAP[0])
map_height_tiles = len(LEVEL_MAP)

WORLD_WIDTH = map_width_tiles * TILE_SIZE
WORLD_HEIGHT = map_height_tiles * TILE_SIZE
WORLD_RECT = pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT)

camera_y = max(0, WORLD_HEIGHT - SCREEN_SIZE[1])

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

def rotate_image_to_velocity(img, vx, vy):
    # image should face RIGHT by default
    angle = -math.degrees(math.atan2(vy, vx))
    return pygame.transform.rotate(img, angle)

def draw_text(surf, text, x, y, size=26):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, (240, 240, 240))
    surf.blit(img, (x, y))

# =====================
# PLAYER
# =====================
class Player:
    def __init__(self):
        self.rect = player_img.get_rect()
        self.rect.topleft = (200, WORLD_HEIGHT - TILE_SIZE * 2)
        self.hp = 5
        self.last_shot = 0

player = Player()

# =====================
# MOVEMENT + COLLISION (PLAYER)
# =====================
def move_rect_with_walls(rect: pygame.Rect, dx: int, dy: int):
    # X axis
    rect.x += dx
    for w in walls:
        if rect.colliderect(w):
            if dx > 0:
                rect.right = w.left
            elif dx < 0:
                rect.left = w.right

    # Y axis
    rect.y += dy
    for w in walls:
        if rect.colliderect(w):
            if dy > 0:
                rect.bottom = w.top
            elif dy < 0:
                rect.top = w.bottom

    rect.clamp_ip(WORLD_RECT)

def handle_player_movement():
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * player_speed
    dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * player_speed
    move_rect_with_walls(player.rect, dx, dy)

# =====================
# BULLET (IMAGE)
# =====================
class Bullet:
    def __init__(self, x, y, vx, vy, owner, base_image):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.owner = owner

        self.spawn_time = pygame.time.get_ticks()
        self.alive = True

        self.image = rotate_image_to_velocity(base_image, self.vx, self.vy)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self):
        if not self.alive:
            return

        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))

        # world bounds
        if not WORLD_RECT.collidepoint(self.rect.center):
            self.alive = False
            return

        # lifetime
        if pygame.time.get_ticks() - self.spawn_time > BULLET_LIFETIME_MS:
            self.alive = False
            return

        # walls
        for w in walls:
            if self.rect.colliderect(w):
                self.alive = False
                return

    def draw(self, surf):
        screen_y = self.rect.y - camera_y
        if -100 <= screen_y <= SCREEN_SIZE[1] + 100:
            surf.blit(self.image, (self.rect.x, screen_y))

# =====================
# ENEMY (flying + shooting)
# =====================
class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)

        angle = random.random() * math.tau
        self.vx = math.cos(angle) * ENEMY_SPEED
        self.vy = math.sin(angle) * ENEMY_SPEED

        self.last_shot = pygame.time.get_ticks() + random.randint(0, ENEMY_SHOOT_COOLDOWN_MS)

    def move_and_collide(self, dx, dy):
        # X
        self.rect.x += dx
        hit_x = False
        for w in walls:
            if self.rect.colliderect(w):
                hit_x = True
                if dx > 0:
                    self.rect.right = w.left
                elif dx < 0:
                    self.rect.left = w.right
        if hit_x:
            self.vx *= -1

        # Y
        self.rect.y += dy
        hit_y = False
        for w in walls:
            if self.rect.colliderect(w):
                hit_y = True
                if dy > 0:
                    self.rect.bottom = w.top
                elif dy < 0:
                    self.rect.top = w.bottom
        if hit_y:
            self.vy *= -1

        self.rect.clamp_ip(WORLD_RECT)

        # bounce on world edges
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

    def shoot_at(self, target_pos, bullet_list):
        tx, ty = target_pos
        sx, sy = self.rect.center
        dx, dy = (tx - sx), (ty - sy)
        nx, ny = normalize(dx, dy)
        bullet_list.append(
            Bullet(
                sx, sy,
                nx * BULLET_SPEED, ny * BULLET_SPEED,
                owner="enemy",
                base_image=enemy_bullet_img_base
            )
        )

    def update(self, target_pos, bullet_list):
        # wander
        self.vx += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)
        self.vy += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)

        # drift slightly toward player
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
            self.shoot_at(target_pos, bullet_list)

    def draw(self, surf):
        sr = self.rect.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surf, (200, 60, 60), sr, border_radius=6)

# =====================
# SPAWN
# =====================
def spawn_enemy(enemies_list):
    # Spawn near top of camera view (world coords)
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

        enemies_list.append(e)
        return

# =====================
# SHOOTING
# =====================
def player_shoot(player_bullets):
    now = pygame.time.get_ticks()
    if now - player.last_shot < PLAYER_SHOOT_COOLDOWN_MS:
        return
    player.last_shot = now

    # Aim at mouse (mouse is screen coords; convert to world coords)
    mx, my = pygame.mouse.get_pos()
    target_world = (mx, my + camera_y)

    sx, sy = player.rect.center
    dx, dy = (target_world[0] - sx), (target_world[1] - sy)
    nx, ny = normalize(dx, dy)

    player_bullets.append(
        Bullet(
            sx, sy,
            nx * BULLET_SPEED, ny * BULLET_SPEED,
            owner="player",
            base_image=player_bullet_img_base
        )
    )

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
    
    top_limit = camera_y
    bottom_limit = camera_y + SCREEN_SIZE[1] - mario_rect.height

    if player.ypos < top_limit:
        player.ypos = top_limit
    elif player.ypos > bottom_limit:
        player.ypos = bottom_limit

    player.xpos = max(0, min(player.xpos, WORLD_WIDTH - mario_rect.width))

    mario_rect.topleft = (player.xpos, player.ypos)
    
    

# =====================
# CAMERA SCROLL
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
# GAME STATE
# =====================
enemies = []
enemy_bullets = []
player_bullets = []

SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL_MS)

# =====================
# UPDATE
# =====================
def update_all():
    # enemies
    player_center = player.rect.center
    for e in enemies:
        e.update(player_center, enemy_bullets)

    # bullets
    for b in enemy_bullets:
        b.update()
    for b in player_bullets:
        b.update()

    # enemy bullets -> player
    for b in enemy_bullets:
        if b.alive and b.rect.colliderect(player.rect):
            b.alive = False
            player.hp -= 1

    # player bullets -> enemies
    for b in player_bullets:
        if not b.alive:
            continue
        for e in enemies:
            if b.rect.colliderect(e.rect):
                b.alive = False
                enemies.remove(e)
                break

    # cleanup bullets
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    player_bullets[:] = [b for b in player_bullets if b.alive]

# =====================
# RENDER
# =====================
def render():
    surface.fill((0, 0, 0))

    # walls
    for w in walls:
        sr = w.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surface, (120, 120, 120), sr)

    draw_grid(surface)

    # enemies
    for e in enemies:
        e.draw(surface)

    # bullets
    for b in enemy_bullets:
        b.draw(surface)
    for b in player_bullets:
        b.draw(surface)

    # player
    surface.blit(player_img, (player.rect.x, player.rect.y - camera_y))

    # UI
    draw_text(surface, f"HP: {player.hp}", 12, 10)
    draw_text(surface, f"Enemies: {len(enemies)}/{MAX_ENEMIES}", 12, 34)
    draw_text(surface, "Move: Arrow keys | Shoot: SPACE (aim with mouse) | Grid: G", 12, 58, size=22)

    flip()




def check_ceiling_crush():
    """
    If player is at the bottom of the screen and hits a wall above, you die.
    """
    # Player screen rect
    player_screen_rect = mario_rect.move(0, -camera_y)
    
    # Check if player is at bottom of screen
    if player_screen_rect.bottom >= SCREEN_SIZE[1]:
        # Look for walls that overlap player
        for wall in walls:
            wall_screen_rect = wall.move(0, -camera_y)
            if wall_screen_rect.colliderect(player_screen_rect):
                # Optional: only trigger if wall is above player
                if wall_screen_rect.bottom < player_screen_rect.bottom:
                    print("Player crushed! Game over!")
                    pygame.quit()
                    exit()


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
                if event.key == pygame.K_SPACE:
                    player_shoot(player_bullets)

            if event.type == SPAWN_EVENT:
                if len(enemies) < MAX_ENEMIES:
                    spawn_enemy(enemies)

        handle_player_movement()
        update_camera()
        update_all()
        render()

        if player.hp <= 0:
            pygame.quit()
            exit()

        check_ceiling_crush()
        update_enemies()
        render_frame(surface)
        clock.tick(60)

main()
