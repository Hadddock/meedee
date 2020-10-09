import sys 
import os
import pygame 
from pygame import midi
from pygame.locals import *
from mido import MidiFile
import tkinter
from tkinter import filedialog

pygame.init()
vec = pygame.math.Vector2 
'''GLOBAL CONSTANTS---------------------------------------GLOBAL CONSTANTS'''
# Height and Width of Display Surface
HEIGHT = 1080
WIDTH = 1980
SCREENPOSITION = 0
global STAGE_SIZE
STAGE_SIZE = 0

# Framerate
FPS = 60
# Player related constants
ACC = .7
FRIC = -0.035
GRAVITY = .7
JUMP_HEIGHT = -13
TOP_SPEED = 8
RUN_TOP_SPEED = 16
MAX_FALL_SPEED = 80
SIZE = 30
# Colors
PLAYER_COLOR = (12, 32, 19)
BACKGROUND_COLOR = (250, 240, 240)
RED = (213, 28, 60)
YELLOW = (241, 191, 21)
PURPLE = (147, 82, 168)
ORANGE = (247, 118, 11)
LIGHT_BLUE = (153, 198, 249)
BUFF = (200, 177, 139)
GREEN = (35, 234, 165)
PURPLISH_PINK = (244, 131, 205)
BLUE = (39, 108, 189)
YELLOWISH_PINK = (245, 144, 128)
VIOLET = (97, 65, 156)
PURPLISH_RED = (184, 55, 115)
GREENISH_YELLOW = (235, 221, 33)
REDDISH_BROWN = (139, 28, 14)
YELLOW_GREEN = (167, 220, 38)
YELLOW_BROWN = (103, 63, 11)
# Define array of channel colors
CHANNEL_COLORS = [
    RED, YELLOW, PURPLE, ORANGE,
    LIGHT_BLUE, BUFF, GREEN, PURPLISH_PINK,
    BLUE, YELLOWISH_PINK, VIOLET, PURPLISH_RED,
    GREENISH_YELLOW, REDDISH_BROWN, YELLOW_GREEN, YELLOW_BROWN,
    ]

# File Explorer
root = tkinter.Tk()
root.withdraw()
selectedMidi = None
defaultLocation = os.getcwd() + os.sep + 'Assets' + os.sep + 'midi'
while selectedMidi is None:
    try:
        selectedMidi = MidiFile(filedialog.askopenfilename(initialdir = defaultLocation , filetypes=[("Midi files", ".mid")]))
    except:
        print("please select a valid midi file")
    
all_platforms = []

# noteRange
maxNote = 0 
minNote = 100000
'''Platform CLASS---------------------------------------Platform CLASS'''


