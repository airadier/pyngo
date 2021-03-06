#!/usr/bin/python

from game import *
from gamegui import *
from ConfigParser import SafeConfigParser
import sys
import random
import os

CONFIG = 'bingo.cfg'

def configDefaults():
    global DELAY_NEXTBALL, BALL_SHOWTIME, USE_FULLSCREEN, VOICE_FOLDER
    loadConfig()

    # Default config
    DELAY_NEXTBALL = getConfigInt('game', 'ball_delay', 4000)
    BALL_SHOWTIME = getConfigInt('game', 'ball_showtime', DELAY_NEXTBALL - 1000)
    USE_FULLSCREEN = getConfigBool('display', 'fullscreen', False)
    VOICE_FOLDER = getConfigString('game', 'voice', 'jorge')

def loadCards():
    if not loadCards1():
        if not loadCards2():
            print "Error loading cards.csv"

def loadCards1():
    global cards
    cards = {}
    try:
        f = open("cards.csv", "rb")
        #Skip headers
        next(f)
        #Read data
        for line in f:
            nums = line.split('\t')
            card_num = nums[0]
            line1, line2, line3 = [], [], []
            for i in range(9):
                if nums[1 + i*3] != '*':
                    line1.append(int(nums[1 + i*3]))
                if nums[2 + i*3] != '*':
                    line2.append(int(nums[2 + i*3]))
                if nums[3 + i*3] != '*':
                    line3.append(int(nums[3 + i*3]))
            cards[int(card_num)] = (line1, line2, line3)
        f.close()
        return True
    except:
        return False

def loadCards2():
    global cards
    cards = {}
    try:
        f = open("cards.csv", "rb")
        #Skip headers
        next(f)
        #Read data
        for line in f:
            nums = line.split(',')
            card_num = nums[0]
            line1 = [int(x) for x in nums[1:6]]
            line2 = [int(x) for x in nums[6:11]]
            line3 = [int(x) for x in nums[11:]]
            cards[int(card_num)] = (line1, line2, line3)
        f.close()
        print cards
        return True
    except:
        return False

EVENT_BALL = USEREVENT
EVENT_LASTBALL = USEREVENT + 1
NUM_BALLS = 90

SCREEN_RES = (800, 600)

BALL_TEXTSIZE = 128
BALL_TEXTCOLOR = (1, 1, 1)
BALL_SMALLSIZE = (45, 45)
BALL_BIGSIZE = (200, 200)
BALL_MARGIN = 10
BALL_STEPS = 15

PENDING_TEXTSIZE = 32
PENDING_TEXTCOLOR = (200, 200, 200)

STATE_MAINMENU, STATE_PLAYING, STATE_PAUSED, STATE_FINISHED, STATE_OPTIONS, STATE_CHECKING = range(6)

def loadConfig():
    global config
    config = SafeConfigParser()
    try:
        config.readfp(file(CONFIG))
    except Exception, e:
        pass


def getConfigBool(section, key, default):
    try:
        return config.getboolean(section, key)
    except:
        setConfig(section, key, default)
        return default


def getConfigInt(section, key, default):
    try:
        return config.getint(section, key)
    except:
        setConfig(section, key, default)
        return default

def getConfigString(section, key, default):
    try:
        return config.get(section, key)
    except:
        setConfig(section, key, default)
        return default


def getConfigInt(section, key, default):
    try:
        return config.getint(section, key)
    except:
        setConfig(section, key, default)
        return default


def setConfig(section, key, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, str(value))


def saveConfig():
    config.write(file(CONFIG, "w"))


def exitGame():
    saveConfig()
    sys.exit(0)


def startGame():
    game.setState(STATE_PLAYING)
    BingoRound(game)


def options():
    game.setState(STATE_OPTIONS)
    OptionsMenu(game)


def toggleFullScreen(ev):
    setConfig('display', 'fullscreen', game.toggleFullscreen())
    return False


