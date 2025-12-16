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

BG_SCALE = 1.5

USE_ZQSD = True  # False = WASD, True = ZQSD

SCREEN_SIZE = (1024, 768)
TILE_SIZE = 64  
player_speed = 5

scroll_speed = 0.7
SHOW_GRID = False

# ENEMIES
MAX_ENEMIES = 5
ENEMY_SIZE = 44
ENEMY_SPEED = 2.2
ENEMY_WANDER_JITTER = 0.35
ENEMY_SHOOT_COOLDOWN_MS = 900
SPAWN_INTERVAL_MS = 1200

# BULLETS
BULLET_SPEED = 3
BULLET_LIFETIME_MS = 2600
PLAYER_SHOOT_COOLDOWN_MS = 250

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
#..............#d
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
background_img = pygame.image.load("IMAGES/bkg1.png").convert()
background_img2 = pygame.image.load("IMAGES/bkg2.png").convert()

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




present_img = pygame.image.load("images/present1.png").convert_alpha()
present_img = pygame.transform.scale(present_img, (PRESENT_SIZE, PRESENT_SIZE))


# =====================
# TILE TEXTURES (MAP LETTERS)
# =====================

# Walkable tiles
empty_tile  = pygame.image.load("images/EMPTY.png").convert_alpha()


# Solid wall tiles
tile_cliff_corner_RO = pygame.image.load("images/CLIFF_RO.png").convert_alpha()

# scale all to tile size
tile_cliff_corner_RO = pygame.transform.scale(tile_cliff_corner_RO, (TILE_SIZE, TILE_SIZE))
empty_tile = pygame.transform.scale(empty_tile, (TILE_SIZE, TILE_SIZE))



# Which map chars are SOLID (collision)
SOLID_TILES = {"#"}   # add/remove letters freely

# Which texture to draw for each map char
TILE_TEXTURES = {
    ".": empty_tile,        # walkable

    "#": tile_cliff_corner_RO, # solid
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
# WALLS
# =====================
def build_walls():
    walls.clear()
    for row_i, row in enumerate(LEVEL_MAP):
        for col_i, tile in enumerate(row):
            if tile in SOLID_TILES:
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


# =====================
# PLAYER
# =====================
class Player:
    def __init__(self):
        self.rect = player_img.get_rect()
        self.rect.topleft = (200, WORLD_HEIGHT - TILE_SIZE * 2)
        self.hp = 500
        self.last_shot = 0

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
        y_min = 0
        y_max = int(camera_y + SCREEN_SIZE[1] - PRESENT_SIZE)

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
     


    # cleanup bullets
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    player_bullets[:] = [b for b in player_bullets if b.alive]

        
    # player bullets -> enemies
    for b in player_bullets:
        if not b.alive:
            continue
        for e in enemies:
            if e.dead:
                continue
            if b.rect.colliderect(e.rect):
                b.alive = False
                e.hp -= 1

                if e.hp <= 0:
                    e.dead = True
                break  # bullet stopt na 1 hit

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
    player.hp = 500
    player.last_shot = 0

    # reset camera/background/timer
    camera_y = max(0, WORLD_HEIGHT - SCREEN_SIZE[1])
    camera_start_y = camera_y
    bg_y = 0.0
    bg_index = 0

    game_start_ticks = pygame.time.get_ticks()
    fade_text = None
    fade_text_start = 0

# =====================
# RENDER
# =====================
def render():
    surface.fill((0, 0, 0))
    img_a = background_imgs[bg_index]
    img_b = background_imgs[(bg_index + 1) % 2]

    surface.blit(img_a, (0, int(bg_y)))
    surface.blit(img_b, (0, int(bg_y) - bg_height))


    # walls
    for w in walls:
        sr = w.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            row_i = w.y // TILE_SIZE
            col_i = w.x // TILE_SIZE
            ch = LEVEL_MAP[row_i][col_i]
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
    draw_text(surface,f"Presents: {present_count}",12,82)
    elapsed=(pygame.time.get_ticks()-game_start_ticks)//1000
    draw_text(surface,f"Time: {elapsed}s",12,SCREEN_SIZE[1]-40)

    # Fade text
    if fade_text:
        t=pygame.time.get_ticks()-fade_text_start
        if t<FADE_DURATION:
            alpha=255-int((t/FADE_DURATION)*255)
            font=pygame.font.SysFont(None,40)
            img=font.render(fade_text,True,(255,220,0))
            img.set_alpha(alpha)
            surface.blit(img,img.get_rect(center=(SCREEN_SIZE[0]//2,80)))



    flip()

def check_ceiling_crush():
    """
    If player is at the bottom of the screen and hits a wall above, you die.
    """
    # Player screen rect
    player_screen_rect = player.rect.move(0, -camera_y)
    
    # Check if player is at bottom of screen
    if player_screen_rect.bottom >= SCREEN_SIZE[1]:
        # Look for walls that overlap player
        for wall in walls:
            wall_screen_rect = wall.move(0, -camera_y)
            if wall_screen_rect.colliderect(player_screen_rect):
                # Optional: only trigger if wall is above player
                if wall_screen_rect.bottom < player_screen_rect.bottom:
                    print("Player crushed! Game over!")
                    player.hp = 0
                    

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
                continue  # walls get drawn via your existing walls loop
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

# =====================
# MODIFIED MAIN LOOP
# =====================
def main():
    global SHOW_GRID, game_over, death_stats, USE_ZQSD, game_state

    enemies_killed = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            
             
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

            # Playing events
            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        SHOW_GRID = not SHOW_GRID
                    if event.key == pygame.K_SPACE:
                        player_shoot(player_bullets)
                    if event.key == pygame.K_ESCAPE:
                        game_state = "pause"


                if event.type == SPAWN_EVENT:
                    if len(enemies) < MAX_ENEMIES:
                        spawn_enemy(enemies)

                if event.type == PRESENT_EVENT:
                    spawn_present()

        # Update & render depending on state
        if game_state == "menu":
            render_menu()

        elif game_state == "settings":
            render_settings()

        elif game_state == "pause":
            render_pause()

        elif game_state == "playing":
            handle_player_movement()
            update_camera()
            update_background()
            update_all()
            check_present_pickup()
            despawn_present_if_offscreen()
            render()
            if player.hp <= 0:
                game_state = "game_over"

        elif game_state == "game_over":
            render_game_over()

        clock.tick(60)

main()
