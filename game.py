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

FLAME_CYCLE_MS = 5000
FLAME_ON_MS = 800


DEBUG_CAMERA = False
DEBUG_CAMERA_STEP = 80   # how many pixels per tap (change if you want faster/slower)


BG_SCALE = 1.5

USE_ZQSD = True  # False = WASD, True = ZQSD

SCREEN_SIZE = (1024, 768)
TILE_SIZE = 64  
player_speed = 5

scroll_speed = 0.7
SHOW_GRID = False

BOSS_BULLET_SPEED = 4
BOSS_SHOOT_INTERVAL_MS = 400  # shoot every half second
BOSS_BULLET_LINES = 6
BOSS_BULLET_ROT_SPEED = 10  # degrees per update
boss_spawned = False
boss = None

# ENEMIES
MAX_ENEMIES = 5
ENEMY_SIZE = 64 
ENEMY_SPEED = 2.2
ENEMY_WANDER_JITTER = 0.35
ENEMY_SHOOT_COOLDOWN_MS = 900
SPAWN_INTERVAL_MS = 2000
last_enemy_spawn_time = 0

# BULLETS
BULLET_SPEED = 4
BULLET_LIFETIME_MS = 3500
PLAYER_SHOOT_COOLDOWN_MS = 250

#LASER
LASER_WARNING_MS = 1200
LASER_ACTIVE_MS = 1500
LASER_DAMAGE = 2
LASER_HEIGHT = TILE_SIZE

BOSS_WIDTH_TILES = 4
BOSS_HEIGHT_TILES = 4
boss = None
boss_spawned = False
stop_enemy_spawning = False

# PRESENTS
PRESENT_SIZE = 40
PRESENT_SPAWN_MS = 3000
PRESENT_EVENT = pygame.USEREVENT + 2
pygame.time.set_timer(PRESENT_EVENT, PRESENT_SPAWN_MS)
present_rect = None
present_count = 0

# TIMER & FADE TEXT
game_start_ticks = pygame.time.get_ticks()
fade_text = None
fade_text_start = 0
FADE_DURATION = 2000  # ms

LASER_SPAWN_MS = random.randint(10000, 20000)
LASER_EVENT = pygame.USEREVENT + 3
pygame.time.set_timer(LASER_EVENT, LASER_SPAWN_MS)

# =====================
# LEVEL
# =====================
LEVEL_TEXT = """
1tttttttttttttt2
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
3bbbbb6..5bbbbb4
1ttttt7..8ttttt2
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l...5bbbbbb6...r
lFFFr######lFFFr
l...82####17...r
l....8tttt7....r
l..............r
l..............r
l..............r
36.............r
#36............r
##l............r
##3b6..........r
####36.........r
#####3bb6...5bb2
##1ttttt7...8tt2
#17............r 
17.............r
l.....5bbbbb6..r
l.....8ttttt7..r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
l..............r
3bbbbbbbbbbbbbb4
"""

LEVEL_MAP = [row for row in LEVEL_TEXT.strip().splitlines()]
walls = []

#56
#87

# =====================
# SCREEN
# =====================
surface = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Pygame Shooter")

# =====================
# IMAGES
# =====================

enemy_hit_img = pygame.image.load("images/ENEMY_HIT.png").convert_alpha()
enemy_hit_img = pygame.transform.scale(enemy_hit_img, (ENEMY_SIZE, ENEMY_SIZE))


enemy_img = pygame.image.load("images/ENEMY.png").convert_alpha()
enemy_img = pygame.transform.scale(enemy_img, (ENEMY_SIZE, ENEMY_SIZE))

