import pygame
from pygame.display import flip
from sys import exit
import os
import random
import math

#todo
#laser moet 1 dmg doen idp van oneshot



pygame.init()
os.chdir(os.path.dirname(__file__))
pygame.mixer.init()
pygame.mixer.music.load("sounds/background_music.ogg")
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)
snowball_hit_sound = pygame.mixer.Sound("sounds/snowball_hit.wav")
snowball_hit_sound.set_volume(1) 
snowball_shoot_sound = pygame.mixer.Sound("sounds/SNOWBALLCANNON.wav")
snowball_shoot_sound.set_volume(1)



clock = pygame.time.Clock()

prev_ticks = pygame.time.get_ticks()


# =====================
# SETTINGS
# =====================




DIFFICULTIES = {
    "EASY": {
        "enemy_count": 3,
        "player_hp": 75,
        "enemy_spawn": 4000,
        "heal": 25,
        "boss_hp": 50,
        "laser_damage" : 10,
    },
    "NORMAL": {
        "enemy_count": 5,
        "player_hp": 50,
        "enemy_spawn": 2000,
        "heal": 10,
        "boss_hp": 50,
        "laser_damage" : 15,
    },
    "HARD": {
        "enemy_count": 10,
        "player_hp": 20,
        "enemy_spawn": 1000,
        "heal": 5,
        "boss_hp": 100,
        "laser_damage" : 20,
    }
}

#tut ui
TUT_SCALE = 1.0       # grootte (1.0 = origineel)
TUT_CENTER_X = 0        # horizontale offset vanaf scherm-midden
TUT_CENTER_Y = 0      # verticale offset vanaf scherm-midden
TUT_SMOOTH = False       # smoothscale of normale scale

TITLE_X = 0          # horizontal offset from screen center
TITLE_Y = 0         # y position (pixels from top)

BUTTON_SIZE = (260, 56)
BUTTON_SPACING = 90



difficulty_names = list(DIFFICULTIES.keys())
current_difficulty_index = 1  # NORMAL
current_difficulty = difficulty_names[current_difficulty_index]

SHAKE_TIME_MS = 150
SHAKE_STRENGTH = 6  # pixels

shake_end_time = 0


FLAME_CYCLE_MS = 5000
FLAME_ON_MS = 800


DEBUG_CAMERA = False
DEBUG_CAMERA_STEP = 80   # how many pixels per tap (change if you want faster/slower)


BG_SCALE = 1.5

USE_ZQSD = True  # False = WASD, True = ZQSD

SCREEN_SIZE = (1024, 768)
TILE_SIZE = 64  

DASH_AFTERIMAGE_EVERY_MS = 18
DASH_AFTERIMAGE_LIFE_MS = 140  # how long each ghost lasts
ICE_ACCEL = 0.4      # how fast you accelerate
ICE_FRICTION = 0.96  # closer to 1 = more sliding
ICE_MAX_SPEED = 5.0

scroll_speed = 0.7
SHOW_GRID = False

BOSS_BULLET_SPEED = 3
BOSS_BULLET_SPEED_PHASE_2 = 5
BOSS_SHOOT_INTERVAL_MS = 500  # shoot every half second
BOSS_BULLET_LINES = 6
BOSS_BULLET_LINES_PHASE_2 = 9
BOSS_BULLET_ROT_SPEED = 10  # degrees per update
boss_spawned = False
boss = None

# ENEMIES
MAX_ENEMIES = DIFFICULTIES[current_difficulty]["enemy_count"]
ENEMY_SIZE = 64 
ENEMY_SPEED = 2.2
ENEMY_WANDER_JITTER = 0.35
ENEMY_SHOOT_COOLDOWN_MS = 900
SPAWN_INTERVAL_MS = DIFFICULTIES[current_difficulty]["enemy_spawn"]
last_enemy_spawn_time = 0

# BULLETS
BULLET_SPEED = 4
BULLET_LIFETIME_MS = 3500
PLAYER_SHOOT_COOLDOWN_MS = 250

#LASER
LASER_WARNING_MS = 1200
LASER_ACTIVE_MS = 1500
LASER_DAMAGE = DIFFICULTIES[current_difficulty]["laser_damage"]

LASER_HEIGHT = TILE_SIZE

BOSS_WIDTH_TILES = 4
BOSS_HEIGHT_TILES = 4
boss = None
boss_spawned = False
stop_enemy_spawning = False

# PRESENTS
PRESENT_SIZE = 40
PRESENT_SPAWN_MS = 5000
PRESENT_EVENT = pygame.USEREVENT + 2
pygame.time.set_timer(PRESENT_EVENT, PRESENT_SPAWN_MS)
present_count = 0

# TIMER & FADE TEXT
game_start_ticks = pygame.time.get_ticks()
fade_text = None
fade_text_start = 0
FADE_DURATION = 2000  # ms

LASER_SPAWN_MS = random.randint(10000, 20000)
LASER_EVENT = pygame.USEREVENT + 3
pygame.time.set_timer(LASER_EVENT, LASER_SPAWN_MS)

#ui
last_powerup_name = ""
last_powerup_end_time = 0   # pygame ticks when it should disappear
POWERUP_UI_DURATION_MS = 2500


# --- WALK SWAY (rotate + bob) ---
SWAY_MAX_DEG = 6.0       # max rotation angle at full walk speed
BOB_MAX_Y = 4.0          # max vertical bob (pixels) at full walk speed
SWAY_FREQ_BASE = 7.5     # cycles/sec at full walk speed (tweak)

# --- ENEMY SWAY (subtle) ---
ENEMY_SWAY_MAX_DEG = SWAY_MAX_DEG * 0.5
ENEMY_BOB_MAX_Y    = BOB_MAX_Y * 0.5
ENEMY_SWAY_FREQ    = SWAY_FREQ_BASE * 0.7   # slightly slower than player

# =====================
# SNOW (VISUAL)
# =====================
SNOW_ENABLED = True
SNOW_MAX_FLAKES = 180
SNOW_SPAWN_PER_FRAME = 3     # how many new flakes per frame (cap by MAX)
SNOW_FALL_MIN = 0.8
SNOW_FALL_MAX = 2.4
SNOW_DRIFT = 0.6             # sideways drift strength
snowflakes = []



# =====================
# LEVEL
# =====================
with open("images/map.txt", "r", encoding="utf-8") as file:
    LEVEL_TEXT = file.read()

LEVEL_MAP = [row for row in LEVEL_TEXT.strip().splitlines()]
walls = []
walls_player = []
walls_bullets = []

# =====================
# SCREEN
# =====================
surface = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Pygame Shooter")

# =====================
# MENU IMAGES (PNG)
# =====================
menu_bg_img = pygame.image.load("images/BACKGROUND.png").convert()          # achtergrond (geen alpha nodig)
menu_title_img = pygame.image.load("images/TITLE.png").convert_alpha()     # title png (met transparantie)
menu_controls_img = pygame.image.load("images/TUT_UI.png").convert_alpha()  # controls/explanation png

# achtergrond altijd exact naar scherm schalen
menu_bg_img = pygame.transform.smoothscale(menu_bg_img, SCREEN_SIZE)

# OPTIONAL: title/controls schalen (als ze te groot zijn)
TITLE_SCALE = 1.2
CONTROLS_SCALE = 1.0

menu_title_img = pygame.transform.smoothscale(
    menu_title_img,
    (int(menu_title_img.get_width() * TITLE_SCALE),
     int(menu_title_img.get_height() * TITLE_SCALE))
)

menu_controls_img = pygame.transform.smoothscale(
    menu_controls_img,
    (int(menu_controls_img.get_width() * CONTROLS_SCALE),
     int(menu_controls_img.get_height() * CONTROLS_SCALE))
)


enemy_hit_img = pygame.image.load("images/ENEMY_HIT.png").convert_alpha()
enemy_hit_img = pygame.transform.scale(enemy_hit_img, (ENEMY_SIZE, ENEMY_SIZE))



enemy_img = pygame.image.load("images/ENEMY.png").convert_alpha()
enemy_img = pygame.transform.scale(enemy_img, (ENEMY_SIZE, ENEMY_SIZE))

