import os
import pygame
import random
from sys import exit
from queue import PriorityQueue

# Configurazione di pygame senza rendering
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

# Costanti del gioco
WIN_HEIGHT = 720
WIN_WIDTH = 551
SCROLL_SPEED = 5
BIRD_START_POSITION = (100, 250)

# Variabili globali per il punteggio
score = 0
high_score = 0

class Bird:
    def __init__(self):
        self.rect = pygame.Rect(BIRD_START_POSITION[0], BIRD_START_POSITION[1], 34, 24)  # Dimensioni dell'uccello
        self.prevVel = 0
        self.vel = 0
        self.flap = False
        self.alive = True

    def update(self, action):
        if self.alive:
            self.prevVel = self.vel
            self.vel = min(self.vel + 1, 7)
            if self.rect.y < 500:
                self.rect.y += int(self.vel)
            if self.vel == 0:
                self.flap = False

            if action[0] == 1 and not self.flap and self.rect.y > 0 and self.alive:
                self.flap = True
                self.vel = -7

class Pipe:
    def __init__(self, x, y, height, pipe_type):
        self.rect = pygame.Rect(x, y, 52, height)  # Dimensioni del tubo
        self.pipe_type = pipe_type
        self.passed = False

    def update(self):
        global score  # Dichiarazione esplicita della variabile globale

        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            return True  # Rimuovi il tubo se esce dallo schermo

        if self.pipe_type == 'bottom' and not self.passed:
            if BIRD_START_POSITION[0] > self.rect.left:
                self.passed = True
                score += 1  # Incrementa il punteggio quando il bird supera il tubo
                return 2
        return 0

class Ground:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, WIN_WIDTH, 100)  # Dimensioni del terreno

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.rect.x = WIN_WIDTH

class simpleSearchFlappy:
    def __init__(self):
        self.reset()

    def reset(self):
        global score, high_score  # Dichiarazione esplicita delle variabili globali

        if score > high_score:
            high_score = score
        score = 0  # Reset del punteggio a ogni nuova partita

        self.bird = Bird()
        self.pipe_timer = 0
        self.pipes = []
        self.ground = [Ground(0, 520), Ground(WIN_WIDTH, 520)]

    def game_step(self, action=None):
        global score  # Dichiarazione esplicita della variabile globale

        # Spawn dei tubi
        self.spawn_pipe()

        for pipe in self.pipes:
            pipe_update = pipe.update()

            if pipe.pipe_type == 'bottom' and not pipe.passed:
                if self.bird.rect.x > pipe.rect.right:
                    pipe.passed = True
                    score += 1  # Aggiornamento del punteggio

            if pipe_update:
                self.pipes.remove(pipe)

        # Aggiorna il terreno
        for ground in self.ground:
            ground.update()

        # Aggiorna l'uccello
        if action is None:
            action = [0]  # Default: non saltare
        self.bird.update(action)

        # Controllo di collisione con i tubi o il suolo
        for pipe in self.pipes:
            if self.bird.rect.colliderect(pipe.rect):
                self.bird.alive = False
                return True, score

        for ground in self.ground:
            if self.bird.rect.colliderect(ground.rect):
                self.bird.alive = False
                return True, score

        return not self.bird.alive, score

    def spawn_pipe(self):
        if self.pipe_timer <= 0 and self.bird.alive:
            y_top = random.randint(-600, -480)
            y_bottom = y_top + random.randint(90, 130) + 320  # Altezza del tubo inferiore
            self.pipes.append(Pipe(WIN_WIDTH, y_top, 320, 'top'))
            self.pipes.append(Pipe(WIN_WIDTH, y_bottom, 320, 'bottom'))
            self.pipe_timer = 70
        self.pipe_timer -= 1

if __name__ == "__main__":
    game = simpleSearchFlappy()
    try:
        while True:
            done, score = game.game_step()
            if done:
                print(f"Game Over! Score: {score}")
                game.reset()
    except KeyboardInterrupt:
        print("Game interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
