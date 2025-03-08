import os
import pygame
import random
from sys import exit
import copy

# Configurazione di pygame
pygame.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((720, 551))

# Costanti del gioco
WIN_HEIGHT = 720
WIN_WIDTH = 551
SCROLL_SPEED = 5
BIRD_START_POSITION = (100, 250)

# Caricamento immagini
bird_images = [
    pygame.image.load("../assets/bird_down.png").convert_alpha(),
    pygame.image.load("../assets/bird_mid.png").convert_alpha(),
    pygame.image.load("../assets/bird_up.png").convert_alpha()
]
skyline_image = pygame.image.load("../assets/background.png").convert()
ground_image = pygame.image.load("../assets/ground.png").convert_alpha()
top_pipe_image = pygame.image.load("../assets/pipe_top.png").convert_alpha()
bottom_pipe_image = pygame.image.load("../assets/pipe_bottom.png").convert_alpha()

# Setup finestra
window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird AI")

font = pygame.font.SysFont('Segoe', 26)


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = bird_images[0]
        self.rect = self.image.get_rect(center=BIRD_START_POSITION)
        self.image_index = 0
        self.vel = 0
        self.flap = False
        self.alive = True
        self.prevVel = 0

    def update(self, action):
        if self.alive:
            self.image_index = (self.image_index + 1) % 30
            self.image = bird_images[self.image_index // 10]

        self.prevVel = self.vel
        self.vel = min(self.vel + 0.5, 7)
        if self.rect.y < 500:
            self.rect.y += int(self.vel)
        if self.vel == 0:
            self.flap = False

        if action[0] == 1 and not self.flap and self.rect.y > 0 and self.alive:
            self.flap = True
            self.vel = -7

        # Rotazione immagine
        angle = max(-30, min(self.vel * -7, 90))
        self.image = pygame.transform.rotate(self.image, angle)


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, pipe_type):
        super().__init__()
        self.image = top_pipe_image if pipe_type == 'top' else bottom_pipe_image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pipe_type = pipe_type
        self.passed = False

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.kill()
            return True
        return False


class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = ground_image
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.rect.x = WIN_WIDTH


class simpleSearchFlappy:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.high_score = 0
        self.bird = Bird()
        self.pipes = pygame.sprite.Group()
        self.ground = pygame.sprite.Group(
            Ground(0, 520),
            Ground(WIN_WIDTH, 520)
        )
        self.pipe_timer = 0

    def clone(self):
        new_game = simpleSearchFlappy()
        new_game.score = self.score
        new_game.high_score = self.high_score

        # Clona l'uccello
        new_game.bird = Bird()
        new_game.bird.rect = self.bird.rect.copy()
        new_game.bird.vel = self.bird.vel
        new_game.bird.flap = self.bird.flap
        new_game.bird.alive = self.bird.alive
        new_game.bird.image_index = self.bird.image_index

        # Clona i tubi
        new_game.pipes = pygame.sprite.Group()
        for pipe in self.pipes:
            new_pipe = Pipe(pipe.rect.x, pipe.rect.y, pipe.pipe_type)
            new_pipe.passed = pipe.passed
            new_game.pipes.add(new_pipe)

        # Clona il terreno
        new_game.ground = pygame.sprite.Group()
        for ground in self.ground:
            new_ground = Ground(ground.rect.x, ground.rect.y)
            new_game.ground.add(new_ground)

        new_game.pipe_timer = self.pipe_timer
        return new_game

    def evaluate_state(self, game_state):
        if not game_state.bird.alive:
            return -1000

        target_y = WIN_HEIGHT // 2
        for pipe in game_state.pipes:
            if pipe.pipe_type == 'bottom' and pipe.rect.x > game_state.bird.rect.x:
                for top_pipe in game_state.pipes:
                    if top_pipe.pipe_type == 'top' and top_pipe.rect.x == pipe.rect.x:
                        gap_top = top_pipe.rect.bottom
                        gap_bottom = pipe.rect.top
                        target_y = (gap_top + gap_bottom) // 2
                        break
                break

        return -abs(game_state.bird.rect.centery - target_y)

    def choose_action(self, horizon=35):
        best_action = 0
        best_eval = -float('inf')

        for action in [0, 1]:
            cloned_game = self.clone()
            done = False
            for i in range(horizon):
                current_action = [action] if i == 0 else [0]
                done, _ = cloned_game.game_step(current_action, render=False)
                if done:
                    break
            eval_value = self.evaluate_state(cloned_game)
            if eval_value > best_eval:
                best_eval = eval_value
                best_action = action
        return [best_action]

    def game_step(self, action=None, render=True):
        if action is None:
            action = self.choose_action()

        # Gestione eventi
        if render:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

        # Generazione nuovi tubi
        if self.pipe_timer <= 0 and self.bird.alive:
            y_top = random.randint(-600, -480)
            y_bottom = y_top + random.randint(90, 130) + bottom_pipe_image.get_height()
            self.pipes.add(Pipe(WIN_WIDTH, y_top, 'top'))
            self.pipes.add(Pipe(WIN_WIDTH, y_bottom, 'bottom'))
            self.pipe_timer = 70
        self.pipe_timer -= 1

        # Aggiornamento elementi di gioco
        self.bird.update(action)
        self.pipes.update()
        self.ground.update()

        # Controllo punteggio
        for pipe in self.pipes:
            if pipe.pipe_type == 'bottom' and not pipe.passed:
                if self.bird.rect.left > pipe.rect.right:
                    pipe.passed = True
                    self.score += 1

        # Controllo collisioni
        if pygame.sprite.spritecollide(self.bird, self.pipes, False) or \
                pygame.sprite.spritecollide(self.bird, self.ground, False):
            self.bird.alive = False

        # Rendering
        if render:
            window.blit(skyline_image, (0, 0))
            self.pipes.draw(window)
            self.ground.draw(window)
            window.blit(self.bird.image, self.bird.rect)

            # Testo punteggio
            score_text = font.render(f'Score: {self.score}  High Score: {self.high_score}', True, (255, 255, 255))
            window.blit(score_text, (20, 20))
            pygame.display.update()
            clock.tick(60)

        return not self.bird.alive, self.score


if __name__ == "__main__":
    game = simpleSearchFlappy()
    while True:
        done, score = game.game_step()
        if done:
            print(f"Game Over! Score: {score}")
            game.reset()