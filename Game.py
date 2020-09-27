import pygame 
from pygame import midi
from pygame.locals import *
import sys 
import os
import helperFunctions
from mido import MidiFile
from sympy import Point
from sympy.geometry import Line, Segment2D

pygame.init()
vec = pygame.math.Vector2 
'''GLOBAL CONSTANTS"""--------------------------------------------------GLOBAL CONSTANTS'''
# Height and Width of Display Surface
HEIGHT = 1080
WIDTH = 1980
SCREENPOSITION = 0
STAGESIZE = 180000
# Framerate
FPS = 30
# Physics constants for player
ACC = 1.5
FRIC = -0.07
GRAVITY = 1.8
JUMPHEIGHT = -20
TOPSPEED = 20
# Colors
PLAYERCOLOR = (12, 32, 19)
BACKGROUNDCOLOR = (255, 183, 184)
PLATFORMCOLOR = (176, 255, 176)

all_platforms = []
# determine if the line segments intersect

# noteRange
maxNote = 0 
minNote = 100000
'''Platform CLASS"""--------------------------------------------------Platform CLASS'''


class Platform(pygame.sprite.Sprite):

# 656 colors in default library in pygame.THECOLORS
    def __init__(self, channel, note, start, end, velocity, instrument, offVelocity):
        super().__init__()
        global tempo
        pygame.color.THECOLORS
        self.lengthRatio = TOPSPEED / tempo * (end - start)
        print('velocity: ', velocity)
        print(note , ' maxNote: ' , maxNote , ' minNote: ' , minNote)
        print(note * HEIGHT / (maxNote - minNote))
        self.rect = pygame.Rect(start * 500, (maxNote - note) * HEIGHT / (maxNote - minNote), (end - start) * 800, 4)
        self.surf = pygame.Surface((self.rect.width, self.rect.height))
        self.surf.fill(((channel + 634) * 452 % 255, (channel + 43) * 17 % 255, (channel + 1123) * 123 % 255))
        self.note = note
        self.channel = channel
        self.velocity = velocity
        self.offVelocity = offVelocity
        self.start = start
        self.end = end
        self.on = False
        self.instrument = instrument

    def playNote(self):
        if self.velocity == 0:
            Output.pitch_bend(self.note, self.channel) 
        if self.on == False:
            Output.set_instrument(self.instrument)
            Output.note_on(self.note, self.velocity // 2, self.channel)
            self.on = True

    def noteOff(self):  
        if self.on == True:
            Output.note_off(self.note, self.offVelocity, self.channel)
            self.on = False

            
class ground(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(0, HEIGHT - 10, STAGESIZE, 50)
        self.surf = pygame.Surface((self.rect.width, self.rect.height))
        
# class Line():
#     def __init__(self, x1, y1, x2 ,y2):
#         self.x1 = x1
#         self.y1 = y1
#         self.x2 = x2
#         self.y2 = y2
#         
#         self.slope = (y1- y2)/(x1 - x2)
#         self.slope = max(self.slope, self.slope*-1)
#     def getY(self, x):
#         return self.slope*(x - self.x1) + self.y1
#     def getX(self,y):
#         return (y -self.y1)/ self.slope + self.x1   
#     def intercept(self, otherLine):
#         if otherLine.slope == self.slope:
#             return None
#         
        
        
'''PLAYER CLASS"""--------------------------------------------------PLAYER CLASS'''


class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__() 
        self.size = 30
        self.surf = pygame.Surface((self.size, self.size))
        self.surf.fill(PLAYERCOLOR)
        self.rect = self.surf.get_rect()
        self.pos = vec((0, 0))
        self.screenPos = vec((0, 0))
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.currentPlatform = None
        
    def testCollision2(self, newPosition):
        L = Segment2D(Point(self.pos.x, self.pos.y), Point(newPosition.x, newPosition.y))
        for platforms in all_platforms:
            if newPosition.x > platforms.rect.left and newPosition.x < platforms.rect.left + platforms.rect.width:
            # if newPosition.y <= platforms.rect.top and self.pos.y >= platforms.rect.top:
                Y = Segment2D(Point(platforms.rect.left, platforms.rect.top), Point(platforms.rect.left + platforms.rect.width, platforms.rect.top))
                intercept = L.intersection(Y)
                if intercept:
                    return vec(intercept[0], intercept[1])
                
        return newPosition
        
    def testCollision(self, newPosition):
        for platforms in all_platforms:
            if newPosition.x > platforms.rect.left and newPosition.x < platforms.rect.left + platforms.rect.width:

                # points of line segments (A to B) (C to D)
                A = vec(platforms.rect.left, platforms.rect.top)
                B = vec(platforms.rect.left + platforms.rect.width, platforms.rect.top)
                
                # middle
                C = vec(self.pos[0], self.pos[1])
                D = vec(newPosition[0], newPosition[1])
                
                # right corner
                E = vec(self.pos[0] + 15, self.pos[1])
                F = vec(newPosition[0] + 15, newPosition[1])
                
                # left corner
                G = vec(self.pos[0] - 15, self.pos[1])
                H = vec(newPosition[0] - 15, newPosition[1])
                
                middleIntersection = helperFunctions.segmentsIntersect(B, A, C, D)
                # check if the segments intersect
                if middleIntersection:
                    self.onPlatform = True
                    self.currentPlatform = platforms
                    return helperFunctions.line_intersection((A, B), (C, D))                              
        self.currentPlatform = None
        return newPosition

    def getNotes(self):
        for platforms in all_platforms:
            if self.rect.right > platforms.rect.left and self.rect.left < platforms.rect.left + platforms.rect.width:
                if platforms.rect.width != STAGESIZE:
                    if platforms == self.currentPlatform:
                        platforms.playNote()
                    else:
                        platforms.playNote()
                platforms.on = True
                
            elif platforms.rect.width != STAGESIZE:
                platforms.noteOff()

    def move(self):
        self.acc = vec(0, 0)
        k = pygame.key.get_pressed()
        # move left
        if k[K_LEFT]:
            self.acc.x = -ACC
        # move right
        if k[K_RIGHT]:
            self.acc.x = ACC
            
        elif k[K_d]:
            self.acc.x = ACC / 2
        # drop through Platform
        if self.currentPlatform and k[K_DOWN]:
            self.currentPlatform = None
        # calculate acceleration and velocity
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        # limit velocity to TOPSPEED
        if self.vel.x < 0:
            self.vel = vec(max(self.vel.x, -TOPSPEED), self.vel[1])
        else:
            self.vel = vec(min(self.vel.x, TOPSPEED), self.vel[1])
        # no downward velocity when on platform
        if self.currentPlatform:
            self.vel.y = 0
        # jump
        if self.currentPlatform and k[K_UP]:
            self.currentPlatform = None
            self.vel.y = JUMPHEIGHT
            
        # apply gravity
        if not self.currentPlatform:
            self.vel.y += GRAVITY
        # calculate and set new position
        newPosition = self.pos + self.vel + 0.5 * self.acc
        if not self.currentPlatform and self.vel.y > 0:
            if not k[K_DOWN]:
                newPosition = self.testCollision(newPosition)
                
        self.pos = vec(newPosition[0], newPosition[1])
        self.rect.midbottom = self.pos
        # wrap vertically
        if(self.pos.y > HEIGHT):
            self.pos = vec(self.pos.x, 0)
        
        # if the player leaves the currentPlatform 
        if self.currentPlatform:
            # from the left side
            if self.pos.x < self.currentPlatform.rect.left and self.vel.x < 0 :
                self.currentPlatform = None
            # from the right side
            elif self.pos.x > self.currentPlatform.rect.left + self.currentPlatform.rect.width and self.vel.x > 0:
                    self.currentPlatform = None
        # determine note currently being played based on position
        self.getNotes()
        
        # adjust screen position for screen scrolling
        if self.pos.x >= WIDTH / 2:
            global SCREENPOSITION 
            SCREENPOSITION = self.rect.left
        if self.pos.x < WIDTH / 2 :
            SCREENPOSITION = 0
            self.screenPos.x = self.pos.x
        if self.pos.x >= STAGESIZE - WIDTH / 2:
            self.screenPos = self.pos.x - STAGESIZE - WIDTH / 2
    

'''INITIALIZATION"""--------------------------------------------------INITIALIZATION'''
FramePerSec = pygame.time.Clock()

# Display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")
# WINDOW
gameIcon = pygame.image.load(os.path.join(os.getcwd(), 'Assets', 'Icon.png')).convert()
pygame.display.set_icon(gameIcon)
# Players
P1 = Player()
# Player Sound effects
jumpSound = pygame.mixer.Sound(os.path.join(os.getcwd(), 'Assets', 'Sounds', 'jump.WAV'))
jumpSound.set_volume(.2)

# Midi parse
pygame.midi.init()
# proto = MidiFile(pygame.mixer.Sound(os.path.join(os.getcwd(), 'Assets', 'midi', 'Protoman.mid')))
proto = MidiFile("C:\\Users\\justi\\eclipse-workspace\\Python\\Game\\Assets\\midi\\Sonic_Advance_2_-_Hot_Crater_Act_1.mid")

Channels = []
Output = pygame.midi.Output(0)
# Channels[0] = pygame.midi.Output(1)
Output.set_instrument(58)  # 107
queue = [];
tempo = 500000
# default tempo

'''MIDI PARSING"""--------------------------------------------------MIDI PARSING'''


def parseMidi(MidiFile):
    Ground = ground()
    all_platforms.append(Ground)
    instrument = 0
    y = -150
    x = -(WIDTH / 32)
    index = -1
    z = 0
    tempo = 500000
    global maxNote         
    global minNote
    for msg in MidiFile:
        if msg.type == 'note_on':
            if msg.note > maxNote:
                maxNote = msg.note
            if msg.note < minNote:
                minNote = msg.note
        
    for msg in MidiFile:
        z += msg.time
        if msg.type == 'set_tempo':
            tempo = msg.tempo
        elif msg.type == 'program_change':
            instrument = msg.program
        elif msg.type == 'note_on' and msg.velocity != 0:
            # print(msg.note)
            # print(msg.velocity)
            y = 15
            x += WIDTH / 32
            index += 1
            
            platformData = (msg.channel, msg.note, z, msg.velocity)
            
            # currentPlatform = Platform(pygame.Rect(x, HEIGHT - msg.note*9 , WIDTH / 32, 5),index)
            queue.append(platformData)
            
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            for queuedPlatform in queue:
                if msg.note == queuedPlatform[1] and msg.channel == queuedPlatform[0]:
                    queue.remove(queuedPlatform)
                    all_platforms.append(Platform(queuedPlatform[0], queuedPlatform[1], queuedPlatform[2], z, queuedPlatform[3], instrument, msg.velocity))      
        elif msg.type == 'pitch_bend':
            all_platforms.append(Platform(msg.channel, msg.value, z, 0, 0, 0, 0))       
#     if not all_platforms:
#         for queuedPlatform in queue:
#             all_platforms.append((Platform(queuedPlatform[0],queuedPlatform[1],queuedPlatform[2],queuedPlatform[2] +.2,queuedPlatform[3],instrument, 0)))

                         
parseMidi(proto)
# Sprite Group
all_sprites = pygame.sprite.Group()
all_sprites.add(P1)

for platformz in all_platforms:
    all_sprites.add(platformz)

screen.fill(BACKGROUNDCOLOR)
'''MAIN LOOP"""--------------------------------------------------MAIN LOOP'''
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            del Output
            pygame.midi.quit()
            pygame.quit()
            sys.exit()
    
    screen.fill(BACKGROUNDCOLOR)
    for entity in all_sprites:
        if type(entity) == Platform :
            # if entity.rect.left >= SCREENPOSITION - WIDTH/2 and entity.rect.width + entity.rect.left <= SCREENPOSITION + WIDTH:
                if SCREENPOSITION >= WIDTH / 2:
                    entity.rect.left = entity.rect.left - SCREENPOSITION + WIDTH // 2 
                    screen.blit(entity.surf, entity.rect)
                    entity.rect.left = entity.rect.left + SCREENPOSITION - WIDTH // 2
                else:
                    screen.blit(entity.surf, entity.rect)
            
        if type(entity) == Player:
            entity.rect.left = (entity.screenPos.x)
            screen.blit(entity.surf, entity.rect)
                  
    P1.move() 
    screen.blit(helperFunctions.update_fps(FramePerSec), (10, 0))
    pygame.display.update()
    FramePerSec.tick(FPS)