player_img = pygame.image.load("images/kerstman-def.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (55, 55))
player_img_base = player_img.copy()

player_bullet_img_base = pygame.image.load("images/SNOWBALL.png").convert_alpha()
enemy_bullet_img_base = pygame.image.load("images/ENEMYBULLET.png").convert_alpha()
player_bullet_img_base = pygame.transform.scale(player_bullet_img_base, (25,25))
enemy_bullet_img_base = pygame.transform.scale(enemy_bullet_img_base, (25,25))
background_img = pygame.image.load("IMAGES/bkg1.png").convert()
background_img2 = pygame.image.load("IMAGES/bkg2.png").convert()

# LASER IMAGES (replace later with PNGs)
laser_warning_img = pygame.Surface(((SCREEN_SIZE[0]), LASER_HEIGHT), pygame.SRCALPHA)
# laser_warning_img = pygame.image.load("images/laser_warning.png").convert_alpha()
laser_warning_img.fill((255, 50, 50, 120))  # semi-transparent red

laser_active_img = pygame.Surface(((SCREEN_SIZE[0]), LASER_HEIGHT), pygame.SRCALPHA)
# laser_active_img = pygame.image.load("images/laser_active.png").convert_alpha()
laser_active_img.fill((255, 0, 0))  # solid red

# ENEMY HEALTHBAR IMAGES (replace filenames with yours)
hb_full  = pygame.image.load("images/hb_full.png").convert_alpha()
hb_23    = pygame.image.load("images/hb_23.png").convert_alpha()
hb_13    = pygame.image.load("images/hb_13.png").convert_alpha()
hb_empty = pygame.image.load("images/hb_empty.png").convert_alpha()

# scale them to enemy width (44) and a small height (adjust if you want)
HB_W, HB_H = ENEMY_SIZE, 10
hb_full  = pygame.transform.scale(hb_full,  (HB_W, HB_H))
hb_23    = pygame.transform.scale(hb_23,    (HB_W, HB_H))
hb_13    = pygame.transform.scale(hb_13,    (HB_W, HB_H))
hb_empty = pygame.transform.scale(hb_empty, (HB_W, HB_H))


background_img = pygame.transform.smoothscale(
    background_img,
    (int(background_img.get_width() * BG_SCALE),
     int(background_img.get_height() * BG_SCALE))
)
background_img2 = pygame.transform.smoothscale(
    background_img2,
    (int(background_img2.get_width() * BG_SCALE),
     int(background_img2.get_height() * BG_SCALE))
)


background_imgs = [background_img, background_img2]
bg_index = 0
bg_y = 0.0
bg_height = background_img.get_height()

boss_img = pygame.image.load("images/boss.png").convert_alpha()
boss_img = pygame.transform.scale(boss_img, (TILE_SIZE * BOSS_WIDTH_TILES, TILE_SIZE * BOSS_HEIGHT_TILES))



present_img = pygame.image.load("images/present1.png").convert_alpha()
present_img = pygame.transform.scale(present_img, (PRESENT_SIZE, PRESENT_SIZE))


# =====================
# TILE TEXTURES (MAP LETTERS)
# =====================

# Walkable tiles
empty_tile  = pygame.image.load("images/ICE.png").convert_alpha()
cracked_tile = pygame.image.load("images/CRACKED_ICE.png").convert_alpha()


empty_tile   = pygame.transform.scale(empty_tile, (TILE_SIZE, TILE_SIZE))
cracked_tile = pygame.transform.scale(cracked_tile, (TILE_SIZE, TILE_SIZE))


# Solid wall tiles
tile_cliff = pygame.image.load("images/WHITE.png").convert_alpha()

#hazards
flame_tile = pygame.image.load("images/FLAME.png").convert_alpha()


#hazards
flame_tile = pygame.transform.scale(flame_tile, (TILE_SIZE, TILE_SIZE))


#standart cliff tiles
tile_cliff_L = pygame.image.load("images/CLIFF_L.png").convert_alpha()
tile_cliff_T = pygame.image.load("images/CLIFF_T.png").convert_alpha()
tile_cliff_R = pygame.image.load("images/CLIFF_R.png").convert_alpha()
tile_cliff_B = pygame.image.load("images/CLIFF_B.png").convert_alpha()

#inner corner tiles
tile_cliff_innercorner_LO = pygame.image.load("images/CLIFF_INNERCORNER_LO.png").convert_alpha()
tile_cliff_innercorner_RO = pygame.image.load("images/CLIFF_INNERCORNER_RO.png").convert_alpha()
tile_cliff_innercorner_LB = pygame.image.load("images/CLIFF_INNERCORNER_LB.png").convert_alpha()
tile_cliff_innercorner_RB = pygame.image.load("images/CLIFF_INNERCORNER_RB.png").convert_alpha()

#outer corner tiles
tile_cliff_outercorner_LO = pygame.image.load("images/CLIFF_OUTERCORNER_LO.png").convert_alpha()
tile_cliff_outercorner_RO = pygame.image.load("images/CLIFF_OUTERCORNER_RO.png").convert_alpha()
tile_cliff_outercorner_LB = pygame.image.load("images/CLIFF_OUTERCORNER_LB.png").convert_alpha()
tile_cliff_outercorner_RB = pygame.image.load("images/CLIFF_OUTERCORNER_RB.png").convert_alpha()



# scale all to tile size
tile_cliff = pygame.transform.scale(tile_cliff, (TILE_SIZE, TILE_SIZE))
empty_tile = pygame.transform.scale(empty_tile, (TILE_SIZE, TILE_SIZE))
tile_cliff_L = pygame.transform.scale(tile_cliff_L, (TILE_SIZE, TILE_SIZE))
tile_cliff_T = pygame.transform.scale(tile_cliff_T, (TILE_SIZE, TILE_SIZE))
tile_cliff_R = pygame.transform.scale(tile_cliff_R, (TILE_SIZE, TILE_SIZE))
tile_cliff_B = pygame.transform.scale(tile_cliff_B, (TILE_SIZE, TILE_SIZE))
tile_cliff_innercorner_LO = pygame.transform.scale(tile_cliff_innercorner_LO, (TILE_SIZE, TILE_SIZE))
tile_cliff_innercorner_RO = pygame.transform.scale(tile_cliff_innercorner_RO, (TILE_SIZE, TILE_SIZE))
tile_cliff_innercorner_LB = pygame.transform.scale(tile_cliff_innercorner_LB, (TILE_SIZE, TILE_SIZE))
tile_cliff_innercorner_RB = pygame.transform.scale(tile_cliff_innercorner_RB, (TILE_SIZE, TILE_SIZE))



# Which map chars are SOLID (collision)
SOLID_TILES = {"#","r","t","l","b","1","2","3","4","5","6","7","8","F"}   # add/remove letters freely

# Which texture to draw for each map char
TILE_TEXTURES = {
    ".": empty_tile,        # walkable

    "#": tile_cliff, # solid
    "r": tile_cliff_L,
    "t": tile_cliff_T,
    "l": tile_cliff_R,
    "b": tile_cliff_B,
    "1": tile_cliff_innercorner_RO,
    "2": tile_cliff_innercorner_LO,
    "3": tile_cliff_innercorner_RB,
    "4": tile_cliff_innercorner_LB,
    "5": tile_cliff_outercorner_LB,
    "6": tile_cliff_outercorner_RB,
    "7": tile_cliff_outercorner_RO,
    "8": tile_cliff_outercorner_LO

}


# =====================
# WORLD SIZE + CAMERA
# =====================
map_width_tiles = len(LEVEL_MAP[0])
map_height_tiles = len(LEVEL_MAP)

WORLD_WIDTH = map_width_tiles * TILE_SIZE
WORLD_HEIGHT = map_height_tiles * TILE_SIZE
WORLD_RECT = pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT)

