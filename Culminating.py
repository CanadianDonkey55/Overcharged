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
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

### ADD ANY OTHER COLOUR CONSTANTS HERE ###
YELLOW = (255, 165, 0)
DARK_RED = (100, 0, 0)
DARK_GREY = (40, 44, 52)
LIGHT_GREY = (90, 95, 105)
GRID_LINE = (30, 30, 35)
OVERLAY_COLOR = (20, 20, 20, 180) # Semi-transparent color for pause overlay

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
GAME_OVER = "game_over"
WIRE_MINIGAME = "wire_minigame"
scene = MAIN_MENU

# Fonts for on screen things
timerFont = pygame.font.SysFont("Arial", 50)
menuFont = pygame.font.SysFont("Arial", 40)
titleFont = pygame.font.SysFont("Arial", 80, bold=True)
uiFont = pygame.font.SysFont("Arial", 30, bold=True)
TIMER_SECONDS = 600

# Tracking variables for scaled time and repair stats
gameTimeAccumulator = 0.0
lastTickTime = 0
tilesRepairedCount = 0

# Damage intervals in miliseconds
minDamageInterval = 500
maxDamageInterval = 3000

# Dice roll timer creation
DICE_ROLL_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(DICE_ROLL_EVENT, 15000) # 15 seconds between each dice roll

# Damage timer creation
DAMAGE_EVENT = pygame.USEREVENT + 2
randomDelay = random.randint(minDamageInterval, maxDamageInterval)
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
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

totalFloorTiles = sum(row.count(0) + row.count(2) for row in gridMap)

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
    "speed", "less repairs", "slower timer"
]

debuffs = [
    "slowness", "increased repairs", "faster timer"
]

### WIRE MINIGAME SYSTEMS ###
wireColors = [RED, GREEN, BLUE, YELLOW]
targetWireColor = RED
selectedNode = None
currentDragPos = (0, 0)
activeRepairTile = (0, 0) # Stores (row, col) currently being fixed
leftNodes = []
rightNodes = []

def startWireMinigame(row, col):
    global scene, targetWireColor, selectedNode, activeRepairTile, leftNodes, rightNodes

    panelOpenSound.play()

    activeRepairTile = (row, col)
    selectedNode = None

    # Select which color wire needs to be reconnected
    targetWireColor = random.choice(wireColors)

    # Generate random layouts for both sides so the paths cross in a tangle
    leftColors = list(wireColors)
    rightColors = list(wireColors)
    random.shuffle(leftColors)
    random.shuffle(rightColors)

    # UI Setup
    screenW = screen.get_width()
    screenH = screen.get_height()
    panelW, panelH = 600, 400
    startX = (screenW - panelW) // 2
    startY = (screenH - panelH) // 2

    leftNodes = []
    rightNodes = []

    # Create interactive bounding boxes for mouse selections
    for i, color in enumerate(leftColors):
        nodeY = startY + 80 + (i * 80)
        rect = pygame.Rect(startX + 40, nodeY - 15, 30, 30)
        leftNodes.append({"rect": rect, "color": color})

    for i, color in enumerate(rightColors):
        nodeY = startY + 80 + (i * 80)
        rect = pygame.Rect(startX + panelW - 70, nodeY - 15, 30, 30)
        rightNodes.append({"rect": rect, "color": color})

    scene = WIRE_MINIGAME

