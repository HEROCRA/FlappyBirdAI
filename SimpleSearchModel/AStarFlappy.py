import os
import pygame
from sys import exit
import random
from queue import PriorityQueue

# Configurazione di pygame senza rendering
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

# Costanti del gioco
WIN_HEIGHT = 720
WIN_WIDTH = 551
SCROLL_SPEED = 5
BIRD_START_POSITION = (100, 250)
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
        global score
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            return True  # Rimuovi il tubo se esce dallo schermo

        if self.pipe_type == 'bottom' and not self.passed:
            if BIRD_START_POSITION[0] > self.rect.left:
                self.passed = True
                score += 1
                return 2  # Aggiungi punti
        return 0

class Ground:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, WIN_WIDTH, 100)  # Dimensioni del terreno

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.rect.x = WIN_WIDTH

class State:
    def __init__(self, bird_x, bird_y, bird_vel, pipe_x, pipe_width, pipe_top_y, pipe_bottom_y):
        self.bird_x = bird_x  # Posizione orizzontale dell'uccello
        self.bird_y = bird_y  # Posizione verticale dell'uccello
        self.bird_vel = bird_vel  # Velocità verticale dell'uccello
        self.pipe_x = pipe_x  # Posizione orizzontale del tubo
        self.pipe_width = pipe_width  # Larghezza del tubo
        self.pipe_top_y = pipe_top_y  # Posizione verticale del tubo superiore
        self.pipe_bottom_y = pipe_bottom_y  # Posizione verticale del tubo inferiore

    def __eq__(self, other):
        # Confronta due stati per l'uguaglianza
        return (self.bird_x == other.bird_x and
                self.bird_y == other.bird_y and
                self.bird_vel == other.bird_vel and
                self.pipe_x == other.pipe_x and
                self.pipe_width == other.pipe_width and
                self.pipe_top_y == other.pipe_top_y and
                self.pipe_bottom_y == other.pipe_bottom_y)

    def __hash__(self):
        # Definisci un hash per lo stato (necessario per usare gli stati in un set o dizionario)
        return hash((self.bird_x, self.bird_y, self.bird_vel, self.pipe_x, self.pipe_width, self.pipe_top_y, self.pipe_bottom_y))

    def __lt__(self, other):
        # Definisci come confrontare due stati (necessario per PriorityQueue)
        return heuristic(self, None) < heuristic(other, None)

def heuristic(state, goal):
    # Calcolo centro del gap
    gap_center = (state.pipe_top_y + state.pipe_bottom_y) / 2

    # Distanza verticale tra l'uccello e il centro del gap
    vertical_distance = abs(state.bird_y - gap_center)

    # Distanza orizzontale tra l'uccello e il tubo
    horizontal_distance = abs(state.pipe_x - state.bird_x)

    # Fattore di velocità (penalizza se l'uccello sta cadendo)
    velocity_penalty = 0
    if state.bird_y <= state.pipe_top_y and state.bird_vel < 0:  # Se l'uccello sta cadendo
        velocity_penalty = 10  # Aggiungi un costo extra

    # Euristica totale
    return vertical_distance + horizontal_distance + velocity_penalty

def is_goal(state, goal):
    # Il goal è raggiunto se l'uccello ha superato completamente il tubo
    return state.bird_x >= state.pipe_x + state.pipe_width/2

def simulate(state, action):
    # Simula il movimento dell'uccello

    new_vel = min(state.bird_vel + 1,7) if action == 0 else -7
    new_y = state.bird_y + new_vel

    # La posizione orizzontale dell'uccello non cambia (a meno che non ci sia uno scorrimento)
    new_bird_x = state.bird_x

    # Simula il movimento dei tubi
    new_pipe_x = state.pipe_x - SCROLL_SPEED

    return State(new_bird_x, new_y, new_vel, new_pipe_x, state.pipe_width, state.pipe_top_y, state.pipe_bottom_y)

def reconstruct_path(came_from, current):
    # Ricostruisci il percorso dallo stato finale allo stato iniziale
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