camera_y = max(0, WORLD_HEIGHT - SCREEN_SIZE[1])
camera_start_y = camera_y

bg_y = 0
bg_height = background_img.get_height()

# =====================
# HELPERS
# =====================

def flame_is_on(row_i, col_i):
    now = pygame.time.get_ticks()
    t = now % FLAME_CYCLE_MS
    return t < FLAME_ON_MS


def find_debug_final_room_spot():
    """
    Finds a safe walkable '.' spot near the TOP of the map (the end/final area).
    Returns (x, y) world coords for the player's center.
    """
    # search only the top part of the map first (tweak 25 if you want)
    max_rows_to_scan = min(25, len(LEVEL_MAP))

    for row_i in range(max_rows_to_scan):
        row = LEVEL_MAP[row_i]
        for col_i, ch in enumerate(row):
            if ch != ".":
                continue

            # candidate position (center of tile)
            cx = col_i * TILE_SIZE + TILE_SIZE // 2
            cy = row_i * TILE_SIZE + TILE_SIZE // 2

            test_rect = player.rect.copy()
            test_rect.center = (cx, cy)

            # must be inside world and not colliding walls
            if not WORLD_RECT.contains(test_rect):
                continue
            if any(test_rect.colliderect(w) for w in walls):
                continue

            return (cx, cy)

    # fallback: if nothing found in top scan, scan entire map
    for row_i, row in enumerate(LEVEL_MAP):
        for col_i, ch in enumerate(row):
            if ch != ".":
                continue
            cx = col_i * TILE_SIZE + TILE_SIZE // 2
            cy = row_i * TILE_SIZE + TILE_SIZE // 2
            test_rect = player.rect.copy()
            test_rect.center = (cx, cy)
            if WORLD_RECT.contains(test_rect) and not any(test_rect.colliderect(w) for w in walls):
                return (cx, cy)

    return None


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

    # Main text (bright) + small shadow
    txt = font.render(text, True, (255, 255, 255))
    shadow = font.render(text, True, (0, 0, 0))


    # Background box behind the text (semi-transparent)
    pad_x, pad_y = 8, 4
    bg_w = txt.get_width() + pad_x * 2
    bg_h = txt.get_height() + pad_y * 2

    bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))  # (R,G,B,Alpha)

    # Draw box + shadow + text
    surf.blit(bg, (x - pad_x, y - pad_y))
    surf.blit(shadow, (x + 1, y + 1))
    surf.blit(txt, (x, y))


def show_fade_text(text):
    global fade_text, fade_text_start
    fade_text = text
    fade_text_start = pygame.time.get_ticks()

def remaining_ms(end_time):
    if end_time == 0:
        return 0
    return max(0, end_time - pygame.time.get_ticks())

# =====================
# WALLS
# =====================
def build_walls():
    walls.clear()
    for row_i, row in enumerate(LEVEL_MAP):
        for col_i, tile in enumerate(row):
            if tile in SOLID_TILES:
                if tile == "F" and not flame_is_on(row_i, col_i):
                    continue
                walls.append(pygame.Rect(col_i * TILE_SIZE, row_i * TILE_SIZE, TILE_SIZE, TILE_SIZE))


build_walls()

# =====================
# PLAYER
# =====================
class Player:
    def __init__(self):
        self.rect = player_img.get_rect()
        self.image = player_img
        self.rect.topleft = (200, WORLD_HEIGHT - TILE_SIZE * 2)
        self.maxhp = 20 
        self.hp = self.maxhp
        self.last_shot = 0
        self.base_damage = 1
        self.damage = self.base_damage
        self.damage_boost_end = 0
        self.base_size = self.image.get_size()
        self.size_boost_end = 0

player = Player()

# =====================
# BACKGROUND
# =====================