def drawWireMinigame():
    # Dim the game scene underneath
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))

    # Central minigame terminal
    panelW, panelH = 600, 400
    startX = (screen.get_width() - panelW) // 2
    startY = (screen.get_height() - panelH) // 2

    pygame.draw.rect(screen, DARK_GREY, (startX, startY, panelW, panelH))
    pygame.draw.rect(screen, LIGHT_GREY, (startX, startY, panelW, panelH), 4)

    # Header Prompt Text
    colorNameMap = {RED: "RED", GREEN: "GREEN", BLUE: "BLUE", YELLOW: "YELLOW"}
    promptStr = f"CONNECT THE {colorNameMap[targetWireColor]} WIRE"
    promptSurface = uiFont.render(promptStr, True, targetWireColor)
    promptRect = promptSurface.get_rect(center=(screen.get_width() // 2, startY + 35))
    screen.blit(promptSurface, promptRect)

    # Draw existing static tangled background layout wires
    for i in range(len(leftNodes)):
        # Purely decorative mismatched tangles to make it busy
        pygame.draw.line(screen, LIGHT_GREY, leftNodes[i]["rect"].center, rightNodes[(i + 2) % 4]["rect"].center, 4)

    # Draw interactive connection ports
    for node in leftNodes:
        pygame.draw.circle(screen, node["color"], node["rect"].center, 12)
        pygame.draw.circle(screen, WHITE, node["rect"].center, 12, 2)

    for node in rightNodes:
        pygame.draw.circle(screen, node["color"], node["rect"].center, 12)
        pygame.draw.circle(screen, WHITE, node["rect"].center, 12, 2)

    # Draw user's current live connection string
    if selectedNode is not None:
        pygame.draw.line(screen, selectedNode["color"], selectedNode["rect"].center, currentDragPos, 6)

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

        self.idleFrameRight = pygame.transform.scale_by(pygame.image.load(filename).convert_alpha(), 4)
        self.idleFrameLeft = pygame.transform.scale_by(pygame.image.load("Assets/Sprites/Player/Backward/backward_idle.png").convert_alpha(), 4)

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
            if self.facingDirection == "right":
                self.image = self.idleFrameRight
            elif self.facingDirection == "left":
                self.image = self.idleFrameLeft
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
    global scene, lastTickTime, gameTimeAccumulator, tilesRepairedCount, gridMap, speedMultiplier, repairMultiplier, timerMultiplier, chosenPowerup, currentMusic

    gridMap = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    player.setPosition(900, 500)
    gameTimeAccumulator = 0.0
    tilesRepairedCount = 0

    speedMultiplier = 1
    repairMultiplier = 1
    timerMultiplier = 1
    chosenPowerup = ""

    pygame.mixer.music.load("Assets/Audio/MainBGM.mp3")
    pygame.mixer.music.play(-1)
    currentMusic = "main"

    scene = IN_GAME
    lastTickTime = pygame.time.get_ticks()

def quitGame():
    global running
    running = False

def resumeGame():
    global scene, lastTickTime
    scene = IN_GAME
    lastTickTime = pygame.time.get_ticks()

def returnToMenu():
    global scene, currentMusic

    pygame.mixer.music.load("Assets/Audio/MenuMusic.mp3")
    pygame.mixer.music.play(-1)
    currentMusic = "menu"

    scene = MAIN_MENU

### BUTTON SPRITE INSTANCES ###
menuPlayButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2, "Start Shift", startGame, "Assets/Sprites/UI/Button.png")
menuQuitButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2 + 80, "Abandon Ship", quitGame, "Assets/Sprites/UI/Button.png")

pauseResumeButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2, "Resume Shift", resumeGame, "Assets/Sprites/UI/Button.png")
pauseQuitButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2 + 80, "Return to Menu", returnToMenu, "Assets/Sprites/UI/Button.png")

gameOverQuitButton = ButtonSprite(screen.get_width() // 2, screen.get_height() // 2 + 80, "Return to Menu", returnToMenu, "Assets/Sprites/UI/Button.png")

# Group handling for UI
mainMenuButtons = pygame.sprite.Group(menuPlayButton, menuQuitButton)
pauseMenuButtons = pygame.sprite.Group(pauseResumeButton, pauseQuitButton)
gameOverButtons = pygame.sprite.Group(gameOverQuitButton)

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
panelOpenSound = pygame.mixer.Sound("Assets/Audio/PanelOpen.mp3")

pygame.mixer.music.load("Assets/Audio/MenuMusic.mp3")
pygame.mixer.music.play(-1)
currentMusic = "menu"

### OTHER CLASSES OR FUNCTIONS ###
def rollDice(numberOfDice):
    number = 0
    for i in range(numberOfDice):
        number += random.randint(1, 6)
    diceRollSound.play()
    return number

def changeDiceImage(num):
    global chosenPowerup

    chosenPowerup = ""

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

    speedMultiplier = 1
    repairMultiplier = 1
    timerMultiplier = 1

    match effect:
        case "speed":
            speedMultiplier = 2
        case "less repairs":
            repairMultiplier = 2
        case "slower timer":
            timerMultiplier = 0.5
        case "slowness":
            speedMultiplier = 0.75
        case "increased repairs":
            repairMultiplier = 0.5
        case "faster timer":
            timerMultiplier = 2
        case _:
            pass

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
    global tilesRepairedCount
    if gridMap[row][column] == 2:
        gridMap[row][column] = 0
        wrenchRepairSound.play()
        tilesRepairedCount += 1
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

def drawGameOverMenu():
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((150, 0, 0, 100))
    screen.blit(overlay, (0, 0))

    gameOverSurface = titleFont.render("CRITICAL FAILURE", True, RED)
    gameOverRect = gameOverSurface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
    screen.blit(gameOverSurface, gameOverRect)

    subTextSurface = uiFont.render("More than 50% of tiles have been damaged!", True, WHITE)
    subTextRect = subTextSurface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3 + 70))
    screen.blit(subTextSurface, subTextRect)

    gameOverButtons.draw(screen)