def escapeKey(ev):
    if game.getState() == STATE_PLAYING:
        sound = loadSound('pause.ogg')
        sound.play()
        game.setState(STATE_PAUSED)
        PauseMenu(game)
    elif game.getState() == STATE_CHECKING:
        game.setState(STATE_PAUSED)
        PauseMenu(game)
    elif game.getState() == STATE_PAUSED:
        game.setState(STATE_PLAYING)
    elif game.getState() == STATE_MAINMENU:
        exitGame()
    elif game.getState() == STATE_FINISHED:
        game.setState(STATE_MAINMENU)

    return False


def loadImage(name):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemEXit, message
    return image.convert()


def loadSound(name):
    class NoneSound:
        def play(self): pass

        def get_length(self): return 0

    if not pygame.mixer:
        return NoneSound()
    fullname = os.path.join('data', VOICE_FOLDER, name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error, message:
        print  'Cannot load sound:', name, message
        return NoneSound()
        raise SystemExit, message
    return sound


class Title(GameObject):
    def __init__(self, game):
        GameObject.__init__(self, game)

        self.title = loadImage('title.png')
        self.rect = self.title.get_rect()
        self.title.set_colorkey((0, 0, 0))
        self.rect.centerx = SCREEN_RES[0] / 2
        self.rect.top = 20
        self.game.addPainter(self)

        self.title_small = pygame.transform.scale(self.title, (200, 50))
        self.rect_small = self.title_small.get_rect()
        self.rect_small.top = 20
        self.rect_small.centerx = 110

    def paint(self, surface):
        if self.game.getState() in (STATE_MAINMENU, STATE_OPTIONS):
            surface.blit(self.title, self.rect)
        else:
            surface.blit(self.title_small, self.rect_small)


class PauseMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game, 200, title="PAUSA")

        self.addOption("Reanudar", self.resumeGame)
        if cards:
            self.addOption("Comprobar", self.checkCard)
        self.addOption("Salir", self.toMainMenu)

        self.setDepth(10)
        r = self.getRect()
        r.left = BALL_MARGIN
        r.bottom = SCREEN_RES[1] - BALL_MARGIN
        self.setRect(r)

        self.game.addPainter(self)
        self.game.addEventListener(self)

    def stateChanged(self, state):
        if state in (STATE_MAINMENU, STATE_PLAYING, STATE_CHECKING):
            self.game.removeObject(self)

    def toMainMenu(self):
        self.game.setState(STATE_MAINMENU)

    def resumeGame(self):
        self.game.setState(STATE_PLAYING)

    def checkCard(self):
        self.game.setState(STATE_CHECKING)
        CheckCardMenu(self.game)

    def processEvent(self, event):
        if event.type == KEYDOWN and event.key == K_SPACE:
            game.setState(STATE_PLAYING)
        Menu.processEvent(self, event)
        return True


class CheckCardMenu(CheckCardWindow):
    def __init__(self, game):
        CheckCardWindow.__init__(self, game, SCREEN_RES[0] / 2)

        self.game.addPainter(self)
        self.game.addEventListener(self)

        r = self.getRect()
        r.centerx, r.centery = SCREEN_RES[0] / 2, SCREEN_RES[1] / 2
        self.setRect(r)

    def back(self):
        self.game.setState(STATE_PAUSED)
        PauseMenu(game)

    def checkCard(self, cardtext):
        try:
            cardnum = int(cardtext)
            bingo_prize = True
            line_prize = False
            for line in cards[cardnum]:
                curr_line_prize = True
                for num in line:
                    if num not in played_balls:
                        bingo_prize = False
                        curr_line_prize = False
                if curr_line_prize: line_prize = True

            if bingo_prize:
                self.displayBingo()
            elif line_prize:
                self.displayLine()
        except: pass

    def stateChanged(self, state):
        self.game.removeObject(self)

class StartMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game, SCREEN_RES[0] / 2, title="MENU PRINCIPAL")

        self.addOption("Comenzar partida", startGame)
        self.addOption("Opciones", options)
        self.addOption("Salir", exitGame)
        self.game.addPainter(self)
        self.game.addEventListener(self)

        r = self.getRect()
        r.centerx, r.centery = SCREEN_RES[0] / 2, SCREEN_RES[1] / 2
        self.setRect(r)

    def stateChanged(self, state):
        self.game.removeObject(self)


class ShowTimeMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game, SCREEN_RES[0] / 2, title="TIEMPO DE BOLA")

        for i in (1, 2, 3, 4, 5):
            if (DELAY_NEXTBALL >= i * 1000):
                if getConfigInt('game', 'ball_showtime', BALL_SHOWTIME) == i * 1000:
                    self.addOption("[ " + str(i) + " segundos ]", self.setDelay(i * 1000))
                else:
                    self.addOption(str(i) + " segundos", self.setDelay(i * 1000))
        if getConfigInt('game', 'ball_showtime', BALL_SHOWTIME) == 0:
            self.addOption("[ Hasta la siguiente ]", self.setDelay(0))
        else:
            self.addOption("Hasta la siguiente", self.setDelay(0))
        self.addOption("Volver", self.back)
        self.game.addPainter(self)
        self.game.addEventListener(self)

        r = self.getRect()
        r.centerx, r.top = SCREEN_RES[0] / 2, 175
        self.setRect(r)

    def back(self):
        self.game.removeObject(self)
        OptionsMenu(game)

    def setDelay(self, value):
        return lambda: self.setDelayReal(value)

    def setDelayReal(self, value):
        global BALL_SHOWTIME
        BALL_SHOWTIME = value
        setConfig('game', 'ball_showtime', str(value))
        self.back()


class DelayMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game, SCREEN_RES[0] / 2, title="TIEMPO ENTRE BOLAS")

        if getConfigInt('game', 'ball_delay', DELAY_NEXTBALL) == 0:
            self.addOption("[ Manual ]", self.setDelay(0))
        else:
            self.addOption("Manual", self.setDelay(0))
        for i in (1, 2, 3, 4, 5):
            if getConfigInt('game', 'ball_delay', DELAY_NEXTBALL) == i * 1000:
                self.addOption("[ " + str(i) + " segundos ]", self.setDelay(i * 1000))
            else:
                self.addOption(str(i) + " segundos", self.setDelay(i * 1000))
        self.addOption("Volver", self.back)
        self.game.addPainter(self)
        self.game.addEventListener(self)

        r = self.getRect()
        r.centerx, r.top = SCREEN_RES[0] / 2, 175
        self.setRect(r)

    def back(self):
        self.game.removeObject(self)
        OptionsMenu(game)

    def setDelay(self, value):
        return lambda: self.setDelayReal(value)

    def setDelayReal(self, value):
        global DELAY_NEXTBALL
        global BALL_SHOWTIME
        DELAY_NEXTBALL = value
        if BALL_SHOWTIME <= 0 or BALL_SHOWTIME > DELAY_NEXTBALL:
            BALL_SHOWTIME = DELAY_NEXTBALL
        if BALL_SHOWTIME < 0:
            BALL_SHOWTIME = 0
        setConfig('game', 'ball_delay', str(DELAY_NEXTBALL))
        setConfig('game', 'ball_showtime', str(BALL_SHOWTIME))
        self.back()

class VoiceMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game, SCREEN_RES[0] / 2, title="TIEMPO ENTRE BOLAS")

        if VOICE_FOLDER == 'alvaro':
            self.addOption("[ Alvaro ]", self.setVoice('alvaro'))
        else:
            self.addOption("Alvaro", self.setVoice('alvaro'))
        if VOICE_FOLDER == 'jorge':
            self.addOption("[ Jorge ]", self.setVoice('jorge'))
        else:
            self.addOption("Jorge", self.setVoice('jorge'))
        if VOICE_FOLDER == 'laura':
            self.addOption("[ Laura ]", self.setVoice('laura'))
        else:
            self.addOption("Laura", self.setVoice('laura'))
        if VOICE_FOLDER == 'raquel':
            self.addOption("[ Raquel ]", self.setVoice('raquel'))
        else:
            self.addOption("Raquel", self.setVoice('raquel'))
        self.addOption("Volver", self.back)
        self.game.addPainter(self)
        self.game.addEventListener(self)

        r = self.getRect()
        r.centerx, r.top = SCREEN_RES[0] / 2, 175
        self.setRect(r)

    def back(self):
        self.game.removeObject(self)
        OptionsMenu(game)

    def setVoice(self, value):
        return lambda: self.setVoiceReal(value)

    def setVoiceReal(self, value):
        global VOICE_FOLDER
        VOICE_FOLDER = value
        setConfig('game', 'voice', value)
        self.back()

class OptionsMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game, SCREEN_RES[0] / 2, title="OPCIONES")

        self.addOption("Tiempo entre bolas", self.setDelay)
        self.addOption("Tiempo de bola", self.setShowTime)
        self.addOption("Voces", self.setVoice)
        self.addOption("Pantalla Completa", self.toggleFullScreen)
        self.addOption("Volver", self.mainmenu)
        self.game.addPainter(self)
        self.game.addEventListener(self)

        r = self.getRect()
        r.centerx, r.top = SCREEN_RES[0] / 2, 175
        self.setRect(r)

    def setDelay(self):
        self.game.removeObject(self)
        DelayMenu(game)

    def setShowTime(self):
        self.game.removeObject(self)
        ShowTimeMenu(game)

    def setVoice(self):
        self.game.removeObject(self)
        VoiceMenu(game)

    def mainmenu(self):
        self.game.setState(STATE_MAINMENU)
        StartMenu(game)

    def stateChanged(self, state):
        self.game.removeObject(self)

    def toggleFullScreen(self):
        toggleFullScreen(None)


class Round:
    """A Bingo round. Function 'ball' will take a random ball, and return it."""

    def __init__(self):
        self.pending_balls = range(1, NUM_BALLS + 1)

    def pendingBalls(self):
        return self.pending_balls

    def ball(self):
        if not self.pending_balls:
            return None
        next_ball = random.choice(self.pending_balls)
        self.pending_balls.remove(next_ball)
        return next_ball


