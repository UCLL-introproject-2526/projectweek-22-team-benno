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
#.............##
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
#............###
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

present_img = pygame.image.load("images/present1.png").convert_alpha()
present_img = pygame.transform.scale(present_img, (PRESENT_SIZE, PRESENT_SIZE))

# =====================
# WORLD + CAMERA
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
# LOOPED WALLS GENERATOR
# =====================
def iter_looped_walls():
    base = int(camera_y // WORLD_HEIGHT)
    for i in range(base - 1, base + 2):
        offset_y = i * WORLD_HEIGHT
        for wall in walls:
            yield wall.move(0, offset_y)

# =====================
# HELPERS
# =====================
def normalize(vx, vy):
    d = math.hypot(vx, vy)
    if d < 1e-6:
        return 0.0, 0.0
    return vx / d, vy / d

def rotate_image_to_velocity(img, vx, vy):
    angle = -math.degrees(math.atan2(vy, vx))
    return pygame.transform.rotate(img, angle)

def draw_text(surf, text, x, y, size=26):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, (240, 240, 240))
    surf.blit(img, (x, y))

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
# MOVEMENT + COLLISION (PLAYER)
# =====================
def move_rect_with_walls(rect: pygame.Rect, dx: int, dy: int):
    rect.x += dx
    for w in iter_looped_walls():
        if rect.colliderect(w):
            if dx > 0: rect.right = w.left
            elif dx < 0: rect.left = w.right
    rect.y += dy
    for w in iter_looped_walls():
        if rect.colliderect(w):
            if dy > 0: rect.bottom = w.top
            elif dy < 0: rect.top = w.bottom

def handle_player_movement():
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * player_speed
    dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * player_speed
    move_rect_with_walls(player.rect, dx, dy)

# =====================
# BULLET
# =====================
class Bullet:
    def __init__(self, x, y, vx, vy, owner, base_image):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.owner = owner
        self.spawn_time = pygame.time.get_ticks()
        self.alive = True
        self.image = rotate_image_to_velocity(base_image, self.vx, self.vy)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self):
        if not self.alive: return
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
        if not WORLD_RECT.collidepoint(self.rect.center): self.alive = False
        if pygame.time.get_ticks() - self.spawn_time > BULLET_LIFETIME_MS: self.alive = False
        for w in walls:
            if self.rect.colliderect(w): self.alive = False

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
        self.rect.x += dx
        hit_x = False
        for w in walls:
            if self.rect.colliderect(w):
                hit_x=True
                self.rect.right = w.left if dx>0 else self.rect.right
                self.rect.left = w.right if dx<0 else self.rect.left
        if hit_x: self.vx*=-1
        self.rect.y += dy
        hit_y=False
        for w in walls:
            if self.rect.colliderect(w):
                hit_y=True
                self.rect.bottom = w.top if dy>0 else self.rect.bottom
                self.rect.top = w.bottom if dy<0 else self.rect.top
        if hit_y: self.vy*=-1
        self.rect.clamp_ip(WORLD_RECT)

    def shoot_at(self,target_pos,bullet_list):
        tx,ty=target_pos
        sx,sy=self.rect.center
        nx,ny=normalize(tx-sx,ty-sy)
        bullet_list.append(Bullet(sx,sy,nx*BULLET_SPEED,ny*BULLET_SPEED,"enemy",enemy_bullet_img_base))

    def update(self,target_pos,bullet_list):
        self.vx += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)
        self.vy += random.uniform(-ENEMY_WANDER_JITTER, ENEMY_WANDER_JITTER)
        tx,ty=target_pos
        cx,cy=self.rect.center
        nx,ny=normalize(tx-cx,ty-cy)
        self.vx += nx*0.08
        self.vy += ny*0.08
        sp = math.hypot(self.vx,self.vy)
        if sp>ENEMY_SPEED:
            self.vx = (self.vx/sp)*ENEMY_SPEED
            self.vy = (self.vy/sp)*ENEMY_SPEED
        self.move_and_collide(int(round(self.vx)), int(round(self.vy)))
        now = pygame.time.get_ticks()
        if now - self.last_shot >= ENEMY_SHOOT_COOLDOWN_MS:
            self.last_shot = now
            self.shoot_at(target_pos, bullet_list)

# =====================
# SPAWN ENEMY
# =====================
def spawn_enemy(enemies_list):
    spawn_y = max(0, int(camera_y)-TILE_SIZE)
    tries=120
    while tries>0:
        tries-=1
        x=random.randint(0,WORLD_WIDTH-ENEMY_SIZE)
        y_low=spawn_y
        y_high=min(spawn_y+TILE_SIZE*3,WORLD_HEIGHT-ENEMY_SIZE)
        if y_high<y_low:y_low,y_high=0,WORLD_HEIGHT-ENEMY_SIZE
        y=random.randint(y_low,y_high)
        e=Enemy(x,y)
        if any(e.rect.colliderect(w) for w in walls): continue
        enemies_list.append(e)
        return

# =====================
# PRESENTS
# =====================
def spawn_present():
    global present_rect
    if present_rect is not None: return
    tries=100
    while tries>0:
        tries-=1
        x=random.randint(0,WORLD_WIDTH-PRESENT_SIZE)
        y=random.randint(0,WORLD_HEIGHT-PRESENT_SIZE)
        rect = pygame.Rect(x,y,PRESENT_SIZE,PRESENT_SIZE)
        if any(rect.colliderect(w) for w in walls): continue
        present_rect = rect
        show_fade_text("Present spawned")
        return