# group sprites
allSprites = pygame.sprite.Group(player, dice)

# game loop
running = True
while running:
    # keep loop running at the right speed
    clock.tick(FPS)

    # Track physical time markers regardless of game state
    currentTickTime = pygame.time.get_ticks()

    # process input (events)
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousePos = pygame.mouse.get_pos()
            if event.button == 1: # Left click
                if scene == MAIN_MENU:
                    for button in mainMenuButtons:
                        button.checkClick(mousePos)
                elif scene == PAUSED:
                    for button in pauseMenuButtons:
                        button.checkClick(mousePos)
                elif scene == GAME_OVER:
                    for button in gameOverButtons:
                        button.checkClick(mousePos)
                elif scene == WIRE_MINIGAME:
                    # Check if player clicked a Left terminal node matching target color
                    for node in leftNodes:
                        if node["rect"].collidepoint(mousePos) and node["color"] == targetWireColor:
                            selectedNode = node
                            currentDragPos = mousePos

        elif event.type == pygame.MOUSEMOTION:
            if scene == WIRE_MINIGAME and selectedNode is not None:
                currentDragPos = pygame.mouse.get_pos()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and scene == WIRE_MINIGAME and selectedNode is not None:
                mousePos = pygame.mouse.get_pos()
                success = False
                # Check if player released mouse over right terminal matching target color
                for node in rightNodes:
                    if node["rect"].collidepoint(mousePos) and node["color"] == targetWireColor:
                        success = True
                        break

                if success:
                    repairTile(activeRepairTile[0], activeRepairTile[1])
                    scene = IN_GAME
                    lastTickTime = pygame.time.get_ticks()

                selectedNode = None

        elif event.type == pygame.KEYUP:
            if scene == IN_GAME:
                if event.key == pygame.K_ESCAPE:
                    scene = PAUSED
            elif scene == PAUSED:
                if event.key == pygame.K_ESCAPE:
                    resumeGame()
            elif scene == WIRE_MINIGAME:
                if event.key == pygame.K_ESCAPE:
                    scene = IN_GAME # Cancel fixing panel
                    lastTickTime = pygame.time.get_ticks()

        # Should continue causing damage and rolling the dice even when doing the minigame
        if scene == IN_GAME or scene == WIRE_MINIGAME:
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

                scaledMinInterval = int(minDamageInterval / repairMultiplier)
                scaledMaxInterval = int(maxDamageInterval / repairMultiplier)

                # Reset the timer to cause a random delay using current intervals
                nextDelay = random.randint(scaledMinInterval, scaledMaxInterval)
                pygame.time.set_timer(DAMAGE_EVENT, nextDelay)

    # Game state handling
    if scene == MAIN_MENU:
        drawMainMenu()
        lastTickTime = currentTickTime

    elif scene == PAUSED:
        drawPauseMenu()
        lastTickTime = currentTickTime

    elif scene == GAME_OVER:
        drawGameOverMenu()
        lastTickTime = currentTickTime

    elif scene == WIRE_MINIGAME:
        # Makes sure the timer continues while fixing the wire
        elapsedTimeThisFrame = currentTickTime - lastTickTime
        lastTickTime = currentTickTime
        gameTimeAccumulator += elapsedTimeThisFrame * timerMultiplier

        # Keeps the world drawn before drawing minigame on top
        drawGrid()
        allSprites.draw(screen)

        secondsPassed = int(gameTimeAccumulator // 1000)
        timeRemaining = TIMER_SECONDS - secondsPassed
        if timeRemaining <= 0:
            timeRemaining = 0
            scene = GAME_OVER

        minutes = timeRemaining // 60
        seconds = timeRemaining % 60
        timerString = f"{minutes}:{seconds:02d}"
        timerSurface = timerFont.render(timerString, True, RED if timeRemaining <= 30 else WHITE)
        timerRect = timerSurface.get_rect(midtop=(screen.get_width() // 2, 20))
        screen.blit(timerSurface, timerRect)

        if timeRemaining <= 240 and currentMusic == "main":
            pygame.mixer.music.load("Assets/Audio/DifficultyEnhancedBGM.mp3")
            pygame.mixer.music.play(-1)
            currentMusic = "hard"

        # Draw the wire puzzle over everything
        drawWireMinigame()

    elif scene == IN_GAME:
        # Calculate real-world time passed since last frame
        elapsedTimeThisFrame = currentTickTime - lastTickTime
        lastTickTime = currentTickTime

        # Apply multiplier to game time progress
        gameTimeAccumulator += elapsedTimeThisFrame * timerMultiplier

        damagedTileCount = sum(row.count(2) for row in gridMap)

        # Causes a game over if more than half the tiles are destroyed
        if damagedTileCount > (totalFloorTiles / 2):
            scene = GAME_OVER

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

        # Checks for the tile the player is overlapping, and if that tile is damaged starts the minigame
        if keys[K_e]:
            playerRow = player.rect.centery // TILE_SIZE
            playerColumn = player.rect.centerx // TILE_SIZE

            if 0 <= playerRow < len(gridMap) and 0 <= playerColumn < len(gridMap[0]):
                if gridMap[playerRow][playerColumn] == 2:
                    startWireMinigame(playerRow, playerColumn)

        # background fill
        screen.fill(BGCOLOUR)

        drawGrid()

        # Display timer scaled based on accumulated custom ticks
        secondsPassed = int(gameTimeAccumulator // 1000)
        timeRemaining = TIMER_SECONDS - secondsPassed

        if timeRemaining <= 0:
            timeRemaining = 0

        # Adjust damage intervals for the last 4 minutes (240 seconds)
        if timeRemaining <= 240:
            minDamageInterval = 200
            maxDamageInterval = 2000

            if currentMusic == "main":
                pygame.mixer.music.load("Assets/Audio/DifficultyEnhancedBGM.mp3")
                pygame.mixer.music.play(-1)
                currentMusic = "hard"
        else:
            minDamageInterval = 500
            maxDamageInterval = 3000


        # Renders the timer in the top center of the screen
        minutes = timeRemaining // 60
        seconds = timeRemaining % 60

        timerString = f"{minutes}:{seconds:02d}"
        if timeRemaining > 30:
            timerSurface = timerFont.render(timerString, True, WHITE)
        else:
            timerSurface = timerFont.render(timerString, True, RED)

        timerRect = timerSurface.get_rect(midtop=(screen.get_width() // 2, 20))
        screen.blit(timerSurface, timerRect)

        # Render the score tracker in the top right corner
        scoreString = f"Score: {tilesRepairedCount}"
        scoreSurface = uiFont.render(scoreString, True, GREEN)
        scoreRect = scoreSurface.get_rect(topright=(screen.get_width() - 30, 20))
        screen.blit(scoreSurface, scoreRect)

        integrityPercent = int(((totalFloorTiles - damagedTileCount) / totalFloorTiles) * 100)
        integrityString = f"Ship Integrity: {integrityPercent}%"
        integrityColor = GREEN if integrityPercent > 70 else YELLOW if integrityPercent > 50 else RED
        integritySurface = uiFont.render(integrityString, True, integrityColor)
        integrityRect = integritySurface.get_rect(topleft=(30, 20))
        screen.blit(integritySurface, integrityRect)

        # render sprites on screen
        allSprites.draw(screen)

    # ***AFTER*** drawing everything, flip (update) the display
    pygame.display.flip()

pygame.quit()