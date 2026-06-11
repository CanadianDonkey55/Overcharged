# Programmer(s): Devin Murphy, Jayden Li
# Date:
# Description: Game about surviving a shift on a damaged space station.
import random
import pygame
from pygame import *
from pygame.sprite import *

# define colour constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_RED = (100, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARK_GREY = (40, 44, 52)      # Station flooring color
LIGHT_GREY = (90, 95, 105)    # Station wall color
GRID_LINE = (30, 30, 35)      # Grid overlay lines
OVERLAY_COLOR = (20, 20, 20, 180) # Semi-transparent color for pause overlay
### ADD ANY OTHER COLOUR CONSTANTS HERE ###

# define system constants
FPS = 60
#info = pygame.display.Info()
WIDTH = 640
HEIGHT = 480
BGCOLOUR = BLACK ### CHANGE AS NEEDED ###

# Changes the size of the tiles
TILE_SIZE = 128

# initialize pygame, create window, start the clock
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# --- GAME STATE CONSTANTS ---
MAIN_MENU = "main_menu"
IN_GAME = "in_game"
PAUSED = "paused"
scene = MAIN_MENU

EASY = 15
MEDIUM = 10
HARD = 5
currentDifficulty = EASY

# Fonts for on screen things
timerFont = pygame.font.SysFont("Arial", 50)
menuFont = pygame.font.SysFont("Arial", 40)
titleFont = pygame.font.SysFont("Arial", 80, bold=True)
TIMER_SECONDS = 600

# Tracks total time elapsed during pauses to keep game clock accurate
pausedTimeAccumulator = 0
pauseStartTick = 0

# Dice roll timer creation
DICE_ROLL_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(DICE_ROLL_EVENT, currentDifficulty * 1000)

# Damage timer creation
DAMAGE_EVENT = pygame.USEREVENT + 2
MIN_TIME = 1
MAX_TIME = 5
randomDelay = random.randint(MIN_TIME * 1000, MAX_TIME * 1000)
pygame.time.set_timer(DAMAGE_EVENT, randomDelay)

# MAP LAYOUT DATA
# 0 = Normal Floor, 1 = Wall, 2 = Damaged Floor, 3 = Generator
# Calculates the sizes to fill up the entire window
COLS = screen.get_width() // TILE_SIZE + 1
ROWS = screen.get_height() // TILE_SIZE + 1

# Map is 15 wide, 9 tall
gridMap = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

wallRects = []
for rowIndex, row in enumerate(gridMap):
    for columnIndex, tileType in enumerate(row):
        if tileType == 1 or tileType == 3:
            x = columnIndex * TILE_SIZE
            y = rowIndex * TILE_SIZE
            wallRects.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

# Powerup creation
speedMultiplier = 1
repairMultiplier = 1
timerMultiplier = 1

chosenPowerup = ""

powerups = [
    "speed", "faster repair", "slower timer"
]

debuffs = [
    "slowness", "slower repair", "faster timer"
]