def a_star_search(initial_state, goal):
    open_set = PriorityQueue()
    open_set.put((heuristic(initial_state, goal), initial_state))  # Inserisci (f_score, state)
    came_from = {}
    g_score = {initial_state: 0}

    while not open_set.empty():
        _, current = open_set.get()  # Estrai lo stato con il f_score più basso

        if is_goal(current, goal):
            return reconstruct_path(came_from, current)

        for action in [0, 1]:  # 0 = non saltare, 1 = saltare
            next_state = simulate(current, action)
            tentative_g_score = g_score[current] + 1  # Costo uniforme

            if next_state not in g_score or tentative_g_score < g_score[next_state]:
                came_from[next_state] = current
                g_score[next_state] = tentative_g_score
                f_score = tentative_g_score + heuristic(next_state, goal)
                open_set.put((f_score, next_state))  # Inserisci (f_score, next_state)

    return None  # Nessun percorso trovato

class simpleSearchFlappy:
    def __init__(self):
        self.reset()

    def reset(self):
        global score, high_score
        if score > high_score:
            high_score = score
        score = 0

        self.bird = Bird()
        self.pipe_timer = 0
        self.pipes = []
        self.ground = [Ground(0, 520), Ground(WIN_WIDTH, 520)]

    def get_state(self):
        # Trova il tubo più vicino
        min_distance = float('inf')
        closest_top_pipe = None
        closest_bottom_pipe = None

        for pipe in self.pipes:
            if pipe.rect.x + 26 > self.bird.rect.x:  # Considera solo le pipe davanti al bird
                distance = pipe.rect.x - self.bird.rect.x
                if distance <= min_distance:
                    min_distance = distance
                    if pipe.pipe_type == 'bottom':
                        closest_bottom_pipe = pipe
                    else:
                        closest_top_pipe = pipe

        # Se non ci sono pipe davanti, usa valori predefiniti
        if closest_bottom_pipe is None or closest_top_pipe is None:
            pipe_x = WIN_WIDTH
            pipe_width = 52
            pipe_top_y = 0
            pipe_bottom_y = WIN_HEIGHT
        else:
            pipe_x = closest_bottom_pipe.rect.x
            pipe_width = closest_bottom_pipe.rect.width
            pipe_top_y = closest_top_pipe.rect.bottom
            pipe_bottom_y = closest_bottom_pipe.rect.top

        # Crea lo stato
        return State(
            bird_x=self.bird.rect.x,
            bird_y=self.bird.rect.y,
            bird_vel=self.bird.vel,
            pipe_x=pipe_x,
            pipe_width=pipe_width,
            pipe_top_y=pipe_top_y,
            pipe_bottom_y=pipe_bottom_y
        )

    def decide_action(self):
        # Ottieni lo stato corrente
        state = self.get_state()

        # Esegui A* per trovare la migliore azione
        path = a_star_search(state, goal=None)

        if path:
            return [1] if path[0].bird_vel == -7 else [0]  # Restituisci la prima azione del percorso
        else:
            return [0]  # Default: non saltare

    def game_step(self, action=None):
        reward = 0.1
        # Spawn dei tubi
        self.spawn_pipe()


        for pipe in self.pipes:
            pipe_update = pipe.update()
            # Controlla se l'uccello ha superato il tubo (usando la posizione attuale)
            if pipe.pipe_type == 'bottom' and not pipe.passed:
                if self.bird.rect.x > pipe.rect.right:
                    pipe.passed = True
                    self.score += 1
                    reward += 1
            if pipe_update:
                self.pipes.remove(pipe)

        # Aggiorna il terreno
        for ground in self.ground:
            ground.update()

        # Aggiorna l'uccello
        if action is None:
            action = self.decide_action()
        self.bird.update(action)

        # Controllo di collisione con i tubi o il suolo
        for pipe in self.pipes:
            if self.bird.rect.colliderect(pipe.rect):
                self.bird.alive = False
                reward -= 5
                return reward, True, score

        for ground in self.ground:
            if self.bird.rect.colliderect(ground.rect):
                self.bird.alive = False
                reward -= 5
                return reward, True, score

        return reward, not self.bird.alive, score

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
            reward, done, score = game.game_step()
            if done:
                print(f"Game Over! Score: {score}")
                game.reset()
    except KeyboardInterrupt:
        print("Game interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")