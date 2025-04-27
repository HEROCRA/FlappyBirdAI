import os
import pygame
import random
import matplotlib.pyplot as plt
from sys import exit
import copy

# Configurazione di pygame senza rendering
pygame.init()

# Costanti del gioco
WIN_HEIGHT = 720
WIN_WIDTH = 551
SCROLL_SPEED = 5
BIRD_START_POSITION = (100, 250)

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
        self.rect = pygame.Rect(x, y, 52, height)
        self.pipe_type = pipe_type
        self.passed = False

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            return True  # Segnale per rimuovere il tubo
        return False

class Ground:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, WIN_WIDTH, 100)

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.rect.x = WIN_WIDTH

class simpleSearchFlappy:
    def __init__(self):
        self.reset()

    def reset(self):
        # Se è già presente uno score e questo è maggiore dell'high score, aggiorna l'high score
        if hasattr(self, 'score') and self.score > self.high_score:
            self.high_score = self.score
        # Inizializza score e high_score (se non già presenti)
        self.score = 0
        if not hasattr(self, 'high_score'):
            self.high_score = 0

        self.bird = Bird()
        self.pipe_timer = 0
        self.pipes = []
        self.ground = [Ground(0, 520), Ground(WIN_WIDTH, 520)]

    def clone(self):
        new_game = simpleSearchFlappy.__new__(simpleSearchFlappy)
        new_game.score = self.score
        new_game.high_score = self.high_score
        new_game.bird = Bird()
        new_game.bird.rect = self.bird.rect.copy()
        new_game.bird.prevVel = self.bird.prevVel
        new_game.bird.vel = self.bird.vel
        new_game.bird.flap = self.bird.flap
        new_game.bird.alive = self.bird.alive
        new_game.pipe_timer = self.pipe_timer
        new_game.pipes = []
        for pipe in self.pipes:
            new_pipe = Pipe(pipe.rect.x, pipe.rect.y, pipe.rect.height, pipe.pipe_type)
            new_pipe.passed = pipe.passed
            new_game.pipes.append(new_pipe)
        new_game.ground = []
        for g in self.ground:
            new_ground = Ground(g.rect.x, g.rect.y)
            new_game.ground.append(new_ground)
        return new_game

    def evaluate_state(self, game_state):
        # Se il bird è morto, penalizza pesantemente
        if not game_state.bird.alive:
            return -1000

        # Trova il tubo inferiore più vicino che il bird deve attraversare
        target_y = WIN_HEIGHT / 2  # Valore di default se nessun tubo è presente
        for pipe in game_state.pipes:
            if pipe.pipe_type == 'bottom' and pipe.rect.x > game_state.bird.rect.x:
                # Trova il tubo superiore corrispondente con la stessa x
                top_pipe = None
                for p in game_state.pipes:
                    if p.pipe_type == 'top' and p.rect.x == pipe.rect.x:
                        top_pipe = p
                        break
                if top_pipe is not None:
                    gap_top = top_pipe.rect.y + top_pipe.rect.height
                    gap_bottom = pipe.rect.y
                    target_y = (gap_top + gap_bottom) / 2
                    break

        # Valuta lo stato in base alla distanza verticale dal centro del gap
        return -abs(game_state.bird.rect.y - target_y)

    def choose_action(self, horizon=35):
        """
        Implementazione del hill climbing:
        Per ciascuna possibile azione (0 = non saltare, 1 = saltare),
        clona lo stato corrente, simula per 'horizon' passi (usando l'azione candidata
        al primo passo e nessun flap per gli step successivi) e valuta lo stato risultante.
        Viene scelta l'azione con la valutazione migliore.
        """
        best_action = 0
        best_eval = -float('inf')
        for action in [0, 1]:
            cloned_game = self.clone()
            done = False
            for i in range(horizon):
                if i == 0:
                    a = [action]
                else:
                    a = [0]
                done, _ = cloned_game.game_step(a)
                if done:
                    break
            eval_value = self.evaluate_state(cloned_game)
            if eval_value > best_eval:
                best_eval = eval_value
                best_action = action
        return [best_action]

    def game_step(self, action=None):
        if action is None:
            action = self.choose_action()

        # Gestione dello spawn dei tubi
        self.spawn_pipe()

        for pipe in self.pipes[:]:
            pipe_update = pipe.update()

            if pipe.pipe_type == 'bottom' and not pipe.passed:
                if self.bird.rect.x > pipe.rect.right:
                    pipe.passed = True
                    self.score += 1  # Aggiornamento del punteggio

            if pipe_update:
                self.pipes.remove(pipe)

        # Aggiornamento del terreno
        for ground in self.ground:
            ground.update()

        # Aggiornamento dell'uccello
        self.bird.update(action)

        # Controllo di collisione con tubi o suolo
        for pipe in self.pipes:
            if self.bird.rect.colliderect(pipe.rect):
                self.bird.alive = False
                return True, self.score

        for ground in self.ground:
            if self.bird.rect.colliderect(ground.rect):
                self.bird.alive = False
                return True, self.score

        return not self.bird.alive, self.score

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
    scores = []  # Lista per salvare tutti gli score

    plt.ion()  # Modalità interattiva ON
    fig, ax = plt.subplots()
    line, = ax.plot([], [], 'b-')  # Linea blu

    ax.set_xlabel('Numero di partite')
    ax.set_ylabel('Punteggio')
    ax.set_title('Andamento punteggi nel tempo')

    try:
        while True:
            done, current_score = game.game_step()
            if done:
                print(f"Game Over! Score: {current_score}")
                scores.append(current_score)

                # Aggiorna il grafico
                line.set_xdata(range(len(scores)))
                line.set_ydata(scores)
                ax.relim()
                ax.autoscale_view()

                plt.draw()
                plt.pause(0.01)

                game.reset()
    except KeyboardInterrupt:
        print("Game interrotto dall'utente.")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")