def update_background():
    global bg_y, bg_index

    # how far the camera has moved up since the start
    scroll_amount = camera_start_y - camera_y  # increases over time

    # which background we are on (bkg1 -> bkg2 -> bkg1 ...)
    bg_index = int(scroll_amount // bg_height) % 2

    # offset inside the current background (locks perfectly to camera)
    bg_y = scroll_amount % bg_height



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

        self.max_hp = 3
        self.hp = self.max_hp

        self.dead = False
        self.death_time = 0
            
        self.hit_flash_end = 0




    def move_and_collide(self, dx, dy):
        # X
        self.rect.x += dx
        hit_x = False
        for w in walls:
            # Ignore walls if enemy is 3 tiles below the top of the camera
            if self.rect.top >= camera_y + SCREEN_SIZE[1] + TILE_SIZE * 1:
                continue
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
            if self.rect.top >= camera_y + SCREEN_SIZE[1] + TILE_SIZE * 3:
                continue
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
            img = enemy_hit_img if pygame.time.get_ticks() < self.hit_flash_end else enemy_img
            surf.blit(img, sr.topleft)

                # --- healthbar sprite selection ---
        if self.hp >= 3:
            hb_img = hb_full
        elif self.hp == 2:
            hb_img = hb_23
        elif self.hp == 1:
            hb_img = hb_13
        else:
            hb_img = hb_empty


        # draw above enemy (screen space)
        hb_x = sr.x
        hb_y = sr.y - HB_H - 4
        surf.blit(hb_img, (hb_x, hb_y))


class HorizontalLaser:
    def __init__(self, y):
        self.y = y
        self.rect = pygame.Rect(0, y, (SCREEN_SIZE[0]), LASER_HEIGHT)

        self.spawn_time = pygame.time.get_ticks()
        self.state = "warning"  # "warning" → "active" → "dead"

        

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time

        if self.state == "warning" and elapsed > LASER_WARNING_MS:
            self.state = "active"

        elif self.state == "active" and elapsed > LASER_WARNING_MS + LASER_ACTIVE_MS:
            self.state = "dead"

        # damage player
        if self.state == "active":
            if self.rect.colliderect(player.rect):
                player.hp -= LASER_DAMAGE

    def draw(self, surf):
        screen_y = self.y - camera_y
        if screen_y < -LASER_HEIGHT or screen_y > SCREEN_SIZE[1]:
            return

        # blinking warning
        if self.state == "warning":
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                surf.blit(laser_warning_img, (0, screen_y))

        elif self.state == "active":
            surf.blit(laser_active_img, (0, screen_y))


class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, boss_img.get_width(), boss_img.get_height())
        self.image = boss_img
        self.hp = 50
        self.last_shot = pygame.time.get_ticks()
        self.angle_offset = 0  # rotation of bullet lines

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= BOSS_SHOOT_INTERVAL_MS:
            self.last_shot = now
            self.shoot_rotating_bullets()

    def draw(self, surf):
        sr = self.rect.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            surf.blit(boss_img, sr)

    def shoot_rotating_bullets(self):
        # shoot 4 lines from boss center
        cx, cy = self.rect.center
        num_lines = BOSS_BULLET_LINES
        for i in range(num_lines):
            angle_deg = (360 / num_lines) * i + self.angle_offset
            angle_rad = math.radians(angle_deg)
            vx = math.cos(angle_rad) * BOSS_BULLET_SPEED
            vy = math.sin(angle_rad) * BOSS_BULLET_SPEED
            boss_bullets.append(
                Bullet(cx, cy, vx, vy, owner="boss", base_image=enemy_bullet_img_base)
            )
        # rotate for next shot
        self.angle_offset = (self.angle_offset + BOSS_BULLET_ROT_SPEED) % 360

class AoEField:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = TILE_SIZE * 1.5
        self.growth_speed = 1.0         # pixels per frame
        self.spawn_time = pygame.time.get_ticks()
        self.active = False
        self.damage_done = False
        self.duration_ms = 3000         # AoE lasts 3 seconds

    @property
    def alive(self):
        # alive until duration passed
        return pygame.time.get_ticks() - self.spawn_time < self.duration_ms

    def update(self):
        # grow circle until max radius
        if self.radius < self.max_radius:
            self.radius += self.growth_speed
        else:
            self.active = True

        # damage player once
        if self.active and not self.damage_done:
            dist = math.hypot(player.rect.centerx - self.x, player.rect.centery - self.y)
            if dist < self.radius:
                player.hp -= 1
                self.damage_done = True

    def draw(self, surf):
        screen_y = self.y - camera_y
        pygame.draw.circle(
            surf,
            (255, 0, 0),               # full red, opaque
            (int(self.x), int(screen_y)),
            int(self.radius),
            width=0                     # filled circle
        )

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


# PRESENTS
# =====================
def spawn_present():
    global present_rect
    if present_rect is not None:
        return
    tries=100
    while tries>0:
        tries-=1
        x=random.randint(0,WORLD_WIDTH-PRESENT_SIZE)
        y_min = int(camera_y - TILE_SIZE * 2)   # max 2 tiles above screen
        y_max = int(camera_y + SCREEN_SIZE[1] - PRESENT_SIZE)

        y_min = max(0, y_min)  # never above world top

        if y_max < y_min:
            return  # safety

        y = random.randint(y_min, y_max)

        rect = pygame.Rect(x, y, PRESENT_SIZE, PRESENT_SIZE)
        rect = pygame.Rect(x,y,PRESENT_SIZE,PRESENT_SIZE)
        if any(rect.colliderect(w) for w in walls):
            
            continue
        present_rect = rect
        show_fade_text("Present spawned")
        return