class Platform(pygame.sprite.Sprite):

    def __init__(self, channel, note, start, end, velocity, instrument, offVelocity, tempo):
        super().__init__()
        # global tempo
        self.lengthRatio = TOP_SPEED / tempo * (end - start)
        self.rect = pygame.Rect(start * 500, (maxNote - note) * HEIGHT / (maxNote - minNote), (end - start) * 800, 4)

        # minimum platform width is player Size,
        if self.rect.right - self.rect.left < SIZE:
            self.rect.width = SIZE
            
        self.surf = pygame.Surface((self.rect.width, self.rect.height))
        # assign color based on channel
        self.surf.fill(CHANNEL_COLORS[channel])
        self.channel = channel
        self.note = note
        self.start = start
        self.end = end
        self.velocity = velocity
        self.instrument = instrument
        self.offVelocity = offVelocity
        self.sorted = False
        self.on = False
        # test for end of stage
        global STAGE_SIZE 
        STAGE_SIZE = max(STAGE_SIZE, self.rect.right)

    def turn_note_on(self):
        """Begin playing the platform's note."""
        if self.velocity == 0:
            Output.pitch_bend(self.note, self.channel) 
        if not self.on:
            Output.set_instrument(self.instrument)
            Output.note_on(self.note, self.velocity // 2, self.channel)
            self.on = True
        self.surf.fill((max(CHANNEL_COLORS[self.channel][0] -50,0),max(CHANNEL_COLORS[self.channel][1] - 50,0),max(CHANNEL_COLORS[self.channel][2] - 50,0)))
        return None

    def turn_note_off(self): 
        """Stop playing the platform's note.""" 
        if self.on:
            Output.note_off(self.note, self.offVelocity, self.channel)
        self.on = False  
        self.surf.fill(CHANNEL_COLORS[self.channel]) 
        return None


class PlatformCollection():
    
    def __init__(self,Platforms, LeftCollection):
        self.LeftCollection = LeftCollection
        self.RightCollection = None
        self.min = Platforms[0].rect.left
        self.max = Platforms[-1].rect.right
        Platforms.sort(key=lambda x: x.rect.top, reverse=True)
        self.Platforms = Platforms
'''PLAYER CLASS-----------------------------------------------PLAYER CLASS'''


class Player(pygame.sprite.Sprite):
    
    def __init__(self):
        super().__init__() 
        self.size = SIZE
        self.surf = pygame.Surface((self.size, self.size))
        self.surf.fill(PLAYER_COLOR)
        self.rect = self.surf.get_rect()
        self.pos = vec(self.rect.bottomleft)
        self.screenPos = vec((0, 0))
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.currentPlatform = None

    def platform_collision(self, newPosition):
        """
        Return first platform the player collides with.
        If no platform is collided with, return None
        """
        for platform in all_platforms:
            if newPosition.x + self.rect.width > platform.rect.left and newPosition.x < platform.rect.left + platform.rect.width:

                # points of line segments (A to B) (C to D)
                A = vec(platform.rect.left, platform.rect.top)
                B = vec(platform.rect.right, platform.rect.top)
                
                # bottom left corner
                C = vec(self.pos[0], self.pos[1])
                D = vec(newPosition[0], newPosition[1])
                
                # bottom right corner
                E = vec(self.pos[0] + self.rect.width, self.pos[1])
                F = vec(newPosition[0] + self.rect.width, newPosition[1])
                
                leftIntersection = segments_intersect(B, A, C, D)
                
                rightIntersection = segments_intersect(B, A, E, F)
                # check if intersection with bottom left corner
                if leftIntersection:
                    self.onPlatform = True
                    self.currentPlatform = platform
                    return line_intersection((A, B), (C, D))
                # check if intersection with bottom right corner
                if rightIntersection:
                    self.onPlatform = True
                    self.currentPlatform = platform
                    returnValue = line_intersection((A, B), (E, F)) 
                    return (returnValue[0] - self.rect.width, returnValue[1])
                                              
        self.currentPlatform = None
        return newPosition
    
    def find_adjacent_platforms(self):
        """
        Return first platform at directly below the
        Player's current position. If no platforms
        are directly below the player, return None.
        """ 
        for platform in all_platforms:
            if platform != self.currentPlatform:
                if platform.rect.top == self.rect.bottom and (
                    self.rect.left < platform.rect.right and self.rect.right > platform.rect.left):
                    return platform
        return None

    def get_notes(self):
        """
        Turns on the notes of all platforms that overlap the Player's 
        x position and turns off all active notes that whose platform 
        no longer overlaps the Player's x position
        """ 
        # [platform.turn_note_on() if (self.rect.right > platform.rect.left and self.rect.left < platform.rect.left + platform.rect.width) else platform.turn_note_off for platform in all_platforms]
        for platform in all_platforms:
            if self.rect.right > platform.rect.left and self.rect.left < platform.rect.left + platform.rect.width:
                        platform.turn_note_on()
            elif platform.on:
                platform.turn_note_off()
        return None
    
    def move(self):
        "Sets the Player's position on the next frame"
        self.acc = vec(0, 0)
        k = pygame.key.get_pressed()
        # move left
        if k[K_LEFT]:
            self.acc.x = -ACC
            if k[K_LSHIFT]:
                self.acc.x = -ACC 
        # move right
        if k[K_RIGHT]:
            self.acc.x = ACC
            if k[K_LSHIFT]:
                self.acc.x = ACC 
        # drop through Platform
        if self.currentPlatform and k[K_DOWN]:
            self.currentPlatform = None
        # calculate acceleration and velocity
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        # limit max falling speed
        self.vel.y = min (self.vel.y, MAX_FALL_SPEED)
    
        # limit x velocity to TOP_SPEED
        if k[K_LSHIFT]:
            if self.vel.x < 0:
                self.vel = vec(max(self.vel.x, -TOP_SPEED * 1.3), self.vel[1])
            else:
                self.vel = vec(min(self.vel.x, TOP_SPEED * 1.3), self.vel[1])  
        else:
            if self.vel.x < 0:
                self.vel = vec(max(self.vel.x, -TOP_SPEED), self.vel[1])
            else:
                self.vel = vec(min(self.vel.x, TOP_SPEED), self.vel[1])
        # if on a platform, no downward velocity, check for jump input
        if self.currentPlatform is not None:
            self.vel.y = 0
            if k[K_UP]:
                self.currentPlatform = None
                self.vel.y = JUMP_HEIGHT
        # apply gravity if not on a platform
        else:
            self.vel.y += GRAVITY
        # calculate new position on the assumption no platform is collided with
        newPosition = self.pos + self.vel + 0.5 * self.acc
        if self.currentPlatform is None and self.vel.y > 0:
            if not k[K_DOWN]:
                # determine real new position by checking for platform collision
                newPosition = self.platform_collision(newPosition)
        # set new position                
        self.pos = vec(newPosition[0], newPosition[1])
        self.rect.bottomleft = self.pos

        # wrap vertically when falling below screen
        if(self.pos.y > HEIGHT):
            self.pos = vec(self.pos.x, 0)
        
        # cases for sliding off platform
        if self.currentPlatform is not None:
            # from the left side
            if self.rect.bottomleft[0] >= self.currentPlatform.rect.right or self.rect.bottomright[0] <= self.currentPlatform.rect.left:
                self.currentPlatform = self.find_adjacent_platforms()
        # determine note currently being played based on position
        self.get_notes()
        global beforeHalfScreen
        
        # adjust screen position for scrolling
        if self.pos.x > WIDTH / 2 + 10:
            global SCREENPOSITION 
            if beforeHalfScreen:
                self.rect.bottomleft = (WIDTH / 2, self.rect.bottomleft[1])
                beforeHalfScreen = False
                # manually set screen position, keeps player consistently centered on screen,
                # otherwise its possible to go past screenWidth / 2 + 10 and have
                # the player slightly off center
                self.screenPos.x = WIDTH / 2
            SCREENPOSITION = self.rect.left
        if self.pos.x < WIDTH / 2 :
            beforeHalfScreen = True
            SCREENPOSITION = 0
            self.screenPos.x = self.pos.x
        if self.pos.x > STAGE_SIZE - (WIDTH / 2) - SIZE:
            if self.pos.x > STAGE_SIZE - SIZE :
                self.pos.x = STAGE_SIZE - SIZE
            self.screenPos.x = WIDTH / 2
        return None

    
'''INITIALIZATION"""------------------------------------------INITIALIZATION'''
FramePerSec = pygame.time.Clock()
# Display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")
# WINDOW
gameIcon = pygame.image.load(os.path.join(os.getcwd(), 'Assets', 'Icon.png')).convert()
pygame.display.set_icon(gameIcon)
# Players
P1 = Player()

# Midi parse
midi.init()

Output = pygame.midi.Output(0)
Channels = []
queue = [];

'''MIDI PARSING-------------------------------------------------MIDI PARSING'''


def process_midi(MidiFile):
    "Generate an array of"
    instrument = 0
    x = -(WIDTH / 32)
    startTime = 0
    tempo = 500000
    global maxNote         
    global minNote
    all_platforms = []
    for msg in MidiFile:
        if msg.type == 'note_on':
            if msg.note > maxNote:
                maxNote = msg.note
            if msg.note < minNote:
                minNote = msg.note
                
    for msg in MidiFile:
        startTime += msg.time
        if msg.type == 'set_tempo':
            tempo = msg.tempo
        elif msg.type == 'program_change':
            instrument = msg.program
        elif msg.type == 'note_on' and msg.velocity != 0:
            x += WIDTH / 32
            platformData = (msg.channel, msg.note, startTime, msg.velocity, tempo)
            queue.append(platformData)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            for queuedPlatform in queue:
                # if note and channel match the corresponding note has been found, create the platform
                if msg.note == queuedPlatform[1] and msg.channel == queuedPlatform[0]:
                    queue.remove(queuedPlatform)
                    currentPlatform = Platform(queuedPlatform[0], queuedPlatform[1], queuedPlatform[2], startTime, queuedPlatform[3], instrument, msg.velocity, queuedPlatform[4])
                    all_platforms.append(currentPlatform)      
        elif msg.type == 'pitch_bend':
            all_platforms.append(Platform(msg.channel, msg.value, startTime, 0, 0, 0, 0))   
    return all_platforms


all_platforms = process_midi(selectedMidi)
# Sprite Group
all_sprites = pygame.sprite.Group()
all_sprites.add(P1)
platforms1 = []
platforms2 = []
platforms3 = []
platforms4 = []
platforms5 = []
platforms6 = []
for platform in all_platforms:
    if platform.rect.left < STAGE_SIZE/6 and platform.sorted is not True :
        platform.sorted = True
        platforms1.append(platform)
    if platform.rect.left < STAGE_SIZE/6 * 2 and platform.sorted is not True :
        platform.sorted = True
        platforms2.append(platform)
    if platform.rect.left < STAGE_SIZE/6 * 3 and platform.sorted is not True :
        platform.sorted = True
        platforms3.append(platform)
    if platform.rect.left < STAGE_SIZE/6 * 4 and platform.sorted is not True :
        platform.sorted = True
        platforms4.append(platform)
    if platform.rect.left < STAGE_SIZE/6 * 5 and platform.sorted is not True :
        platform.sorted = True
        platforms5.append(platform)    
    if platform.sorted is not True:
        platforms6.append(platform)


platforms1 = PlatformCollection(platforms1, None)
platforms2 = PlatformCollection(platforms2, platforms1)
platforms3 = PlatformCollection(platforms3, platforms2)
platforms4 = PlatformCollection(platforms4, platforms3)
platforms5 = PlatformCollection(platforms5, platforms4)
platforms6 = PlatformCollection(platforms6, platforms5)


all_platforms.sort(key=lambda x: x.rect.top, reverse=True)
for platform in all_platforms:
    all_sprites.add(platform)
'''HELPER METHODS-----------------------------------------------------HELPER METHODS'''    


def update_fps(FramePerSec):
    """Return current FPS"""
    FPS = str(int(FramePerSec.get_fps()))
    font = pygame.font.SysFont("freesansbold.ttf", 18)
    FPS_DISPLAY = font.render(FPS, 1, (0, 0, 0))
    return FPS_DISPLAY


def segments_intersect(A, B, C, D):
    """
    Return whether or not the segment formed by A and B
    intersects the segment formed by C and D
    
    """

    def ccw(A, B, C):
        return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x) 

    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def line_intersection(line1, line2):
    """Return the intersection point of line1 and line2"""
    
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        return None
    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