### ADD YOUR SPRITE CLASSES HERE ###
class ImageSprite(Sprite):
    def __init__(self, x, y, filename):                    # NEW sprite at (x,y)
        Sprite.__init__(self)                              # init the Sprite object
        self.image = image.load(filename).convert_alpha()      # loads the image from filename as the sprite
        self.rect = self.image.get_rect()

        self.rect.x = x
        self.rect.y = y

    # semi-optional part
    def update(self):
        ### ADD MOVEMENT MODIFIERS HERE ###
        pass

    def setPosition(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def changeImage(self, filename):
        self.image = image.load(filename).convert()

class PlayerSprite(ImageSprite):
    def __init__(self, x, y, filename):
        super().__init__(x, y, filename)

        self.rightMovementFrames = [
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Forward/forward0.png").convert_alpha(), 4),
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Forward/forward1.png").convert_alpha(), 4),
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Forward/forward2.png").convert_alpha(), 4),
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Forward/forward3.png").convert_alpha(), 4),
        ]

        self.leftMovementFrames = [
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Backward/backward0.png").convert_alpha(), 4),
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Backward/backward1.png").convert_alpha(), 4),
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Backward/backward2.png").convert_alpha(), 4),
            pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Backward/backward3.png").convert_alpha(), 4),
        ]

        self.idleFrame = pygame.transform.scale_by(pygame.image.load(filename).convert_alpha(), 4)

        self.currentFrameIndex = 0
        self.animationSpeed = 0.15
        self.facingDirection = "right"
        self.isMoving = False

    def moveHorizontal(self, direction):
        self.rect.x += 5 * direction * speedMultiplier
        self.isMoving = True
        if direction > 0:
            self.facingDirection = "right"
        elif direction < 0:
            self.facingDirection = "left"

    def moveVertical(self, direction):
        self.rect.y += 5 * direction * speedMultiplier
        self.isMoving = True

    def update(self):
        if self.isMoving:
            self.currentFrameIndex += self.animationSpeed

            if self.facingDirection == "right":
                if self.currentFrameIndex >= len(self.rightMovementFrames):
                    self.currentFrameIndex = 0
                self.image = self.rightMovementFrames[int(self.currentFrameIndex)]
            elif self.facingDirection == "left":
                if self.currentFrameIndex >= len(self.leftMovementFrames):
                    self.currentFrameIndex = 0
                self.image = self.leftMovementFrames[int(self.currentFrameIndex)]
        else:
            self.image = self.idleFrame
            self.currentFrameIndex = 0

        self.isMoving = False

class ButtonSprite(Sprite):
    def __init__(self, centerX, centerY, text, action, filename):
        Sprite.__init__(self)
        self.action = action
        self.image = pygame.image.load(filename).convert_alpha()
        textSurface = menuFont.render(text, True, WHITE)
        textRect = textSurface.get_rect(center=(175, 30))
        self.image.blit(textSurface, textRect)
        self.rect = self.image.get_rect(center=(centerX, centerY))

    def checkClick(self, mousePos):
        if self.rect.collidepoint(mousePos):
            self.action()

### BUTTON FUNCTIONS ###
def startGame():
    global scene, pausedTimeAccumulator
    scene = IN_GAME
    pausedTimeAccumulator = pygame.time.get_ticks()

def quitGame():
    global running
    running = False

def resumeGame():
    global scene, pausedTimeAccumulator, pauseStartTick
    scene = IN_GAME
    pausedTimeAccumulator += (pygame.time.get_ticks() - pauseStartTick)

def returnToMenu():
    global scene
    scene = MAIN_MENU

### BUTTON SPRITE INSTANCES ###
menuPlayButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2, "Start Shift", startGame, "Assets/Sprites/UI/Button.png")
menuQuitButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2 + 80, "Abandon Ship", quitGame, "Assets/Sprites/UI/Button.png")

pauseResumeButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2, "Resume Shift", resumeGame, "Assets/Sprites/UI/Button.png")
pauseQuitButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2 + 80, "Return to Menu", returnToMenu, "Assets/Sprites/UI/Button.png")

# Group handling for UI
mainMenuButtons = pygame.sprite.Group(menuPlayButton, menuQuitButton)
pauseMenuButtons = pygame.sprite.Group(pauseResumeButton, pauseQuitButton)

### ADD SPRITE INSTANCES HERE ###
player = PlayerSprite(900, 500, "Assets/Sprites/Player/Forward/forward_idle.png")
player.image = pygame.transform.scale_by(player.image, 4)
player.rect = player.image.get_rect(topleft=(900, 500))
player.rect = player.rect.inflate(-40, -40)

floorTileImage = pygame.image.load("Assets/Sprites/Map/SpaceFloorTile.png").convert()
floorTileImage = pygame.transform.scale(floorTileImage, (TILE_SIZE, TILE_SIZE))

damagedTileImage = pygame.image.load("Assets/Sprites/Map/DamagedSpaceTile.png").convert()
damagedTileImage = pygame.transform.scale(damagedTileImage, (TILE_SIZE, TILE_SIZE))

wallTileImage = pygame.image.load("Assets/Sprites/Map/SpaceWallTile.png").convert()
wallTileImage = pygame.transform.scale(wallTileImage, (TILE_SIZE, TILE_SIZE))