player_img = pygame.image.load("images/kerstman-def.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (55, 55))
player_img_base = player_img.copy()
# player_img_shd = pygame.image.load("images/Kerstmanshad.png").convert_alpha()
# player_img_shd = pygame.transform.scale(player_img, (55, 55))
# player_img_shd_base = player_img_shd.copy()

player_bullet_img_base = pygame.image.load("images/SNOWBALL.png").convert_alpha()
enemy_bullet_img_base = pygame.image.load("images/ENEMYBULLET.png").convert_alpha()
player_bullet_img_base = pygame.transform.scale(player_bullet_img_base, (25,25))
enemy_bullet_img_base = pygame.transform.scale(enemy_bullet_img_base, (25,25))
background_img = pygame.image.load("IMAGES/bkg1.png").convert()
background_img2 = pygame.image.load("IMAGES/bkg2.png").convert()

# LASER IMAGES (replace later with PNGs)
# laser_warning_img = pygame.Surface(((SCREEN_SIZE[0]), LASER_HEIGHT), pygame.SRCALPHA)
# laser_warning_img.fill((255, 50, 50, 120))  # semi-transparent red
laser_warning_img = pygame.image.load("images/laser_warning.png").convert_alpha()

# laser_active_img = pygame.Surface(((SCREEN_SIZE[0]), LASER_HEIGHT), pygame.SRCALPHA)
# laser_active_img.fill((255, 0, 0))  # solid red
laser_active_img = pygame.image.load("images/laser_active.png").convert_alpha()

laser_warning_img = pygame.transform.smoothscale(
    laser_warning_img,
    (SCREEN_SIZE[0], LASER_HEIGHT)
)

laser_active_img = pygame.transform.smoothscale(
    laser_active_img,
    (SCREEN_SIZE[0], LASER_HEIGHT)
)

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

# --- POWERUP ICONS (top-right HUD) ---
powerup_heal_icon   = pygame.image.load("images/powerup_heal.png").convert_alpha()
powerup_damage_icon = pygame.image.load("images/powerup_damage.png").convert_alpha()
powerup_small_icon  = pygame.image.load("images/powerup_small.png").convert_alpha()
powerup_shotgun_icon = pygame.image.load("images/shotgun_power_up.png").convert_alpha()

POWERUP_ICON_SIZE = 48
powerup_heal_icon   = pygame.transform.smoothscale(powerup_heal_icon,   (POWERUP_ICON_SIZE, POWERUP_ICON_SIZE))
powerup_damage_icon = pygame.transform.smoothscale(powerup_damage_icon, (POWERUP_ICON_SIZE, POWERUP_ICON_SIZE))
powerup_small_icon  = pygame.transform.smoothscale(powerup_small_icon,  (POWERUP_ICON_SIZE, POWERUP_ICON_SIZE))
powerup_shotgun_icon = pygame.transform.smoothscale(powerup_shotgun_icon,(POWERUP_ICON_SIZE,POWERUP_ICON_SIZE))

POWERUP_ICONS = {
    "Heal": powerup_heal_icon,
    "Damage": powerup_damage_icon,
    "Smaller": powerup_small_icon,
    "Shotgun" : powerup_shotgun_icon,
}

last_powerup_icon = None

boss_hp_decor = pygame.image.load(
    "images/BOSS_HP_BAR_1.png"
).convert_alpha()

# scale it to fit your bar nicely
boss_hp_decor = pygame.transform.smoothscale(boss_hp_decor, (700, 146))




# =====================
# TILE TEXTURES (MAP LETTERS)
# =====================

# Walkable tiles
empty_tile  = pygame.image.load("images/ICE.png").convert_alpha()
cracked_tile = pygame.image.load("images/CRACKED_ICE.png").convert_alpha()
empty_tile_barrel = pygame.image.load("images/ICE_1.png").convert_alpha()
empty_tile_bodie = pygame.image.load("images/ICE_BODIE.png").convert_alpha()
empty_tile_S_U = pygame.image.load("images/ICE_SHADOW_U.png").convert_alpha() 
empty_tile_S_C1 = pygame.image.load("images/ICE_SHADOW_CORNER_1.png").convert_alpha() 
empty_tile_S_C2 = pygame.image.load("images/ICE_SHADOW_CORNER_2.png").convert_alpha() 
empty_tile_S_L = pygame.image.load("images/ICE_shadow_L.png").convert_alpha() 
empty_tile_S_F = pygame.image.load("images/ICE_SHADOW_FULL.png").convert_alpha() 

empty_tile   = pygame.transform.scale(empty_tile, (TILE_SIZE, TILE_SIZE))
cracked_tile = pygame.transform.scale(cracked_tile, (TILE_SIZE, TILE_SIZE))
empty_tile_barrel = pygame.transform.scale(empty_tile_barrel, (TILE_SIZE, TILE_SIZE))
empty_tile_bodie = pygame.transform.scale(empty_tile_bodie, (TILE_SIZE, TILE_SIZE))
empty_tile_S_U  = pygame.transform.scale(empty_tile_S_U, (TILE_SIZE, TILE_SIZE))
empty_tile_S_C1 = pygame.transform.scale(empty_tile_S_C1, (TILE_SIZE, TILE_SIZE))
empty_tile_S_C2 = pygame.transform.scale(empty_tile_S_C2, (TILE_SIZE, TILE_SIZE))
empty_tile_S_L  = pygame.transform.scale(empty_tile_S_L, (TILE_SIZE, TILE_SIZE))
empty_tile_S_F  = pygame.transform.scale(empty_tile_S_F, (TILE_SIZE, TILE_SIZE))
# Solid wall tiles
tile_cliff = pygame.image.load("images/WHITE.png").convert_alpha()

#water
water = pygame.image.load("images/FLAME.png").convert_alpha()
water = pygame.transform.scale(water, (TILE_SIZE, TILE_SIZE))
water_S_C1  = pygame.image.load("images/WATER_SHADOW5_CORNER_1.png").convert_alpha()
water_S_C1 = pygame.transform.scale(water_S_C1, (TILE_SIZE, TILE_SIZE))
water_S_C2  = pygame.image.load("images/WATER_SHADOW5_CORNER_2.png").convert_alpha()
water_S_C2 = pygame.transform.scale(water_S_C2, (TILE_SIZE, TILE_SIZE))
water_S_B  = pygame.image.load("images/WATER_SHADOW_B.png").convert_alpha()
water_S_B = pygame.transform.scale(water_S_B, (TILE_SIZE, TILE_SIZE))
water_S_L  = pygame.image.load("images/WATER_SHADOW_L.png").convert_alpha()
water_S_L = pygame.transform.scale(water_S_L, (TILE_SIZE, TILE_SIZE))
water_S_F = pygame.image.load("images/WATER_SHADOW_L.png").convert_alpha()
water_S_F = pygame.transform.scale(water_S_F, (TILE_SIZE, TILE_SIZE))

#hazards
flame_tile = pygame.image.load("images/FLAME.png").convert_alpha()


#hazards
flame_tile = pygame.transform.scale(flame_tile, (TILE_SIZE, TILE_SIZE))



#standart cliff tiles
tile_cliff_L = pygame.image.load("images/CLIFF_L.png").convert_alpha()
tile_cliff_T = pygame.image.load("images/CLIFF_T.png").convert_alpha()
tile_cliff_R = pygame.image.load("images/CLIFF_R.png").convert_alpha()
tile_cliff_B = pygame.image.load("images/CLIFF_B.png").convert_alpha()
tile_cliff_W_L = pygame.image.load("images/CLIFF_W.png").convert_alpha()

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

#decoration tiles

tile_cliff_R_3T = pygame.image.load("images/CLIFF_R_3BOOM.png").convert_alpha()
tile_cliff_L_3T = pygame.image.load("images/CLIFF_L_3BOOM.png").convert_alpha()
tile_cliff_B_3R = pygame.image.load("images/CLIFF_B_3ROCKS.png").convert_alpha()
tile_cliff_T_3R = pygame.image.load("images/CLIFF_T_3ROCKS.png").convert_alpha()
tile_cliff_B_2S = pygame.image.load("images/CLIFF_B_2SHRUBS.png").convert_alpha()
tile_cliff_T_2S = pygame.image.load("images/CLIFF_T_2SHRUBS.png").convert_alpha()
tile_cliff_R_2S = pygame.image.load("images/CLIFF_R_2SHRUBS.png").convert_alpha()
tile_cliff_L_2S = pygame.image.load("images/CLIFF_L_2SHRUBS.png").convert_alpha()




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
tile_cliff_W_L = pygame.transform.scale(tile_cliff_W_L, (TILE_SIZE, TILE_SIZE))
tile_cliff_R_3T = pygame.transform.scale(tile_cliff_R_3T, (TILE_SIZE, TILE_SIZE))
tile_cliff_L_3T = pygame.transform.scale(tile_cliff_L_3T, (TILE_SIZE, TILE_SIZE))
tile_cliff_B_3R = pygame.transform.scale(tile_cliff_B_3R, (TILE_SIZE, TILE_SIZE))
tile_cliff_T_3R = pygame.transform.scale(tile_cliff_T_3R, (TILE_SIZE, TILE_SIZE))
tile_cliff_B_2S = pygame.transform.scale(tile_cliff_B_2S, (TILE_SIZE, TILE_SIZE))
tile_cliff_T_2S = pygame.transform.scale(tile_cliff_T_2S, (TILE_SIZE, TILE_SIZE))
tile_cliff_R_2S = pygame.transform.scale(tile_cliff_R_2S, (TILE_SIZE, TILE_SIZE))
tile_cliff_L_2S = pygame.transform.scale(tile_cliff_L_2S, (TILE_SIZE, TILE_SIZE))

# Which map chars are SOLID (collision)
SOLID_TILES = {"#","r","t","l","b","1","2","3","4","5","6","7","8","F","w","W","p","P","n","N","h","H","e","E","F","D","d","X","x"}   # add/remove letters freely

# Which texture to draw for each map char
TILE_TEXTURES = {
    ".": empty_tile,        # walkable
    "u": empty_tile_barrel,
    "B": empty_tile_bodie,

    "#": tile_cliff, # solid
    "r": tile_cliff_L,
    "t": tile_cliff_T,
    "l": tile_cliff_R,
    "b": tile_cliff_B,
    "1": tile_cliff_innercorner_RO,
    "2": tile_cliff_innercorner_LO,
    "3": tile_cliff_innercorner_LB,
    "4": tile_cliff_innercorner_RB,
    "5": tile_cliff_outercorner_LB,
    "6": tile_cliff_outercorner_RB,
    "7": tile_cliff_outercorner_RO,
    "8": tile_cliff_outercorner_LO,
    "w": water,
    "W": tile_cliff_W_L,
    "p": tile_cliff_R_3T,
    "P": tile_cliff_L_3T,
    "n": tile_cliff_B_3R,
    "N": tile_cliff_T_3R,
    "h": tile_cliff_B_2S,
    "H": tile_cliff_T_2S,
    "e": tile_cliff_R_2S,
    "E": tile_cliff_L_2S,
    "s": empty_tile_S_U,
    "S": empty_tile_S_C1,
    "C": empty_tile_S_C2,
    "L": empty_tile_S_L,
    "f": empty_tile_S_F,
    "d": water_S_L,
    "D": water_S_B,
    "x": water_S_C1,
    "X": water_S_C2,
    "O": water_S_F
    

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

def vertical_menu(center_x, start_y, spacing, labels, size=(260, 56)):
    """
    Creates buttons stacked vertically with equal spacing.
    Returns a list of Button objects.
    """
    buttons = []
    y = start_y
    for text in labels:
        buttons.append(Button((center_x, y), text, size=size))
        y += spacing
    return buttons


# --- MENU TITLE SCALING ---
TITLE_SCALE = 0.7   # change this (ex: 0.7 smaller, 1.3 bigger)

menu_title_img_original = menu_title_img.copy()  # keep an unscaled copy

def rescale_title():
    global menu_title_img
    w = int(menu_title_img_original.get_width() * TITLE_SCALE)
    h = int(menu_title_img_original.get_height() * TITLE_SCALE)
    menu_title_img = pygame.transform.smoothscale(menu_title_img_original, (w, h))

rescale_title()

def draw_tut_ui(surf, img):
    w, h = img.get_size()
    w = int(w * TUT_SCALE)
    h = int(h * TUT_SCALE)

    if TUT_SMOOTH:
        img = pygame.transform.smoothscale(img, (w, h))
    else:
        img = pygame.transform.scale(img, (w, h))

    rect = img.get_rect(
        center=(
            surf.get_width() // 2 + TUT_CENTER_X,
            surf.get_height() // 2 + TUT_CENTER_Y
        )
    )

    surf.blit(img, rect)


def set_menu_title_png(path):
    global menu_title_img
    menu_title_img = pygame.image.load(path).convert_alpha()

    # als je dezelfde schaal wil behouden:
    menu_title_img = pygame.transform.smoothscale(
        menu_title_img,
        (int(menu_title_img.get_width() * TITLE_SCALE),
         int(menu_title_img.get_height() * TITLE_SCALE))
    )


class Snowflake:
    def __init__(self, x, y):
        self.x = float(x)          # world x
        self.y = float(y)          # world y
        self.r = random.randint(1, 3)
        self.vy = random.uniform(SNOW_FALL_MIN, SNOW_FALL_MAX)
        self.vx = random.uniform(-SNOW_DRIFT, SNOW_DRIFT)
        self.wobble = random.uniform(0.0, math.tau)
        self.wobble_speed = random.uniform(1.2, 2.8)
        self.alpha = random.randint(120, 220)

    def update(self):
        # gentle side wobble
        self.wobble += self.wobble_speed * 0.03
        self.x += self.vx + math.sin(self.wobble) * 0.25
        self.y += self.vy

def spawn_snow():
    if not SNOW_ENABLED:
        return

    # keep number bounded
    need = SNOW_MAX_FLAKES - len(snowflakes)
    if need <= 0:
        return

    count = min(SNOW_SPAWN_PER_FRAME, need)

    # spawn just above the visible camera area
    top_y = camera_y - 20
    for _ in range(count):
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(int(top_y - 60), int(top_y))
        snowflakes.append(Snowflake(x, y))

def update_snow():
    if not SNOW_ENABLED:
        return

    spawn_snow()

    bottom_y = camera_y + SCREEN_SIZE[1] + 80
    for f in snowflakes:
        f.update()

    # remove flakes that are below view
    snowflakes[:] = [f for f in snowflakes if f.y < bottom_y]

def draw_snow(surf):
    if not SNOW_ENABLED:
        return

    # draw in screen coords (world y - camera_y)
    for f in snowflakes:
        sy = f.y - camera_y
        if sy < -80 or sy > SCREEN_SIZE[1] + 80:
            continue

        # small alpha dot
        dot = pygame.Surface((f.r * 2 + 2, f.r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(dot, (255, 255, 255, f.alpha), (f.r + 1, f.r + 1), f.r)
        surf.blit(dot, (int(f.x) - f.r, int(sy) - f.r))


def draw_minimap_progress(surf):
    # Top-left position + size
    x, y = 12, 12
    w, h = 18, 140
    pad = 3

    # If you start at bottom and scroll camera_y up to 0:
    start = max(1, int(camera_start_y))  # avoid /0
    # progress 0.0 at start (bottom), 1.0 at top
    progress = 1.0 - (camera_y / start)
    progress = max(0.0, min(1.0, progress))

    # background box (semi transparent)
    box = pygame.Surface((w + 2*pad, h + 2*pad), pygame.SRCALPHA)
    pygame.draw.rect(box, (0, 0, 0, 160), box.get_rect(), border_radius=8)
    surf.blit(box, (x - pad, y - pad))

    # track
    pygame.draw.rect(surf, (30, 30, 30), (x, y, w, h), border_radius=6)
    pygame.draw.rect(surf, (255, 255, 255), (x, y, w, h), 2, border_radius=6)

    # marker (player/camera position)
    marker_h = 6
    marker_y = y + int((1.0 - progress) * (h - marker_h))  # top when progress=1
    pygame.draw.rect(surf, (255, 220, 120), (x + 2, marker_y, w - 4, marker_h), border_radius=3)

def draw_dash_cooldown_bar(surf, x, y):
    w, h = 300, 12
    radius = 6
    now = pygame.time.get_ticks()

    if now >= player.next_dash_time:
        ratio = 1.0
    else:
        total = player.dash_cooldown_ms
        remaining = max(0, player.next_dash_time - now)
        ratio = 1.0 - (remaining / max(1, total))

    pygame.draw.rect(surf, (40, 40, 40), (x, y, w, h), border_radius=radius)
    fill_w = int(w * max(0.0, min(1.0, ratio)))
    pygame.draw.rect(surf, (120, 220, 255), (x, y, fill_w, h), border_radius=radius)
    pygame.draw.rect(surf, (255, 255, 255), (x, y, w, h), 2, border_radius=radius)

    # font = pygame.font.SysFont(None, 18)
    # txt = font.render("DASH", True, (0, 0, 0))
    # surf.blit(txt, txt.get_rect(midleft=(x + 8, y + h // 2)))


def draw_player_healthbar(surf, player, x=12, y=120, w=260, h=18):
    # avoid divide-by-zero
    max_hp = max(1, int(player.maxhp))
    hp = max(0, min(int(player.hp), max_hp))
    ratio = hp / max_hp

    # background
    pygame.draw.rect(surf, (40, 40, 40), (x, y, w, h), border_radius=6)
    # fill
    pygame.draw.rect(surf, (60, 220, 80), (x, y, int(w * ratio), h), border_radius=6)
    # outline
    pygame.draw.rect(surf, (255, 255, 255), (x, y, w, h), 2, border_radius=6)

    # text on top
    font = pygame.font.SysFont(None, 22)
    txt = font.render(f"HP: {hp}/{max_hp}", True, (255, 255, 255))
    shadow = font.render(f"HP: {hp}/{max_hp}", True, (0, 0, 0))
    surf.blit(shadow, (x + w//2 - shadow.get_width()//2 + 1,
                    y + h//2 - shadow.get_height()//2 + 1))

    surf.blit(txt, txt.get_rect(center=(x + w // 2, y + h // 2)))



def resolve_player_after_resize():
    # push player out of walls after changing size
    for _ in range(20):  # enough iterations for tight corners
        hit = None
        for w in walls:
            if player.rect.colliderect(w):
                hit = w
                break
        if not hit:
            break

        # minimal push direction (smallest overlap axis)
        dx_left   = hit.right - player.rect.left
        dx_right  = player.rect.right - hit.left
        dy_top    = hit.bottom - player.rect.top
        dy_bottom = player.rect.bottom - hit.top

        min_push = min(dx_left, dx_right, dy_top, dy_bottom)

        if min_push == dx_left:
            player.rect.left = hit.right
        elif min_push == dx_right:
            player.rect.right = hit.left
        elif min_push == dy_top:
            player.rect.top = hit.bottom
        else:
            player.rect.bottom = hit.top

    # clamp inside world (and screen vertical limits)
    player.rect.clamp_ip(WORLD_RECT)
    top_limit = camera_y
    bottom_limit = camera_y + SCREEN_SIZE[1] - player.rect.height
    if player.rect.y < top_limit:
        player.rect.y = top_limit
    elif player.rect.y > bottom_limit:
        player.rect.y = bottom_limit


def update_walk_sway(dt):
    # speed in pixels/frame
    speed = math.hypot(player.vel_x, player.vel_y)

    # normalize against normal walk speed (pixels/frame)
    max_walk_pf = max(1e-6, player.speed)
    t = min(1.0, speed / max_walk_pf)  # 0..1

    # faster movement -> faster sway cycle
    freq = SWAY_FREQ_BASE * t
    player.sway_phase += (2 * math.pi) * freq * dt

    # keep it from growing forever
    if player.sway_phase > 1e6:
        player.sway_phase = 0.0


def draw_debug_overlay(surf):
    if not DEBUG_CAMERA:
        return

    lines = [
        "DEBUG OVERLAY (F1 to toggle)",
        f"camera_y: {camera_y:.1f}",
        f"player world: ({player.rect.centerx}, {player.rect.centery})",
        f"enemies: {len(enemies)}  bullets: e={len(enemy_bullets)} p={len(player_bullets)} b={len(boss_bullets)}",
        "",
        "Controls:",
        "PAGEUP / PAGEDOWN  -> move camera up/down",
        "HOME              -> camera to top",
        "END               -> camera to bottom",
        "G                 -> toggle grid",
        "LSHIFT            -> dash",
        "ESC               -> pause",
    ]

    x, y = 12, 140
    for i, s in enumerate(lines):
        if s == "":
            y += 10
            continue
        draw_text(surf, s, x, y + i * 22, size=20)




def draw_hud(surf):
    global last_powerup_icon

    BOX_SIZE = 70
    PAD = 12
    RADIUS = 10  # how round the corners are

    x = SCREEN_SIZE[0] - BOX_SIZE - PAD
    y = PAD

    # --- draw rounded background directly ---
    bg_rect = pygame.Rect(x, y, BOX_SIZE, BOX_SIZE)

    # semi-transparent rounded background
    bg = pygame.Surface((BOX_SIZE, BOX_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(
        bg,
        (0, 0, 0, 160),          # transparent dark
        bg.get_rect(),
        border_radius=RADIUS
    )
    surf.blit(bg, (x, y))

    # border
    pygame.draw.rect(
        surf,
        (255, 255, 255),
        bg_rect,
        2,
        border_radius=RADIUS
    )

    # --- draw powerup icon if present ---
    if last_powerup_icon:
        icon_rect = last_powerup_icon.get_rect(
            center=bg_rect.center
        )
        surf.blit(last_powerup_icon, icon_rect)
    





def start_dash():
    now = pygame.time.get_ticks()
    cx, cy = player.rect.center
    effects.append(ShootRing(cx, cy))

    if now < player.next_dash_time:
        return
    if player.is_dashing:
        return

    # Movement keys
    keys = pygame.key.get_pressed()
    if USE_ZQSD:
        left_key, right_key, up_key, down_key = pygame.K_q, pygame.K_d, pygame.K_z, pygame.K_s
    else:
        left_key, right_key, up_key, down_key = pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s

    # Compute movement vector
    dx = keys[right_key] - keys[left_key]
    dy = keys[down_key] - keys[up_key]

    # If no movement input, dash in last movement direction, or default to right
    if dx == 0 and dy == 0:
        dx, dy = player.vx, player.vy  # keep current velocity as dash direction
        if dx == 0 and dy == 0:
            dx, dy = 1, 0  # default dash to the right

    # Normalize
    nx, ny = normalize(dx, dy)

    # Start dash
    player.is_dashing = True
    player.dash_end_time = now + player.dash_ms
    player.next_dash_time = now + player.dash_ms + player.dash_cooldown_ms
    player.dash_vx = nx * player.dash_speed
    player.dash_vy = ny * player.dash_speed

    start_dash.last_ghost = 0


def spawn_shot_feedback(sx, sy, nx, ny):
    # spawn slightly in front of player (towards aim direction)
    fx = sx + nx * 18
    fy = sy + ny * 18

    effects.append(MuzzleFlash(fx, fy))
    effects.append(ShootRing(fx, fy))

    # sparks fly mostly forward
    for _ in range(6):
        jitter = random.uniform(-0.6, 0.6)
        vx = (nx * 6 + jitter) * random.uniform(0.7, 1.2)
        vy = (ny * 6 + jitter) * random.uniform(0.7, 1.2)
        effects.append(ShotSpark(fx, fy, vx, vy))


def enemy_death_explosion(enemy):
    # small visual pop
    effects.append(
        Explosion(
            enemy.rect.centerx,
            enemy.rect.centery,
            duration_ms=220,
            max_radius=22
        )
    )


def draw_boss_healthbar(surf, boss):
    if not boss:
        return

    decor = boss_hp_decor

    # slot position INSIDE the decor image (measured in the PNG)
    SLOT_LEFT   = 43
    SLOT_TOP    = 50
    SLOT_WIDTH  = 594
    SLOT_HEIGHT = 33

    # ---- place the DECOR image centered on screen ----
    OFFSET_X = 30   # right (+) / left (-)
    OFFSET_Y = -30   # down (+) / up (-)

    decor_x = (SCREEN_SIZE[0] - decor.get_width()) // 2 + OFFSET_X
    decor_y = 20 + OFFSET_Y


    # now the real slot position in screen coords
    slot_x = decor_x + SLOT_LEFT
    slot_y = decor_y + SLOT_TOP

    # ---- draw hp fill inside the slot ----
    max_hp = max(1, int(boss.max_hp))
    hp = max(0, int(boss.hp))
    ratio = hp / max_hp

    pygame.draw.rect(surf, (40, 40, 40),
                     (slot_x, slot_y, SLOT_WIDTH, SLOT_HEIGHT),
                     border_radius=8)

    pygame.draw.rect(surf, (200, 40, 40),
                     (slot_x, slot_y, int(SLOT_WIDTH * ratio), SLOT_HEIGHT),
                     border_radius=8)

    # draw the decor on top (so borders cover the fill nicely)
    surf.blit(decor, (decor_x, decor_y))

    # ---- number centered in the MIDDLE block (slot center) ----
    # font = pygame.font.SysFont(None, 26)
    # hp_text = font.render(f"{hp}", True, (255, 255, 255))

    # center_x = slot_x + SLOT_WIDTH // 2
    # center_y = slot_y + SLOT_HEIGHT // 2

    # surf.blit(hp_text, hp_text.get_rect(center=(center_x, center_y)))







def enemy_on_active_flame(enemy_rect):
    # Check which tiles the enemy overlaps
    left = enemy_rect.left // TILE_SIZE
    right = enemy_rect.right // TILE_SIZE
    top = enemy_rect.top // TILE_SIZE
    bottom = enemy_rect.bottom // TILE_SIZE

    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if 0 <= row < map_height_tiles and 0 <= col < map_width_tiles:
                if LEVEL_MAP[row][col] == "F" and flame_is_on(row, col):
                    return True
    return False

def trigger_screenshake(duration_ms=SHAKE_TIME_MS, strength=SHAKE_STRENGTH):
    global shake_end_time, SHAKE_STRENGTH
    SHAKE_STRENGTH = strength
    shake_end_time = pygame.time.get_ticks() + duration_ms

def get_shake_offset():
    if pygame.time.get_ticks() < shake_end_time:
        return (random.randint(-SHAKE_STRENGTH, SHAKE_STRENGTH),
                random.randint(-SHAKE_STRENGTH, SHAKE_STRENGTH))
    return (0, 0)

def flame_is_on(row_i, col_i):
    now = pygame.time.get_ticks()
    t = now % FLAME_CYCLE_MS
    return t < FLAME_ON_MS

def cycle_difficulty():
    global current_difficulty_index, current_difficulty, MAX_ENEMIES

    current_difficulty_index = (current_difficulty_index + 1) % len(difficulty_names)
    current_difficulty = difficulty_names[current_difficulty_index]

    # Apply difficulty values
    MAX_ENEMIES = DIFFICULTIES[current_difficulty]["enemy_count"]
    player.maxhp = DIFFICULTIES[current_difficulty]["player_hp"]
    player.hp = player.maxhp

    # Update button text
    difficulty_button.text = f"Difficulty: {current_difficulty}"

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
    walls_player.clear()
    walls_bullets.clear()

    for row_i, row in enumerate(LEVEL_MAP):
        for col_i, tile in enumerate(row):
            if tile not in SOLID_TILES:
                continue

            # flame only solid when ON
            if tile == "F" and not flame_is_on(row_i, col_i):
                continue

            rect = pygame.Rect(col_i * TILE_SIZE, row_i * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            # --- player collisions: everything solid (including water) ---
            walls_player.append(rect)

            # --- bullet collisions: everything EXCEPT water ---
            if tile != "w":
                walls_bullets.append(rect)

            # keep your old list if you still use it elsewhere (optional)
            walls.append(rect)

build_walls()

# =====================
# PLAYER
# =====================
class Player:
    def __init__(self):
        self.rect = player_img.get_rect()
        # self.rectshd = player_img_shd.get_rect()
        self.image = player_img
        # self.imageshd = player_img_shd
        self.rect.topleft = (200, WORLD_HEIGHT - TILE_SIZE * 2)
        self.maxhp = 50 
        self.hp = self.maxhp
        self.last_shot = 0
        self.base_damage = 1
        self.damage = self.base_damage
        self.damage_boost_end = 0
        self.base_size = self.image.get_size()
        # self.base_size_shd = self.imageshd.get_size()
        self.size_boost_end = 0
        self.speed = 3
        self.shotgun_end = 0
        self.extra_shots = 0
        self.sniper_end = 0
        self.sniper_active = False
                # --- movement tracking + sway ---
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.sway_phase = 0.0

        self.vy = 0.0
        self.vx = 0.0
        self.hitbox_scale = 0.6  # 55% size hitbox (tweak)
        self.hit_rect = self.rect.copy()
        self.update_hitbox()

        

                # --- DASH ---
        self.dash_speed = 12           # burst speed
        self.dash_ms = 140             # how long dash lasts
        self.dash_cooldown_ms = 5000    # cooldown after dash ends
        self.dash_end_time = 0
        self.next_dash_time = 0
        self.is_dashing = False
        self.dash_vx = 0.0
        self.dash_vy = 0.0

        # visuals
        self.afterimages = []  # list of (time, image, rect)

    def update_hitbox(self):
        """Keep a smaller hit rect centered on the main rect."""
        w = int(self.rect.width * self.hitbox_scale)
        h = int(self.rect.height * self.hitbox_scale)
        self.hit_rect.size = (w, h)
        self.hit_rect.center = self.rect.center


        
        

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
    for w in walls_player:
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
    now = pygame.time.get_ticks()

    if player.is_dashing:
        if now >= player.dash_end_time:
            player.is_dashing = False
        else:
            # --- DASH MOVEMENT OVERRIDE ---
            player.rect.x += player.dash_vx
            player.rect.y += player.dash_vy

            # --- COLLISION WITH WALLS DURING DASH ---
            for wall in walls:
                if player.rect.colliderect(wall):
                    if player.dash_vx > 0:
                        player.rect.right = wall.left
                    elif player.dash_vx < 0:
                        player.rect.left = wall.right
                    if player.dash_vy > 0:
                        player.rect.bottom = wall.top
                    elif player.dash_vy < 0:
                        player.rect.top = wall.bottom

            # Do NOT apply acceleration or friction while dashing
            return  # exit early, dash is handled

    # --- NORMAL ICE MOVEMENT ---
    old_cx, old_cy = player.rect.center


    if USE_ZQSD:
        left_key, right_key, up_key, down_key = pygame.K_q, pygame.K_d, pygame.K_z, pygame.K_s
    else:
        left_key, right_key, up_key, down_key = pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s

    ax = ay = 0
    if USE_ZQSD:
        if keys[pygame.K_q]:
            ax -= ICE_ACCEL
        if keys[pygame.K_d]:
            ax += ICE_ACCEL
        if keys[pygame.K_z]:
            ay -= ICE_ACCEL
        if keys[pygame.K_s]:
            ay += ICE_ACCEL
    else:
        if keys[pygame.K_a]:
            ax -= ICE_ACCEL
        if keys[pygame.K_d]:
            ax += ICE_ACCEL
        if keys[pygame.K_w]:
            ay -= ICE_ACCEL
        if keys[pygame.K_s]:
            ay += ICE_ACCEL

    # --- APPLY ACCELERATION ---
    player.vx += ax
    player.vy += ay

    # --- LIMIT SPEED ---
    speed = math.hypot(player.vx, player.vy)
    if speed > ICE_MAX_SPEED:
        scale = ICE_MAX_SPEED / speed
        player.vx *= scale
        player.vy *= scale

    # --- MOVE PLAYER ---
    player.rect.x += player.vx
    for wall in walls:
        if player.rect.colliderect(wall):
            if player.vx > 0:
                player.rect.right = wall.left
            elif player.vx < 0:
                player.rect.left = wall.right
            player.vx = 0

    player.rect.y += player.vy
    for wall in walls:
        if player.rect.colliderect(wall):
            if player.vy > 0:
                player.rect.bottom = wall.top
            elif player.vy < 0:
                player.rect.top = wall.bottom
            player.vy = 0

    # --- ICE FRICTION ---
    player.vx *= ICE_FRICTION
    player.vy *= ICE_FRICTION

    # --- KEEP PLAYER INSIDE SCREEN/WORLD ---
    top_limit = camera_y
    bottom_limit = camera_y + SCREEN_SIZE[1] - player.rect.height
    if player.rect.y < top_limit:
        player.rect.y = top_limit
    elif player.rect.y > bottom_limit:
        player.rect.y = bottom_limit

    player.rect.x = max(0, min(player.rect.x, WORLD_WIDTH - player.rect.width))



    new_cx, new_cy = player.rect.center
    player.vel_x = new_cx - old_cx
    player.vel_y = new_cy - old_cy

    player.update_hitbox()





def update_dash_effects():
    now = pygame.time.get_ticks()

    # End dash
    if player.is_dashing and now >= player.dash_end_time:
        player.is_dashing = False
        player.dash_vx = 0
        player.dash_vy = 0

    # Spawn afterimages while dashing
    if player.is_dashing:
        last = getattr(start_dash, "last_ghost", 0)
        if now - last >= DASH_AFTERIMAGE_EVERY_MS:
            start_dash.last_ghost = now

            ghost = player.image.copy()
            ghost.set_alpha(120)
            r = player.rect.copy()
            player.afterimages.append((now, ghost, r))

    # Decay old afterimages
    new_list = []
    for t0, img, r in player.afterimages:
        age = now - t0
        if age < DASH_AFTERIMAGE_LIFE_MS:
            a = int(120 * (1 - age / DASH_AFTERIMAGE_LIFE_MS))
            img.set_alpha(a)
            new_list.append((t0, img, r))
    player.afterimages = new_list

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

    def update(self, collision_targets=[]):
        if not self.alive:
            return

        # Move
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))

        # Check world bounds
        if not WORLD_RECT.collidepoint(self.rect.center):
            self.kill()
            return

        # Lifetime
        if pygame.time.get_ticks() - self.spawn_time > BULLET_LIFETIME_MS:
            self.kill()
            return

        # Check walls
        for w in walls_bullets:
            if self.rect.colliderect(w):
                row_i = w.y // TILE_SIZE
                col_i = w.x // TILE_SIZE
                ch = LEVEL_MAP[row_i][col_i]

                # Let PLAYER bullets pass through flame walls only
                if ch == "F" and self.owner == "player":
                    continue

                self.kill()
                return

        # --- Collision with targets ---
        for target in collision_targets:
            target_rect = getattr(target, "hit_rect", target.rect)
            if self.rect.colliderect(target_rect):
                if self.owner == "player":
                    # Damage boss or enemy
                    if hasattr(target, "hp"):
                        target.hp -= player.damage
                        if hasattr(target, "hit_flash_end"):
                            target.hit_flash_end = pygame.time.get_ticks() + 120
                        if target.hp <= 0:
                            if isinstance(target, Boss):
                                # Boss death handled elsewhere
                                pass
                            else:
                                target.dead = True
                                effects.append(DramaticExplosion(target.rect.centerx, target.rect.centery))
                elif self.owner in ("boss", "enemy"):
                    # Damage player
                    player.hp -= 1
                    trigger_screenshake()

                # Bullet dies on hitting a target
                self.kill()
                return

    def draw(self, surf):
        screen_y = self.rect.y - camera_y
        if -100 <= screen_y <= SCREEN_SIZE[1] + 100:
            surf.blit(self.image, (self.rect.x, screen_y))

    def kill(self):
        if not self.alive:
            return
        self.alive = False
        effects.append(Explosion(self.x, self.y))




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
        self.hit_flash_end = 0


        #animation 
        self.sway_phase = random.random() * math.tau  # different start per enemy
        self.vel_x = 0.0
        self.vel_y = 0.0

        self.sway_offset = random.random() * math.tau  # different start
        self.sway_intensity = 0.0                      # smoothed 0..1



    def move_and_collide(self, dx, dy):
        # ---------- X ----------
        self.rect.x += dx
        for w in walls:
            if self.rect.top >= int(camera_y) + SCREEN_SIZE[1] + TILE_SIZE * 1:
                continue

            if self.rect.colliderect(w):
                row_i = w.y // TILE_SIZE
                col_i = w.x // TILE_SIZE
                ch = LEVEL_MAP[row_i][col_i]

                # die only if flame is ON
                if ch == "F" and flame_is_on(row_i, col_i):
                    self.dead = True
                    return

                if dx > 0:
                    self.rect.right = w.left
                elif dx < 0:
                    self.rect.left = w.right

                self.vx *= -1

        # ---------- Y ----------
        self.rect.y += dy
        for w in walls:
            if self.rect.top >= int(camera_y) + SCREEN_SIZE[1] + TILE_SIZE * 3:
                continue

            if self.rect.colliderect(w):
                row_i = w.y // TILE_SIZE
                col_i = w.x // TILE_SIZE
                ch = LEVEL_MAP[row_i][col_i]

                # die only if flame is ON
                if ch == "F" and flame_is_on(row_i, col_i):
                    self.dead = True
                    return

                if dy > 0:
                    self.rect.bottom = w.top
                elif dy < 0:
                    self.rect.top = w.bottom

                self.vy *= -1

        self.rect.clamp_ip(WORLD_RECT)

    def shoot_at(self, target_pos, bullet_list):
        tx, ty = target_pos
        sx, sy = self.rect.center
        dx, dy = (tx - sx), (ty - sy)
        nx, ny = normalize(dx, dy)
        spawn_shot_feedback(sx, sy, nx, ny)


        bullet_list.append(
            Bullet(sx, sy, nx * BULLET_SPEED, ny * BULLET_SPEED,
                   owner="enemy", base_image=enemy_bullet_img_base)
        )

    def update(self, target_pos, bullet_list):
        old_cx, old_cy = self.rect.center

        if enemy_on_active_flame(self.rect):
            self.hp = 0
            self.dead = True
            return

        self.vx += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)
        self.vy += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)

        tx, ty = target_pos
        cx, cy = self.rect.center
        to_px, to_py = (tx - cx), (ty - cy)
        nx, ny = normalize(to_px, to_py)
        self.vx += nx * 0.08
        self.vy += ny * 0.08

        sp = math.hypot(self.vx, self.vy)
        if sp > ENEMY_SPEED:
            self.vx = (self.vx / sp) * ENEMY_SPEED
            self.vy = (self.vy / sp) * ENEMY_SPEED

        self.move_and_collide(int(round(self.vx)), int(round(self.vy)))
        new_cx, new_cy = self.rect.center
        self.vel_x = new_cx - old_cx
        self.vel_y = new_cy - old_cy
        speed = math.hypot(self.vel_x, self.vel_y)
        t = min(1.0, speed / max(1e-6, ENEMY_SPEED))

        # smooth t so it doesn't jitter
        self.sway_intensity += (t - self.sway_intensity) * 0.12



        now = pygame.time.get_ticks()
        if now - self.last_shot >= ENEMY_SHOOT_COOLDOWN_MS:
            self.last_shot = now
            self.shoot_at(target_pos, bullet_list)

    def draw(self, surf):
        cy = int(camera_y)
        sr = self.rect.move(0, -cy)
        if sr.bottom < 0 or sr.top > SCREEN_SIZE[1]:
            return

        img = enemy_hit_img if pygame.time.get_ticks() < self.hit_flash_end else enemy_img
                # --- time-based sway (actually animates) ---
        now = pygame.time.get_ticks() / 1000.0  # seconds
        phase = now * (2 * math.pi) * ENEMY_SWAY_FREQ + self.sway_offset

        angle = math.sin(phase) * ENEMY_SWAY_MAX_DEG * self.sway_intensity
        bob_y = math.cos(phase) * ENEMY_BOB_MAX_Y * self.sway_intensity

        rotated = pygame.transform.rotozoom(img, angle, 1.0)

        # IMPORTANT: center using sr (screen rect), not world rect
        draw_center = (sr.centerx, sr.centery + int(bob_y))
        draw_rect = rotated.get_rect(center=draw_center)
        surf.blit(rotated, draw_rect.topleft)



        if self.hp >= 3:
            hb_img = hb_full
        elif self.hp == 2:
            hb_img = hb_23
        elif self.hp == 1:
            hb_img = hb_13
        else:
            hb_img = hb_empty

        surf.blit(hb_img, (sr.x, sr.y - HB_H - 4))



class HorizontalLaser:
    def __init__(self, y):
        self.did_damage = False
        self.y = y
        self.rect = pygame.Rect(0, y, (SCREEN_SIZE[0]), LASER_HEIGHT)

        self.spawn_time = pygame.time.get_ticks()
        self.state = "warning"  # "warning" → "active" → "dead"

        

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time

        if self.state == "warning" and elapsed > LASER_WARNING_MS:
            self.state = "active"
            self.did_damage = False


        elif self.state == "active" and elapsed > LASER_WARNING_MS + LASER_ACTIVE_MS:
            self.state = "dead"

        # damage player
        if self.state == "active":
            if (not self.did_damage) and self.rect.colliderect(player.hit_rect):
                player.hp -= LASER_DAMAGE
                trigger_screenshake()
                self.did_damage = True



    def draw(self, surf):
        shake_x, shake_y = get_shake_offset()

        screen_y = self.y - camera_y
        if screen_y < -LASER_HEIGHT or screen_y > SCREEN_SIZE[1]:
            return

        if self.state == "warning":
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                surf.blit(laser_warning_img, (shake_x, screen_y + shake_y))

        elif self.state == "active":
            surf.blit(laser_active_img, (shake_x, screen_y + shake_y))




class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, boss_img.get_width(), boss_img.get_height())
        self.image = boss_img

        self.max_hp = DIFFICULTIES[current_difficulty]["boss_hp"]
        self.hp = self.max_hp
        
        self.last_shot = pygame.time.get_ticks()
        self.angle_offset = 0
        self.phase_two = False

    def update(self):
        if not self.phase_two and self.hp <= self.max_hp // 2:
            self.phase_two = True
            trigger_screenshake(250, 10)
            show_fade_text("BOSS PHASE 2!")
            self.spawn_screen_lasers()

        now = pygame.time.get_ticks()
        if now - self.last_shot >= BOSS_SHOOT_INTERVAL_MS:
            self.last_shot = now
            self.shoot_rotating_bullets()

    def shoot_rotating_bullets(self):
        cx, cy = self.rect.center
        num_lines = BOSS_BULLET_LINES_PHASE_2 if self.phase_two else BOSS_BULLET_LINES
        speed_bullet = BOSS_BULLET_SPEED_PHASE_2 if self.phase_two else BOSS_BULLET_SPEED


        for i in range(num_lines):
            angle_deg = (360 / num_lines) * i + self.angle_offset
            angle_rad = math.radians(angle_deg)
            vx = math.cos(angle_rad) * speed_bullet
            vy = math.sin(angle_rad) * speed_bullet

            # Spawn bullet slightly outside boss to avoid sticking
            offset = 20  # pixels away from center
            start_x = cx + math.cos(angle_rad) * offset
            start_y = cy + math.sin(angle_rad) * offset

            boss_bullets.append(Bullet(start_x, start_y, vx, vy, owner="boss", base_image=enemy_bullet_img_base))

        self.angle_offset = (self.angle_offset + BOSS_BULLET_ROT_SPEED) % 360


    def spawn_screen_lasers(self):
        gap = int(TILE_SIZE * 2.5)
        y = 0
        while y < SCREEN_SIZE[1]:
            lasers.append(HorizontalLaser(camera_y + y))
            y += gap

    def draw(self, surf):
        sr = self.rect.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            surf.blit(self.image, sr)



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
    tries = 100
    while tries > 0:
        tries -= 1

        x = random.randint(0, WORLD_WIDTH - PRESENT_SIZE)
        y_min = max(0, int(camera_y - TILE_SIZE * 2))
        y_max = int(camera_y + SCREEN_SIZE[1] - PRESENT_SIZE)
        if y_max < y_min:
            return

        y = random.randint(y_min, y_max)
        rect = pygame.Rect(x, y, PRESENT_SIZE, PRESENT_SIZE)

        if any(rect.colliderect(w) for w in walls):
            continue

        presents.append(rect)
        show_fade_text("Present spawned")
        return

def check_present_pickup():
    global present_count, last_powerup_name, last_powerup_end_time, last_powerup_icon

    for rect in presents[:]:  # copy so we can remove safely
        if player.rect.colliderect(rect):
            presents.remove(rect)
            present_count += 1

            powerup = random.choice(["Heal", "Damage", "Smaller", "Shotgun"])
            last_powerup_icon = POWERUP_ICONS.get(powerup)
            # UI message
            last_powerup_name = powerup
            last_powerup_end_time = pygame.time.get_ticks() + POWERUP_UI_DURATION_MS

            if powerup == "Heal":
                heal = DIFFICULTIES[current_difficulty]["heal"]
                player.hp = min(player.maxhp, player.hp + heal)
                show_fade_text("POWER UP: Heal")

            elif powerup == "Damage":
                player.damage = 3
                player.damage_boost_end = pygame.time.get_ticks() + 5000
                show_fade_text("POWER UP: Damage Boost")

            elif powerup == "Smaller":
                player.speed = 5
                player.size_boost_end = pygame.time.get_ticks() + 5000
                new_size = (
                    int(player.base_size[0] * 0.6),
                    int(player.base_size[1] * 0.6),
                )
                # new_size_shd = (
                #     int(player.base_size_shd[0] * 0.6),
                #     int(player.base_size_shd[1] * 0.6),
                # )
                player.image = pygame.transform.scale(player_img_base, new_size)
                # player.image = pygame.transform.scale(player_img_shd_base, new_size_shd)
                center = player.rect.center
                player.rect = player.image.get_rect(center=center)
                show_fade_text("POWER UP: Shrink")
            
            elif powerup == "Shotgun":
                player.extra_shots = 2          # +2 bullets
                player.shotgun_end = pygame.time.get_ticks() + 5000
                show_fade_text("POWER UP: Shotgun")
            
            

           



# =====================
# SHOOTING
# =====================
def player_shoot(player_bullets):
    now = pygame.time.get_ticks()
    if now - player.last_shot < PLAYER_SHOOT_COOLDOWN_MS:
        return
    player.last_shot = now
    
    snowball_shoot_sound.play()


    # Aim at mouse (mouse = screen coords → world coords)
    mx, my = pygame.mouse.get_pos()
    target_world = (mx, my + camera_y)

    sx, sy = player.rect.center
    dx, dy = target_world[0] - sx, target_world[1] - sy
    nx, ny = normalize(dx, dy)

    # Always fire center bullet
    directions = [(nx, ny)]

    # Shotgun powerup: add 2 extra shots
    if player.extra_shots > 0:
        spread = 12  # degrees
        directions.append(rotate_vector(nx, ny, -spread))
        directions.append(rotate_vector(nx, ny, spread))

    for vx, vy in directions:
        player_bullets.append(
            Bullet(
                sx, sy,
                vx * BULLET_SPEED,
                vy * BULLET_SPEED,
                owner="player",
                base_image=player_bullet_img_base
            )
        )

def rotate_vector(x, y, degrees):
    rad = math.radians(degrees)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    return (
        x * cos_r - y * sin_r,
        x * sin_r + y * cos_r
    )

# =====================
# MOVEMENT + COLLISION (PLAYER)
# =====================


    # keep inside screen vertical limits (your existing code)
    top_limit = camera_y
    bottom_limit = camera_y + SCREEN_SIZE[1] - player.rect.height
    if player.rect.y < top_limit:
        player.rect.y = top_limit
    elif player.rect.y > bottom_limit:
        player.rect.y = bottom_limit

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
effects = []   # <-- add this


pending_aoe_spawns = []  
presents = []
boss_bullets = []
enemy_bullets = []
player_bullets = []
game_over=False
death_stats={}
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL_MS)
game_state = "menu"
boss_death_end_time = 0
previous_state = "menu"
  # "menu", "settings", "playing"

# Button helper
class Button:
    def __init__(self, center, text,
                 size=(260, 56),              # 👈 FIXED SIZE
                 font_size=32,
                 color=(40, 80, 200),
                 hover_color=(70, 120, 255),
                 text_color=(255, 255, 255),
                 radius=12):
        self.center = center
        self.text = text
        self.size = size
        self.font_size = font_size
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.radius = radius

        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)

        # shadow
        shadow_rect = self.rect.move(0, 4)
        shadow = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(), border_radius=self.radius)
        surf.blit(shadow, shadow_rect.topleft)

        # body
        body = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        base_col = self.hover_color if is_hover else self.color
        pygame.draw.rect(body, (*base_col, 230), body.get_rect(), border_radius=self.radius)
        surf.blit(body, self.rect.topleft)

        # outline
        pygame.draw.rect(surf, (255, 255, 255), self.rect, 2, border_radius=self.radius)

        # text (centered)
        font = pygame.font.SysFont(None, self.font_size)
        img = font.render(self.text, True, self.text_color)
        surf.blit(img, img.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )



# --- MENU ---
start_button, settings_button = vertical_menu(
    SCREEN_SIZE[0] // 2,
    360,            # start Y
    90,             # spacing
    ["Start", "Settings"]
)


# --- SETTINGS ---
toggle_keys_button, difficulty_button, back_button = vertical_menu(
    SCREEN_SIZE[0] // 2,
    320,
    90,
    [
        "Keys: ZQSD",
        f"Difficulty: {current_difficulty}",
        "Back"
    ]
)

# --- PAUSE (make separate buttons; don't reuse settings_button) ---
resume_button, pause_settings_button, restart_button = vertical_menu(
    SCREEN_SIZE[0] // 2,
    320,
    90,
    ["Resume", "Settings", "Restart"]
)


# --- GAME OVER ---
try_again_button, back_to_menu_button = vertical_menu(
    SCREEN_SIZE[0] // 2,
    380,
    90,
    ["Try Again", "Back to Menu"]
)


# --- WIN ---
win_play_again_button, win_back_to_menu_button = vertical_menu(
    SCREEN_SIZE[0] // 2,
    380,
    90,
    ["Play Again", "Back to Menu"]
)



# difficulty_button = Button(
#     (SCREEN_SIZE[0]//2, 380),                 # center (x,y) ✅
#     f"Difficulty: {current_difficulty}",
#     size=(200, 60)                            # size ✅
# )



# =====================
# EFFECTS
# =====================

class Explosion:
    def __init__(self, x, y, duration_ms=180, max_radius=18):
        self.x = x
        self.y = y
        self.spawn = pygame.time.get_ticks()
        self.duration = duration_ms
        self.max_radius = max_radius
        self.dead = False

    def update(self):
        t = pygame.time.get_ticks() - self.spawn
        if t >= self.duration:
            self.dead = True

    def draw(self, surf):
        t = pygame.time.get_ticks() - self.spawn
        if t < 0:
            return

        p = min(1.0, t / self.duration)
        radius = int(2 + p * self.max_radius)
        alpha = int(255 * (1.0 - p))

        # draw in screen coords (world y minus camera)
        screen_pos = (int(self.x), int(self.y - camera_y))

        # small ring + filled core
        tmp = pygame.Surface((radius*2 + 4, radius*2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (255, 220, 180, alpha), (radius+2, radius+2), radius, width=2)
        pygame.draw.circle(tmp, (255, 150, 120, alpha//2), (radius+2, radius+2), max(1, radius//2), width=0)

        surf.blit(tmp, (screen_pos[0] - radius - 2, screen_pos[1] - radius - 2))

class DramaticExplosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.spawn = pygame.time.get_ticks()
        self.duration = 420
        self.dead = False

    def update(self):
        if pygame.time.get_ticks() - self.spawn > self.duration:
            self.dead = True

    def draw(self, surf):
        t = pygame.time.get_ticks() - self.spawn
        p = min(1.0, t / self.duration)

        screen_x = int(self.x)
        screen_y = int(self.y - camera_y)

        # --- SHOCKWAVE RING ---
        ring_radius = int(10 + p * 60)
        ring_alpha = int(200 * (1 - p))

        ring = pygame.Surface((ring_radius*2, ring_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(
            ring,
            (255, 110, 80, ring_alpha),
            (ring_radius, ring_radius),
            ring_radius,
            width=4
        )
        surf.blit(ring, (screen_x - ring_radius, screen_y - ring_radius))

        # --- CORE FLASH ---
        flash_radius = int(8 + (1 - p) * 32)
        flash_alpha = int(255 * (1 - p))

        flash = pygame.Surface((flash_radius*2, flash_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(
            flash,
            (255, 255, 255, flash_alpha),
            (flash_radius, flash_radius),
            flash_radius
        )
        surf.blit(flash, (screen_x - flash_radius, screen_y - flash_radius))

class MassiveBossExplosion:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.spawn = pygame.time.get_ticks()
            self.duration = 1600  # ms
            self.dead = False

        def update(self):
            if pygame.time.get_ticks() - self.spawn >= self.duration:
                self.dead = True

        def draw(self, surf):
            t = pygame.time.get_ticks() - self.spawn
            p = min(1.0, t / self.duration)

            sx = int(self.x)
            sy = int(self.y - camera_y)

            # ---- BIG FLASH OVERLAY (fills screen briefly) ----
            flash_alpha = int(170 * max(0.0, 1.0 - p*1.8))
            if flash_alpha > 0:
                overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
                overlay.fill((255, 255, 255, flash_alpha))
                surf.blit(overlay, (0, 0))

            # ---- MULTI SHOCKWAVE RINGS ----
            # three rings, different speeds
            for i, speed in enumerate([1.0, 1.35, 1.75]):
                ring_p = min(1.0, p * speed)
                r = int(20 + ring_p * (220 + i*60))
                a = int(220 * (1.0 - ring_p))
                if a <= 0:
                    continue

                ring = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(
                    ring,
                    (255, 120, 80, a),
                    (r, r),
                    r,
                    width=6
                )
                surf.blit(ring, (sx - r, sy - r))

            # ---- HOT CORE GLOW ----
            core_r = int(16 + (1.0 - p) * 90)
            core_a = int(240 * (1.0 - p))
            if core_a > 0:
                core = pygame.Surface((core_r*2, core_r*2), pygame.SRCALPHA)
                pygame.draw.circle(core, (255, 200, 140, core_a), (core_r, core_r), core_r)
                surf.blit(core, (sx - core_r, sy - core_r))
    
class Spark:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        ang = random.random() * math.tau
        spd = random.uniform(3.0, 9.0)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd - random.uniform(1.0, 3.5)  # slight upward kick
        self.life = random.randint(25, 45)  # frames
        self.dead = False

    def update(self):
        if self.dead:
            return
        self.life -= 1
        if self.life <= 0:
            self.dead = True
            return
        # gravity + drag
        self.vy += 0.18
        self.vx *= 0.985
        self.vy *= 0.985
        self.x += self.vx
        self.y += self.vy

    def draw(self, surf):
        if self.dead:
            return
        sy = int(self.y - camera_y)
        if sy < -50 or sy > SCREEN_SIZE[1] + 50:
            return
        a = max(0, min(255, int(255 * (self.life / 45))))
        r = 2
        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 220, 140, a), (r+1, r+1), r)
        surf.blit(s, (int(self.x) - (r+1), sy - (r+1)))


class SmokePuff:
    def __init__(self, x, y, start_r=18, end_r=90, duration_ms=900):
        self.x = x
        self.y = y
        self.start_r = start_r
        self.end_r = end_r
        self.spawn = pygame.time.get_ticks()
        self.duration = duration_ms
        self.dead = False

    def update(self):
        if pygame.time.get_ticks() - self.spawn >= self.duration:
            self.dead = True

    def draw(self, surf):
        t = pygame.time.get_ticks() - self.spawn
        p = min(1.0, t / self.duration)

        r = int(self.start_r + (self.end_r - self.start_r) * p)
        a = int(120 * (1.0 - p))
        if a <= 0:
            return

        sx = int(self.x)
        sy = int(self.y - camera_y)

        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (80, 80, 80, a), (r, r), r)
        surf.blit(s, (sx - r, sy - r))



class BossDeathCinematic:
    """
    One effect object that:
    - triggers several blast pulses over ~1.6s
    - spawns sparks and smoke
    - draws a flickery core + multiple rings
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.spawn = pygame.time.get_ticks()
        self.duration = 1700
        self.dead = False

        self.parts = []  # sparks + smoke
        self._next_pulse = self.spawn
        self._pulse_index = 0

        # pulse timings (ms after start)
        self.pulse_times = [0, 180, 360, 650, 980, 1250]
        self.max_pulses = len(self.pulse_times)

    def _do_pulse(self, strength):
        # smoke
        self.parts.append(SmokePuff(
            self.x + random.randint(-20, 20),
            self.y + random.randint(-20, 20),
            start_r=18 + int(10*strength),
            end_r=110 + int(40*strength),
            duration_ms=900 + int(200*strength)
        ))

        # sparks burst
        for _ in range(int(18 + 18*strength)):
            self.parts.append(Spark(self.x, self.y))

        # extra little “sub explosions” look: reuse your Explosion rings (optional)
        for _ in range(int(2 + 2*strength)):
            ox = self.x + random.randint(-90, 90)
            oy = self.y + random.randint(-70, 70)
            effects.append(Explosion(ox, oy, duration_ms=260, max_radius=28))

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn

        # fire pulses at specific times
        if self._pulse_index < self.max_pulses:
            if elapsed >= self.pulse_times[self._pulse_index]:
                # later pulses slightly weaker
                strength = max(0.25, 1.0 - self._pulse_index * 0.12)
                # add some random variation
                strength *= random.uniform(0.85, 1.1)
                self._do_pulse(strength)
                self._pulse_index += 1

        for p in self.parts:
            p.update()
        self.parts[:] = [p for p in self.parts if not p.dead]

        if elapsed >= self.duration and len(self.parts) == 0:
            self.dead = True

    def draw(self, surf):
        now = pygame.time.get_ticks()
        t = now - self.spawn
        p = min(1.0, t / self.duration)

        sx = int(self.x)
        sy = int(self.y - camera_y)

        # ---- screen flash that FADES QUICKLY (no shake) ----
        flash_alpha = int(140 * max(0.0, 1.0 - p * 2.2))
        if flash_alpha > 0:
            overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
            overlay.fill((255, 255, 255, flash_alpha))
            surf.blit(overlay, (0, 0))

        # ---- flickery hot core ----
        flicker = 0.75 + 0.25 * math.sin(now * 0.04)  # fast flicker
        core_r = int((30 + (1.0 - p) * 120) * flicker)
        core_a = int(220 * (1.0 - p))
        if core_a > 0:
            core = pygame.Surface((core_r*2, core_r*2), pygame.SRCALPHA)
            pygame.draw.circle(core, (255, 200, 140, core_a), (core_r, core_r), core_r)
            surf.blit(core, (sx - core_r, sy - core_r))

        # ---- multiple rings, animated ----
        for i in range(4):
            ring_p = min(1.0, p * (1.1 + i*0.25))
            r = int(40 + ring_p * (260 + i * 80))
            a = int(200 * (1.0 - ring_p))
            if a <= 0:
                continue
            ring = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 120, 80, a), (r, r), r, width=7)
            surf.blit(ring, (sx - r, sy - r))

        # draw smoke + sparks LAST so they sit “on top”
        for part in self.parts:
            part.draw(surf)
class MuzzleFlash:
    def __init__(self, x, y, duration_ms=90):
        self.x = x
        self.y = y
        self.spawn = pygame.time.get_ticks()
        self.duration = duration_ms
        self.dead = False

    def update(self):
        if pygame.time.get_ticks() - self.spawn >= self.duration:
            self.dead = True

    def draw(self, surf):
        t = pygame.time.get_ticks() - self.spawn
        p = min(1.0, t / self.duration)

        r = int(10 + (1.0 - p) * 18)
        a = int(220 * (1.0 - p))
        if a <= 0:
            return

        sx = int(self.x)
        sy = int(self.y - camera_y)

        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, a), (r, r), r)
        pygame.draw.circle(s, (255, 200, 120, a), (r, r), max(2, r//2))
        surf.blit(s, (sx - r, sy - r))


class ShootRing:
    def __init__(self, x, y, duration_ms=160):
        self.x = x
        self.y = y
        self.spawn = pygame.time.get_ticks()
        self.duration = duration_ms
        self.dead = False

    def update(self):
        if pygame.time.get_ticks() - self.spawn >= self.duration:
            self.dead = True

    def draw(self, surf):
        t = pygame.time.get_ticks() - self.spawn
        p = min(1.0, t / self.duration)

        r = int(6 + p * 26)
        a = int(160 * (1.0 - p))
        if a <= 0:
            return

        sx = int(self.x)
        sy = int(self.y - camera_y)

        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, a), (r+1, r+1), r, width=2)
        surf.blit(s, (sx - (r+1), sy - (r+1)))


class ShotSpark:
    def __init__(self, x, y, vx, vy, life=18):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = life
        self.dead = False

    def update(self):
        if self.dead:
            return
        self.life -= 1
        if self.life <= 0:
            self.dead = True
            return
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92

    def draw(self, surf):
        if self.dead:
            return
        a = int(200 * (self.life / 18))
        sx = int(self.x)
        sy = int(self.y - camera_y)
        dot = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(dot, (255, 220, 140, a), (3, 3), 2)
        surf.blit(dot, (sx - 3, sy - 3))




# =====================
# UPDATE
# =====================
def update_all():
    global boss, boss_spawned, stop_enemy_spawning, game_state, boss_death_end_time

    now = pygame.time.get_ticks()
    player_center = player.rect.center

    # enemies
    for e in enemies:
        e.update(player_center, enemy_bullets)

    handle_enemy_spawning()

    if boss:
        boss.update()

    for e in enemies[:]:  # iterate over a copy so we can remove safely
    # Kill enemy if it goes 2 tiles below the bottom of the screen
        if e.rect.top > camera_y + SCREEN_SIZE[1] + 2 * TILE_SIZE:
            enemies.remove(e)

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

    # collisions with player
    # for b in boss_bullets:
    #     if b.alive and b.rect.colliderect(player.rect):
    #         b.kill()
    #         player.hp -= 1
    #         trigger_screenshake()


    # --- Update bullets ---
    for b in enemy_bullets:
        b.update(collision_targets=[player])

    for b in boss_bullets:
        b.update(collision_targets=[player])

    for b in player_bullets:
        b.update()  # only move + walls + lifetime (NO target damage here)


    # Remove dead bullets
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    player_bullets[:] = [b for b in player_bullets if b.alive]
    boss_bullets[:] = [b for b in boss_bullets if b.alive]
    
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
        player.speed = 3

        center = player.rect.center
        player.image = player_img_base.copy()
        # player.imageshd = player_img_shd_base.copy()
        player.rect = player.image.get_rect(center=center)

        # IMPORTANT: stop leftover slide + fix wall overlap
        player.vx = 0
        player.vy = 0
        resolve_player_after_resize()

    if player.extra_shots > 0 and now > player.shotgun_end:
        player.extra_shots = 0

    # cleanup bullets
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    player_bullets[:] = [b for b in player_bullets if b.alive]

    for laser in lasers:
        laser.update()

    lasers[:] = [l for l in lasers if l.state != "dead"]
        
    # player bullets -> enemies
    # --- PLAYER BULLETS → ENEMIES & BOSS ---
    for b in player_bullets:
        if not b.alive:
            continue

        # hit normal enemies first
        for e in enemies:
            if e.dead:
                continue
            if b.rect.colliderect(e.rect):
                b.kill()
                e.hp -= player.damage
                e.hit_flash_end = pygame.time.get_ticks() + 120  # ms
                snowball_hit_sound.play()

                if e.hp <= 0:
                    effects.append(DramaticExplosion(e.rect.centerx, e.rect.centery))
                    e.dead = True

                break  # bullet stops after hitting one enemy

        # hit boss if exists
        if boss and b.alive and b.rect.colliderect(boss.rect):
            b.kill()
            boss.hp -= player.damage
            snowball_hit_sound.play()  # hit sound for boss too

            if boss.hp <= 0:
                now = pygame.time.get_ticks()
                # start cinematic explosion
                effects.append(BossDeathCinematic(boss.rect.centerx, boss.rect.centery))

                # clear threats so it feels like "final blow"
                enemies.clear()
                enemy_bullets.clear()
                player_bullets.clear()
                boss_bullets.clear()
                lasers.clear()
                aoe_fields.clear()
                pending_aoe_spawns.clear()

                
                boss_spawned = False
                boss = None
                stop_enemy_spawning = True

                boss_death_end_time = now + 1700
                game_state = "boss_dying"



    # remove dead enemies
    enemies[:] = [e for e in enemies if not e.dead]

    for fx in effects:
        fx.update()
    effects[:] = [fx for fx in effects if not fx.dead]



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


# =====================
# RESTART FUNCTION
# =====================

def reset_game():
    global enemies, enemy_bullets, player_bullets, boss_bullets
    global lasers, aoe_fields, pending_aoe_spawns
    global present_rect, present_count
    global camera_y, camera_start_y, bg_y, bg_index
    global game_start_ticks, fade_text, fade_text_start
    global boss, boss_spawned, stop_enemy_spawning
    global player
    global last_powerup_icon, last_powerup_name, last_powerup_end_time
    last_powerup_icon = None
    last_powerup_name = ""
    last_powerup_end_time = 0


    # clear entities
    enemies.clear()
    enemy_bullets.clear()
    player_bullets.clear()
    boss_bullets.clear()
    lasers.clear()
    aoe_fields.clear()
    pending_aoe_spawns.clear()
    boss = None
    boss_spawned = False
    stop_enemy_spawning = False
    
    
    player.maxhp = DIFFICULTIES[current_difficulty]["player_hp"]
    player.hp = player.maxhp

    player.vx = 0
    player.vy = 0

    # reset presents
    present_count = 0

    # reset player
    player.rect.topleft = (200, WORLD_HEIGHT - TILE_SIZE * 2)
    player.hp = player.maxhp
    player.last_shot = 0
    player.image = player_img_base.copy()
    # player.imageshd = player_img_shd_base.copy
    player.rect = player.image.get_rect(center=player.rect.center)

    # reset camera/background/timer
    camera_y = max(0, WORLD_HEIGHT - SCREEN_SIZE[1])
    camera_start_y = camera_y
    bg_y = 0.0
    bg_index = 0

    game_start_ticks = pygame.time.get_ticks()
    fade_text = None
    fade_text_start = 0

    # clear boss entirely
    boss = None
    boss_spawned = False

    # reset AoE spawn timer
    if hasattr(update_all, "_next_aoe_spawn"):
        delattr(update_all, "_next_aoe_spawn")

    # spawn enemies fresh
    

# =====================
# RENDER
# =====================
def render():
    global DEBUG_CAMERA

    cy = int(camera_y)
    surface.fill((0, 0, 0))
    shake_x, shake_y = (0, 0) if game_state == "boss_dying" else get_shake_offset()    

    img_a = background_imgs[bg_index]
    img_b = background_imgs[(bg_index + 1) % 2]

    surface.blit(img_a, (shake_x, int(bg_y) + shake_y))
    surface.blit(img_b, (shake_x, int(bg_y) - bg_height + shake_y))

    draw_walkable_tiles(surface)

    # walls
    for w in walls:
        sr = w.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            row_i = w.y // TILE_SIZE
            col_i = w.x // TILE_SIZE
            ch = LEVEL_MAP[row_i][col_i]

            if ch == "F":
                img = flame_tile
            else:
                img = TILE_TEXTURES.get(ch, TILE_TEXTURES["#"])

            surface.blit(img, (sr.x + shake_x, sr.y + shake_y))

    draw_grid(surface)

    for rect in presents:
        p_screen_y = rect.y - camera_y
        if -100 <= p_screen_y <= SCREEN_SIZE[1] + 100:
            surface.blit(
                present_img,
                (rect.x + shake_x, p_screen_y + shake_y)
            )

    for e in enemies:
        e.draw(surface)

    for field in aoe_fields:
        field.draw(surface)

    if boss:
        boss.draw(surface)

    for b in enemy_bullets:
        b.draw(surface)
    for b in player_bullets:
        b.draw(surface)
    for b in boss_bullets:
        b.draw(surface)

    for laser in lasers:
        laser.draw(surface)

    for fx in effects:
        fx.draw(surface)

        # dash afterimages behind player
    for t0, img, r in player.afterimages:
        surface.blit(img, (r.x + shake_x, r.y - camera_y + shake_y))


        # how much we're moving (0..1)
    speed = math.hypot(player.vel_x, player.vel_y)
    max_walk_pf = max(1e-6, player.speed)
    t = min(1.0, speed / max_walk_pf)

    # sway = rotate left/right + bob up/down (phase-linked)
    angle = math.sin(player.sway_phase) * SWAY_MAX_DEG * t
    bob_y = math.cos(player.sway_phase) * BOB_MAX_Y * t

    # rotate around center using the BASE (unrotated) sprite for clean quality
    base = player.image  # or player_img_base if you never want powerups to affect rotation source
    rotated = pygame.transform.rotozoom(base, angle, 1.0)

    # keep position stable by re-centering to player's rect center
    draw_center = (player.rect.centerx + shake_x, player.rect.centery - camera_y + shake_y + int(bob_y))
    # draw_center_shd = (player.rectshd.centerx + shake_x, player.rectshd.centery - camera_y + shake_y + int(bob_y))
    draw_rect = rotated.get_rect(center=draw_center)
    # draw_rectshd = rotated.get_rect(center=draw_center_shd)

    surface.blit(rotated, draw_rect.topleft)
    # surface.blit(rotated, draw_rectshd.topleft)


    # UI
    
    HUD_W = 300
    HP_H  = 20
    DASH_H = 12
    PAD = 12
    GAP = 8

    hud_x = SCREEN_SIZE[0] - HUD_W - PAD
    hud_y = SCREEN_SIZE[1] - PAD - (HP_H + GAP + DASH_H)

        # --- HUD BACKGROUND PANEL ---
    panel_pad = 10
    panel_w = HUD_W + panel_pad * 2
    panel_h = HP_H + GAP + DASH_H + panel_pad * 2

    panel_x = hud_x - panel_pad
    panel_y = hud_y - panel_pad

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(
        panel,
        (0, 0, 0, 170),          # dark transparent background
        panel.get_rect(),
        border_radius=12
    )
    surface.blit(panel, (panel_x, panel_y))

    # subtle outline
    pygame.draw.rect(
        surface,
        (255, 255, 255),
        (panel_x, panel_y, panel_w, panel_h),
        2,
        border_radius=12
    )

    # --- ACTUAL BARS ---
    draw_player_healthbar(surface, player, x=hud_x, y=hud_y, w=HUD_W, h=HP_H)
    draw_dash_cooldown_bar(surface, x=hud_x, y=hud_y + HP_H + GAP)


    # draw_text(surface, f"Enemies: {len(enemies)}/{MAX_ENEMIES}", 12, 34)

    # dash already drawn at y=58 in your code
    draw_hud(surface)  # ✅ ADD THIS

    

    # ✅ DRAW BOSS HEALTH BAR (CENTER TOP)
    if boss:
        draw_boss_healthbar(surface, boss)

    draw_debug_overlay(surface)
    draw_minimap_progress(surface)
    draw_snow(surface)


    

    flip()


def check_ceiling_crush():
    """
    If player is at the bottom of the screen and hits a wall above, you die.
    """
    cy = int(camera_y)
    player_screen_rect = player.rect.move(0, -cy)

    # Only trigger if player is at the bottom of the screen
    if player_screen_rect.bottom >= SCREEN_SIZE[1]:
        for wall in walls:
            wall_screen_rect = wall.move(0, -cy)

            # Horizontal overlap
            if player_screen_rect.right > wall_screen_rect.left and player_screen_rect.left < wall_screen_rect.right:
                # Wall is above the player top and overlapping
                if wall_screen_rect.bottom > player_screen_rect.top and wall_screen_rect.top < player_screen_rect.top:
                    print("Player crushed! Game over!")
                    player.hp = 0
                    break

def despawn_present_if_offscreen():
    presents[:] = [
        p for p in presents
        if p.y - camera_y <= SCREEN_SIZE[1]
    ]


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
    # 1) achtergrond
    surface.blit(menu_bg_img, (0, 0))

    # 2) title png (center-top)
    title_rect = menu_title_img.get_rect(
    midtop=(SCREEN_SIZE[0] // 2 + TITLE_X, TITLE_Y)
    )
    surface.blit(menu_title_img, title_rect)


    # 4) buttons (zorg dat ze niet onder je controls vallen)
    start_button.draw(surface)
    settings_button.draw(surface)

    draw_tut_ui(surface, menu_controls_img)

    flip()

def render_pause():
    surface.fill((20, 20, 30))
    font = pygame.font.SysFont(None, 72)
    title_img = font.render("PAUSE", True, (255, 255, 255))
    surface.blit(title_img, title_img.get_rect(center=(SCREEN_SIZE[0]//2, 150)))
    resume_button.draw(surface)
    pause_settings_button.draw(surface)
    restart_button.draw(surface)


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

def render_settings():
    surface.fill((30, 20, 20))
    font = pygame.font.SysFont(None, 64)
    title_img = font.render("Settings", True, (255, 255, 255))
    surface.blit(title_img, title_img.get_rect(center=(SCREEN_SIZE[0]//2, 150)))

    # ✅ update button texts every frame
    toggle_keys_button.text = "Keys: ZQSD" if USE_ZQSD else "Keys: WASD"
    difficulty_button.text = f"Difficulty: {current_difficulty}"

    # draw buttons
    toggle_keys_button.draw(surface)
    difficulty_button.draw(surface)
    back_button.draw(surface)

    flip()



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
    global previous_state

    prev_ticks = pygame.time.get_ticks()  

    enemies_killed = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # shoot
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                player_shoot(player_bullets)

            # ---- MENU / SETTINGS / PAUSE BUTTONS (as you already had) ----
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
                if difficulty_button.is_clicked(event):
                    cycle_difficulty()

            elif game_state == "pause":
                if resume_button.is_clicked(event):
                    game_state = "playing"
                if pause_settings_button.is_clicked(event):
                    previous_state = game_state
                    game_state = "settings"
                if restart_button.is_clicked(event):
                    reset_game()
                    game_state = "playing"
            elif game_state == "boss_dying":
                build_walls()
                update_background()

                # update/draw effects (cinematic lives in effects[])
                for fx in effects:
                    fx.update()
                effects[:] = [fx for fx in effects if not fx.dead]

                render()

                if pygame.time.get_ticks() >= boss_death_end_time:
                    game_state = "win"


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

            # ---- PLAYING EVENTS ----
            if game_state == "playing":

                # timers MUST be here (NOT inside KEYDOWN)
                if event.type == PRESENT_EVENT:
                    spawn_present()

                if event.type == LASER_EVENT:
                    spawn_horizontal_laser()
                    pygame.time.set_timer(LASER_EVENT, random.randint(10000, 20000))

                # key handling
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        SHOW_GRID = not SHOW_GRID
                    elif event.key == pygame.K_ESCAPE:
                        game_state = "pause"
                    elif event.key == pygame.K_F1:
                        DEBUG_CAMERA = not DEBUG_CAMERA
                    elif event.key == pygame.K_LSHIFT:
                        start_dash()

                    if DEBUG_CAMERA:
                        if event.key == pygame.K_PAGEUP:
                            camera_y -= DEBUG_CAMERA_STEP
                        elif event.key == pygame.K_PAGEDOWN:
                            camera_y += DEBUG_CAMERA_STEP
                        elif event.key == pygame.K_HOME:
                            camera_y = 0
                        elif event.key == pygame.K_END:
                            camera_y = WORLD_HEIGHT - SCREEN_SIZE[1]
                        elif event.key == pygame.K_F2:
                            spot = find_debug_final_room_spot()
                            if spot:
                                player.rect.center = spot
                                camera_y = player.rect.centery - SCREEN_SIZE[1] // 2

                        camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_SIZE[1]))

        # ---- UPDATE & RENDER (runs once per frame, OUTSIDE event loop) ----
        if game_state == "menu":
            render_menu()

        elif game_state == "settings":
            render_settings()

        elif game_state == "pause":
            render_pause()

        elif game_state == "playing":
            build_walls()
            update_dash_effects()
            handle_player_movement()
            update_camera()
            check_boss_spawn()
            update_background()
            update_all()
            update_snow()

            check_present_pickup()
            despawn_present_if_offscreen()

            now_ticks = pygame.time.get_ticks()
            dt = (now_ticks - prev_ticks) / 1000.0
            prev_ticks = now_ticks
            update_walk_sway(dt)

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