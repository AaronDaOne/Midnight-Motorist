import os
import sys
import pygame as pg
import random as ra
from time import perf_counter
from imports import src

# SCREEN_SIZE = 1600, 900
SCREEN_SIZE = 1920, 1080

pg.init()

C_DEAD_ZONE = 0.2

WIN = pg.display.set_mode(SCREEN_SIZE, flags= pg.NOFRAME | pg.FULLSCREEN, vsync=1)
FPS = 120

SAVE_FOLDER_PATH = os.path.join(os.getenv("APPDATA"), "midnight-motorist")

# assets

FONT = pg.font.Font(src.FONT, SCREEN_SIZE[0]//32)

BG_SPR = pg.transform.smoothscale(pg.image.load(src.MAIN_ROAD).convert(),SCREEN_SIZE)
# CHR_SPR = pg.image.load(os.path.join("assets", "textures", "chr", "01.png"))
# CHR_SPR = pg.transform.smoothscale(CHR_SPR, pg.Vector2(CHR_SPR.get_size())*0.8)
# CHR_SPRS = [pg.transform.rotate(CHR_SPR, i*6) for i in range(60)] 
CHR_SPRS = list(
  pg.transform.smoothscale(
    pg.image.load(
      src.CHR_SPRS[i]
    ).convert_alpha(),
    (SCREEN_SIZE[0] * 0.07, SCREEN_SIZE[0] * 0.07)
  ) for i in range(20)
)
LIVES_SPR = pg.image.load(src.LIVES).convert_alpha()
NPC_F_SPR = pg.transform.smoothscale(
  pg.image.load(src.NPC).convert_alpha(),
  (SCREEN_SIZE[0] * 0.07, SCREEN_SIZE[0] * 0.07)
)
NPC_B_SPR = pg.transform.rotate(NPC_F_SPR, 180)
OVERLAY_SPR = pg.transform.smoothscale(pg.image.load(src.OVERLAY).convert_alpha(), SCREEN_SIZE)

CD1_SPR = pg.transform.smoothscale(pg.image.load(src.CD1).convert_alpha(), SCREEN_SIZE)
CD2_SPR = pg.transform.smoothscale(pg.image.load(src.CD2).convert_alpha(), SCREEN_SIZE)
CD3_SPR = pg.transform.smoothscale(pg.image.load(src.CD3).convert_alpha(), SCREEN_SIZE)
GO_SPR = pg.transform.smoothscale(pg.image.load(src.GO).convert_alpha(), SCREEN_SIZE)

TITLE_SPR = pg.transform.smoothscale(pg.image.load(src.TITLE).convert_alpha(), (SCREEN_SIZE[0], SCREEN_SIZE[1]/2))
TITLE_GLOW_SPR = pg.transform.smoothscale(pg.image.load(src.TITLE_GLOW).convert_alpha(), (SCREEN_SIZE[0], SCREEN_SIZE[1]/2))

pg.mixer.music.load(src.SFX_MUSIC)
CAR_SOUND = pg.mixer.Sound(src.SFX_DRIVE)
HIT_SOUND = pg.mixer.Sound(src.SFX_CRASH)
COUNTDOWN_SOUND = pg.mixer.Sound(src.SFX_COUNTDOWN)
GO_SOUND = pg.mixer.Sound(src.SFX_GO)

#########################

CHR_SPR_OFFSET = (pg.Vector2(CHR_SPRS[0].get_size()) / 2)
NPC_SPR_OFFSET = (pg.Vector2(NPC_F_SPR.get_size()) / 2)

CHR_SIZE = pg.Vector2(SCREEN_SIZE[0]/40, SCREEN_SIZE[1]/30)
NPC_SIZE = pg.Vector2(SCREEN_SIZE[0]/40, SCREEN_SIZE[1]/30)

#########################

CHR_MIN_POS = CHR_SIZE[0], CHR_SIZE[1] + 30
CHR_MAX_POS = SCREEN_SIZE[0]/10*8 - CHR_SIZE[0], SCREEN_SIZE[1] - CHR_SIZE[1] - 30
CHR_MOVEMENT_SPEED = 8
SPR_HIT_ROTATION_SPEED = 0.5

LIVES_X_POSES = [
  SCREEN_SIZE[0]-LIVES_SPR.get_width(),
  SCREEN_SIZE[0]-LIVES_SPR.get_width()*2,
  SCREEN_SIZE[0]-LIVES_SPR.get_width()*3,
  SCREEN_SIZE[0]-LIVES_SPR.get_width()*4,
  SCREEN_SIZE[0]-LIVES_SPR.get_width()*5
]

LIVES_Y_POS = (SCREEN_SIZE[1]/10*9.7)-LIVES_SPR.get_height()

NPC_X_SPAWN_POINT = SCREEN_SIZE[0]*1.2
NPC_Y_SPAWN_POINTS = [
  (SCREEN_SIZE[1]/20*1.2, True),
  (SCREEN_SIZE[1]/20*3, True),
  (SCREEN_SIZE[1]/20*5, True),
  (SCREEN_SIZE[1]/20*7, True),
  (SCREEN_SIZE[1]/20*9, True),
  (SCREEN_SIZE[1]/20*11, False),
  (SCREEN_SIZE[1]/20*13, False),
  (SCREEN_SIZE[1]/20*15, False),
  (SCREEN_SIZE[1]/20*17, False),
  (SCREEN_SIZE[1]/20*18.8, False)
]

class GameState:
  EXIT = 0
  START = 1
  GAME = 2
  LOST = 3

def get_high_score():
  
  if not os.path.exists(SAVE_FOLDER_PATH):
    os.mkdir(SAVE_FOLDER_PATH)

  try:
    with open(os.path.join(SAVE_FOLDER_PATH, "score"), "r") as f:
      lines = list(
        filter(
          lambda x: x,
          (x.replace("\n", "") for x in f.readlines())
        )
      )
      
      return max([int(x) for x in lines]+[0])
  
  except IndexError:
    pass

  except FileNotFoundError:
    with open(os.path.join(SAVE_FOLDER_PATH, "score"), "w") as f:
      pass

  except Exception as e:
    print(e)
    with open("error.log", "a+") as f:
      f.write(f"{e}\n")
    
  return ""

def set_high_score(score):
  if score <= 0: return

  if not os.path.exists(SAVE_FOLDER_PATH):
    os.mkdir(SAVE_FOLDER_PATH)

  with open(os.path.join(SAVE_FOLDER_PATH, "score"), "w") as f:
    f.write(f"{score}")

def get_joystick():
  if pg.joystick.get_count() > 0:
    return pg.joystick.Joystick(0)
  return  

def change_volume(amount):
  pg.mixer.music.set_volume(pg.mixer.music.get_volume()+amount)
  CAR_SOUND.set_volume(CAR_SOUND.get_volume()+amount)
  HIT_SOUND.set_volume(HIT_SOUND.get_volume()+amount)
  COUNTDOWN_SOUND.set_volume(COUNTDOWN_SOUND.get_volume()+amount)
  GO_SOUND.set_volume(GO_SOUND.get_volume()+amount)

class Npc:
  def __init__(self) -> None:
    pos = [NPC_X_SPAWN_POINT, ra.choice(NPC_Y_SPAWN_POINTS)]
    self.pos = pg.Vector2(pos[0], pos[1][0])
    self.is_forward = pos[1][1]
    self.speed = ra.randint(1,4)
    self.hitbox = get_hitbox(self.pos, NPC_SIZE)

  def update_pos(self, d_time, chr_speed):
    if self.is_forward:
      self.pos[0] -= (chr_speed - self.speed) * d_time
    else:
      self.pos[0] -= (chr_speed + self.speed) * d_time

    self.hitbox = get_hitbox(self.pos, NPC_SIZE)

def check_collision(a, b) -> bool:
  x_not_colliding = a[2] < b[0] or b[2] < a[0]
  y_not_colliding = a[3] < b[1] or b[3] < a[1]

  # 0 is length of x
  # 1 is length of y
  # 2 is length of x + size
  # 3 is length of y + size

  if x_not_colliding or y_not_colliding:
    return False
  else:
    return True

def handle_movement(pos, keys, joystick, delta):
  vel = pg.Vector2()
    
  if keys[pg.K_w]:
    vel.y -= 1
  if keys[pg.K_s]:
    vel.y += 1
  if keys[pg.K_a]:
    vel.x -= 1
  if keys[pg.K_d]:
    vel.x += 1

  if joystick != None:
    j_input = pg.Vector2(
      joystick.get_axis(pg.CONTROLLER_AXIS_LEFTX),
      joystick.get_axis(pg.CONTROLLER_AXIS_LEFTY)
    )

    if j_input.length() > C_DEAD_ZONE:
      vel = pg.Vector2()
      vel += j_input

  next_pos :pg.Vector2 = pos + (vel*CHR_MOVEMENT_SPEED * delta)

  next_pos.x = max(min(next_pos.x, CHR_MAX_POS[0]), CHR_MIN_POS[0])
  next_pos.y = max(min(next_pos.y, CHR_MAX_POS[1]), CHR_MIN_POS[1])

  return next_pos

def get_hitbox(pos, size):
  return *(pos - size), pos[0] + size[0], pos[1] + size[1]

def draw(chr_loc, bg_scroll, npc_list:list[Npc], speed_txt, score_txt, hitbox, fps_txt, lives, spr_hit_count):
  WIN.blit(BG_SPR,(bg_scroll,0))
  WIN.blit(BG_SPR,(bg_scroll+SCREEN_SIZE[0],0))

  for npc in npc_list:
    WIN.blit(NPC_F_SPR if npc.is_forward else NPC_B_SPR, npc.pos - NPC_SPR_OFFSET)
    # pg.draw.rect(WIN, (0, 255, 0), pg.Rect(*npc.hitbox[:2], (npc.hitbox[2]-npc.pos[0])*2, (npc.hitbox[3]-npc.pos[1])*2))
    # pg.draw.circle(WIN, (0, 255, 255), npc.pos, 10)

  # pg.draw.rect(WIN, (255, 0, 0), pg.Rect(*hitbox[:2], (hitbox[2] - chr_loc[0])*2, (hitbox[3]-chr_loc[1])*2))
  WIN.blit(
    CHR_SPRS[int(spr_hit_count)],
    chr_loc - CHR_SPR_OFFSET
  )
  # pg.draw.circle(WIN, (255, 255, 255), chr_loc, 20)

  for n in range(lives):
    WIN.blit(LIVES_SPR, (LIVES_X_POSES[n], LIVES_Y_POS))

  WIN.blit(speed_txt, (0, 30))
  WIN.blit(score_txt, (0, SCREEN_SIZE[1]-112))

  # WIN.blit(fps_txt, (SCREEN_SIZE[0]-120, 30))

  WIN.blit(OVERLAY_SPR, (0, 0))

  pg.display.update()


def game_loop(chr_pos: pg.Vector2, bg_scroll: float):
  state = GameState.GAME
  CLOCK = pg.time.Clock()

  # character state
  player_hitbox = get_hitbox(chr_pos, CHR_SIZE)
  chr_speed = 1
  score = 0
  lives = 5
  lost = not lives
  spr_hit_count = 0
  hit_spin_count = -1

  bg_scroll
  npc_list : list[Npc] = []
  npc_timer = 0
  
  score_txt = FONT.render("0", False, (255, 255, 255))
  fps_txt = FONT.render("0", False, (255, 255, 255))
  speed_txt = FONT.render(str(int(chr_speed*10)), False, (255, 255, 255))

  pg.mixer.music.set_volume(0.5)
  CAR_SOUND.set_volume(0.5)
  HIT_SOUND.set_volume(0.5)

  pg.mixer.music.play(loops=-1)
  CAR_SOUND.play(loops=-1)

  while state == GameState.GAME:
    d_time = CLOCK.tick(FPS)
    d_movement = d_time / 16
    joystick = get_joystick()

    if joystick != None:
      if joystick.get_button(6):
        state = GameState.START

    for e in pg.event.get():
      match e.type:
        
        case pg.KEYDOWN:
          
          match e.key:
            case pg.K_UP:
              change_volume(0.05)

            case pg.K_DOWN:
              change_volume(-0.05)

            case pg.K_F2:
              state = GameState.START

            case pg.K_F11:
              pg.display.toggle_fullscreen()
            
            case pg.K_ESCAPE:
              state = GameState.EXIT

    keys_pressed = pg.key.get_pressed()
    chr_pos = handle_movement(chr_pos, keys_pressed, joystick, d_movement)
    player_hitbox = get_hitbox(chr_pos, CHR_SIZE)

    # npc spawner
    if npc_timer > 200 / chr_speed:
      npc_list.append(Npc())
      npc_timer = 0
    else:
      npc_timer += 1 * d_movement

    # handle npc list
    for n, npc in enumerate(npc_list):
      npc.update_pos(d_movement, chr_speed)
      if npc.pos[0] < -500:
        npc_list.pop(n)
      # got hit
      # elif npc.check_player_collision(player_hitbox):
      elif check_collision(player_hitbox, npc.hitbox):
        npc_list.pop(n)
        chr_speed = 1
        lives -= 1
        HIT_SOUND.play()
        if not lives:
          state = GameState.LOST
          break
        else:
          hit_spin_count = 0

    # handle hit sprite rotation
    if hit_spin_count == 2:
      hit_spin_count = -1
      spr_hit_count = 0
    
    elif hit_spin_count != -1:
      spr_hit_count += (SPR_HIT_ROTATION_SPEED * d_movement)
  
      if spr_hit_count >= len(CHR_SPRS):
        hit_spin_count += 1
        spr_hit_count = 0

    # handle chr_speed / background scroll value
    if chr_speed < 15:
      chr_speed += 0.03 * d_movement
    elif chr_speed < 20:
      chr_speed += 0.008 * d_movement
      score += 1
    else:
      score += 2

    # scroll the background
    if bg_scroll < -SCREEN_SIZE[0]:
      bg_scroll = 0
    else:
      bg_scroll -= chr_speed * d_movement
    
    # texts
    score_txt = FONT.render(f"SCORE: {score}", False, (255, 255, 255))
    fps_txt = FONT.render(str(1000 // d_time), False, (255, 255, 255))
    speed_txt = FONT.render(f"{int(chr_speed*10)} MPH", False, (255, 255, 255))

    draw(chr_pos, bg_scroll, npc_list, speed_txt, score_txt, player_hitbox, fps_txt, lives, spr_hit_count)
    # print(f"FPS: {int(1000 / d_time)}" ,end="\r")
  
  pg.mixer.music.stop()
  CAR_SOUND.stop()
  
  return state, chr_pos, score

###############################################################################################################

def pre_game_draw(chr_loc, bg_scroll, countdown, high_score):
  WIN.blit(BG_SPR,(bg_scroll,0))
  WIN.blit(BG_SPR,(bg_scroll+SCREEN_SIZE[0],0))

  WIN.blit(CHR_SPRS[0], chr_loc - (pg.Vector2(CHR_SPRS[0].get_size()) / 2))

  if countdown > 3:
    WIN.blit(GO_SPR, (0, 0))
    WIN.blit(FONT.render(f"0 MPH", False, (255, 255, 255)), (0, 30))
    WIN.blit(FONT.render(f"SCORE: 0", False, (255, 255, 255)), (0, SCREEN_SIZE[1]-112))
    for i in LIVES_X_POSES:
      WIN.blit(LIVES_SPR, (i, LIVES_Y_POS))
  elif countdown > 2:
    WIN.blit(CD1_SPR, (0, 0))
  elif countdown > 1:
    WIN.blit(CD2_SPR, (0, 0))
  elif countdown > 0:
    WIN.blit(CD3_SPR, (0, 0))
  else:
    WIN.blit(TITLE_GLOW_SPR, (0, -120))
    WIN.blit(TITLE_SPR, (0, -120))
    WIN.blit(high_score, (0, SCREEN_SIZE[1]-112))
    WIN.blit(FONT.render(f"Made by @AaronDaOne", False, (255, 255, 255)), (SCREEN_SIZE[0]/10*5.8, SCREEN_SIZE[1]-112))
    if int(perf_counter() % 1.5) == 0:
      WIN.blit(FONT.render(f"Press SPACE to Start", False, (255, 255, 255)), (SCREEN_SIZE[0]/10*3, SCREEN_SIZE[1]/10*8.15))



  WIN.blit(OVERLAY_SPR, (0, 0))

  pg.display.update()

def pre_game_loop(chr_pos: pg.Vector2):
  state = GameState.START
  CLOCK = pg.time.Clock()

  bg_scroll = 0

  counting_down = False
  countdown = 0

  played_cd0 = played_cd1 = played_cd2 = played_cd3 = False

  HIGH_SCORE = FONT.render("HIGH SCORE: " + str(get_high_score()).zfill(1), False, (255, 255, 255))

  while state == GameState.START:
    d_time = CLOCK.tick_busy_loop(FPS)
    d_movement = d_time / 16
    joystick = get_joystick()

    if joystick != None:
      if joystick.get_button(7):
        # Start
        counting_down = True

    for e in pg.event.get():
      match e.type:

        case pg.KEYDOWN:
          match e.key:

            case pg.K_SPACE:
              # Start
              counting_down = True

            case pg.K_UP:
              change_volume(0.05)

            case pg.K_DOWN:
              change_volume(-0.05)

            case pg.K_F11:
              pg.display.toggle_fullscreen()
          
            case pg.K_ESCAPE:
              state = GameState.EXIT
              break

    keys_pressed = pg.key.get_pressed()
    chr_pos = handle_movement(chr_pos, keys_pressed, joystick, d_movement)

    if bg_scroll < -SCREEN_SIZE[0]:
      bg_scroll = 0
    else:
      bg_scroll -= d_movement * 2

    # countdown
    if counting_down:
        countdown += d_time / 1000
        if not played_cd0:
          COUNTDOWN_SOUND.play()
          played_cd0 = True
        elif countdown > 1 and not played_cd1:
          COUNTDOWN_SOUND.play()
          played_cd1 = True
        elif countdown > 2 and not played_cd2:
          COUNTDOWN_SOUND.play()
          played_cd2 = True
        elif countdown > 3 and not played_cd3:
          GO_SOUND.play()
          played_cd3 = True
          CAR_SOUND.play(-1)
        elif countdown > 4:
          counting_down = False
          state = GameState.GAME
          CAR_SOUND.stop()

    pre_game_draw(chr_pos, bg_scroll, countdown, HIGH_SCORE)
  
  return state, chr_pos, bg_scroll

def main():
  state = GameState.START
  chr_pos = pg.Vector2(ra.randint(CHR_MIN_POS[0], CHR_MAX_POS[0]), ra.randint(CHR_MIN_POS[1], CHR_MAX_POS[1]))
  bg_scroll = 0
  score = 0

  while state != GameState.EXIT:
    
    if state == GameState.START:
      state, chr_pos, bg_scroll = pre_game_loop(chr_pos=chr_pos)
    
    if state == GameState.GAME:
      state, chr_pos, score = game_loop(chr_pos, bg_scroll)

    if state == GameState.LOST:
      if score > get_high_score():
        set_high_score(score)
      score = 0
      state = GameState.START

if __name__ == "__main__":
  main()