generatorTileImage = pygame.image.load("Assets/Sprites/Map/GeneratorDesign.png").convert_alpha()
generatorTileImage = pygame.transform.scale(generatorTileImage, (TILE_SIZE, TILE_SIZE))

dice1 = "Assets/Sprites/Dice/Dice1.png"
dice2 = "Assets/Sprites/Dice/Dice2.png"
dice3 = "Assets/Sprites/Dice/Dice3.png"
dice4 = "Assets/Sprites/Dice/Dice4.png"
dice5 = "Assets/Sprites/Dice/Dice5.png"
dice6 = "Assets/Sprites/Dice/Dice6.png"
emptyDice = "Assets/Sprites/Dice/EmptyDice.png"

dice = ImageSprite(1800, 950, emptyDice)
dice.image = pygame.transform.scale_by(dice.image, 5)

### SOUND INITIALIZATION ###
diceRollSound = pygame.mixer.Sound("Assets/Audio/DiceRoll.mp3")
panelSparkSound = pygame.mixer.Sound("Assets/Audio/PanelSpark.mp3")
wrenchRepairSound = pygame.mixer.Sound("Assets/Audio/Wrench.mp3")

### OTHER CLASSES OR FUNCTIONS ###
def rollDice(numberOfDice):
    number = 0
    for i in range(numberOfDice):
        number += random.randint(1, 6)
    diceRollSound.play()
    return number

def changeDiceImage(num):
    global chosenPowerup
    if num == 1:
        dice.changeImage(dice1)
        chosenPowerup = random.choice(debuffs)
    elif num == 2:
        dice.changeImage(dice2)
        chosenPowerup = random.choice(debuffs)
    elif num == 3:
        dice.changeImage(dice3)
    elif num == 4:
        dice.changeImage(dice4)
    elif num == 5:
        dice.changeImage(dice5)
        chosenPowerup = random.choice(powerups)
    elif num == 6:
        dice.changeImage(dice6)
        chosenPowerup = random.choice(powerups)
    dice.image = pygame.transform.scale_by(dice.image, 5)
    applyEffect(chosenPowerup)
    print(chosenPowerup)

def applyEffect(effect):
    global speedMultiplier
    global repairMultiplier
    global timerMultiplier

    match effect:
        case "speed":
            speedMultiplier = 2
        case "faster repair":
            repairMultiplier = 2
        case "slower timer":
            timerMultiplier = 0.5
        case "slowness":
            speedMultiplier = 0.75
        case "slower repair":
            repairMultiplier = 0.5
        case "faster timer":
            timerMultiplier = 2
        case _:
            speedMultiplier = 1
            repairMultiplier = 1
            timerMultiplier = 1

def drawGrid():
    for rowIndex, row in enumerate(gridMap):
        for columnIndex, tileType in enumerate(row):
            x = columnIndex * TILE_SIZE
            y = rowIndex * TILE_SIZE

            tileRect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            if tileType == 0:
                screen.blit(floorTileImage, (x, y))
            elif tileType == 1:
                screen.blit(wallTileImage, (x, y))
            elif tileType == 2:
                screen.blit(damagedTileImage, (x, y))
            elif tileType == 3:
                screen.blit(generatorTileImage, (x, y))

            pygame.draw.rect(screen, GRID_LINE, tileRect, 1)

def damageTile(row, column):
    if gridMap[row][column] == 0:
        gridMap[row][column] = 2
        panelSparkSound.play()
    elif gridMap[row][column] == 1:
        gridMap[row][column] = 1

def repairTile(row, column):
    if gridMap[row][column] == 2:
        gridMap[row][column] = 0
        wrenchRepairSound.play()
    elif gridMap[row][column] == 3:
        gridMap[row][column] = 1

def drawMainMenu():
    screen.fill(BLACK)

    titleSurface = titleFont.render("OVERCHARGED", True, RED)
    titleRect = titleSurface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
    screen.blit(titleSurface, titleRect)

    mainMenuButtons.draw(screen)

