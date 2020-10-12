import sys 
import os

from constants import *
from helper import *
from pygame import midi
from pygame.locals import *
from mido import MidiFile
import tkinter
from tkinter import filedialog

global STAGE_SIZE
STAGE_SIZE = 0

def resource_path(relative_path):
    try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
        pass
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
class Platform(pygame.sprite.Sprite):
    """A Platform generated from midi note data"""
    def __init__(self, channel, note, start, end, velocity, instrument, offVelocity, tempo):
        """
        Parameters:
            channel (int) : 0-15 representing the channel the note is played on
            note (int) : 0-127 representing note number 
            start (int) : 0
        """
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
        self.surf.fill((max(CHANNEL_COLORS[self.channel][0] - 50, 0), max(CHANNEL_COLORS[self.channel][1] - 50, 0), max(CHANNEL_COLORS[self.channel][2] - 50, 0)))
        return None

    def turn_note_off(self): 
        """Stop playing the platform's note.""" 
        if self.on:
            Output.note_off(self.note, self.offVelocity, self.channel)
        self.on = False  
        self.surf.fill(CHANNEL_COLORS[self.channel]) 
        return None
class pitchBend(Platform):
    def turn_note_on(self): 
        Output.pitch_bend(self.note, self.channel)
    def turn_note_off(self):
        pass
class PlatformCollection():
    
    def __init__(self, LeftCollection):
        self.right = None
        
        self.min = sys.maxsize
        self.max = 0
        self.platforms = []
        self.active = False
        self.left = LeftCollection
        if self.left is None:
            self.left = self
        self.active = False
        self.right = self
    def append(self, Platform):
        self.min = min(self.min, Platform.rect.left)
        self.max = max(self.max,Platform.rect.right)
        self.platforms.append(Platform)
    def sort(self):
        self.platforms.sort(key=lambda x: x.rect.top, reverse=True)

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
        Return first platform the player collides with while moving to newPosition.
        If no platform is collided with, return None
        """
        for PlatformCollection in all_platforms:
            if PlatformCollection.active:
                for platform in PlatformCollection.platforms:
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
                        elif rightIntersection:
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
        for PlatformCollection in all_platforms:
            if PlatformCollection.active:
                for platform in PlatformCollection.platforms:
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
        for PlatformCollection in all_platforms:
            if PlatformCollection.active:
                for platform in PlatformCollection.platforms:
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
        if self.pos.x < 0:
            self.pos.x = 0
        return None

def process_midi(MidiFile):
    "Generate a list of platform collections from a MidiFile"
    all_platforms = []
    all_platform_collections = []
    all_platform_collections.append(PlatformCollection(None))
    for x in range (COLLECTIONS_COUNT-1):
        all_platform_collections.append(PlatformCollection(all_platform_collections[x]))
        all_platform_collections[x].right = all_platform_collections[x+1]
 
    instrument = 0
    #x coordinate of platform
    x = -(WIDTH / 32)
    startTime = 0
    #current tempo
    tempo = 500000
    global maxNote         
    global minNote
    for msg in MidiFile:
        if msg.type == 'note_on':
            maxNote = max(msg.note, maxNote)
            minNote = min(msg.note, minNote)
            
 
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
       
                    break
        elif msg.type == 'pitchwheel':
            all_platforms.append(pitchBend(msg.channel,msg.pitch,startTime,startTime,0,0,0,tempo))
            pass
            
            #all_platform_collections.append(Platform(msg.channel, msg.value, startTime, 0, 0, 0, 0))
    for platform in all_platforms:
        for x in range(COLLECTIONS_COUNT):
            if platform.rect.left < (STAGE_SIZE /(COLLECTIONS_COUNT) *( x+1)) or (x == COLLECTIONS_COUNT-1):
                all_platform_collections[x].append(platform)
                break
    for x in range (COLLECTIONS_COUNT):
        all_platform_collections[x].sort()
    return all_platform_collections

'''INITIALIZATION--------------------------------------------INITIALIZATION'''   
pygame.init()
FramePerSec = pygame.time.Clock()
vec = pygame.math.Vector2 
# File Explorer
root = tkinter.Tk()
root.withdraw()
selectedMidi = None
defaultLocation = os.getcwd() + os.sep + 'Assets' + os.sep + 'midi'
while selectedMidi is None:
    try:
        file = filedialog.askopenfilename(initialdir=defaultLocation , title="Please select a midi file", filetypes=[("Midi files", ".mid")])
        
        selectedMidi = MidiFile(file)
    except:
        # exit if select file dialog closed
        if file == "":
            quit()
        print("please select a valid midi file")
    
all_platforms = []

# noteRange
maxNote = 0 
minNote = 100000

# Display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")
# WINDOW
#gameIcon = pygame.image.load(os.path.join(os.getcwd(), 'Assets', 'Icon.png')).convert()
#pygame.display.set_icon(gameIcon)
# Players
P1 = Player()


midi.init()

Output = pygame.midi.Output(0)
Channels = []
queue = [];

all_platforms = process_midi(selectedMidi)
# Sprite Group
all_sprites = pygame.sprite.Group()
all_sprites.add(P1)

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
    for PlatformCollection in all_platforms:
        #if platform collection contains platforms within potential player collision, or if
        #a neighboring platform collection is within potential player collision, set active and blit
        if (PlatformCollection.min <= P1.pos.x + SIZE * 2 and PlatformCollection.max >= P1.pos.x - SIZE * 2) or (
            PlatformCollection.left.min <= P1.pos.x + SIZE * 2 and PlatformCollection.left.max >= P1.pos.x - SIZE * 2) or (
            PlatformCollection.right.min <= P1.pos.x + SIZE * 2 and PlatformCollection.right.max >= P1.pos.x - SIZE * 2):
            
            PlatformCollection.active = True
            for Platform in PlatformCollection.platforms:
            # only blit platform within viewing distance
                # if  Platform.rect.right >= SCREENPOSITION - WIDTH / 2 and Platform.rect.left <= SCREENPOSITION + WIDTH + WIDTH:
                    if SCREENPOSITION >= WIDTH / 2:
                        Platform.rect.left = Platform.rect.left - SCREENPOSITION + WIDTH / 2 
                        screen.blit(Platform.surf, Platform.rect)
                        Platform.rect.left = Platform.rect.left + SCREENPOSITION - WIDTH / 2
                    else:
                        screen.blit(Platform.surf, Platform.rect)
        else:
            PlatformCollection.active = False   
    #blit player
    P1.rect.left = (P1.screenPos.x)
    screen.blit(P1.surf, P1.rect)
            
    # update fps counter
    #screen.blit(update_fps(FramePerSec), (10, 0))
    # Line marking center screen
    # r = pygame.draw.line(screen, (0,0,0), ( WIDTH/2,0),( WIDTH/2, HEIGHT),2)
    pygame.display.update()
    FramePerSec.tick(FPS)