'''MAIN LOOP-----------------------------------------------------MAIN LOOP'''
while True:
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                del Output
                pygame.midi.quit()
                pygame.quit()
                sys.exit()
    P1.move() 
    screen.fill(BACKGROUND_COLOR)
    for entity in all_sprites:
        if type(entity) == Platform:
            # only blit platform within viewing distance
            if entity.rect.width > WIDTH or (
                entity.rect.right >= SCREENPOSITION - WIDTH / 2 and 
                entity.rect.width + entity.rect.left <= SCREENPOSITION + WIDTH + WIDTH):
                if SCREENPOSITION >= WIDTH / 2:
                    entity.rect.left = entity.rect.left - SCREENPOSITION + WIDTH / 2 
                    screen.blit(entity.surf, entity.rect)
                    entity.rect.left = entity.rect.left + SCREENPOSITION - WIDTH / 2
                else:
                    screen.blit(entity.surf, entity.rect)
            
        elif type(entity) == Player:
            entity.rect.left = (entity.screenPos.x)
            screen.blit(entity.surf, entity.rect)
    # update fps counter
    screen.blit(update_fps(FramePerSec), (10, 0))
    # Line marking center screen
    # r = pygame.draw.line(screen, (0,0,0), ( WIDTH/2,0),( WIDTH/2, HEIGHT),2)
    pygame.display.update()
    FramePerSec.tick(FPS)