def drawPauseMenu():
    # Dims the background game scene using a transparency layer
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))

    pauseSurface = titleFont.render("SHIFT PAUSED", True, WHITE)
    pauseRect = pauseSurface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
    screen.blit(pauseSurface, pauseRect)

    pauseMenuButtons.draw(screen)

# group sprites
allSprites = pygame.sprite.Group(player, dice)

# game loop
running = True
while running:
    # keep loop running at the right speed
    clock.tick(FPS)

    # process input (events)
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mousePos = pygame.mouse.get_pos()
                if scene == MAIN_MENU:
                    for button in mainMenuButtons:
                        button.checkClick(mousePos)
                elif scene == PAUSED:
                    for button in pauseMenuButtons:
                        button.checkClick(mousePos)

        elif event.type == pygame.KEYUP:
            if scene == IN_GAME:
                if event.key == pygame.K_ESCAPE:
                    scene = PAUSED
                    pauseStartTick = pygame.time.get_ticks()
            elif scene == PAUSED:
                if event.key == pygame.K_ESCAPE:
                    resumeGame()

        if scene == IN_GAME:
            # ROLLS DICE
            if event.type == DICE_ROLL_EVENT:
                currentDiceNumber = rollDice(1)
                changeDiceImage(currentDiceNumber)
            # CAUSES DAMAGE
            elif event.type == DAMAGE_EVENT:
                # Picks a random tile to damage
                randomRow = random.randint(0, len(gridMap) - 1)
                randomColumn = random.randint(0, len(gridMap[randomRow]) - 1)
                damageTile(randomRow, randomColumn)

                # Reset the timer to cause a random delay
                nextDelay = random.randint(MIN_TIME * 1000, MAX_TIME * 1000)
                pygame.time.set_timer(DAMAGE_EVENT, nextDelay)

    # Game state handling
    if scene == MAIN_MENU:
        drawMainMenu()

    elif scene == PAUSED:
        drawPauseMenu()

    elif scene == IN_GAME:
        # game loop updates (including movement)
        allSprites.update()

        # check for keypresses
        keys = pygame.key.get_pressed()

        # PLAYER MOVEMENT
        if keys[K_LEFT] or keys[K_a]:
            player.moveHorizontal(-1)
            if player.rect.collidelist(wallRects) != -1:
                player.moveHorizontal(1)
        if keys[K_RIGHT] or keys[K_d]:
            player.moveHorizontal(1)
            if player.rect.collidelist(wallRects) != -1:
                player.moveHorizontal(-1)
        if keys[K_UP] or keys[K_w]:
            player.moveVertical(-1)
            if player.rect.collidelist(wallRects) != -1:
                player.moveVertical(1)
        if keys[K_DOWN] or keys[K_s]:
            player.moveVertical(1)
            if player.rect.collidelist(wallRects) != -1:
                player.moveVertical(-1)

        # REPAIR DAMAGE
        if keys[K_e]:
            playerRow = player.rect.centery // TILE_SIZE
            playerColumn = player.rect.centerx // TILE_SIZE

            if 0 <= playerRow < len(gridMap) and 0 <= playerColumn < len(gridMap[0]):
                repairTile(playerRow, playerColumn)

        # background fill
        screen.fill(BGCOLOUR)

        drawGrid()

        # Display timer on screen with adjustments for pause times
        secondsPassed = (pygame.time.get_ticks() - pausedTimeAccumulator) // 1000
        timeRemaining = TIMER_SECONDS - secondsPassed

        if timeRemaining <= 0:
            timeRemaining = 0

        minutes = timeRemaining // 60
        seconds = timeRemaining % 60

        timerString = f"{minutes}:{seconds:02d}"
        if timeRemaining > 30:
            timerSurface = timerFont.render(timerString, True, WHITE)
        else:
            timerSurface = timerFont.render(timerString, True, RED)

        timerRect = timerSurface.get_rect(midtop=(screen.get_width() // 2, 20))
        screen.blit(timerSurface, timerRect)

        # render sprites on screen
        allSprites.draw(screen)

    # ***AFTER*** drawing everything, flip (update) the display
    pygame.display.flip()

pygame.quit()