def check_present_pickup():
    global present_rect, present_count
    if present_rect and player.rect.colliderect(present_rect):
        
        present_rect = None
        present_count += 1

        powerup = random.choice(["Heal", "Damage", "Smaller"])

        if powerup == "Heal":
            player.hp = player.maxhp
            show_fade_text("POWER UP: Heal")
        elif powerup == "Damage":
            player.damage = 3
            player.damage_boost_end = pygame.time.get_ticks() + 5000
            show_fade_text("POWER UP: Damage Boost")
        elif powerup == "Smaller":
            player.size_boost_end = pygame.time.get_ticks() + 5000

            new_size = (
                int(player.base_size[0] * 0.6),
                int(player.base_size[1] * 0.6),
            )

            player.image = pygame.transform.scale(player_img_base, new_size)

            # keep center when resizing
            center = player.rect.center
            player.rect = player.image.get_rect(center=center)
            show_fade_text("POWER UP: Shrink")
           



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
    # Toggle between WASD and ZQSD
    if USE_ZQSD:
        left_key  = pygame.K_q
        right_key = pygame.K_d
        up_key    = pygame.K_z
        down_key  = pygame.K_s
    else:
        left_key  = pygame.K_a
        right_key = pygame.K_d
        up_key    = pygame.K_w
        down_key  = pygame.K_s

    dx = (keys[right_key] - keys[left_key]) * player_speed
    dy = (keys[down_key] - keys[up_key]) * player_speed

    move_rect_with_walls(player.rect, dx, dy)

    # Keep player inside screen vertical limits
    top_limit = camera_y
    bottom_limit = camera_y + SCREEN_SIZE[1] - player.rect.height
    if player.rect.y < top_limit:
        player.rect.y = top_limit
    elif player.rect.y > bottom_limit:
        player.rect.y = bottom_limit

    # Keep player inside world horizontal limits
    player.rect.x = max(0, min(player.rect.x, WORLD_WIDTH - player.rect.width))
    
    

# =====================
# CAMERA SCROLL
# =====================
def update_camera():
    global camera_y

    if DEBUG_CAMERA:
        return  # manual camera in debug mode

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
lasers = []
aoe_fields = []

pending_aoe_spawns = []  

boss_bullets = []
enemy_bullets = []
player_bullets = []
game_over=False
death_stats={}
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL_MS)
game_state = "menu"
previous_state = "menu"
  # "menu", "settings", "playing"

