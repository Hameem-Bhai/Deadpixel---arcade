import pygame
import sys
import random
import time
import os, json, wave, struct  # new imports for persistence & audio synthesis
import math  # added for animations
from typing import Any, Dict  # typing for clearer color dict

# =====================================================================
# Hameem's Gaming Zone - Zombie Apocalypse Edition
# Local 2‑Player Mini Game Collection with ZOMBIE THEME!
# Show this to friends: spooky, fun, replayable zombie games.
# Features:
#   - Main Menu / Name Entry / Game Select Hub
#   - 5 Mini-Games (Reaction Duel, Timing Duel, Lantern Chase Arena, Pong, Snake)
#   - Local 2 Player controls
#   - Particle effects + animated transitions
#   - Scoreboard & persistent match stats (session)
#   - ZOMBIE APOCALYPSE THEME with dark colors and blood effects
#   - Clear comments for learning
# =====================================================================

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()  # Initialize pygame
WIDTH, HEIGHT = 1200, 800  # Big window for showcase
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hameem's Gaming Zone - Zombie Edition")
clock = pygame.time.Clock()
FPS = 120  # Smooth responsiveness

# ---------------- Zombie Theme Colors -----------------
WHITE=(255,255,255); BLACK=(0,0,0); GRAY=(45,45,55)
BLOOD_RED=(180,20,20); DARK_BLOOD=(90,10,10)  # Zombie blood colors
TOXIC_GREEN=(100,255,100); DARK_GREEN=(40,120,50)  # Toxic waste green
FLESH=(220,180,140); ROTTEN_FLESH=(140,120,80)  # Zombie skin tones
BONE=(230,230,210); DARK_BONE=(150,150,130)  # Bone colors
ZOMBIE_PURPLE=(100,50,120); NIGHT_SKY=(20,20,40)  # Dark atmosphere
BRAIN_PINK=(255,100,150); DARK_GRAY=(30,30,30)  # Brain and shadows
# Keep some original colors for compatibility
BLUE=(80,130,210); DARK_BLUE=(40,70,140)
GREEN=(70,190,80); RED=(220,60,60); DARK_RED=(150,30,30)
GOLD=(240,200,70); ORANGE=(255,140,40)
PURPLE=(150,70,200); CYAN=(70,220,220)

# ---------------- Fonts (dynamic with UI scale) ------------------
BASE_FONT_SIZES = {
    'TITLE':72,
    'SUB':48,
    'UI':36,
    'TEXT':30,
    'SMALL':22
}
FONT_TITLE=pygame.font.Font(None, BASE_FONT_SIZES['TITLE']); FONT_SUB=pygame.font.Font(None, BASE_FONT_SIZES['SUB']); FONT_UI=pygame.font.Font(None, BASE_FONT_SIZES['UI']); FONT_TEXT=pygame.font.Font(None, BASE_FONT_SIZES['TEXT']); FONT_SMALL=pygame.font.Font(None, BASE_FONT_SIZES['SMALL'])

def rebuild_fonts():
    global FONT_TITLE, FONT_SUB, FONT_UI, FONT_TEXT, FONT_SMALL
    scale = getattr(settings, 'ui_scale', 1.0)
    FONT_TITLE = pygame.font.Font(None, int(BASE_FONT_SIZES['TITLE']*scale))
    FONT_SUB   = pygame.font.Font(None, int(BASE_FONT_SIZES['SUB']*scale))
    FONT_UI    = pygame.font.Font(None, int(BASE_FONT_SIZES['UI']*scale))
    FONT_TEXT  = pygame.font.Font(None, int(BASE_FONT_SIZES['TEXT']*scale))
    FONT_SMALL = pygame.font.Font(None, int(BASE_FONT_SIZES['SMALL']*scale))

# ---------------- Particle System (simple) ------------------
class Particle:
    def __init__(self, x, y, color):
        self.x = x; self.y = y
        self.radius = random.randint(4,9)
        self.color = color
        self.vx = random.uniform(-1.5,1.5)
        self.vy = random.uniform(-2.5, -0.5)
        self.life = random.uniform(0.7,1.4)
        self.spawn = time.time()
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.04  # gravity
    def draw(self, surf):
        age = time.time() - self.spawn
        if age > self.life: return
        alpha = max(0, 255 - int((age/self.life)*255))
        s = pygame.Surface((self.radius*2,self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.radius,self.radius), self.radius)
        surf.blit(s, (self.x-self.radius, self.y-self.radius))
    def dead(self):
        return time.time() - self.spawn > self.life

particles = []  # Global particle list for flourish

def spawn_burst(x,y,color,count=16):
    for _ in range(count): particles.append(Particle(x,y,color))

# ---------------- Button UI ----------------
class Button:
    def __init__(self, rect, label, callback, base=BLUE, hover=DARK_BLUE, key=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.cb = callback
        self.base, self.hover, self.key = base, hover, key
    def handle(self, e):
        clicked = e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos)
        shortcut = e.type == pygame.KEYDOWN and self.key is not None and e.key == self.key
        if clicked or shortcut:
            if settings.sound_enabled and _click_sound is not None:
                _click_sound.play()
            self.cb()
    def draw(self, surf):
        over = self.rect.collidepoint(pygame.mouse.get_pos())
        dark = settings.current_theme != 'arcade'
        fill = (29, 39, 54) if dark else (231, 239, 250)
        if over:
            fill = tuple(int(fill[i] * .72 + self.base[i] * .28) for i in range(3))
        pygame.draw.rect(surf, (5, 8, 14), self.rect.move(0, 5), border_radius=14)
        pygame.draw.rect(surf, fill, self.rect, border_radius=14)
        pygame.draw.rect(surf, self.base if over else (80, 94, 115), self.rect, 2 if over else 1, border_radius=14)
        pygame.draw.rect(surf, self.base, (self.rect.x + 12, self.rect.y + 13, 4, self.rect.height - 26), border_radius=2)
        font = FONT_UI
        size = FONT_UI.get_height()
        while font.size(self.label)[0] > self.rect.width - 45 and size > 16:
            size -= 1
            font = pygame.font.Font(None, size)
        label = font.render(self.label, True, BONE if dark else (25, 38, 60))
        surf.blit(label, label.get_rect(center=self.rect.center))


# ---------------- Global Session Stats ----------------
class SessionStats:
    def __init__(self):
        self.reaction_wins = {1:0,2:0}
        self.timing_wins = {1:0,2:0}
        self.lantern_points = {1:0,2:0}  # cumulative points across matches
        self.pong_wins = {1:0,2:0}       # added for Pong
        self.snake_wins = {1:0,2:0}      # added for 2-player Snake
        self.yatzy_wins = {1:0,2:0,3:0,4:0}  # Yahtzee wins (4 players)
        self.racing_wins = {1:0,2:0,3:0,4:0}  # Racing wins (up to 4 players)
    def reset(self):
        self.__init__()

stats = SessionStats()

# ---------------- Settings ----------------
class GameSettings:
    def __init__(self):
        self.touch_enabled = True
        self.num_players = 2
        self.current_theme = "zombie"
        self.lock_theme = False  # if True, do not auto-change theme
        self.ui_scale = 1.0
        self.sound_enabled = True
        # theme transition
        self.transition_active=False
        self.transition_start=0.0
        self.transition_duration=1.2
        self.transition_from=None
        self.transition_to=None
    def start_transition(self, new_theme):
        self.transition_active=True
        self.transition_start=time.time()
        self.transition_from=self.current_theme
        self.transition_to=new_theme
        self.current_theme=new_theme
    def update_theme(self):
        # Auto theme only when not locked
        if self.lock_theme:
            return
        old=self.current_theme
        if self.num_players == 2: new="zombie"
        elif self.num_players == 3: new="wasteland"
        else: new="apocalypse"
        if new!=old: self.start_transition(new)
    def cycle_scale(self):
        opts=[0.85,1.0,1.25]; idx=opts.index(self.ui_scale) if self.ui_scale in opts else 1
        self.ui_scale=opts[(idx+1)%len(opts)]
        rebuild_fonts(); save_settings()
        #print("Settings saved:", self.__dict__)

settings = GameSettings()

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')

def save_settings():
    data={
        "touch_enabled":settings.touch_enabled,
        "num_players":settings.num_players,
        "ui_scale":settings.ui_scale,
        "sound_enabled":settings.sound_enabled,
        "current_theme":settings.current_theme,
        "lock_theme":settings.lock_theme
    }
    try:
        with open(SETTINGS_PATH,'w') as f: json.dump(data,f)
    except Exception: pass

def load_settings():
    try:
        with open(SETTINGS_PATH,'r') as f:
            data=json.load(f)
        settings.touch_enabled=data.get('touch_enabled',True)
        settings.num_players=data.get('num_players',2)
        settings.sound_enabled=data.get('sound_enabled',True)
        settings.ui_scale=float(data.get('ui_scale',1.0))
        settings.current_theme=data.get('current_theme', settings.current_theme)
        settings.lock_theme=bool(data.get('lock_theme', False))
        settings.update_theme()
    except Exception: pass

load_settings(); rebuild_fonts()
if settings.num_players < 2 or settings.num_players > 4:
    settings.num_players = 2
    save_settings()

# ---------------- Theme Color System ----------------
def blend(c1,c2,t):
    return tuple(int(c1[i]*(1-t)+c2[i]*t) for i in range(3))

def get_theme_colors() -> Dict[str, Any]:
    base_map: Dict[str, Dict[str, Any]]={
        'zombie':{
            'player_colors':[BLOOD_RED,TOXIC_GREEN],
            'bg_primary':(8,12,18),'bg_secondary':(15,20,25),
            'accent':TOXIC_GREEN,'danger':BLOOD_RED,
            'title':BLOOD_RED,'subtitle':TOXIC_GREEN
        },
        'wasteland':{
            'player_colors':[BLOOD_RED,TOXIC_GREEN,ZOMBIE_PURPLE],
            'bg_primary':(10,15,10),'bg_secondary':(20,30,20),
            'accent':(150,255,100),'danger':(200,50,50),
            'title':(150,255,100),'subtitle':ZOMBIE_PURPLE
        },
        'apocalypse':{
            'player_colors':[BLOOD_RED,TOXIC_GREEN,BRAIN_PINK,ZOMBIE_PURPLE],
            'bg_primary':(12,8,18),'bg_secondary':(25,15,35),
            'accent':BRAIN_PINK,'danger':BLOOD_RED,
            'title':BRAIN_PINK,'subtitle':(180,100,255)
        },
        'arcade':{ # Apple Arcade-inspired
            'player_colors':[(78,109,255),(80,220,176),(255,159,64),(255,105,97)],
            'bg_primary':(232,246,255),  # light top
            'bg_secondary':(199,232,255), # deeper bottom
            'accent':(62,120,255),
            'danger':(255,92,92),
            'title':(40,90,240),
            'subtitle':(90,170,255)
        }
    }
    cur={k:(v[:] if isinstance(v,list) else v) for k,v in base_map[settings.current_theme].items()}
    if settings.transition_active and settings.transition_from and settings.transition_to:
        t=(time.time()-settings.transition_start)/settings.transition_duration
        if t>=1.0:
            settings.transition_active=False
        else:
            frm=base_map[settings.transition_from]; to=base_map[settings.transition_to]
            cur['bg_primary']=blend(frm['bg_primary'],to['bg_primary'],t)  # type: ignore
            cur['bg_secondary']=blend(frm['bg_secondary'],to['bg_secondary'],t)  # type: ignore
            cur['accent']=blend(frm['accent'],to['accent'],t)  # type: ignore
            cur['title']=blend(frm['title'],to['title'],t)  # type: ignore
            cur['subtitle']=blend(frm['subtitle'],to['subtitle'],t)  # type: ignore
    return cur
# Audio synthesis ---------------------------------------------------
pygame.mixer.pre_init(22050,-16,1,512)
try:
    pygame.mixer.init()
except Exception:
    pass
AUDIO_READY = pygame.mixer.get_init() is not None
_dice_sound=None; _click_sound=None