class BallPainter(GameObject):
    ball_surface = None
    UNSEEN, SEEN, CURRENT, MOVING = range(4)

    def __init__(self, game, ballnum):
        GameObject.__init__(self, game)
        game.addPainter(self)
        self.number = ballnum

        if not BallPainter.ball_surface:
            BallPainter.ball_surface = loadImage('ball.png')
            BallPainter.ball_surface.set_colorkey((0, 0, 0))

        self.state = BallPainter.UNSEEN
        self.surface_big = BallPainter.ball_surface.copy()

        # Create fontfont and text surface
        font = pygame.font.Font(FONT_NAME, BALL_TEXTSIZE)
        text = font.render(str(ballnum), 1, BALL_TEXTCOLOR)

        self.rect = self.surface_big.get_rect()
        text_rect = text.get_rect()
        text_rect.centerx, text_rect.centery = self.rect.centerx, self.rect.centery
        self.surface_big.blit(text, text_rect)

        self.surface = pygame.transform.scale(self.surface_big, BALL_SMALLSIZE)
        self.rect = self.surface.get_rect()
        self.rect.centerx, self.rect.centery = self.ballPosition(ballnum)
        self.surface.set_alpha(UNSEEN_BALL_ALPHA)

    def ballPosition(self, ball):
        x = SCREEN_RES[0] - ((9 - (ball - 1)) % 10) * (BALL_SMALLSIZE[0] + BALL_MARGIN) - BALL_SMALLSIZE[
            0] - BALL_MARGIN
        y = BALL_SMALLSIZE[1] + ((ball - 1) / 10) * (BALL_SMALLSIZE[1] + BALL_MARGIN)
        return (x, y)

    def paint(self, surface):
        surface.blit(self.surface, self.rect)
        if self.state in (BallPainter.CURRENT, BallPainter.MOVING):
            surface.blit(self.surface_curr, self.rect_curr)

    def seen(self):
        self.state = BallPainter.CURRENT

        self.setDepth(self.depth - 1)

        self.surface_curr = pygame.transform.scale(self.surface_big, BALL_BIGSIZE)
        self.rect_curr = self.surface.get_rect()
        self.rect_curr.top, self.rect_curr.left = 150 + BALL_MARGIN, BALL_MARGIN
        self.surface_curr.set_alpha(255)
        self.ticks = pygame.time.get_ticks()

    def move(self):
        if self.state == BallPainter.CURRENT:
            self.state = BallPainter.MOVING
            self.move_step = 0

    def update(self):
        if BALL_SHOWTIME > 0 and self.state == BallPainter.CURRENT:
            if pygame.time.get_ticks() - self.ticks > BALL_SHOWTIME:
                self.state = BallPainter.MOVING
                self.move_step = 0
        elif self.state == BallPainter.MOVING:

            curr_w = BALL_SMALLSIZE[0] + (BALL_STEPS - self.move_step) * (
            BALL_BIGSIZE[0] - BALL_SMALLSIZE[0]) / BALL_STEPS
            curr_h = BALL_SMALLSIZE[1] + (BALL_STEPS - self.move_step) * (
            BALL_BIGSIZE[1] - BALL_SMALLSIZE[1]) / BALL_STEPS

            self.surface_curr = pygame.transform.scale(self.surface_big, (curr_w, curr_h))
            self.rect_curr = self.surface.get_rect()
            self.rect_curr.top = 150 + BALL_MARGIN + self.move_step * (
            self.rect.top - self.rect_curr.top - 150) / BALL_STEPS
            self.rect_curr.left = BALL_MARGIN + self.move_step * (self.rect.left - self.rect_curr.left) / BALL_STEPS
            self.ticks = pygame.time.get_ticks()

            self.move_step = self.move_step + 1
            if self.move_step > BALL_STEPS:
                self.surface.set_alpha(255)
                self.state = BallPainter.SEEN
                self.setDepth(self.depth + 1)

    def clear(self):
        game.removeObject(self)


