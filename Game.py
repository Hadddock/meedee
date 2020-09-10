import pygame, sys, os , helperFunctions, mido, time, pygame.midi
from pygame.locals import *
pygame.init()
vec = pygame.math.Vector2 
'''GLOBAL CONSTANTS"""--------------------------------------------------GLOBAL CONSTANTS'''
# Height and Width of Display Surface
HEIGHT = 1080
WIDTH = 1920
# Framerate
FPS = 30
# Physics constants for player
ACC = 1.5
FRIC = -0.07
GRAVITY = 1
JUMPHEIGHT = -20
# Colors
PLAYERCOLOR = (12, 32, 19)
BACKGROUNDCOLOR = (255, 183, 184)
PLATFORMCOLOR = (176, 255, 176)

# determine if the line segments intersect
'''PLATFORM CLASS"""--------------------------------------------------PLATFORM CLASS'''


class platform(pygame.sprite.Sprite):

    def __init__(self, rect):
        super().__init__()
        self.rect = rect
        self.surf = pygame.Surface((rect.width, rect.height))
        self.surf.fill(PLATFORMCOLOR)


'''PLAYER CLASS"""--------------------------------------------------PLAYER CLASS'''


class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__() 
        self.surf = pygame.Surface((30, 30))
        self.surf.fill(PLAYERCOLOR)
        self.rect = self.surf.get_rect()
        
        self.pos = vec((10, 75))
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.currentPlatform = None
        self.onPlatform = False
        
    def testCollision(self, newPosition):
        for platform in all_platforms:
            # points of line segments
            A = vec(platform.rect.left, platform.rect.top)
            B = vec(platform.rect.left + platform.rect.left + platform.rect.width, platform.rect.top)
            C = vec(self.pos[0], self.pos[1])
            D = vec(newPosition[0], newPosition[1])
            
#             R = intersection.calculateIntersectPoint(A,B,C,D)
#             if R != None:
#                 self.onPlatform = True
#                 self.currentPlatform = platform
#                 return (R[0],R[1])
            # if the segments intersect, get the point they intersect at
            
            if helperFunctions.segmentsIntersect(A, B, C, D):
                self.onPlatform = True
                self.currentPlatform = platform
                return helperFunctions.line_intersection((A, B), (C, D))
        self.onPlatform = False
        return newPosition

    def move(self):
        # test for collision
        self.acc = vec(0, 0)
        k = pygame.key.get_pressed()
        if k[K_LEFT]:
            self.acc.x = -ACC
        if k[K_RIGHT]:
            self.acc.x = ACC
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        # jump if on platform
        if self.onPlatform:
            self.vel.y = 0
        if self.onPlatform and k[K_UP]:
            self.onPlatform = False
            self.vel.y = JUMPHEIGHT
            jumpSound.play()
        # apply gravity if not on platform
        if not self.onPlatform:
            self.vel.y += GRAVITY
         
        newPosition = self.pos + self.vel + 0.5 * self.acc
        if not self.onPlatform and self.vel.y > 0:
            newPosition = self.testCollision(newPosition)
        
        self.pos = vec(newPosition[0], newPosition[1])
        
        self.rect.midbottom = self.pos
        
        if self.onPlatform and self.currentPlatform:
            if self.pos.x < self.currentPlatform.rect.left and self.vel.x < 0:
                self.currentPlatform = None
                self.onPlatform = False
            # Bugged
            elif self.pos.x > self.currentPlatform.rect.left + self.currentPlatform.rect.width and self.vel.x > 0:
                self.currentPlatform = None
                self.onPlatform = False
                self.vel = vec(self.vel.x, self.vel.y)
        # move midbottom of rectangle to pos, so player stands on the platform


'''INITIALIZATION"""--------------------------------------------------INITIALIZATION'''
FramePerSec = pygame.time.Clock()
# Display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")

# gameIcon = pygame.image.load(os.path.join(os.getcwd(),'Assets','Icon.png'))
# pygame.display.set_icon(gameIcon)
# Platforms
PT1 = platform(pygame.Rect(320, HEIGHT - 50, WIDTH - 640, 50))
PT2 = platform(pygame.Rect(0, HEIGHT - 75, WIDTH / 8, 5))
all_platforms = [2]

all_platforms[0] = PT1
all_platforms.append(PT2)

# Players
P1 = Player()
# Sprite Group
all_sprites = pygame.sprite.Group()
all_sprites.add(P1)
for platform in all_platforms:
    all_sprites.add(platform)
    
# Sound effects
jumpSound = pygame.mixer.Sound(os.path.join(os.getcwd(), 'Assets', 'Sounds', 'jump.WAV'))
jumpSound.set_volume(.2)

pygame.midi.init()
# mid = mido.MidiFile(os.path.join(os.getcwd(),'Assets','midi','Protoman.mid'))
# mid.play()
player = pygame.midi.Output(0)
player.set_instrument(0)

screen.fill(BACKGROUNDCOLOR)
'''MAIN LOOP"""--------------------------------------------------MAIN LOOP'''
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            del player
            pygame.midi.quit()
            pygame.quit()
            sys.exit()
    
    screen.fill(BACKGROUNDCOLOR)
    for entity in all_sprites:
        screen.blit(entity.surf, entity.rect)
    P1.move() 
    # display fps
    screen.blit(helperFunctions.update_fps(FramePerSec), (10, 0))
    pygame.display.update()
    # print(P1.onPlatform)
    FramePerSec.tick(FPS)