def synth_noise(path, length_sec=0.35, volume=0.5, bursts=3):
    if not AUDIO_READY: return None
    if os.path.exists(path):
        try: return pygame.mixer.Sound(path)
        except Exception: pass
    try:
        fr=22050; frames=int(fr*length_sec)
        data=[]
        for i in range(frames):
            # Base amplitude decays over time
            amp = float(volume) * (1.0 - (i/frames))
            # Occasional impact bursts (but don't exceed 1.0 total)
            if bursts:
                period = max(1, frames//max(1, bursts))
                if (i % period) < 120:
                    amp *= 1.8  # gentle boost
            # Clamp amplitude to [-1.0, 1.0]
            amp = max(0.0, min(1.0, amp))
            s = random.uniform(-1.0, 1.0) * amp
            # Convert to 16-bit and clamp to valid range
            sample_int = int(max(-1.0, min(1.0, s)) * 32767)
            data.append(struct.pack('<h', sample_int))
        with wave.open(path,'w') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(fr)
            w.writeframes(b''.join(data))
        return pygame.mixer.Sound(path)
    except Exception:
        # If anything goes wrong, disable this sound gracefully
        return None

if AUDIO_READY:
    _dice_sound=synth_noise(os.path.join(os.path.dirname(__file__),'dice_roll.wav'))
    _click_sound=synth_noise(os.path.join(os.path.dirname(__file__),'click.wav'),length_sec=0.18,volume=0.35,bursts=1)

# ---------------- Player Data ----------------
class PlayerInfo:
    def __init__(self, pid, name="Player"):
        self.id = pid
        self.name = name
        # Controls (split-keyboard): Player1 uses WASD + F; Player2 uses Arrow keys + RCTRL
        # Player3 uses TFGH + R; Player4 uses IJKL + U
        if pid == 1:
            self.up=pygame.K_w; self.down=pygame.K_s; self.left=pygame.K_a; self.right=pygame.K_d; self.action=pygame.K_f
        elif pid == 2:
            self.up=pygame.K_UP; self.down=pygame.K_DOWN; self.left=pygame.K_LEFT; self.right=pygame.K_RIGHT; self.action=pygame.K_RCTRL
        elif pid == 3:
            self.up=pygame.K_t; self.down=pygame.K_b; self.left=pygame.K_v; self.right=pygame.K_n; self.action=pygame.K_r
        else:  # pid == 4
            self.up=pygame.K_i; self.down=pygame.K_k; self.left=pygame.K_j; self.right=pygame.K_l; self.action=pygame.K_u

players = {1: PlayerInfo(1, "Survivor1"), 2: PlayerInfo(2, "Survivor2"), 3: PlayerInfo(3, "Survivor3"), 4: PlayerInfo(4, "Survivor4")}

# ---------------- Scene System ----------------
class Scene:
    def __init__(self): self.buttons=[]
    def enter(self): self.buttons=[]
    def exit(self): pass
    def update(self, dt): pass
    def draw(self,surf): pass
    def handle(self,e):
        for b in self.buttons: b.handle(e)

current_scene = None
show_help = False  # define early

def set_scene(scene_obj):
    global current_scene
    if current_scene: current_scene.exit()
    current_scene = scene_obj
    if current_scene: current_scene.enter()

def quit_game():
    save_settings(); pygame.quit(); sys.exit(0)

def get_player_color(pid:int):
    theme=get_theme_colors(); return theme['player_colors'][min(pid-1,len(theme['player_colors'])-1)]

def go_scene(name: str):
    cls = globals().get(name)
    if cls:
        fade.start(cls())

class YatzyResult(Scene):
    def __init__(self, scores, num_players):
        super().__init__(); self.scores=scores; self.num_players=num_players
        self.totals={}
        for pid in range(1,num_players+1):
            upper=sum(v for k,v in scores[pid].items() if k in ['ones','twos','threes','fours','fives','sixes'] and v is not None)
            total=sum(v for v in scores[pid].values() if v is not None) + (35 if upper>=63 else 0)
            self.totals[pid]=total
        self.winner=max(self.totals,key=self.totals.get)
    def enter(self):
        # increment stats for winner once entering result scene
        if hasattr(stats,'yatzy_wins') and self.winner in stats.yatzy_wins:
            stats.yatzy_wins[self.winner]+=1
        self.buttons=[Button((WIDTH//2-160, HEIGHT-140, 320, 60), 'Back Hub', lambda: go_scene('GameHub'), TOXIC_GREEN, DARK_GREEN, pygame.K_RETURN)]
    def draw(self,surf):
        theme=get_theme_colors(); surf.fill(theme['bg_primary'])
        center_text(surf,'YATZY FINAL', FONT_TITLE, 100, theme['title'])
        center_text(surf,f'Winner: {players[self.winner].name}', FONT_SUB, 180, get_player_color(self.winner))
        y=260
        for pid,total in sorted(self.totals.items(), key=lambda kv: kv[1], reverse=True):
            upper=sum(v for k,v in self.scores[pid].items() if k in ['ones','twos','threes','fours','fives','sixes'] and v is not None)
            bonus=' +35' if upper>=63 else ''
            line=f"{players[pid].name}: {total}{bonus}"; txt=FONT_UI.render(line,True,get_player_color(pid)); surf.blit(txt,(WIDTH//2 - txt.get_width()//2, y)); y+=48
        center_text(surf,'ENTER to return', FONT_SMALL, y+30, BONE)
        for b in self.buttons: b.draw(surf)

# ---------------- Fade Transition Class ----------------
class Fade:
    def __init__(self):
        self.active = False
        self.t = 0.0
        self.duration = 0.4
        self.next = None
        self.switched = False
    def start(self, next_scene):
        if self.active:
            return
        self.active = True
        self.t = 0.0
        self.next = next_scene
        self.switched = False
    def update(self, dt):
        if not self.active:
            return
        self.t += dt
        if self.t >= self.duration / 2 and not self.switched:
            set_scene(self.next)
            self.switched = True
        if self.t >= self.duration:
            self.active = False
    def draw(self, surf):
        if not self.active:
            return
        progress = min(1.0, self.t / self.duration)
        alpha = int(255 * (1 - abs(2 * progress - 1)))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(alpha)
        surf.blit(overlay, (0, 0))


fade = Fade()

# Utility text center

def center_text(surf, text, font, y, color=WHITE):
    t=font.render(text,True,color)
    surf.blit(t,(WIDTH//2 - t.get_width()//2, y))

# Add a lightweight help overlay and control cheat-sheets
control_help = {
    'MainMenu': 'ENTER to Start • S for Settings • ESC to Quit',
    'SettingsMenu': 'Tap/Click to toggle options • ESC back',
    'NameEntry': 'Type name • ENTER confirm • ESC cancel',
    'GameHub': 'Choose a game (1–8) or click buttons • ESC back',
    'ReactionDuel': 'Wait for ATTACK • F (P1) / RightCtrl (P2)',
    'TimingDuel': 'Stop at exactly 3.0s • F / RightCtrl',
    'LanternChase': 'Move WASD / Arrows • Collect brains',
    'Pong': 'W/S vs Up/Down • First to 7 wins',
    'Snake2P': 'WASD and Arrows • Eat brains • Don’t crash',
    'RacingGame': 'WASD / Arrows • Race 3 laps • Avoid obstacles',
    'Yatzy': 'SPACE or ROLL • Tap dice to HOLD • Click a category',
    'Scoreboard': 'View stats • R to reset • ESC back'
}

def draw_help_overlay(surf, scene):
    if not show_help:
        return
    name = scene.__class__.__name__ if scene else ''
    text = control_help.get(name, 'Press ESC to close help')
    box = pygame.Rect(50, HEIGHT-220, WIDTH-100, 160)
    layer = pygame.Surface(box.size, pygame.SRCALPHA)
    # Dark gradient panel
    for gy in range(box.height):
        ratio = gy/max(1,box.height)
        c1=(20,28,36); c2=(36,44,60)
        col = tuple(int(c1[i]*(1-ratio)+c2[i]*ratio) for i in range(3))
        pygame.draw.line(layer, (*col, 220), (0,gy), (box.width,gy))
    pygame.draw.rect(layer, TOXIC_GREEN, layer.get_rect(), 3, border_radius=18)
    surf.blit(layer, box.topleft)
    title = FONT_SUB.render('HELP', True, BONE)
    body = FONT_TEXT.render(text, True, BONE)
    hint = FONT_SMALL.render('Press F1 to hide', True, TOXIC_GREEN)
    surf.blit(title, (box.left+16, box.top+12))
    surf.blit(body, (box.left+16, box.top+68))
    surf.blit(hint, (box.right-hint.get_width()-16, box.bottom-hint.get_height()-12))

# ---------------- Menu Scene ----------------
class MainMenu(Scene):
    def enter(self):
        super().enter()
        self.buttons = [
            Button((130, 405, 400, 70), 'START SURVIVAL', lambda: go_scene('NameEntry'), TOXIC_GREEN, DARK_GREEN, pygame.K_RETURN),
            Button((130, 495, 400, 62), 'SETTINGS', lambda: go_scene('SettingsMenu'), BLUE, DARK_BLUE, pygame.K_s),
            Button((130, 577, 400, 62), 'EXIT', quit_game, BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]
    def draw(self, surf):
        draw_bg(surf)
        light = settings.current_theme == 'arcade'
        ink = (25, 38, 60) if light else BONE
        surf.blit(FONT_SMALL.render('LOCAL MULTIPLAYER / SEVEN MINI-GAMES', True, get_theme_colors()['accent']), (130, 150))
        surf.blit(FONT_TITLE.render("HAMEEM'S", True, ink), (125, 205))
        surf.blit(FONT_TITLE.render('GAMING ZONE', True, ink), (125, 275))
        surf.blit(FONT_SMALL.render('One keyboard. Your squad. A little friendly chaos.', True, get_theme_colors()['subtitle']), (130, 355))
        panel = pygame.Rect(680, 185, 380, 430)
        pygame.draw.rect(surf, (24, 33, 45) if not light else (215, 229, 245), panel, border_radius=28)
        for i, radius in enumerate((130, 102, 74)):
            pygame.draw.circle(surf, (42, 65 + i * 18, 62), panel.center, radius, 2)
        pygame.draw.circle(surf, TOXIC_GREEN, (835, 365), 18)
        pygame.draw.circle(surf, TOXIC_GREEN, (905, 365), 18)
        pygame.draw.line(surf, BLOOD_RED, (825, 440), (915, 440), 6)
        for x in range(840, 920, 20):
            pygame.draw.line(surf, BONE, (x, 430), (x, 450), 3)
        center_text(surf, 'F1 help  /  F11 fullscreen', FONT_SMALL, 735, get_theme_colors()['subtitle'])
        for b in self.buttons:
            b.draw(surf)


# ---------------- Settings Menu Scene ----------------
class SettingsMenu(Scene):
    def enter(self):
        super().enter()
        self.buttons=[
            Button((WIDTH//2-200, 620, 400, 60), "Back to Menu", lambda: go_scene('MainMenu'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)
        ]
        # UI controls
        self.touch_btn = pygame.Rect(WIDTH//2-200, 300, 400, 64)
        self.players_btn = pygame.Rect(WIDTH//2-200, 380, 400, 64)
        self.theme_btn = pygame.Rect(WIDTH//2-200, 460, 400, 64)
        self.scale_btn = pygame.Rect(WIDTH//2-200, 540, 190, 60)
        self.sound_btn = pygame.Rect(WIDTH//2+10, 540, 190, 60)
    def handle(self,e):
        super().handle(e)
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            if self.touch_btn.collidepoint(e.pos):
                settings.touch_enabled=not settings.touch_enabled; save_settings()
            elif self.players_btn.collidepoint(e.pos):
                settings.num_players=(settings.num_players % 4)+1
                if settings.num_players==1: settings.num_players=2
                if not settings.lock_theme:
                    settings.update_theme()
                save_settings()
            elif self.theme_btn.collidepoint(e.pos):
                # Cycle through curated themes and lock selection
                themes=['arcade','zombie','wasteland','apocalypse']
                cur=settings.current_theme
                try: idx=themes.index(cur)
                except ValueError: idx=0
                new=themes[(idx+1)%len(themes)]
                settings.lock_theme=True
                settings.start_transition(new)
                save_settings()
            elif self.scale_btn.collidepoint(e.pos):
                settings.cycle_scale()
            elif self.sound_btn.collidepoint(e.pos):
                settings.sound_enabled=not settings.sound_enabled; save_settings()
    def draw(self,surf):
        draw_bg(surf)
        theme=get_theme_colors()
        center_text(surf,"SETTINGS", FONT_TITLE, 96, theme['title'])
        center_text(surf,"Tune your experience", FONT_SMALL, 160, theme['subtitle'])
        m=pygame.mouse.get_pos()
        # Touch
        pygame.draw.rect(surf, (255,255,255,30), self.touch_btn, border_radius=16)
        pygame.draw.rect(surf, theme['accent'], self.touch_btn, 2, border_radius=16)
        txt=FONT_UI.render(f"Touch: {'ON' if settings.touch_enabled else 'OFF'}", True, BONE)
        surf.blit(txt, txt.get_rect(center=self.touch_btn.center))
        # Players
        pygame.draw.rect(surf, (255,255,255,30), self.players_btn, border_radius=16)
        pygame.draw.rect(surf, theme['accent'], self.players_btn, 2, border_radius=16)
        txt=FONT_UI.render(f"Players: {settings.num_players}", True, BONE)
        surf.blit(txt, txt.get_rect(center=self.players_btn.center))
        # Theme
        pygame.draw.rect(surf, (255,255,255,30), self.theme_btn, border_radius=16)
        pygame.draw.rect(surf, theme['accent'], self.theme_btn, 2, border_radius=16)
        lock='(locked)' if settings.lock_theme else '(auto)'
        txt=FONT_UI.render(f"Theme: {settings.current_theme.title()} {lock}", True, BONE)
        surf.blit(txt, txt.get_rect(center=self.theme_btn.center))
        # Scale
        pygame.draw.rect(surf, (255,255,255,30), self.scale_btn, border_radius=16)
        pygame.draw.rect(surf, theme['accent'], self.scale_btn, 2, border_radius=16)
        txt=FONT_UI.render("UI Scale", True, BONE)
        surf.blit(txt, txt.get_rect(center=self.scale_btn.center))
        # Sound
        pygame.draw.rect(surf, (255,255,255,30), self.sound_btn, border_radius=16)
        pygame.draw.rect(surf, theme['accent'], self.sound_btn, 2, border_radius=16)
        txt=FONT_UI.render(f"Sound: {'ON' if settings.sound_enabled else 'OFF'}", True, BONE)
        surf.blit(txt, txt.get_rect(center=self.sound_btn.center))
        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

# ---------------- Name Entry Scene ----------------
class NameEntry(Scene):
    def enter(self):
        super().enter()
        self.stage = 1
        self.input_text = players[1].name
        self.blink = 0.0
        self.buttons = [Button((440, 540, 320, 62), "CONTINUE", self.finish,
                               BLUE, DARK_BLUE, pygame.K_RETURN)]
    def finish(self):
        players[self.stage].name = self.input_text.strip() or f"Survivor{self.stage}"
        if self.stage < settings.num_players:
            self.stage += 1
            self.input_text = players[self.stage].name
        else:
            go_scene('GameHub')
    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                go_scene('MainMenu')
                return
            if e.key == pygame.K_RETURN:
                self.finish()
                return
            if e.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif len(self.input_text) < 12 and e.unicode.isprintable():
                self.input_text += e.unicode
        elif e.type == pygame.MOUSEBUTTONDOWN:
            super().handle(e)
    def update(self, dt):
        self.blink += dt
    def draw(self, surf):
        draw_bg(surf)
        center_text(surf, 'BUILD YOUR SQUAD', FONT_TITLE, 145, BONE)
        center_text(surf, f'Player {self.stage} of {settings.num_players}', FONT_TEXT, 235, get_player_color(self.stage))
        box = pygame.Rect(340, 330, 520, 86)
        pygame.draw.rect(surf, (20, 28, 39), box, border_radius=16)
        pygame.draw.rect(surf, get_player_color(self.stage), box, 2, border_radius=16)
        text = self.input_text + ('|' if int(self.blink * 2) % 2 == 0 else '')
        label = FONT_UI.render(text, True, BONE)
        surf.blit(label, label.get_rect(center=box.center))
        center_text(surf, 'Type a name / ENTER to confirm / ESC to return', FONT_SMALL, 455, (150, 165, 180))
        for b in self.buttons:
            b.draw(surf)


# ---------------- Game Hub Scene ----------------
class GameHub(Scene):
    def enter(self):
        super().enter()
        games = [('Reaction Survival', 'ReactionDuel', '2 players'),
                 ('Timing Escape', 'TimingDuel', '2 players'),
                 ('Brain Hunt', 'LanternChase', '2 players'),
                 ('Zombie Pong', 'Pong', '2 players'),
                 ('Infected Snake', 'Snake2P', '2 players'),
                 ('Yatzy', 'Yatzy', '2-4 players'),
                 ('Zombie Race', 'RacingGame', '2-4 players')]
        self.cards = []
        colors = [ORANGE, PURPLE, BRAIN_PINK, BLUE, TOXIC_GREEN, CYAN, GOLD]
        for i, (title, target, count) in enumerate(games):
            x, y = 90 + (i % 3) * 350, 230 + (i // 3) * 130
            self.buttons.append(Button((x, y, 320, 78), f'{i+1}. {title}', lambda name=target: go_scene(name), colors[i], DARK_BLUE, getattr(pygame, f'K_{i+1}')))
            self.cards.append((x + 10, y + 87, count))
        self.buttons += [Button((440, 665, 320, 58), 'SURVIVOR BOARD', lambda: go_scene('Scoreboard'), BLUE, DARK_BLUE, pygame.K_8),
                         Button((90, 665, 260, 58), 'BACK', lambda: go_scene('MainMenu'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]
    def draw(self, surf):
        draw_bg(surf)
        theme = get_theme_colors()
        center_text(surf, 'CHOOSE YOUR CHALLENGE', FONT_TITLE, 65, theme['title'])
        names = ' / '.join(players[i].name for i in range(1, settings.num_players + 1))
        center_text(surf, names, FONT_TEXT, 150, theme['subtitle'])
        for x, y, count in self.cards:
            surf.blit(FONT_SMALL.render(count, True, theme['subtitle']), (x, y))
        for b in self.buttons:
            b.draw(surf)
        center_text(surf, '1-7 games / 8 scoreboard / F1 controls', FONT_SMALL, 755, theme['subtitle'])


# ---------------- Reaction Duel ----------------
class ReactionDuel(Scene):
    def enter(self):
        super().enter(); self.started=False; self.cue=False; self.result=None
        self.delay=random.uniform(1.5,4.0); self.start_time=time.time(); self.cue_time=0.0
        self.press_time={1:0.0,2:0.0}
        self.info = "Zombie incoming! React when you see ATTACK! (F for P1, RightCtrl for P2)" if True else ""
        self.buttons=[Button((WIDTH//2-140, 650, 280, 60), "Back Hub", lambda: go_scene('GameHub'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]
        # Animation enhancements
        self.warning_pulse = 0.0
        self.attack_scale = 1.0
        self.result_glow = 0.0
    def handle(self,e):
        super().handle(e)
        if e.type==pygame.KEYDOWN and self.cue and self.result is None:
            if e.key == players[1].action and self.press_time[1] == 0.0:
                self.press_time[1] = time.time(); spawn_burst(WIDTH//2-150, 400, BLOOD_RED, count=25)
            if e.key == players[2].action and self.press_time[2] == 0.0:
                self.press_time[2] = time.time(); spawn_burst(WIDTH//2+150, 400, TOXIC_GREEN, count=25)
    def update(self,dt):
        self.warning_pulse += dt * 4
        self.attack_scale += (1.0 - self.attack_scale) * 0.1
        if self.result:
            self.result_glow += dt * 2

        if not self.cue and time.time()-self.start_time >= self.delay:
            self.cue=True; self.cue_time = time.time(); self.attack_scale = 2.0
        if self.cue and self.result is None:
            if self.press_time[1]>0 and self.press_time[2]>0:
                p1= self.press_time[1]-self.cue_time; p2= self.press_time[2]-self.cue_time
                if abs(p1-p2) < 0.01: self.result="Both survived!"
                elif p1 < p2: self.result=f"{players[1].name} survived!"
                else: self.result=f"{players[2].name} survived!"
            elif (self.press_time[1]>0 or self.press_time[2]>0) and time.time()-self.cue_time>3.0:
                if self.press_time[1]>0: self.result=f"{players[1].name} survived!"
                else: self.result=f"{players[2].name} survived!"
            if self.result:
                if self.result.startswith(players[1].name): stats.reaction_wins[1]+=1
                elif self.result.startswith(players[2].name): stats.reaction_wins[2]+=1
    def draw(self,surf):
        surf.fill(NIGHT_SKY)  # Dark zombie night
        center_text(surf,"⚠️ REACTION SURVIVAL ⚠️", FONT_TITLE, 60, BLOOD_RED)
        center_text(surf,self.info, FONT_TEXT, 140, BONE)

        if not self.cue:
            # Pulsing warning
            pulse_scale = 1.0 + 0.2 * abs(math.sin(self.warning_pulse))
            warn_font = pygame.font.Font(None, int(BASE_FONT_SIZES['SUB'] * pulse_scale * settings.ui_scale))
            warn_txt = warn_font.render("Zombie approaching...", True, TOXIC_GREEN)
            surf.blit(warn_txt, warn_txt.get_rect(center=(WIDTH//2, 340)))
        else:
            # Scaling ATTACK text with glow
            attack_font = pygame.font.Font(None, int(BASE_FONT_SIZES['TITLE'] * self.attack_scale * settings.ui_scale))
            attack_color = BLOOD_RED if self.result is None else TOXIC_GREEN
            # Glow layers
            for i in range(3):
                glow_font = pygame.font.Font(None, int(BASE_FONT_SIZES['TITLE'] * self.attack_scale * settings.ui_scale) + i*4)
                glow_txt = glow_font.render("🧟 ATTACK! 🧟", True, (*attack_color, 80//(i+1)))
                surf.blit(glow_txt, glow_txt.get_rect(center=(WIDTH//2, 320)))
            attack_txt = attack_font.render("🧟 ATTACK! 🧟", True, attack_color)
            surf.blit(attack_txt, attack_txt.get_rect(center=(WIDTH//2, 320)))

        # Reaction times with animation
        if self.press_time[1]>0:
            time_text = f"{players[1].name}: {self.press_time[1]-self.cue_time:.3f}s"
            center_text(surf, time_text, FONT_UI, 420, BLOOD_RED)
        if self.press_time[2]>0:
            time_text = f"{players[2].name}: {self.press_time[2]-self.cue_time:.3f}s"
            center_text(surf, time_text, FONT_UI, 470, TOXIC_GREEN)

        if self.result:
            # Result with pulsing glow
            result_color = TOXIC_GREEN if "survived" in self.result else BLOOD_RED
            glow_intensity = abs(math.sin(self.result_glow))
            for i in range(2):
                glow_font = pygame.font.Font(None, int(BASE_FONT_SIZES['SUB'] * settings.ui_scale) + i*6)
                glow_txt = glow_font.render(self.result, True, (*result_color, int(100*glow_intensity/(i+1))))
                surf.blit(glow_txt, glow_txt.get_rect(center=(WIDTH//2, 540)))
            center_text(surf, self.result, FONT_SUB, 540, result_color)
            center_text(surf,"ESC to hub", FONT_SMALL, 590, BONE)

        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

# ---------------- Timing Duel ----------------
class TimingDuel(Scene):
    def enter(self):
        super().enter(); self.target=3.0; self.start_time=time.time(); self.stop_time={1:0.0,2:0.0}; self.result=None
        self.buttons=[Button((WIDTH//2-140, 690, 280, 60), "Back Hub", lambda: go_scene('GameHub'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]
        # Animation enhancements
        self.progress_display = 0.0  # Smooth progress bar
        self.target_glow = 0.0
        self.player_ready = {1: False, 2: False}
        self.ready_flash = {1: 0.0, 2: 0.0}
    def handle(self,e):
        super().handle(e)
        if e.type==pygame.KEYDOWN and self.result is None:
            if e.key==players[1].action and self.stop_time[1]==0.0:
                self.stop_time[1]=time.time(); self.player_ready[1] = True; self.ready_flash[1] = 1.0
                spawn_burst(WIDTH//2-200, 400, BLOOD_RED, count=30)
            if e.key==players[2].action and self.stop_time[2]==0.0:
                self.stop_time[2]=time.time(); self.player_ready[2] = True; self.ready_flash[2] = 1.0
                spawn_burst(WIDTH//2+200, 400, TOXIC_GREEN, count=30)
    def update(self,dt):
        self.target_glow += dt * 3
        self.ready_flash[1] = max(0, self.ready_flash[1] - dt * 3)
        self.ready_flash[2] = max(0, self.ready_flash[2] - dt * 3)

        # Smooth progress bar animation
        elapsed = time.time()-self.start_time
        target_progress = min(elapsed/7.0, 1.0)
        self.progress_display += (target_progress - self.progress_display) * 0.15

        if self.result is None and self.stop_time[1]>0 and self.stop_time[2]>0:
            d1=abs(self.stop_time[1]- (self.start_time+self.target)); d2=abs(self.stop_time[2]- (self.start_time+self.target))
            if abs(d1-d2) < 0.01: self.result="Both escaped!"
            elif d1<d2: self.result=f"{players[1].name} escaped!"; stats.timing_wins[1]+=1
            else: self.result=f"{players[2].name} escaped!"; stats.timing_wins[2]+=1
        if self.result is None and time.time()-self.start_time > 7:
            if self.stop_time[1]==0.0 and self.stop_time[2]==0.0: self.result="Both got eaten"
            elif self.stop_time[1]>0 and self.stop_time[2]==0.0: self.result=f"{players[1].name} escaped!"; stats.timing_wins[1]+=1
            elif self.stop_time[2]>0 and self.stop_time[1]==0.0: self.result=f"{players[2].name} escaped!"; stats.timing_wins[2]+=1
    def draw(self,surf):
        surf.fill((10,15,20))  # Very dark zombie atmosphere
        center_text(surf,"⏰ TIMING ESCAPE ⏰", FONT_TITLE, 60, BLOOD_RED)
        center_text(surf,"Escape at EXACTLY 3.0 seconds before zombie bite!", FONT_TEXT, 140, BONE)

        # Smooth animated progress bar with gradient
        bar=pygame.Rect(200,260,WIDTH-400,40)
        pygame.draw.rect(surf,BONE,bar,2)
        fill_width = int((bar.width-4) * self.progress_display)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar.left+2,bar.top+2, fill_width, bar.height-4)
            # Gradient fill
            grad_surf = pygame.Surface(fill_rect.size, pygame.SRCALPHA)
            for gx in range(fill_rect.width):
                ratio = gx / max(1, fill_rect.width)
                color = TOXIC_GREEN if self.result is None else BLOOD_RED
                col = tuple(int(color[i] * (0.6 + 0.4*ratio)) for i in range(3))
                pygame.draw.line(grad_surf, col, (gx, 0), (gx, fill_rect.height))
            surf.blit(grad_surf, fill_rect.topleft)

        # Target marker at 3.0s with pulse
        target_x = bar.left + int((bar.width) * (self.target / 7.0))
        pulse = abs(math.sin(self.target_glow))
        marker_height = int(50 + 10 * pulse)
        marker_y = bar.centery - marker_height//2
        # Glow
        for i in range(3):
            glow_surf = pygame.Surface((8+i*4, marker_height+i*8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*TOXIC_GREEN, 60//(i+1)), glow_surf.get_rect(), border_radius=4)
            surf.blit(glow_surf, (target_x-(4+i*2), marker_y-i*4))
        pygame.draw.rect(surf, TOXIC_GREEN, (target_x-2, marker_y, 4, marker_height), border_radius=2)

        # Player times with flash animation
        if self.stop_time[1]>0:
            flash = self.ready_flash[1]
            time_val = self.stop_time[1]-self.start_time
            time_text = f"{players[1].name}: {time_val:.3f}s"
            if flash > 0:
                time_font = pygame.font.Font(None, int(BASE_FONT_SIZES['UI'] * (1 + flash*0.3) * settings.ui_scale))
            else:
                time_font = FONT_UI
            txt = time_font.render(time_text, True, BLOOD_RED)
            surf.blit(txt, txt.get_rect(center=(WIDTH//2, 360)))

        if self.stop_time[2]>0:
            flash = self.ready_flash[2]
            time_val = self.stop_time[2]-self.start_time
            time_text = f"{players[2].name}: {time_val:.3f}s"
            if flash > 0:
                time_font = pygame.font.Font(None, int(BASE_FONT_SIZES['UI'] * (1 + flash*0.3) * settings.ui_scale))
            else:
                time_font = FONT_UI
            txt = time_font.render(time_text, True, TOXIC_GREEN)
            surf.blit(txt, txt.get_rect(center=(WIDTH//2, 410)))

        if self.result:
            result_color = TOXIC_GREEN if "escaped" in self.result else BLOOD_RED
            center_text(surf,self.result, FONT_SUB, 500, result_color)
            center_text(surf,"ESC to hub", FONT_SMALL, 550, BONE)

        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

# ---------------- Brain Hunt Arena (was Lantern Chase) ----------------
class LanternChase(Scene):
    def enter(self):
        super().enter()
        self.duration = 40  # seconds match
        self.start_time = time.time()
        self.player_rect = {1: pygame.Rect(WIDTH//2-220, HEIGHT//2, 42,42), 2: pygame.Rect(WIDTH//2+220, HEIGHT//2, 42,42)}
        self.player_vel = {1:[0,0],2:[0,0]}
        self.speed = 5
        self.lantern = self.spawn_lantern()  # Actually spawns brains now
        self.points = {1:0,2:0}
        self.buttons=[Button((WIDTH//2-140, 720, 280, 60), "Back Hub", lambda: go_scene('GameHub'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]
        self.obstacles = [pygame.Rect(random.randint(100, WIDTH-180), random.randint(180, HEIGHT-220), random.randint(80,140), random.randint(60,160)) for _ in range(8)]
        # Animation enhancements
        self.player_display_pos = {1: [self.player_rect[1].x, self.player_rect[1].y],
                                    2: [self.player_rect[2].x, self.player_rect[2].y]}
        self.brain_float = 0.0  # Floating animation
        self.score_pop = {1: 0.0, 2: 0.0}  # Score popup effect
        self.player_scale = {1: 1.0, 2: 1.0}  # Player size pulse
        self.timer_pulse = 0.0
    def spawn_lantern(self):
        return pygame.Rect(random.randint(80, WIDTH-120), random.randint(140, HEIGHT-120), 34,34)
    def handle(self,e):
        super().handle(e)
    def update(self,dt):
        # Update animations
        self.brain_float += dt * 3
        self.timer_pulse += dt * 2
        self.score_pop[1] = max(0, self.score_pop[1] - dt * 3)
        self.score_pop[2] = max(0, self.score_pop[2] - dt * 3)
        self.player_scale[1] += (1.0 - self.player_scale[1]) * 0.15
        self.player_scale[2] += (1.0 - self.player_scale[2]) * 0.15

        # Movement input
        keys = pygame.key.get_pressed()
        for pid in (1,2):
            v=[0,0]
            info=players[pid]
            if keys[info.left]: v[0]-=1
            if keys[info.right]: v[0]+=1
            if keys[info.up]: v[1]-=1
            if keys[info.down]: v[1]+=1
            self.player_vel[pid]=v
        # Apply movement & collisions
        for pid in (1,2):
            rect=self.player_rect[pid]
            vx,vy=self.player_vel[pid]
            rect.x += vx*self.speed
            rect.y += vy*self.speed
            rect.clamp_ip(pygame.Rect(40,140,WIDTH-80,HEIGHT-200))
            # Smooth display position (lerp)
            self.player_display_pos[pid][0] += (rect.x - self.player_display_pos[pid][0]) * 0.3
            self.player_display_pos[pid][1] += (rect.y - self.player_display_pos[pid][1]) * 0.3
            # Obstacle collision simple push-back (zombie barricades)
            for o in self.obstacles:
                if rect.colliderect(o):
                    if vx>0: rect.right=o.left
                    if vx<0: rect.left=o.right
                    if vy>0: rect.bottom=o.top
                    if vy<0: rect.top=o.bottom
        # Brain pickup (was lantern)
        for pid in (1,2):
            if self.player_rect[pid].colliderect(self.lantern):
                self.points[pid]+=1
                stats.lantern_points[pid]+=1
                self.score_pop[pid] = 1.0
                self.player_scale[pid] = 1.4
                spawn_burst(self.lantern.centerx, self.lantern.centery, BRAIN_PINK, count=30)
                self.lantern = self.spawn_lantern()
        # End match
        if time.time()-self.start_time >= self.duration:
            fade.start(LanternResult(self.points))
    def draw(self,surf):
        surf.fill((8,12,18))  # Very dark zombie apocalypse
        center_text(surf,"🧠 BRAIN HUNT 🧠", FONT_TITLE, 50, BRAIN_PINK)
        remaining = max(0,int(self.duration-(time.time()-self.start_time)))

        # Animated timer with pulse
        timer_scale = 1.0 + 0.05 * abs(math.sin(self.timer_pulse))
        if remaining <= 10:
            timer_scale += 0.15 * abs(math.sin(self.timer_pulse * 2))
            timer_color = BLOOD_RED if remaining % 2 == 0 else TOXIC_GREEN
        else:
            timer_color = TOXIC_GREEN
        timer_font = pygame.font.Font(None, int(BASE_FONT_SIZES['UI'] * timer_scale * settings.ui_scale))
        timer_txt = timer_font.render(f"Time: {remaining}s", True, timer_color)
        surf.blit(timer_txt, timer_txt.get_rect(center=(WIDTH//2, 120)))

        # Arena bounds
        pygame.draw.rect(surf,DARK_BLOOD,(40,140,WIDTH-80,HEIGHT-200),3)
        # Obstacles (zombie barricades - with gradient)
        for o in self.obstacles:
            obs_surf = pygame.Surface(o.size, pygame.SRCALPHA)
            for oy in range(o.height):
                ratio = oy / o.height
                col = tuple(int(40 * (1-ratio*0.5)) for _ in range(3))
                pygame.draw.line(obs_surf, col, (0,oy), (o.width, oy))
            surf.blit(obs_surf, o.topleft)
            pygame.draw.rect(surf, (60,55,50), o, 2)

        # Floating brain animation
        brain_offset_y = int(8 * math.sin(self.brain_float))
        brain_rect = self.lantern.copy()
        brain_rect.y += brain_offset_y
        # Brain glow
        for i in range(4):
            glow_rect = brain_rect.inflate(i*12, i*12)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (*BRAIN_PINK, 50//(i+1)), glow_surf.get_rect())
            surf.blit(glow_surf, glow_rect.topleft)
        pygame.draw.ellipse(surf,BRAIN_PINK,brain_rect)
        pygame.draw.circle(surf,BRAIN_PINK,(brain_rect.centerx,brain_rect.centery),18,3)

        # Players with smooth movement and scale
        for pid in [1, 2]:
            color = BLOOD_RED if pid == 1 else TOXIC_GREEN
            pos = self.player_display_pos[pid]
            scale = self.player_scale[pid]
            size = int(42 * scale)
            player_rect = pygame.Rect(int(pos[0]), int(pos[1]), size, size)

            # Player glow trail
            if self.player_vel[pid] != [0, 0]:
                trail_surf = pygame.Surface((size+20, size+20), pygame.SRCALPHA)
                pygame.draw.rect(trail_surf, (*color, 40), trail_surf.get_rect(), border_radius=12)
                surf.blit(trail_surf, (player_rect.x-10, player_rect.y-10))

            # Player body with gradient
            player_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            for py in range(size):
                ratio = py / size
                player_color = tuple(int(color[i] * (1-ratio*0.3)) for i in range(3))
                pygame.draw.line(player_surf, player_color, (0, py), (size, py))
            surf.blit(player_surf, player_rect.topleft)
            pygame.draw.rect(surf, color, player_rect, 3, border_radius=10)

        # Animated scores
        for pid in [1, 2]:
            color = BLOOD_RED if pid == 1 else TOXIC_GREEN
            pop = self.score_pop[pid]
            score_text = f"{players[pid].name}: {self.points[pid]} 🧠"
            if pop > 0:
                scale = 1.0 + pop * 0.5
                score_font = pygame.font.Font(None, int(BASE_FONT_SIZES['UI'] * scale * settings.ui_scale))
                y_offset = -int(pop * 20)
            else:
                score_font = FONT_UI
                y_offset = 0
            txt = score_font.render(score_text, True, color)
            y_pos = 200 + y_offset if pid == 1 else 250 + y_offset
            surf.blit(txt, txt.get_rect(center=(WIDTH//2, y_pos)))

        center_text(surf,"Move: WASD / Arrows - Collect brains!", FONT_SMALL, 300, BONE)
        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

class LanternResult(Scene):
    def __init__(self, points):
        super().__init__(); self.points=points
    def enter(self):
        super().enter()
        self.buttons=[Button((WIDTH//2-160, 600, 320, 70), "Back Hub", lambda: go_scene('GameHub'), TOXIC_GREEN, DARK_GREEN, pygame.K_RETURN)]
    def draw(self,surf):
        surf.fill((12,18,25))
        center_text(surf,"🧠 Brain Hunt Result 🧠", FONT_TITLE, 120, BRAIN_PINK)
        if self.points[1] == self.points[2]:
            center_text(surf,"Tie! Both zombies equally hungry!", FONT_SUB, 240, ZOMBIE_PURPLE)
        elif self.points[1] > self.points[2]:
            center_text(surf,f"👑 {players[1].name} hunted more brains!", FONT_SUB, 240, BLOOD_RED)
        else:
            center_text(surf,f"👑 {players[2].name} hunted more brains!", FONT_SUB, 240, TOXIC_GREEN)
        center_text(surf,f"{players[1].name} Brains: {self.points[1]}", FONT_UI, 340, BLOOD_RED)
        center_text(surf,f"{players[2].name} Brains: {self.points[2]}", FONT_UI, 390, TOXIC_GREEN)
        center_text(surf,"ENTER to return", FONT_SMALL, 460, BONE)
        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

# ---------------- Scoreboard Scene ----------------
class Scoreboard(Scene):
    def enter(self):
        super().enter()
        self.buttons = [Button((230, 670, 320, 60), 'BACK TO HUB', lambda: go_scene('GameHub'), BLUE, DARK_BLUE, pygame.K_ESCAPE),
                        Button((650, 670, 320, 60), 'RESET STATS', stats.reset, BLOOD_RED, DARK_BLOOD, pygame.K_r)]
    def draw(self, surf):
        draw_bg(surf)
        theme = get_theme_colors()
        center_text(surf, 'SURVIVOR BOARD', FONT_TITLE, 65, theme['title'])
        center_text(surf, 'Session statistics / reset when the game closes', FONT_SMALL, 145, theme['subtitle'])
        columns = [390 + i * (710 // settings.num_players) for i in range(settings.num_players)]
        for pid, x in enumerate(columns, 1):
            surf.blit(FONT_SMALL.render(players[pid].name, True, get_player_color(pid)), (x, 220))
        rows = [('Reaction wins', stats.reaction_wins), ('Timing wins', stats.timing_wins),
                ('Brains collected', stats.lantern_points), ('Pong wins', stats.pong_wins),
                ('Snake wins', stats.snake_wins), ('Yatzy wins', stats.yatzy_wins), ('Racing wins', stats.racing_wins)]
        for i, (label, values) in enumerate(rows):
            y = 280 + i * 46
            surf.blit(FONT_TEXT.render(label, True, theme['subtitle']), (110, y))
            for pid, x in enumerate(columns, 1):
                surf.blit(FONT_TEXT.render(str(values.get(pid, 0)), True, get_player_color(pid)), (x, y))
        for b in self.buttons:
            b.draw(surf)


# ---------------- Pong (2-Player) ----------------
class Pong(Scene):
    def enter(self):
        super().enter()
        # Paddle rectangles (left = P1, right = P2)
        self.p1 = pygame.Rect(80, HEIGHT//2 - 50, 18, 100)
        self.p2 = pygame.Rect(WIDTH-98, HEIGHT//2 - 50, 18, 100)
        # Ball as rect
        self.ball = pygame.Rect(WIDTH//2-12, HEIGHT//2-12, 24, 24)
        self.ball_vel = [random.choice([-5,5]), random.choice([-3,3])]
        self.score = {1:0, 2:0}
        self.max_score = 7
        self.speed = 6
        self.buttons=[Button((WIDTH//2-140, 700, 280, 60), "Back Hub", lambda: go_scene('GameHub'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]
        # instructional text
        self.tip = "Zombie Survivors: WASD vs Arrows - First to 7 wins!"
        # Animation enhancements
        self.ball_trail = []  # Trail effect for ball
        self.paddle_glow = {1: 0.0, 2: 0.0}  # Glow intensity when hit
        self.score_flash = {1: 0.0, 2: 0.0}  # Score flash animation
        self.ball_scale = 1.0  # Ball scale for bounce effect
        self.shake_offset = [0, 0]  # Screen shake on score
        self.shake_intensity = 0.0
    def handle(self,e):
        super().handle(e)
    def update(self,dt):
        # Decay animations
        self.paddle_glow[1] = max(0, self.paddle_glow[1] - dt * 3)
        self.paddle_glow[2] = max(0, self.paddle_glow[2] - dt * 3)
        self.score_flash[1] = max(0, self.score_flash[1] - dt * 2)
        self.score_flash[2] = max(0, self.score_flash[2] - dt * 2)
        self.ball_scale += (1.0 - self.ball_scale) * 0.2
        self.shake_intensity *= 0.85
        self.shake_offset = [random.uniform(-self.shake_intensity, self.shake_intensity),
                             random.uniform(-self.shake_intensity, self.shake_intensity)]

        keys = pygame.key.get_pressed()
        # Player 1 movement (W/S)
        if keys[players[1].up]: self.p1.y -= self.speed
        if keys[players[1].down]: self.p1.y += self.speed
        # Player 2 movement (Up/Down)
        if keys[players[2].up]: self.p2.y -= self.speed
        if keys[players[2].down]: self.p2.y += self.speed
        # Clamp inside play area
        self.p1.clamp_ip(pygame.Rect(40,140,WIDTH-80,HEIGHT-200))
        self.p2.clamp_ip(pygame.Rect(40,140,WIDTH-80,HEIGHT-200))

        # Add ball trail
        self.ball_trail.append((self.ball.centerx, self.ball.centery, time.time()))
        self.ball_trail = [(x,y,t) for x,y,t in self.ball_trail if time.time()-t < 0.3]

        # Move ball
        self.ball.x += int(self.ball_vel[0])
        self.ball.y += int(self.ball_vel[1])
        # Collide with top/bottom
        if self.ball.top <= 140 or self.ball.bottom >= HEIGHT-60:
            self.ball_vel[1] = -self.ball_vel[1]
            self.ball_scale = 1.15
        # Collide with paddles
        if self.ball.colliderect(self.p1):
            self.ball_vel[0] = abs(self.ball_vel[0]) + 0.5
            offset = (self.ball.centery - self.p1.centery) / (self.p1.height/2)
            self.ball_vel[1] += offset * 3
            spawn_burst(self.p1.centerx, self.ball.centery, BLOOD_RED, count=12)
            self.paddle_glow[1] = 1.0
            self.ball_scale = 1.3
        if self.ball.colliderect(self.p2):
            self.ball_vel[0] = -abs(self.ball_vel[0]) - 0.5
            offset = (self.ball.centery - self.p2.centery) / (self.p2.height/2)
            self.ball_vel[1] += offset * 3
            spawn_burst(self.p2.centerx, self.ball.centery, TOXIC_GREEN, count=12)
            self.paddle_glow[2] = 1.0
            self.ball_scale = 1.3
        # Score when ball leaves sides
        if self.ball.left <= 0:
            self.score[2] += 1
            spawn_burst(self.p2.centerx, self.p2.centery, TOXIC_GREEN, count=30)
            self.score_flash[2] = 1.0
            self.shake_intensity = 12
            self.reset_ball(direction=1)
        if self.ball.right >= WIDTH:
            self.score[1] += 1
            spawn_burst(self.p1.centerx, self.p1.centery, BLOOD_RED, count=30)
            self.score_flash[1] = 1.0
            self.shake_intensity = 12
            self.reset_ball(direction=-1)
        # Win check
        if self.score[1] >= self.max_score or self.score[2] >= self.max_score:
            winner = 1 if self.score[1] > self.score[2] else 2
            stats.pong_wins[winner] += 1
            fade.start(PongResult(self.score))
    def reset_ball(self, direction=1):
        # Put ball in center and send towards 'direction' (-1 left, 1 right)
        self.ball.center = (WIDTH//2, HEIGHT//2)
        self.ball_vel = [direction * random.uniform(4.5,6.5), random.uniform(-3.0,3.0)]
    def draw(self,surf):
        # Apply screen shake
        shake_surf = pygame.Surface((WIDTH, HEIGHT))
        shake_surf.fill((8,12,18))  # Very dark zombie night

        # Draw trail effect for ball
        for i, (x, y, t) in enumerate(self.ball_trail):
            age = time.time() - t
            alpha = int(180 * (1 - age/0.3))
            size = int(20 * (1 - age/0.3))
            trail_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*BONE, alpha), (size, size), size)
            shake_surf.blit(trail_surf, (int(x-size), int(y-size)))

        center_text(shake_surf,"🧟 ZOMBIE PONG 🧟", FONT_TITLE, 60, BLOOD_RED)
        # Arena
        pygame.draw.rect(shake_surf,DARK_BLOOD,(40,140,WIDTH-80,HEIGHT-200),3)
        # Center line (toxic green dashed)
        for y in range(150, HEIGHT-60, 30):
            pygame.draw.rect(shake_surf, TOXIC_GREEN, (WIDTH//2-2, y, 4, 18))

        # Draw paddles with glow effect
        for pid, paddle in [(1, self.p1), (2, self.p2)]:
            color = BLOOD_RED if pid == 1 else TOXIC_GREEN
            glow = self.paddle_glow[pid]
            if glow > 0:
                # Glow layers
                for i in range(3):
                    glow_rect = paddle.inflate(int(20*glow*(3-i)), int(20*glow*(3-i)))
                    glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (*color, int(80*glow/(i+1))), glow_surf.get_rect(), border_radius=8)
                    shake_surf.blit(glow_surf, glow_rect.topleft)
            pygame.draw.rect(shake_surf, color, paddle, border_radius=6)

        # Draw ball with scale effect
        ball_size = int(self.ball.width * self.ball_scale)
        ball_rect = pygame.Rect(0, 0, ball_size, ball_size)
        ball_rect.center = self.ball.center
        pygame.draw.ellipse(shake_surf, BONE, ball_rect)

        # Animated scores with flash
        for pid in [1, 2]:
            flash = self.score_flash[pid]
            color = BLOOD_RED if pid == 1 else TOXIC_GREEN
            if flash > 0:
                scale = 1.0 + flash * 0.5
                score_font = pygame.font.Font(None, int(BASE_FONT_SIZES['SUB'] * scale * settings.ui_scale))
            else:
                score_font = FONT_SUB
            score_surf = score_font.render(str(self.score[pid]), True, color)
            x = WIDTH//4 if pid == 1 else 3*WIDTH//4
            shake_surf.blit(score_surf, score_surf.get_rect(center=(x, 180)))

        center_text(shake_surf, self.tip, FONT_SMALL, 230, BONE)
        for p in particles: p.draw(shake_surf)
        for b in self.buttons: b.draw(shake_surf)

        # Apply shake to main surface
        surf.blit(shake_surf, self.shake_offset)

class PongResult(Scene):
    def __init__(self, score):
        super().__init__(); self.score = score
    def enter(self):
        super().enter()
        self.buttons=[Button((WIDTH//2-160, 600, 320, 70), "Back Hub", lambda: go_scene('GameHub'), TOXIC_GREEN, DARK_GREEN, pygame.K_RETURN)]
    def draw(self,surf):
        surf.fill((10,15,22))
        center_text(surf, "🧟 Zombie Pong Result 🧟", FONT_TITLE, 120, BLOOD_RED)
        if self.score[1] == self.score[2]:
            center_text(surf, "Tie! Both zombies equally skilled!", FONT_SUB, 240, ZOMBIE_PURPLE)
        elif self.score[1] > self.score[2]:
            center_text(surf, f"💀 {players[1].name} survives!", FONT_SUB, 240, BLOOD_RED)
        else:
            center_text(surf, f"💀 {players[2].name} survives!", FONT_SUB, 240, TOXIC_GREEN)
        center_text(surf, f"{players[1].name}: {self.score[1]}", FONT_UI, 340, BLOOD_RED)
        center_text(surf, f"{players[2].name}: {self.score[2]}", FONT_UI, 390, TOXIC_GREEN)
        center_text(surf, "ENTER to return", FONT_SMALL, 460, BONE)
        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

# ---------------- Snake (2-Player) ----------------
class Snake2P(Scene):
    def enter(self):
        super().enter()
        # Grid config
        self.cell = 18
        self.cols = (WIDTH-160)//self.cell
        self.rows = (HEIGHT-220)//self.cell
        # Start positions: P1 left, P2 right
        self.snake = {1: [(5, self.rows//2),(4,self.rows//2),(3,self.rows//2)],
                      2: [(self.cols-6, self.rows//2),(self.cols-5,self.rows//2),(self.cols-4,self.rows//2)]}
        self.dir = {1:(1,0), 2:(-1,0)}  # dx,dy per tick
        self.next_dir = {1:self.dir[1], 2:self.dir[2]}
        self.food = self.spawn_food()
        self.dead = {1:False, 2:False}
        self.tick = 0.12  # movement interval seconds
        self.acc = 0
        self.buttons=[Button((WIDTH//2-140, 720, 280, 60), "Back Hub", lambda: go_scene('GameHub'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]
        self.scores = {1:0,2:0}
        # Animation enhancements
        self.snake_interpolation = {1: 0.0, 2: 0.0}  # Smooth movement
        self.food_pulse = 0.0  # Pulsing food animation
        self.death_flash = {1: 0.0, 2: 0.0}  # Death animation
        self.eat_flash = {1: 0.0, 2: 0.0}  # Eat animation
    def spawn_food(self):
        while True:
            fx = random.randint(2, self.cols-3)
            fy = random.randint(2, self.rows-3)
            if (fx,fy) not in self.snake[1] and (fx,fy) not in self.snake[2]:
                return (fx,fy)
    def handle(self,e):
        super().handle(e)
        # Keyboard direction changes (prevent reverse)
        if e.type==pygame.KEYDOWN:
            # Player1 WASD
            if e.key==pygame.K_w and self.dir[1] != (0,1): self.next_dir[1] = (0,-1)
            if e.key==pygame.K_s and self.dir[1] != (0,-1): self.next_dir[1] = (0,1)
            if e.key==pygame.K_a and self.dir[1] != (1,0): self.next_dir[1] = (-1,0)
            if e.key==pygame.K_d and self.dir[1] != (-1,0): self.next_dir[1] = (1,0)
            # Player2 arrows
            if e.key==pygame.K_UP and self.dir[2] != (0,1): self.next_dir[2] = (0,-1)
            if e.key==pygame.K_DOWN and self.dir[2] != (0,-1): self.next_dir[2] = (0,1)
            if e.key==pygame.K_LEFT and self.dir[2] != (1,0): self.next_dir[2] = (-1,0)
            if e.key==pygame.K_RIGHT and self.dir[2] != (-1,0): self.next_dir[2] = (1,0)
    def update(self,dt):
        # Update animations
        self.food_pulse += dt * 4
        self.eat_flash[1] = max(0, self.eat_flash[1] - dt * 4)
        self.eat_flash[2] = max(0, self.eat_flash[2] - dt * 4)
        self.death_flash[1] = max(0, self.death_flash[1] - dt * 3)
        self.death_flash[2] = max(0, self.death_flash[2] - dt * 3)

        self.acc += dt
        if self.acc < self.tick:
            # Smooth interpolation between grid positions
            progress = self.acc / self.tick
            self.snake_interpolation[1] = progress
            self.snake_interpolation[2] = progress
            return
        self.acc = 0
        self.snake_interpolation = {1: 0.0, 2: 0.0}

        # apply next_dir
        for pid in (1,2): self.dir[pid] = self.next_dir[pid]
        # Move snakes
        for pid in (1,2):
            if self.dead[pid]: continue
            head = self.snake[pid][0]
            nx = head[0] + self.dir[pid][0]
            ny = head[1] + self.dir[pid][1]
            new_head = (nx,ny)
            # Check wall collision
            if nx < 2 or nx >= self.cols-2 or ny < 2 or ny >= self.rows-2:
                self.dead[pid] = True
                self.death_flash[pid] = 1.0
                spawn_burst(40 + nx*self.cell, 140 + ny*self.cell, BLOOD_RED, count=25)
                continue
            # Check collision with self
            if new_head in self.snake[pid]:
                self.dead[pid] = True
                self.death_flash[pid] = 1.0
                spawn_burst(40 + nx*self.cell, 140 + ny*self.cell, BLOOD_RED, count=25)
                continue
            # Check collision with other snake
            other = 1 if pid==2 else 2
            if new_head in self.snake[other]:
                self.dead[pid] = True
                self.death_flash[pid] = 1.0
                spawn_burst(40 + nx*self.cell, 140 + ny*self.cell, BLOOD_RED, count=25)
                continue
            # Move: add new head
            self.snake[pid].insert(0, new_head)
            # Eat food? (Brains for infected snakes)
            if new_head == self.food:
                self.scores[pid] += 1
                self.eat_flash[pid] = 1.0
                spawn_burst(80 + new_head[0]*self.cell, 160 + new_head[1]*self.cell, BRAIN_PINK, count=20)
                self.food = self.spawn_food()
            else:
                self.snake[pid].pop()  # no growth
        # Check end conditions: if one dead and other alive -> winner; if both dead -> tie
        if (self.dead[1] or self.dead[2]):
            if self.dead[1] and not self.dead[2]:
                stats.snake_wins[2] += 1
                fade.start(SnakeResult(self.scores, dict(self.dead)))
            elif self.dead[2] and not self.dead[1]:
                stats.snake_wins[1] += 1
                fade.start(SnakeResult(self.scores, dict(self.dead)))
            else:
                fade.start(SnakeResult(self.scores, dict(self.dead)))
    def draw(self,surf):
        surf.fill((8,12,20))  # Very dark zombie night
        center_text(surf,"🐍 INFECTED SNAKE 🐍", FONT_TITLE, 48, TOXIC_GREEN)
        center_text(surf,"WASD / Arrows to slither - Eat brains, avoid collision!", FONT_SMALL, 110, BONE)
        # Draw arena
        arena = pygame.Rect(40,140, WIDTH-80, HEIGHT-200)
        pygame.draw.rect(surf, DARK_BLOOD, arena, 3, border_radius=8)
        # Draw grid (subtle dark lines)
        for x in range(40, 40 + self.cols*self.cell, self.cell):
            pygame.draw.line(surf, (15,20,25), (x,140), (x, HEIGHT-60))
        for y in range(140, 140 + self.rows*self.cell, self.cell):
            pygame.draw.line(surf, (15,20,25), (40,y), (WIDTH-40, y))

        # Draw pulsing food (brain) with animation
        fx = 40 + self.food[0]*self.cell
        fy = 140 + self.food[1]*self.cell
        pulse_scale = 1.0 + 0.15 * abs(math.sin(self.food_pulse))
        food_size = int(self.cell * pulse_scale)
        food_rect = pygame.Rect(fx + (self.cell-food_size)//2, fy + (self.cell-food_size)//2, food_size-4, food_size-4)
        # Glow effect
        for i in range(3):
            glow_size = food_size + i*8
            glow_rect = pygame.Rect(fx + (self.cell-glow_size)//2, fy + (self.cell-glow_size)//2, glow_size, glow_size)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (*BRAIN_PINK, 40//(i+1)), glow_surf.get_rect())
            surf.blit(glow_surf, glow_rect.topleft)
        pygame.draw.ellipse(surf, BRAIN_PINK, food_rect)

        # Draw snakes with smooth interpolation
        for pid, parts in self.snake.items():
            if self.dead[pid]: continue
            color = BLOOD_RED if pid==1 else TOXIC_GREEN
            eat_glow = self.eat_flash[pid]

            for i,cellpos in enumerate(parts):
                x = 40 + cellpos[0]*self.cell
                y = 140 + cellpos[1]*self.cell

                # Smooth interpolation for head
                if i == 0 and len(parts) > 1:
                    prev_pos = parts[1]
                    interp = self.snake_interpolation[pid]
                    dx = (cellpos[0] - prev_pos[0]) * self.cell * interp
                    dy = (cellpos[1] - prev_pos[1]) * self.cell * interp
                    x -= int(dx)
                    y -= int(dy)

                # Head glow effect when eating
                if i == 0 and eat_glow > 0:
                    for j in range(2):
                        glow_rect = pygame.Rect(x-j*6, y-j*6, self.cell+j*12, self.cell+j*12)
                        glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                        pygame.draw.rect(glow_surf, (*color, int(80*eat_glow/(j+1))), glow_surf.get_rect(), border_radius=5)
                        surf.blit(glow_surf, glow_rect.topleft)

                # Draw segment with gradient
                c = tuple(min(255, int(color[j] * (1.2 if i==0 else 0.8))) for j in range(3)) if i==0 else color
                seg_surf = pygame.Surface((self.cell-2, self.cell-2), pygame.SRCALPHA)
                for sy in range(self.cell-2):
                    ratio = sy / (self.cell-2)
                    seg_color = tuple(int(c[j] * (1-ratio*0.3)) for j in range(3))
                    pygame.draw.line(seg_surf, seg_color, (0,sy), (self.cell-2, sy))
                surf.blit(seg_surf, (x+1, y+1))
                pygame.draw.rect(surf, c, (x+1,y+1,self.cell-2,self.cell-2), 2, border_radius=4)

        # Scores with animation
        for pid in [1, 2]:
            flash = self.eat_flash[pid]
            color = BLOOD_RED if pid == 1 else TOXIC_GREEN
            score_text = f"{players[pid].name}: {self.scores[pid]} brains"
            if flash > 0:
                scale = 1.0 + flash * 0.3
                score_font = pygame.font.Font(None, int(BASE_FONT_SIZES['UI'] * scale * settings.ui_scale))
            else:
                score_font = FONT_UI
            txt = score_font.render(score_text, True, color)
            y_pos = 160 if pid == 1 else 200
            surf.blit(txt, txt.get_rect(center=(WIDTH//2, y_pos)))

        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

class SnakeResult(Scene):
    def __init__(self, scores, dead):
        super().__init__(); self.scores = scores; self.dead = dead
    def enter(self):
        super().enter()
        self.buttons=[Button((WIDTH//2-160, 600, 320, 70), "Back Hub", lambda: go_scene('GameHub'), TOXIC_GREEN, DARK_GREEN, pygame.K_RETURN)]
    def draw(self,surf):
        surf.fill((10,15,22))
        center_text(surf, "🐍 Infected Snake Result 🐍", FONT_TITLE, 120, TOXIC_GREEN)
        if self.dead[1] == self.dead[2]:
            center_text(surf, "Tie! Both snakes equally infected!", FONT_SUB, 240, ZOMBIE_PURPLE)
        elif not self.dead[1]:
            center_text(surf, f"🧟 {players[1].name} survives!", FONT_SUB, 240, BLOOD_RED)
        else:
            center_text(surf, f"🧟 {players[2].name} survives!", FONT_SUB, 240, TOXIC_GREEN)
        center_text(surf, f"{players[1].name}: {self.scores[1]} brains", FONT_UI, 340, BLOOD_RED)
        center_text(surf, f"{players[2].name}: {self.scores[2]} brains", FONT_UI, 390, TOXIC_GREEN)
        center_text(surf, "ENTER to return", FONT_SMALL, 460, BONE)
        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

# ---------------- Racing Game (Multi-Player) ----------------
class RacingGame(Scene):
    def enter(self):
        super().enter()
        self.num_players = settings.num_players
        # Track settings
        self.track_width = 600
        self.track_x = (WIDTH - self.track_width) // 2
        self.laps_to_win = 3

        # Car properties
        self.car_width = 40
        self.car_height = 60
        self.cars = {}
        lane_spacing = self.track_width / self.num_players
        for pid in range(1, self.num_players + 1):
            self.cars[pid] = {
                'x': self.track_x + lane_spacing * (pid - 0.5) - self.car_width//2,
                'y': HEIGHT - 150,
                'speed': 0,
                'max_speed': 8,
                'acceleration': 0.3,
                'friction': 0.15,
                'lap': 0,
                'finished': False,
                'finish_time': 0,
                'angle': 0,  # For drift animation
                'drift_momentum': 0,
                'boost_particles': [],
                'collision_flash': 0
            }

        # Track scroll
        self.scroll_y = 0
        self.scroll_speed = 0

        # Obstacles
        self.obstacles = []
        self.obstacle_spawn_timer = 0
        self.obstacle_spawn_interval = 1.5

        # Lap markers
        self.checkpoint_y = -2000  # One lap is 2000 pixels
        self.lap_line_y = 0

        # Animation properties
        self.speed_lines = []
        self.finish_celebration = 0
        self.race_started = False
        self.countdown = 3
        self.countdown_timer = 0

        # UI
        self.buttons=[Button((20, 20, 140, 50), "Back Hub", lambda: go_scene('GameHub'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE)]

    def spawn_obstacle(self):
        # Spawn random obstacles on the track
        lane = random.randint(0, self.num_players - 1)
        lane_spacing = self.track_width / self.num_players
        obs_x = self.track_x + lane_spacing * (lane + 0.5) - 20
        obs_y = -self.scroll_y - 800
        self.obstacles.append({
            'x': obs_x,
            'y': obs_y,
            'width': 40,
            'height': 40,
            'type': random.choice(['barrel', 'zombie', 'spike'])
        })

    def handle(self, e):
        super().handle(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and not self.race_started:
            self.countdown_timer = time.time()
            self.race_started = True

    def update(self, dt):
        # Countdown
        if self.race_started and self.countdown > 0:
            elapsed = time.time() - self.countdown_timer
            self.countdown = max(0, 3 - int(elapsed))
            if self.countdown == 0:
                self.countdown = -1  # Race active
            return

        if self.countdown != -1:
            return  # Wait for countdown

        # Update animations
        self.finish_celebration += dt

        keys = pygame.key.get_pressed()

        # Find leading car for camera
        max_progress = 0
        for pid in range(1, self.num_players + 1):
            car = self.cars[pid]
            if not car['finished']:
                progress = car['y'] - self.scroll_y
                if progress < max_progress:
                    max_progress = progress

        # Smooth camera follow
        target_scroll = max_progress + 200
        self.scroll_y += (target_scroll - self.scroll_y) * 0.1

        # Update each car
        for pid in range(1, self.num_players + 1):
            car = self.cars[pid]
            if car['finished']:
                car['collision_flash'] = max(0, car['collision_flash'] - dt * 3)
                continue

            info = players[pid]

            # Input
            if keys[info.up]:
                car['speed'] = min(car['max_speed'], car['speed'] + car['acceleration'])
            if keys[info.down]:
                car['speed'] = max(-2, car['speed'] - car['acceleration'])

            # Steering
            drift_speed = 5
            if keys[info.left]:
                car['x'] -= drift_speed
                car['drift_momentum'] -= 0.3
            if keys[info.right]:
                car['x'] += drift_speed
                car['drift_momentum'] += 0.3

            # Apply friction
            car['speed'] *= (1 - car['friction'] * dt)
            car['drift_momentum'] *= 0.85
            car['angle'] = max(-15, min(15, car['drift_momentum'] * 10))

            # Move car
            car['y'] -= car['speed']

            # Keep in track bounds
            car['x'] = max(self.track_x + 5, min(self.track_x + self.track_width - self.car_width - 5, car['x']))

            # Collision flash decay
            car['collision_flash'] = max(0, car['collision_flash'] - dt * 3)

            # Speed particles
            if car['speed'] > 4:
                if random.random() < 0.3:
                    spawn_burst(int(car['x'] + self.car_width//2), int(car['y'] + self.car_height),
                               get_player_color(pid), count=3)

            # Check lap completion
            car_world_y = car['y'] - self.scroll_y
            if car_world_y < self.checkpoint_y and car['lap'] < self.laps_to_win:
                car['lap'] += 1
                spawn_burst(int(car['x'] + self.car_width//2), int(car['y']), GOLD, count=30)

                if car['lap'] >= self.laps_to_win:
                    car['finished'] = True
                    car['finish_time'] = time.time()
                    stats.racing_wins[pid] += 1

                    # Check if all finished
                    all_finished = all(self.cars[p]['finished'] for p in range(1, self.num_players + 1))
                    if all_finished:
                        fade.start(RacingResult(self.cars, self.num_players))

        # Obstacle spawning
        self.obstacle_spawn_timer += dt
        if self.obstacle_spawn_timer >= self.obstacle_spawn_interval:
            self.obstacle_spawn_timer = 0
            self.spawn_obstacle()

        # Update obstacles
        for obs in self.obstacles[:]:
            obs['y'] += self.scroll_speed * dt

            # Check collisions
            obs_rect = pygame.Rect(obs['x'], obs['y'] + self.scroll_y, obs['width'], obs['height'])
            for pid in range(1, self.num_players + 1):
                car = self.cars[pid]
                if not car['finished']:
                    car_rect = pygame.Rect(car['x'], car['y'], self.car_width, self.car_height)
                    if car_rect.colliderect(obs_rect):
                        car['speed'] *= 0.3  # Slow down
                        car['collision_flash'] = 1.0
                        spawn_burst(int(car['x'] + self.car_width//2), int(car['y'] + self.car_height//2),
                                   BLOOD_RED, count=20)
                        if obs in self.obstacles:
                            self.obstacles.remove(obs)
                        break

            # Remove off-screen obstacles
            if obs['y'] > HEIGHT + 100:
                if obs in self.obstacles:
                    self.obstacles.remove(obs)

    def draw(self, surf):
        # Dark road background
        surf.fill((15, 20, 18))

        # Draw track with gradient
        track_rect = pygame.Rect(self.track_x, 0, self.track_width, HEIGHT)
        track_surf = pygame.Surface((self.track_width, HEIGHT), pygame.SRCALPHA)
        for tx in range(self.track_width):
            ratio = abs(tx / self.track_width - 0.5) * 2
            col = tuple(int(40 * (1 - ratio * 0.5)) for _ in range(3))
            pygame.draw.line(track_surf, col, (tx, 0), (tx, HEIGHT))
        surf.blit(track_surf, track_rect.topleft)

        # Track borders
        pygame.draw.rect(surf, TOXIC_GREEN, (self.track_x - 5, 0, 5, HEIGHT))
        pygame.draw.rect(surf, TOXIC_GREEN, (self.track_x + self.track_width, 0, 5, HEIGHT))

        # Lane dividers (scrolling)
        scroll_offset = int(self.scroll_y % 60)
        for pid in range(1, self.num_players):
            lane_x = self.track_x + (self.track_width / self.num_players) * pid
            for y in range(-scroll_offset, HEIGHT, 60):
                pygame.draw.rect(surf, (100, 100, 100), (lane_x - 2, y, 4, 30))

        # Lap line
        lap_line_screen_y = int(self.lap_line_y + self.scroll_y)
        if -50 < lap_line_screen_y < HEIGHT + 50:
            for i in range(3):
                line_y = lap_line_screen_y - i * 2
                alpha = 255 - i * 80
                line_surf = pygame.Surface((self.track_width, 4), pygame.SRCALPHA)
                pygame.draw.rect(line_surf, (*GOLD, alpha), line_surf.get_rect())
                surf.blit(line_surf, (self.track_x, line_y))

        # Draw obstacles
        for obs in self.obstacles:
            obs_y = int(obs['y'] + self.scroll_y)
            if -100 < obs_y < HEIGHT + 100:
                obs_rect = pygame.Rect(int(obs['x']), obs_y, obs['width'], obs['height'])

                if obs['type'] == 'barrel':
                    pygame.draw.ellipse(surf, (139, 90, 43), obs_rect)
                    pygame.draw.ellipse(surf, (101, 67, 33), obs_rect, 3)
                elif obs['type'] == 'zombie':
                    pygame.draw.rect(surf, ROTTEN_FLESH, obs_rect, border_radius=8)
                    # Eyes
                    pygame.draw.circle(surf, BLOOD_RED, (obs_rect.centerx - 8, obs_rect.centery - 5), 4)
                    pygame.draw.circle(surf, BLOOD_RED, (obs_rect.centerx + 8, obs_rect.centery - 5), 4)
                else:  # spike
                    pygame.draw.polygon(surf, GRAY, [
                        (obs_rect.centerx, obs_rect.top),
                        (obs_rect.left, obs_rect.bottom),
                        (obs_rect.right, obs_rect.bottom)
                    ])

        # Draw cars
        for pid in range(1, self.num_players + 1):
            car = self.cars[pid]
            if car['finished']:
                continue

            color = get_player_color(pid)
            car_rect = pygame.Rect(int(car['x']), int(car['y']), self.car_width, self.car_height)

            # Car with rotation
            car_surf = pygame.Surface((self.car_width + 20, self.car_height + 20), pygame.SRCALPHA)

            # Car body gradient
            for cy in range(self.car_height):
                ratio = cy / self.car_height
                car_color = tuple(int(color[i] * (1 - ratio * 0.3)) for i in range(3))
                pygame.draw.line(car_surf, car_color, (10, cy + 10), (self.car_width + 10, cy + 10))

            # Rotate if drifting
            if abs(car['angle']) > 1:
                car_surf = pygame.transform.rotate(car_surf, car['angle'])

            # Collision flash
            if car['collision_flash'] > 0:
                flash_surf = pygame.Surface(car_surf.get_size(), pygame.SRCALPHA)
                flash_surf.fill((*WHITE, int(200 * car['collision_flash'])))
                car_surf.blit(flash_surf, (0, 0))

            surf.blit(car_surf, (car_rect.centerx - car_surf.get_width()//2,
                                 car_rect.centery - car_surf.get_height()//2))

            # Speed indicator
            speed_bar_width = 80
            speed_bar = pygame.Rect(10 + (pid - 1) * 100, HEIGHT - 80, speed_bar_width, 12)
            pygame.draw.rect(surf, GRAY, speed_bar, border_radius=6)
            fill_width = int((speed_bar_width - 4) * (car['speed'] / car['max_speed']))
            if fill_width > 0:
                fill_rect = pygame.Rect(speed_bar.x + 2, speed_bar.y + 2, fill_width, speed_bar.height - 4)
                pygame.draw.rect(surf, color, fill_rect, border_radius=4)

        # HUD
        center_text(surf, "🏁 ZOMBIE RACE 🏁", FONT_TITLE, 30, BLOOD_RED)

        # Lap counters
        y_offset = 120
        for pid in range(1, self.num_players + 1):
            car = self.cars[pid]
            color = get_player_color(pid)
            lap_text = f"{players[pid].name}: Lap {car['lap']}/{self.laps_to_win}"
            if car['finished']:
                lap_text += " ✓ FINISHED!"
            txt = FONT_SMALL.render(lap_text, True, color)
            surf.blit(txt, (20, y_offset))
            y_offset += 30

        # Countdown
        if self.countdown > 0:
            countdown_scale = 2.0 - (time.time() - self.countdown_timer) % 1
            countdown_font = pygame.font.Font(None, int(150 * countdown_scale * settings.ui_scale))
            countdown_txt = countdown_font.render(str(self.countdown), True, TOXIC_GREEN)
            surf.blit(countdown_txt, countdown_txt.get_rect(center=(WIDTH//2, HEIGHT//2)))
        elif self.countdown == 0:
            go_txt = FONT_TITLE.render("GO!", True, TOXIC_GREEN)
            surf.blit(go_txt, go_txt.get_rect(center=(WIDTH//2, HEIGHT//2)))
        elif not self.race_started:
            start_txt = FONT_SUB.render("Press SPACE to Start!", True, BONE)
            surf.blit(start_txt, start_txt.get_rect(center=(WIDTH//2, HEIGHT//2)))

        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

class RacingResult(Scene):
    def __init__(self, cars, num_players):
        super().__init__()
        self.cars = cars
        self.num_players = num_players
        # Sort by finish time
        self.rankings = []
        for pid in range(1, num_players + 1):
            if cars[pid]['finished']:
                self.rankings.append((pid, cars[pid]['finish_time']))
        self.rankings.sort(key=lambda x: x[1])

    def enter(self):
        super().enter()
        self.buttons=[Button((WIDTH//2-160, 600, 320, 70), "Back Hub", lambda: go_scene('GameHub'),
                            TOXIC_GREEN, DARK_GREEN, pygame.K_RETURN)]

    def draw(self, surf):
        draw_bg(surf)
        theme = get_theme_colors()
        center_text(surf, "🏁 RACE RESULTS 🏁", FONT_TITLE, 100, theme['title'])

        if self.rankings:
            winner_pid = self.rankings[0][0]
            center_text(surf, f"🏆 {players[winner_pid].name} WINS! 🏆", FONT_SUB, 180,
                       get_player_color(winner_pid))

            # Show all placements
            y = 260
            medals = ["🥇", "🥈", "🥉", ""]
            for i, (pid, finish_time) in enumerate(self.rankings):
                medal = medals[i] if i < len(medals) else ""
                place_text = f"{medal} {i+1}. {players[pid].name}"
                color = get_player_color(pid)
                txt = FONT_UI.render(place_text, True, color)
                surf.blit(txt, txt.get_rect(center=(WIDTH//2, y)))
                y += 45

        center_text(surf, "ENTER to return", FONT_SMALL, HEIGHT - 150, BONE)
        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)

# ---------------- Yatzy (Yahtzee) Game - 4 Players with Touch Support ----------------
class Yatzy(Scene):
    def enter(self):
        super().enter()
        self.num_players = settings.num_players
        self.current_player = 1
        self.round = 1
        self.max_rounds = 13
        self.roll_count = 0
        self.max_rolls = 3
        self.dice = [1,1,1,1,1]
        self.held = [False]*5
        self.dice_rolling=False; self.roll_animation_time=0; self.roll_duration=0.6
        self.dice_rotation=[0.0]*5; self.dice_scale=[1.0]*5; self.dice_target_y=[0.0]*5; self.dice_velocity=[0.0]*5
        self.glow_pulse=0; self.category_hover_time={}; self.last_scored_category=None; self.score_flash_time=0
        self.scores={pid:{'ones':None,'twos':None,'threes':None,'fours':None,'fives':None,'sixes':None,'three_kind':None,'four_kind':None,'full_house':None,'small_straight':None,'large_straight':None,'yatzy':None,'chance':None} for pid in range(1,self.num_players+1)}
        # Premium layout rectangles
        self.category_panel = pygame.Rect(40,150,320,470)
        self.dice_area = pygame.Rect(380,210,780,240)
        self.roll_button = pygame.Rect(self.dice_area.centerx-130, self.dice_area.bottom+20, 260, 70)
        self.footer_bar = pygame.Rect(40, HEIGHT-110, WIDTH-80, 70)
        self.avatar_row_y = self.dice_area.top - 70
        # Dice rects evenly spaced within dice_area
        gap = self.dice_area.width // 5
        self.dice_rects=[pygame.Rect(self.dice_area.left + i*gap + gap//2 - 60, self.dice_area.centery - 60, 120,120) for i in range(5)]
        # Category rects (precompute for handle & draw)
        self.categories=[('ones','Ones','①'),('twos','Twos','②'),('threes','Threes','③'),('fours','Fours','④'),('fives','Fives','⑤'),('sixes','Sixes','⑥'),('three_kind','3 of Kind','3×'),('four_kind','4 of Kind','4×'),('full_house','Full House','FH'),('small_straight','Sm Straight','S4'),('large_straight','Lg Straight','S5'),('yatzy','YATZY!','★'),('chance','Chance','?')]
        cy= self.category_panel.top+60
        self.category_rects=[]
        for key,name,icon in self.categories:
            r=pygame.Rect(self.category_panel.left+20, cy, self.category_panel.width-40, 38)
            self.category_rects.append((key,name,icon,r))
            cy+=42
        # Buttons (small back top-left, scoreboard shortcut top-right)
        self.buttons=[Button((20,20,140,50),"Back Hub", lambda: go_scene('GameHub'), BLOOD_RED, DARK_BLOOD, pygame.K_ESCAPE),
                      Button((WIDTH-180,20,160,50),"Scoreboard", lambda: go_scene('Scoreboard'), TOXIC_GREEN, DARK_GREEN, pygame.K_TAB)]
        self.hover_category = None
        self.progress_current = 0.0
        self.progress_target = 0.0
        self.roll_hover_t = 0.0  # hover animation for roll button
        self.category_rules = {
            'ones': 'Sum of all 1s', 'twos':'Sum of all 2s','threes':'Sum of all 3s','fours':'Sum of all 4s','fives':'Sum of all 5s','sixes':'Sum of all 6s',
            'three_kind':'3+ same: sum all dice','four_kind':'4+ same: sum all dice','full_house':'3 of one + 2 of another =25','small_straight':'Sequence of 4 =30','large_straight':'Sequence of 5 =40','yatzy':'All 5 same =50','chance':'Any combo: sum all'
        }
    def roll_dice(self):
        # Roll all dice that aren't held with animation
        if self.roll_count < self.max_rolls and not self.dice_rolling:
            self.dice_rolling = True
            self.roll_animation_time = 0

            # Initialize animation for each die
            for i in range(5):
                if not self.held[i]:
                    self.dice[i]=random.randint(1,6)
                    self.dice_rotation[i]=float(random.uniform(0,360))
                    self.dice_velocity[i]=float(random.uniform(-15,-25))
                    self.dice_target_y[i]=0.0

            self.roll_count += 1
            spawn_burst(WIDTH//2, 460, TOXIC_GREEN, count=30)
            if settings.sound_enabled and AUDIO_READY and _dice_sound: _dice_sound.play()

    def calculate_score(self, category):
        # Calculate score for a given category
        dice_counts = [self.dice.count(i) for i in range(1, 7)]

        if category == 'ones': return self.dice.count(1) * 1
        elif category == 'twos': return self.dice.count(2) * 2
        elif category == 'threes': return self.dice.count(3) * 3
        elif category == 'fours': return self.dice.count(4) * 4
        elif category == 'fives': return self.dice.count(5) * 5
        elif category == 'sixes': return self.dice.count(6) *  6
        elif category == 'three_kind':
            for i in range(1, 7):
                if dice_counts[i-1] >= 3: return sum(self.dice)
            return 0
        elif category == 'four_kind':
            for i in range(1, 7):
                if dice_counts[i-1] >= 4: return sum(self.dice)
            return 0
        elif category == 'full_house':
            if 3 in dice_counts and 2 in dice_counts: return 25
            return 0
        elif category == 'small_straight':
            sorted_dice = sorted(set(self.dice))
            if len(sorted_dice) >= 4:
                for i in range(len(sorted_dice)-3):
                    if sorted_dice[i:i+4] == list(range(sorted_dice[i], sorted_dice[i]+4)):
                        return 30
            return 0
        elif category == 'large_straight':
            if sorted(self.dice) == [1,2,3,4,5] or sorted(self.dice) == [2,3,4,5,6]:
                return 40
            return 0
        elif category == 'yatzy':
            if len(set(self.dice)) == 1: return 50
            return 0
        elif category == 'chance':
            return sum(self.dice)
        return 0

    def draw_dice_pips(self, surf, rect, value, color):
        cx, cy = rect.center; r=8; off=25
        def pip(dx,dy): pygame.draw.circle(surf,color,(cx+dx,cy+dy),r)
        if value==1: pip(0,0)
        elif value==2: pip(-off,-off); pip(off,off)
        elif value==3: pip(-off,-off); pip(0,0); pip(off,off)
        elif value==4: pip(-off,-off); pip(off,-off); pip(-off,off); pip(off,off)
        elif value==5: pip(-off,-off); pip(off,-off); pip(0,0); pip(-off,off); pip(off,off)
        elif value==6: pip(-off,-off); pip(off,-off); pip(-off,0); pip(off,0); pip(-off,off); pip(off,off)
    def update(self, dt):
        # Update animations
        self.glow_pulse += dt * 3

        # Dice roll animation
        if self.dice_rolling:
            self.roll_animation_time += dt

            # Physics-based bounce animation for each die
            for i in range(5):
                if not self.held[i]:
                    # Apply gravity
                    self.dice_velocity[i] += 60 * dt  # Gravity
                    self.dice_target_y[i] += self.dice_velocity[i] * dt

                    # Bounce when hitting ground
                    if self.dice_target_y[i] > 0:
                        self.dice_target_y[i] = 0
                        self.dice_velocity[i] = float(-self.dice_velocity[i]*0.6)  # Bounce with damping
                        if abs(self.dice_velocity[i]) < 2:  # Stop bouncing
                            self.dice_velocity[i] = 0

                    # Rotation during roll
                    self.dice_rotation[i] += 720 * dt  # Spin

                    # Scale bounce effect
                    bounce_factor = abs(self.dice_velocity[i]) / 20
                    self.dice_scale[i] = 1.0 + bounce_factor * 0.2

            # End animation after duration
            if self.roll_animation_time >= self.roll_duration:
                self.dice_rolling = False
                for i in range(5):
                    self.dice_target_y[i] = 0
                    self.dice_velocity[i] = 0
                    self.dice_scale[i] = 1.0
                    self.dice_rotation[i] = 0

        # Score flash animation
        if self.score_flash_time > 0:
            self.score_flash_time -= dt

    def score_category(self, category):
        # Score current roll in category and advance turn
        if self.scores[self.current_player][category] is None:
            score = self.calculate_score(category)
            self.scores[self.current_player][category] = score
            spawn_burst(WIDTH//2, 300, BRAIN_PINK, count=40)
            if settings.sound_enabled and AUDIO_READY and _click_sound: _click_sound.play()
            self.current_player += 1
            if self.current_player > self.num_players:
                self.current_player = 1
                self.round += 1

            # Reset for next turn
            self.roll_count = 0
            self.held = [False] * 5
            self.dice = [1, 1, 1, 1, 1]

            # Check if game over
            if self.round > self.max_rounds:
                fade.start(YatzyResult(self.scores, self.num_players))

    def get_total_score(self, pid):
        total = sum([v for v in self.scores[pid].values() if v is not None])
        # Bonus for upper section
        upper = sum([self.scores[pid][cat] for cat in ['ones','twos','threes','fours','fives','sixes'] if self.scores[pid][cat] is not None])
        if upper >= 63:
            total += 35
        return total

    def handle(self, e):
        super().handle(e)
        # Hover detection for categories (for tooltip)
        if e.type==pygame.MOUSEMOTION:
            self.hover_category=None
            for key,name,icon,r in self.category_rects:
                if r.collidepoint(e.pos): self.hover_category=key; break
        # Keyboard roll shortcut
        if e.type==pygame.KEYDOWN and e.key==pygame.K_SPACE and self.roll_count<self.max_rolls and not self.dice_rolling:
            self.roll_dice()
        if settings.touch_enabled or e.type==pygame.MOUSEBUTTONDOWN:
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if self.roll_count>0 and not self.dice_rolling:
                    for i,rect in enumerate(self.dice_rects):
                        if rect.collidepoint(e.pos):
                            self.held[i]=not self.held[i]
                            spawn_burst(rect.centerx,rect.centery,(BLOOD_RED if self.held[i] else TOXIC_GREEN),count=18)
                            self.dice_scale[i]=1.3
                            if settings.sound_enabled and AUDIO_READY and _click_sound: _click_sound.play()
                if self.roll_button.collidepoint(e.pos) and self.roll_count<self.max_rolls and not self.dice_rolling:
                    self.roll_dice()
                for key,name,icon,r in self.category_rects:
                    if r.collidepoint(e.pos) and self.roll_count>0 and not self.dice_rolling and self.scores[self.current_player][key] is None:
                        self.score_category(key)
    def draw(self,surf):
        # Background gradient
        for y in range(0,HEIGHT,3):
            shade=int(10+(y/HEIGHT)*20); pygame.draw.line(surf,(shade,shade//2,shade//3),(0,y),(WIDTH,y))
        self.glow_pulse += 0.015
        # Title
        title="Premium Yatzy"; center_text(surf,title,FONT_TITLE,50,BONE)
        subtitle=f"Round {self.round}/{self.max_rounds} | {players[self.current_player].name}'s turn (Roll {self.roll_count}/{self.max_rolls})"
        center_text(surf,subtitle,FONT_TEXT,110,TOXIC_GREEN)
        # Category panel
        panel=pygame.Surface(self.category_panel.size,pygame.SRCALPHA)
        pygame.draw.rect(panel,(30,30,40,220),panel.get_rect(),border_radius=22)
        pygame.draw.rect(panel,TOXIC_GREEN,self.category_panel,3,border_radius=22)
        surf.blit(panel,self.category_panel.topleft)
        cat_header=FONT_SUB.render("Categories",True,BONE); surf.blit(cat_header,(self.category_panel.left+20,self.category_panel.top+15))
        # Draw categories
        m=pygame.mouse.get_pos()
        for key,name,icon,r in self.category_rects:
            can=self.scores[self.current_player][key] is None and self.roll_count>0 and not self.dice_rolling
            hover=r.collidepoint(m)
            base=(50,50,65); active=(80,140,80) if can else (70,50,50)
            color=active if hover and can else base
            cat_surf=pygame.Surface(r.size,pygame.SRCALPHA)
            pygame.draw.rect(cat_surf,color,(0,0,r.width,r.height),border_radius=12)
            pygame.draw.rect(cat_surf,(120,120,140), (0,0,r.width,r.height),1,border_radius=12)
            surf.blit(cat_surf,r.topleft)
            # Icon & Name
            icon_txt=FONT_SMALL.render(icon,True,TOXIC_GREEN if can else BONE)
            name_txt=FONT_SMALL.render(name,True,BONE)
            surf.blit(icon_txt,(r.left+10,r.centery-icon_txt.get_height()//2))
            surf.blit(name_txt,(r.left+50,r.centery-name_txt.get_height()//2))
            # Score / potential
            val=self.scores[self.current_player][key]
            if val is not None:
                score_txt=FONT_SMALL.render(str(val),True,BLOOD_RED)
            elif can:
                pot=self.calculate_score(key)
                score_txt=FONT_SMALL.render(f"{pot}",True,TOXIC_GREEN)
            else:
                score_txt=FONT_SMALL.render("-",True,GRAY)
            surf.blit(score_txt,(r.right-score_txt.get_width()-10,r.centery-score_txt.get_height()//2))
        # Tooltip for hovered category
        if self.hover_category:
            key=self.hover_category
            rule=self.category_rules.get(key,'')
            if rule:
                mx,my=pygame.mouse.get_pos()
                tip_font=FONT_SMALL
                tip_w=max(140, tip_font.size(rule)[0]+20)
                tip_h=48
                tip_rect=pygame.Rect(mx+16,my+16,tip_w,tip_h)
                if tip_rect.right>WIDTH: tip_rect.right=WIDTH-10
                if tip_rect.bottom>HEIGHT: tip_rect.bottom=HEIGHT-10
                shadow=pygame.Surface((tip_rect.width+8, tip_rect.height+8), pygame.SRCALPHA)
                pygame.draw.rect(shadow,(0,0,0,90),shadow.get_rect(),border_radius=14)
                surf.blit(shadow,(tip_rect.x-4,tip_rect.y-4))
                tip_surf=pygame.Surface(tip_rect.size,pygame.SRCALPHA)
                for gy in range(tip_rect.height):
                    ratio=gy/tip_rect.height
                    base=TOXIC_GREEN; dark=(30,60,40)
                    col=tuple(int(base[i]*(1-ratio*0.6)+dark[i]*ratio*0.6) for i in range(3))
                    pygame.draw.line(tip_surf,col,(0,gy),(tip_rect.width,gy))
                pygame.draw.rect(tip_surf,BONE,tip_surf.get_rect(),2,border_radius=12)
                surf.blit(tip_surf, tip_rect.topleft)
                t1=tip_font.render(self.hover_category.upper(),True,BONE); t2=tip_font.render(rule,True,BONE)
                surf.blit(t1,(tip_rect.x+12, tip_rect.y+6)); surf.blit(t2,(tip_rect.x+12, tip_rect.y+26))
        # Dice with shadows
        for i,(val,rect) in enumerate(zip(self.dice,self.dice_rects)):
            if self.dice_scale[i]>1.0: self.dice_scale[i]=max(1.0,self.dice_scale[i]-0.04)
            y_offset=int(self.dice_target_y[i]); r=rect.copy(); r.y+=y_offset
            # Shadow ellipse under die
            shadow_rect = pygame.Rect(r.left+10, r.bottom-6, r.width-20, 14)
            shsurf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(shsurf,(0,0,0,90),shsurf.get_rect())
            surf.blit(shsurf, shadow_rect.topleft)
            # Scaled die rect
            scale=self.dice_scale[i]
            if scale!=1.0:
                c=r.center; r.width=int(r.width*scale); r.height=int(r.height*scale); r.center=c
            body=pygame.Surface(r.size,pygame.SRCALPHA)
            for gy in range(r.height):
                ratio=gy/r.height; base=BONE if not self.held[i] else BLOOD_RED; dark=tuple(max(0,base[j]-60) for j in range(3))
                col=tuple(int(base[j]*(1-ratio*0.5)+dark[j]*ratio*0.5) for j in range(3)); pygame.draw.line(body,col,(0,gy),(r.width,gy))
            if self.dice_rolling and not self.held[i]:
                body=pygame.transform.rotate(body,self.dice_rotation[i]); rr=body.get_rect(center=r.center); surf.blit(body,rr); pygame.draw.rect(surf,TOXIC_GREEN,rr,4,border_radius=18)
            else:
                surf.blit(body,r); pygame.draw.rect(surf,TOXIC_GREEN,r,4,border_radius=18); self.draw_dice_pips(surf,r,val,BLACK if not self.held[i] else DARK_GRAY)
            if self.held[i]:
                held=FONT_SMALL.render("HELD",True,BONE); surf.blit(held,(r.centerx-held.get_width()//2,r.bottom+4))
        # Roll button with hover scale + glow
        m = pygame.mouse.get_pos()
        hovered = self.roll_button.collidepoint(m)
        self.roll_hover_t += ((1.0 if hovered else 0.0) - self.roll_hover_t) * 0.18
        roll_active=self.roll_count<self.max_rolls and not self.dice_rolling
        rb_color=TOXIC_GREEN if roll_active else DARK_GRAY
        # Glow trail layers
        for i in range(3,0,-1):
            g = self.roll_button.inflate(i*10 + int(8*self.roll_hover_t), i*10 + int(8*self.roll_hover_t))
            gs = pygame.Surface((g.width,g.height), pygame.SRCALPHA)
            pygame.draw.rect(gs, (rb_color[0],rb_color[1],rb_color[2], 30), gs.get_rect(), border_radius=30+i*2)
            surf.blit(gs, g.topleft)
        # Scaled button rect
        scaled_rect = self.roll_button.inflate(int(14*self.roll_hover_t), int(14*self.roll_hover_t))
        btn_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        for gy in range(scaled_rect.height):
            ratio = gy / max(1,scaled_rect.height)
            c1=rb_color; c2=tuple(max(0,c-60) for c in rb_color)
            col=tuple(int(c1[i]*(1-ratio*0.5)+c2[i]*ratio*0.5) for i in range(3))
            pygame.draw.line(btn_surf,col,(0,gy),(scaled_rect.width,gy))
        pygame.draw.rect(btn_surf,BONE, btn_surf.get_rect(),3,border_radius=30)
        surf.blit(btn_surf, scaled_rect.topleft)
        roll_txt=FONT_UI.render("ROLL",True,BONE); surf.blit(roll_txt,roll_txt.get_rect(center=scaled_rect.center))
        # Progress bar (with stripes) fill by roll_count
        bar_w=420; bar_h=18
        bar_rect=pygame.Rect(self.dice_area.centerx-bar_w//2, scaled_rect.top-40, bar_w, bar_h)
        pygame.draw.rect(surf,(25,25,35),bar_rect,border_radius=10)
        pygame.draw.rect(surf,BONE,bar_rect,2,border_radius=10)
        progress_ratio = self.roll_count / self.max_rolls if self.max_rolls else 0
        fill_w=int((bar_w-4)*progress_ratio)
        if fill_w>0:
            fill_rect=pygame.Rect(bar_rect.left+2, bar_rect.top+2, fill_w, bar_h-4)
            grad=pygame.Surface(fill_rect.size,pygame.SRCALPHA)
            for gy in range(fill_rect.height):
                ratio=gy/fill_rect.height; c1=TOXIC_GREEN; c2=(60,120,60)
                col=tuple(int(c1[i]*(1-ratio)+c2[i]*ratio) for i in range(3))
                pygame.draw.line(grad,col,(0,gy),(fill_rect.width,gy))
            surf.blit(grad,fill_rect.topleft)
        pct_txt=FONT_SMALL.render(f"Roll {self.roll_count}/{self.max_rolls}",True,BONE)
        surf.blit(pct_txt,(bar_rect.centerx - pct_txt.get_width()//2, bar_rect.centery - pct_txt.get_height()//2))
        # Player total scores (footer above upper bar)
        footer_y=self.footer_bar.top+4
        for pid in range(1,self.num_players+1):
            total=self.get_total_score(pid)
            ttxt=FONT_SMALL.render(f"{players[pid].name} Total: {total}",True,get_player_color(pid))
            surf.blit(ttxt,(40 + (pid-1)*(WIDTH//self.num_players), footer_y))
        # Upper bonus progress visualization bar variables
        bar_x=40; bar_y=self.footer_bar.top+8; bar_w=WIDTH-80; bar_h=24
        pygame.draw.rect(surf,(30,30,40),(bar_x,bar_y,bar_w,bar_h),border_radius=12)
        pygame.draw.rect(surf,BONE,(bar_x,bar_y,bar_w,bar_h),2,border_radius=12)
        total_segments=63; seg_w=(bar_w-4)/total_segments
        # Multi-player stacked visualization
        for pid in range(1,self.num_players+1):
            upper_sum=sum(v for k,v in self.scores[pid].items() if k in ['ones','twos','threes','fours','fives','sixes'] and v is not None)
            pct=min(upper_sum/63,1.0)
            filled=int(pct*total_segments)
            col=get_player_color(pid)
            for s in range(filled):
                pygame.draw.rect(surf,col,(bar_x+2+int(s*seg_w), bar_y+2+ (pid-1)* (bar_h//self.num_players) , int(seg_w-1), (bar_h-4)//self.num_players -2),border_radius=3)
            if upper_sum>=63:
                bonus_txt=FONT_SMALL.render(f"+35 Bonus P{pid}",True,col)
                surf.blit(bonus_txt,(bar_x+bar_w - bonus_txt.get_width()-10, bar_y+4+(pid-1)* ((bar_h)//self.num_players)))

        # Numeric upper subtotals line
        upper_cats=['ones','twos','threes','fours','fives','sixes']
        for pid in range(1,self.num_players+1):
            upper=sum(v for k,v in self.scores[pid].items() if k in upper_cats and v is not None)
            bonus=' (BONUS)' if upper>=63 else ''
            info=FONT_SMALL.render(f"P{pid} Upper: {upper}{bonus}", True, get_player_color(pid))
            surf.blit(info,(40 + (pid-1)* (WIDTH//self.num_players), self.footer_bar.top+36))
        for p in particles: p.draw(surf)
        for b in self.buttons: b.draw(surf)


# Cache static gradients; only theme transitions need regeneration.
_bg_key = None
_bg_surface = None

def draw_bg(surf):
    global _bg_key, _bg_surface
    theme = get_theme_colors()
    key = (theme['bg_primary'], theme['bg_secondary'])
    if key != _bg_key:
        strip = pygame.Surface((1, HEIGHT))
        for y in range(HEIGHT):
            strip.set_at((0, y), blend(key[0], key[1], y / max(1, HEIGHT - 1)))
        _bg_surface = pygame.transform.smoothscale(strip, (WIDTH, HEIGHT))
        _bg_key = key
    surf.blit(_bg_surface, (0, 0))

control_help['GameHub'] = '1-7: games / 8: scoreboard / ESC: back'
control_help['RacingGame'] = 'P1 WASD / P2 arrows / P3 TVBN / P4 IJKL'

# ---------------- Crash Reporting ----------------
def _show_crash_screen(trace_text: str):
    try:
        pygame.quit()
        pygame.init()
        w,h=1000,600
        scr=pygame.display.set_mode((w,h))
        pygame.display.set_caption("Hameem's Gaming Zone - Crash Report")
        font=pygame.font.Font(None,24)
        lines=trace_text.splitlines()[-22:]
        running=True
        while running:
            for e in pygame.event.get():
                if e.type==pygame.QUIT or e.type==pygame.KEYDOWN or e.type==pygame.MOUSEBUTTONDOWN:
                    running=False
            scr.fill((15,15,22))
            y=20
            head=pygame.font.Font(None,32).render("The game crashed. crash_log.txt was written.",True,(255,120,120))
            scr.blit(head,(20,y)); y+=40
            for ln in lines:
                txt=font.render(ln[:140],True,(230,230,230))
                scr.blit(txt,(20,y)); y+=26
            foot=font.render("Press any key or click to exit.",True,(160,255,180))
            scr.blit(foot,(20,h-40))
            pygame.display.flip()
    except Exception:
        pass

# ---------------- Main Loop ----------------
if __name__ == '__main__':
    try:
        set_scene(MainMenu())
        running = True
        fullscreen = False
        accumulator = 0.0
        step = 1.0 / 120.0
        while running:
            dt = min(clock.tick(FPS) / 1000.0, 0.1)
            accumulator += dt
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                    continue
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_F1:
                        show_help = not show_help
                        continue
                    if e.key == pygame.K_F11:
                        fullscreen = not fullscreen
                        flags = pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0)
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
                        continue
                    if show_help and e.key == pygame.K_ESCAPE:
                        show_help = False
                        continue
                if current_scene and not fade.active and not show_help:
                    current_scene.handle(e)
            while accumulator >= step:
                if current_scene and not fade.active:
                    current_scene.update(step)
                for p in particles[:]:
                    p.update()
                    if p.dead():
                        particles.remove(p)
                fade.update(step)
                accumulator -= step
            screen.fill(BLACK)
            if current_scene:
                current_scene.draw(screen)
            draw_help_overlay(screen, current_scene)
            fade.draw(screen)
            pygame.display.flip()
        save_settings()
        pygame.quit()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            with open(os.path.join(os.path.dirname(__file__), 'crash_log.txt'), 'w', encoding='utf-8') as f:
                f.write(tb)
        except OSError:
            pass
        _show_crash_screen(tb)
        pygame.quit()