class BingoRound(GameObject):
    def __init__(self, game):
        global played_balls
        GameObject.__init__(self, game)

        game.addEventListener(self)
        game.addPainter(self)

        self.round = Round()
        played_balls = []
        self.last_ball = None
        self.smallball = loadImage('smallball.png')
        self.smallball.set_colorkey((0, 0, 0))

        self.pendingfont = pygame.font.Font(FONT_NAME, PENDING_TEXTSIZE)

        self.ball_painters = []
        for i in range(1, NUM_BALLS + 1):
            self.ball_painters.append(BallPainter(game, i))

        sound_begin = loadSound('begin.ogg')
        sound_begin.play()

        pygame.mouse.set_visible(False)

        if DELAY_NEXTBALL > 0:
            pygame.time.set_timer(EVENT_BALL, DELAY_NEXTBALL + int(sound_begin.get_length() * 1000))

    def paint(self, surface):
        global played_balls
        rect = self.smallball.get_rect()
        bolitas = len(self.round.pendingBalls())
        if bolitas > 30: bolitas = 30
        for i in range(bolitas):
            rect.centerx = random.randint(0, 200)
            rect.centery = SCREEN_RES[1] - random.expovariate(9) * 100
            surface.blit(self.smallball, rect)

        self.pendingtext = self.pendingfont.render("BOLAS JUGADAS: " + str(len(played_balls)), 1, PENDING_TEXTCOLOR)
        rect = self.pendingtext.get_rect()
        rect.centery = 550
        rect.centerx = 500
        surface.blit(self.pendingtext, rect)

    def processEvent(self, event):
        global played_balls
        if event.type == MOUSEBUTTONDOWN:
            if self.game.getState() == STATE_PLAYING and DELAY_NEXTBALL:
                sound = loadSound('pause.ogg')
                sound.play()
                game.setState(STATE_PAUSED)
                PauseMenu(game)
            elif self.game.getState() == STATE_PLAYING:
                pygame.event.post(pygame.event.Event(EVENT_BALL))
            elif self.game.getState() == STATE_FINISHED:
                game.setState(STATE_MAINMENU)
        elif self.game.getState() == STATE_PLAYING and event.type == KEYDOWN and event.key == K_SPACE:
            sound = loadSound('pause.ogg')
            sound.play()
            game.setState(STATE_PAUSED)
            PauseMenu(game)
        elif event.type == EVENT_BALL:
            ball = self.round.ball()
            if self.last_ball: self.ball_painters[self.last_ball - 1].move()
            self.last_ball = ball

            if not ball:
                pygame.time.set_timer(EVENT_BALL, 0)
                game.setState(STATE_FINISHED)
                sound = loadSound("end.ogg")
                sound.play()
                return True

            self.ball_painters[ball - 1].seen()
            played_balls.append(ball)

            sound = loadSound(str(ball) + '.ogg')
            sound.play()

            if DELAY_NEXTBALL > 0:
                pygame.time.set_timer(EVENT_BALL, DELAY_NEXTBALL + int(sound.get_length() * 1000))

        elif event.type == EVENT_LASTBALL:
            pygame.time.set_timer(EVENT_LASTBALL, 0)

            if self.last_ball:
                self.ball_painters[self.last_ball - 1].seen()

                sound = loadSound(str(self.last_ball) + '.ogg')
                sound.play()

                if DELAY_NEXTBALL > 0:
                    pygame.time.set_timer(EVENT_BALL, DELAY_NEXTBALL + int(sound.get_length() * 1000))

            else:
                pygame.time.set_timer(EVENT_BALL, DELAY_NEXTBALL)

        return True

    def stateChanged(self, state):
        if state == STATE_MAINMENU:
            pygame.mouse.set_visible(True)
            StartMenu(self.game)
            # Title(self.game)
            for ball in self.ball_painters:
                ball.clear()
            game.removeObject(self)
        elif state == STATE_PLAYING:
            pygame.mouse.set_visible(False)
            game.addEventListener(self)
            game.addPainter(self)

            # Reproducir "Continua el juego", y esperar su duracion y repetir ultima bola
            sound = loadSound('resume.ogg')
            sound.play()
            pygame.time.wait(500 + int(sound.get_length() * 1000))

            if self.last_ball:
                sound = loadSound('lastball.ogg')
                sound.play()
                pygame.time.wait(500 + int(sound.get_length() * 1000))

            pygame.event.post(pygame.event.Event(EVENT_LASTBALL))
        elif state == STATE_PAUSED:
            pygame.mouse.set_visible(True)
            game.removeEventListener(self)
            game.removePainter(self)
            pygame.time.set_timer(EVENT_BALL, 0)
            pygame.time.set_timer(EVENT_LASTBALL, 0)


configDefaults()
loadCards()

game = Game(SCREEN_RES, "Bingo AIM", 100, fullscreen=USE_FULLSCREEN)

hotkeys = HotKeyManager(game)
hotkeys.addAction(K_ESCAPE, escapeKey, True)

back = loadImage('back.jpg')

game.background.blit(back, (0, 0))

game.setState(STATE_MAINMENU)

StartMenu(game)
Title(game)

game.mainLoop()