def check_present_pickup():
    global present_rect, present_count
    if present_rect and player.rect.colliderect(present_rect):
        present_rect = None
        present_count += 1

# =====================
# SHOOT PLAYER
# =====================
def player_shoot(player_bullets):
    now=pygame.time.get_ticks()
    if now - player.last_shot < PLAYER_SHOOT_COOLDOWN_MS: return
    player.last_shot = now
    mx,my = pygame.mouse.get_pos()
    tx,ty = mx, my + camera_y
    sx,sy = player.rect.center
    nx,ny = normalize(tx-sx, ty-sy)
    player_bullets.append(Bullet(sx,sy,nx*BULLET_SPEED,ny*BULLET_SPEED,"player",player_bullet_img_base))

# =====================
<<<<<<< Updated upstream
<<<<<<< Updated upstream
# MOVEMENT + COLLISION (PLAYER)
# =====================




def handle_player_movement():
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * player_speed
    dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * player_speed

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
=======
# CAMERA (NORMAAL)
>>>>>>> Stashed changes
=======
# CAMERA (NORMAAL)
>>>>>>> Stashed changes
# =====================
def update_camera():
    global camera_y
    camera_y -= scroll_speed
    # geen modulo, camera kan normaal omhoog scrollen

# =====================
# GRID
# =====================
def draw_grid(surf):
    if not SHOW_GRID: return
    w,h = surf.get_size()
    start_y = -(camera_y % TILE_SIZE)
    x=0
    while x<=w:
        pygame.draw.line(surf,(50,50,50),(x,0),(x,h))
        x+=TILE_SIZE
    y=start_y
    while y<=h:
        pygame.draw.line(surf,(50,50,50),(0,y),(w,y))
        y+=TILE_SIZE

# =====================
# GAME STATE
# =====================
enemies=[]
enemy_bullets=[]
player_bullets=[]
SPAWN_EVENT=pygame.USEREVENT+1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL_MS)
game_over=False
death_stats={}

# =====================
# UPDATE ALL
# =====================
def update_all():
    player_center = player.rect.center
    for e in enemies: e.update(player_center, enemy_bullets)
    for b in enemy_bullets: b.update()
    for b in player_bullets: b.update()
    for b in enemy_bullets:
        if b.alive and b.rect.colliderect(player.rect):
            b.alive=False
            player.hp -= 1
    for b in player_bullets:
        if not b.alive: continue
        for e in enemies:
            if b.rect.colliderect(e.rect):
                enemies.remove(e)
                b.alive=False
                break
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    player_bullets[:] = [b for b in player_bullets if b.alive]
    check_present_pickup()

# =====================
# RENDER
# =====================
def render():
    surface.fill((0,0,0))

    # Walls herhalen visueel
    num_repeats = (SCREEN_SIZE[1] // WORLD_HEIGHT) + 2
    for i in range(num_repeats):
        offset_y = i * WORLD_HEIGHT - camera_y
        for w in walls:
            sr = w.move(0, offset_y)
            if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
                pygame.draw.rect(surface, (120,120,120), sr)

    draw_grid(surface)

    # Enemies
    for e in enemies:
        sr = e.rect.move(0, -camera_y)
        if sr.bottom >= 0 and sr.top <= SCREEN_SIZE[1]:
            pygame.draw.rect(surface,(200,60,60),sr,border_radius=6)

    # Bullets
    for b in enemy_bullets + player_bullets:
        b_screen_y = b.rect.y - camera_y
        if -100 <= b_screen_y <= SCREEN_SIZE[1]+100:
            surface.blit(b.image,(b.rect.x,b_screen_y))

    # Present
    if present_rect:
        p_screen_y = present_rect.y - camera_y
        if -100 <= p_screen_y <= SCREEN_SIZE[1]+100:
            surface.blit(present_img,(present_rect.x,p_screen_y))

    # Player
    p_screen_y = player.rect.y - camera_y
    surface.blit(player_img,(player.rect.x,p_screen_y))

    # UI
    draw_text(surface,f"HP: {player.hp}",12,10)
    draw_text(surface,f"Enemies: {len(enemies)}/{MAX_ENEMIES}",12,34)
    draw_text(surface,f"Presents: {present_count}",12,58)
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
                    pygame.quit()
                    exit()


# =====================
# MAIN LOOP
# =====================
def main():
    global SHOW_GRID, game_over, death_stats
    enemies_killed = 0
    while True:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                exit()
<<<<<<< Updated upstream
<<<<<<< Updated upstream

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
        # update_enemies()
        # render_frame(surface)
=======
=======
>>>>>>> Stashed changes
            if not game_over:
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_g: SHOW_GRID=not SHOW_GRID
                    if event.key==pygame.K_SPACE: player_shoot(player_bullets)
                if event.type==SPAWN_EVENT:
                    if len(enemies)<MAX_ENEMIES: spawn_enemy(enemies)
                if event.type==PRESENT_EVENT: spawn_present()
        if not game_over:
            handle_player_movement()
            update_camera()
            update_all()
            enemies_killed = MAX_ENEMIES - len(enemies)
            render()
            if player.hp<=0:
                game_over=True
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        clock.tick(60)

main()