# Button helper
class Button:
    def __init__(self, rect, text, color=(50,50,200), hover_color=(100,100,255), text_color=(255,255,255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(surf, self.hover_color if is_hover else self.color, self.rect, border_radius=6)
        font = pygame.font.SysFont(None, 36)
        img = font.render(self.text, True, self.text_color)
        surf.blit(img, img.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

# Startscherm knoppen
start_button = Button((SCREEN_SIZE[0]//2-100, 300, 200, 60), "Start")
settings_button = Button((SCREEN_SIZE[0]//2-100, 400, 200, 60), "Settings")
# Settings scherm knoppen
back_button = Button((SCREEN_SIZE[0]//2-100, 500, 200, 60), "Back")
toggle_keys_button = Button((SCREEN_SIZE[0]//2-100, 300, 200, 60), "Toggle WASD/ZQSD")
# pause scherm knoppen 
resume_button =  Button((SCREEN_SIZE[0]//2-100, 300, 200, 60), "Resume")
restart_button = Button((SCREEN_SIZE[0]//2-100, 500, 200, 60), "Restart")

try_again_button = Button((SCREEN_SIZE[0]//2-100, 350, 200, 60), "Try Again")
back_to_menu_button = Button((SCREEN_SIZE[0]//2-100, 450, 200, 60), "Back to Menu")

win_play_again_button = Button((SCREEN_SIZE[0]//2-100, 350, 200, 60), "Play Again")
win_back_to_menu_button = Button((SCREEN_SIZE[0]//2-100, 450, 200, 60), "Back to Menu")


# =====================
# UPDATE
# =====================
def update_all():
    global boss_spawned, boss
    # enemies

    now = pygame.time.get_ticks()
    player_center = player.rect.center
    for e in enemies:
        e.update(player_center, enemy_bullets)

    handle_enemy_spawning()

    if boss:
        boss.update()

    if boss_spawned and boss:
        boss.update()

    for field in aoe_fields:
        field.update()
    aoe_fields[:] = [f for f in aoe_fields if f.alive]

    # remove dead AoE fields
    aoe_fields[:] = [f for f in aoe_fields if f.alive]

    # spawn new AoE every 2-3 seconds if boss exists
    if boss_spawned and boss:
        

        if not hasattr(update_all, "_next_aoe_spawn"):
            update_all._next_aoe_spawn = now + random.randint(4000, 6000)

        if now >= update_all._next_aoe_spawn:
            # spawn ONE AoE
            offset_x = random.randint(-TILE_SIZE*2, TILE_SIZE*2)
            offset_y = random.randint(0, TILE_SIZE*6)  # 0–6 tiles
            field_x = boss.rect.centerx + offset_x
            field_y = boss.rect.centery + offset_y
            aoe_fields.append(AoEField(field_x, field_y))

            # schedule next spawn
            update_all._next_aoe_spawn = now + random.randint(4000, 6000)

    # Check if we should spawn the boss
    if not boss_spawned and camera_y <= 0 and len(enemies) == 0:
        # Spawn boss in middle X, tiles 6-7 from top
        boss_x = WORLD_WIDTH // 2 - TILE_SIZE // 2
        boss_y = (6 * TILE_SIZE)  # 6th tile
        boss = Boss(boss_x, boss_y)
        boss_spawned = True

    # boss bullets
    for b in boss_bullets:
        b.update()
    boss_bullets[:] = [b for b in boss_bullets if b.alive]

    # collisions with player
    for b in boss_bullets:
        if b.alive and b.rect.colliderect(player.rect):
            b.alive = False
            player.hp -= 1

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
     
    

    # check pending AoE spawns
    
    for spawn in pending_aoe_spawns[:]:
        spawn_time, x, y = spawn
        if now >= spawn_time:
            aoe_fields.append(AoEField(x, y))
            pending_aoe_spawns.remove(spawn)

    # reset damage if boost expired
    if player.damage > player.base_damage and now > player.damage_boost_end:
        player.damage = player.base_damage

    if player.size_boost_end and now > player.size_boost_end:
        player.size_boost_end = 0

        center = player.rect.center
        player.image = player_img_base.copy()
        player.rect = player.image.get_rect(center=center)

    # cleanup bullets
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    player_bullets[:] = [b for b in player_bullets if b.alive]

    for laser in lasers:
        laser.update()

    lasers[:] = [l for l in lasers if l.state != "dead"]
        
    # player bullets -> enemies
    for b in player_bullets:
        if not b.alive:
            continue

        # hit normal enemies
        for e in enemies:
            if e.dead:
                continue
            if b.rect.colliderect(e.rect):
                b.alive = False
                e.hp -= player.damage
                e.hit_flash_end = pygame.time.get_ticks() + 120  # ms (flash duration)

                if e.hp <= 0:
                    e.dead = True
                break  # bullet stops after hitting one enemy

        # hit boss if exists
        if boss and b.alive and b.rect.colliderect(boss.rect):
            b.alive = False
            boss.hp -= player.damage
            if boss.hp <= 0:
                boss_spawned = False
                boss = None
                show_fade_text("BOSS DEFEATED!")
                # trigger win state
                global game_state
                game_state = "win"

    # remove dead enemies
    enemies[:] = [e for e in enemies if not e.dead]


# =====================
# RESTART FUNCTION
# =====================

def reset_game():
    global enemies, enemy_bullets, player_bullets
    global present_rect, present_count
    global camera_y, camera_start_y, bg_y, bg_index
    global game_start_ticks, fade_text, fade_text_start
    global player

    # clear entities
    enemies.clear()
    enemy_bullets.clear()
    player_bullets.clear()

    # reset presents
    present_rect = None
    present_count = 0

    # reset player
    player.rect.topleft = (200, WORLD_HEIGHT - TILE_SIZE * 2)
    player.hp = player.maxhp
    player.last_shot = 0

    # reset camera/background/timer
    camera_y = max(0, WORLD_HEIGHT - SCREEN_SIZE[1])
    camera_start_y = camera_y
    bg_y = 0.0
    bg_index = 0

    game_start_ticks = pygame.time.get_ticks()
    fade_text = None
    fade_text_start = 0
     # reset boss
    boss = None
    boss_spawned = False
    pending_aoe_spawns.clear()

    # reset next AoE spawn timer
    if hasattr(update_all, "_next_aoe_spawn"):
        delattr(update_all, "_next_aoe_spawn")

# =====================
# RENDER
# =====================
def render():
    global DEBUG_CAMERA
    surface.fill((0, 0, 0))
    img_a = background_imgs[bg_index]
    img_b = background_imgs[(bg_index + 1) % 2]

    surface.blit(img_a, (0, int(bg_y)))
    surface.blit(img_b, (0, int(bg_y) - bg_height))


    draw_walkable_tiles(surface)
    # walls
    for w in walls:
        sr = w.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            row_i = w.y // TILE_SIZE
            col_i = w.x // TILE_SIZE
            ch = LEVEL_MAP[row_i][col_i]

            # F only exists in walls when flame is ON (build_walls skips it when OFF)
            if ch == "F":
                img = flame_tile
            else:
                img = TILE_TEXTURES.get(ch, TILE_TEXTURES["#"])

            surface.blit(img, (sr.x, sr.y))


    draw_grid(surface)

    if present_rect:
        p_screen_y = present_rect.y - camera_y
        if -100 <= p_screen_y <= SCREEN_SIZE[1]+100:
            surface.blit(present_img,(present_rect.x,p_screen_y))

    # enemies
    for e in enemies:
        e.draw(surface)

    for field in aoe_fields:
        field.draw(surface)

    if boss:
        boss.draw(surface)

    if boss_spawned and boss:
        boss.draw(surface)


    # bullets
    for b in enemy_bullets:
        b.draw(surface)
    for b in player_bullets:
        b.draw(surface)

    for b in boss_bullets:
        b.draw(surface)

    for laser in lasers:
        laser.draw(surface)

    # player
    surface.blit(player.image, (player.rect.x, player.rect.y - camera_y))

    # UI
    draw_text(surface, f"HP: {player.hp}", 12, 10)
    draw_text(surface, f"Enemies: {len(enemies)}/{MAX_ENEMIES}", 12, 34)
    draw_text(surface, "Move: Arrow keys | Shoot: SPACE (aim with mouse) | Grid: G", 12, 58, size=22)
    draw_text(surface,f"Presents: {present_count}",12,82)
    elapsed=(pygame.time.get_ticks()-game_start_ticks)//1000
    draw_text(surface,f"Time: {elapsed}s",12,SCREEN_SIZE[1]-40)
    if DEBUG_CAMERA:
        draw_text(surface, "DEBUG MODE (F1)  |  Teleport: F2  |  PgUp/PgDn move camera", 12, 130, size=22)


    # Fade text
    if fade_text:
        t=pygame.time.get_ticks()-fade_text_start
        if t<FADE_DURATION:
            alpha=255-int((t/FADE_DURATION)*255)
            font=pygame.font.SysFont(None,40)
            img=font.render(fade_text,True,(255,220,0))
            img.set_alpha(alpha)
            surface.blit(img,img.get_rect(center=(SCREEN_SIZE[0]//2,80)))

    # ---- POWER-UP TIMERS ----
    now = pygame.time.get_ticks()
    y = 110

    if player.damage > player.base_damage:
        secs = remaining_ms(player.damage_boost_end) // 1000 + 1
        draw_text(surface, f"Damage Boost: {secs}s", 12, y)
        y += 24

    if player.size_boost_end > 0:
        secs = remaining_ms(player.size_boost_end) // 1000 + 1
        draw_text(surface, f"Smaller: {secs}s", 12, y)

    flip()

def check_ceiling_crush():
    """
    If player is at the bottom of the screen and hits a wall above, you die.
    """
    player_screen_rect = player.rect.move(0, -camera_y)

    # Only trigger if player is at the bottom of the screen
    if player_screen_rect.bottom >= SCREEN_SIZE[1]:
        for wall in walls:
            wall_screen_rect = wall.move(0, -camera_y)
            # Horizontal overlap
            if player_screen_rect.right > wall_screen_rect.left and player_screen_rect.left < wall_screen_rect.right:
                # Wall is above the player top and overlapping
                if wall_screen_rect.bottom > player_screen_rect.top and wall_screen_rect.top < player_screen_rect.top:
                    print("Player crushed! Game over!")
                    player.hp = 0
                    break

def despawn_present_if_offscreen():
    global present_rect
    if not present_rect:
        return

    screen_y = present_rect.y - camera_y
    if screen_y > SCREEN_SIZE[1]:
        present_rect = None


# =====================
# MAP TILE DRAWING
# =====================

def draw_walkable_tiles(surf):
    start_row = int(camera_y // TILE_SIZE)
    end_row = int((camera_y + SCREEN_SIZE[1]) // TILE_SIZE) + 1
    start_row = max(0, start_row)
    end_row = min(map_height_tiles, end_row)

    for row_i in range(start_row, end_row):
        y = row_i * TILE_SIZE - camera_y
        row = LEVEL_MAP[row_i]
        for col_i, ch in enumerate(row):
            if ch in SOLID_TILES:
                # Special case: flame tiles are walkable (and should look like cracked ice) when OFF
                if ch == "F" and not flame_is_on(row_i, col_i):
                    surf.blit(cracked_tile, (col_i * TILE_SIZE, y))  # <-- ONLY CHANGE HERE
                continue

            img = TILE_TEXTURES.get(ch)
            if img:
                surf.blit(img, (col_i * TILE_SIZE, y))


# =====================
# MENU / SETTINGS RENDER
# =====================
def render_menu():
    surface.fill((20, 20, 30))
    font = pygame.font.SysFont(None, 72)
    title_img = font.render("Pygame Shooter", True, (255, 255, 255))
    surface.blit(title_img, title_img.get_rect(center=(SCREEN_SIZE[0]//2, 150)))
    start_button.draw(surface)
    settings_button.draw(surface)
    flip()

def render_pause():
    surface.fill((20, 20, 30))
    font = pygame.font.SysFont(None, 72)
    title_img = font.render("PAUSE", True, (255, 255, 255))
    surface.blit(title_img, title_img.get_rect(center=(SCREEN_SIZE[0]//2, 150)))
    resume_button.draw(surface)
    settings_button.draw(surface)
    restart_button.draw(surface)

    flip()

def render_settings():
    surface.fill((30, 20, 20))
    font = pygame.font.SysFont(None, 64)
    title_img = font.render("Settings", True, (255, 255, 255))
    surface.blit(title_img, title_img.get_rect(center=(SCREEN_SIZE[0]//2, 150)))

    toggle_keys_button.text = "Keys: ZQSD" if USE_ZQSD else "Keys: WASD"
    toggle_keys_button.draw(surface)
    back_button.draw(surface)
    flip()

def render_game_over():
    surface.fill((10, 0, 0))

    font_big = pygame.font.SysFont(None, 96)
    font_small = pygame.font.SysFont(None, 36)

    title = font_big.render("GAME OVER", True, (255, 60, 60))
    surface.blit(title, title.get_rect(center=(SCREEN_SIZE[0]//2, 180)))

    try_again_button.draw(surface)
    back_to_menu_button.draw(surface)

    flip()

def render_win():
    surface.fill((0, 50, 0))
    font_big = pygame.font.SysFont(None, 96)
    font_small = pygame.font.SysFont(None, 36)

    title = font_big.render("YOU WIN!", True, (255, 255, 100))
    surface.blit(title, title.get_rect(center=(SCREEN_SIZE[0]//2, 180)))

    # Show present count
    present_text = font_small.render(f"Presents Collected: {present_count}", True, (255, 255, 255))
    surface.blit(present_text, present_text.get_rect(center=(SCREEN_SIZE[0]//2, 260)))

    win_play_again_button.draw(surface)
    win_back_to_menu_button.draw(surface)
    flip()

def spawn_horizontal_laser():
    if boss_spawned:
        return

    # Spawn inside camera view
    y_min = int(camera_y)
    y_max = int(camera_y + SCREEN_SIZE[1] - LASER_HEIGHT)

    if y_max <= y_min:
        return

    # base laser
    y = random.randint(y_min, y_max)
    lasers.append(HorizontalLaser(y))

    # ---- SOMETIMES SPAWN A SECOND LASER ----
    if random.random() < 0.35:  # 35% chance
        direction = random.choice([-1, 1])
        y2 = y + direction * int(TILE_SIZE * 2.5)

        # keep inside screen
        if y_min <= y2 <= y_max:
            lasers.append(HorizontalLaser(y2))

def check_boss_spawn():
    global boss, boss_spawned, stop_enemy_spawning, pending_aoe_spawns

    if boss_spawned:
        return

    if camera_y <= 0:
        stop_enemy_spawning = True

    if stop_enemy_spawning and len(enemies) == 0:
        boss_spawned = True
        boss_width_px = TILE_SIZE * BOSS_WIDTH_TILES
        boss_height_px = TILE_SIZE * BOSS_HEIGHT_TILES

        boss_x = (WORLD_WIDTH // 2) - (boss_width_px // 2)
        boss_y = (6 * TILE_SIZE) - (boss_height_px // 2)   # center vertically on tile 6
        boss = Boss(boss_x, boss_y)
        show_fade_text("⚠ BOSS APPROACHING ⚠")

        # Schedule 3 AoE fields with small delay (e.g., 0.5s apart)
        now = pygame.time.get_ticks()
        for i in range(3):
            offset_x = random.randint(-TILE_SIZE*2, TILE_SIZE*2)
            offset_y = random.randint(-TILE_SIZE*1, TILE_SIZE*3)
            field_x = boss.rect.centerx + offset_x
            field_y = boss.rect.centery + offset_y
            spawn_time = now + i * 500  # 0ms, 500ms, 1000ms
            pending_aoe_spawns.append((spawn_time, field_x, field_y))


def handle_enemy_spawning():
    global last_enemy_spawn_time

    now = pygame.time.get_ticks()
    
    # Only spawn if max enemies not reached and timer elapsed
    if len(enemies) < MAX_ENEMIES and now - last_enemy_spawn_time >= SPAWN_INTERVAL_MS:
        if not stop_enemy_spawning and len(enemies) < MAX_ENEMIES:
                    spawn_enemy(enemies)
        
                    last_enemy_spawn_time = now


# =====================
# MODIFIED MAIN LOOP
# =====================
def main():
    global SHOW_GRID, game_over, death_stats, USE_ZQSD, game_state, DEBUG_CAMERA, camera_y


    enemies_killed = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

                # --- shoot on left click ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 1 = left mouse button
                    player_shoot(player_bullets)
             
            # Menu events
            if game_state == "menu":
                if start_button.is_clicked(event):
                    game_state = "playing"
                if settings_button.is_clicked(event):
                    previous_state = game_state
                    game_state = "settings"
                    

            elif game_state == "settings":
                if back_button.is_clicked(event):
                    game_state = previous_state
                if toggle_keys_button.is_clicked(event):
                    USE_ZQSD = not USE_ZQSD
            
            elif game_state == "pause":
                if resume_button.is_clicked(event):
                    game_state = "playing"
                if settings_button.is_clicked(event):
                    previous_state = game_state
                    game_state = "settings"
                if restart_button.is_clicked(event):
                    reset_game()
                    game_state = "playing"

            elif game_state == "game_over":
                if try_again_button.is_clicked(event):
                    reset_game()
                    game_state = "playing"

                if back_to_menu_button.is_clicked(event):
                    reset_game()
                    game_state = "menu"      

            elif game_state == "win":
                if win_play_again_button.is_clicked(event):
                    reset_game()
                    game_state = "playing"
                if win_back_to_menu_button.is_clicked(event):
                    reset_game()
                    game_state = "menu"

            # Playing events
            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        SHOW_GRID = not SHOW_GRID
                    # if event.key == pygame.K_SPACE:
                    #     player_shoot(player_bullets)
                    if event.key == pygame.K_ESCAPE:
                        game_state = "pause"
                    #debug camera feature
                    if event.key == pygame.K_F1:
                        DEBUG_CAMERA = not DEBUG_CAMERA
                    if DEBUG_CAMERA:
                        if event.key == pygame.K_PAGEUP:
                            camera_y -= DEBUG_CAMERA_STEP
                        if event.key == pygame.K_PAGEDOWN:
                            camera_y += DEBUG_CAMERA_STEP
                        if event.key == pygame.K_HOME:
                            camera_y = 0
                        if event.key == pygame.K_END:
                            camera_y = WORLD_HEIGHT - SCREEN_SIZE[1]

                        camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_SIZE[1]))
                        if DEBUG_CAMERA and event.key == pygame.K_F2:
                            spot = find_debug_final_room_spot()
                            if spot:
                                player.rect.center = spot

                                # move camera so player is visible (roughly centered)
                                camera_y = player.rect.centery - SCREEN_SIZE[1] // 2
                                camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_SIZE[1]))




                # Only spawn enemies if allowed
                

                if event.type == PRESENT_EVENT:
                    spawn_present()

                if event.type == LASER_EVENT:
                    spawn_horizontal_laser()

                    # randomize next spawn
                    pygame.time.set_timer(
                        LASER_EVENT,
                        random.randint(10000, 20000)
    )

        # Update & render depending on state
        if game_state == "menu":
            render_menu()

        elif game_state == "settings":
            render_settings()

        elif game_state == "pause":
            render_pause()

        elif game_state == "playing":
            build_walls()
            handle_player_movement()
            update_camera()
            check_boss_spawn()
            update_background()
            update_all()
            check_present_pickup()
            despawn_present_if_offscreen()
            render()
            check_ceiling_crush()
            if player.hp <= 0:
                game_state = "game_over"

        elif game_state == "game_over":
            render_game_over()

        elif game_state == "win":
            render_win()

        clock.tick(60)

main()