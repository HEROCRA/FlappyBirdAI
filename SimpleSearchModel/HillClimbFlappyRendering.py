import os
import pygame
import random
from sys import exit
import copy

# Configurazione di pygame
pygame.init()
clock = pygame.time.Clock()

# Costanti del gioco
WIN_HEIGHT = 720
WIN_WIDTH = 551
SCROLL_SPEED = 5
BIRD_START_POSITION = (100, 250)
GROUND_HEIGHT = 219  # Altezza dell'immagine del terreno

window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird con Hill Climbing")

# Caricamento delle immagini e del font
bird_images = [pygame.image.load("../assets/bird_down.png"),
               pygame.image.load("../assets/bird_mid.png"),
               pygame.image.load("../assets/bird_up.png")]
skyline_image = pygame.image.load("../assets/background.png")
ground_image = pygame.image.load("../assets/ground.png")
top_pipe_image = pygame.image.load("../assets/pipe_top.png")
bottom_pipe_image = pygame.image.load("../assets/pipe_bottom.png")
font = pygame.font.SysFont('Segoe', 26)


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image_index = 0
        self.image = bird_images[0]
        self.rect = pygame.Rect(BIRD_START_POSITION[0], BIRD_START_POSITION[1], 34, 24)
        self.prevVel = 0
        self.vel = 0
        self.flap = False
        self.alive = True

    def update(self, action):
        if self.alive:
            self.image_index = (self.image_index + 1) % 30
            self.image = bird_images[self.image_index // 10]

            self.prevVel = self.vel
            self.vel = min(self.vel + 1, 7)
            # Limite inferiore basato sul terreno
            max_y = WIN_HEIGHT - GROUND_HEIGHT - self.rect.height
            if self.rect.y < max_y:
                self.rect.y += int(self.vel)
            else:
                self.rect.y = max_y
                self.alive = False

            if self.vel == 0:
                self.flap = False

            angle = max(-30, min(self.vel * -7, 45))
            self.image = pygame.transform.rotate(self.image, angle)

            if action[0] == 1 and not self.flap and self.rect.y > 0 and self.alive:
                self.flap = True
                self.vel = -7


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, image, height, pipe_type):
        super().__init__()
        self.image = pygame.transform.scale(image, (52, height))
        self.rect = pygame.Rect(x, y, 52, height)
        self.pipe_type = pipe_type
        self.passed = False

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            return True  # Segnale per rimuovere il tubo
        return False


class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = ground_image
        self.rect = pygame.Rect(x, y, self.image.get_width(), self.image.get_height())

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.rect.x = WIN_WIDTH


class simpleSearchFlappy:
    def __init__(self):
        self.reset()

    def reset(self):
        if hasattr(self, 'score') and self.score > self.high_score:
            self.high_score = self.score
        self.score = 0
        if not hasattr(self, 'high_score'):
            self.high_score = 0

        self.bird = Bird()
        self.pipe_timer = 0
        self.ground_y = WIN_HEIGHT - GROUND_HEIGHT
        self.ground = [Ground(0, self.ground_y), Ground(WIN_WIDTH, self.ground_y)]
        self.pipes = []

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
        new_game.ground_y = self.ground_y
        new_game.ground = [Ground(g.rect.x, g.rect.y) for g in self.ground]
        new_game.pipes = []
        for pipe in self.pipes:
            new_pipe = Pipe(pipe.rect.x, pipe.rect.y,
                            top_pipe_image if pipe.pipe_type == 'top' else bottom_pipe_image,
                            pipe.rect.height,
                            pipe.pipe_type)
            new_pipe.passed = pipe.passed
            new_game.pipes.append(new_pipe)
        return new_game

    def evaluate_state(self, game_state):
        if not game_state.bird.alive:
            return -1000

        target_y = WIN_HEIGHT / 2
        for pipe in game_state.pipes:
            if pipe.pipe_type == 'bottom' and pipe.rect.x > game_state.bird.rect.x:
                top_pipe = next((p for p in game_state.pipes if p.pipe_type == 'top' and p.rect.x == pipe.rect.x), None)
                if top_pipe:
                    gap_top = top_pipe.rect.bottom
                    gap_bottom = pipe.rect.top
                    target_y = (gap_top + gap_bottom) // 2
                    break
        return -abs(game_state.bird.rect.centery - target_y)

    def choose_action(self, horizon=40):
        best_action = 0
        best_eval = -float('inf')
        for action in [0, 1]:
            cloned_game = self.clone()
            for i in range(horizon):
                a = [action] if i == 0 else [0]
                done, _ = cloned_game.game_step(a, render=False)
                if done: break
            eval_value = self.evaluate_state(cloned_game)
            if eval_value > best_eval:
                best_eval, best_action = eval_value, action
        return [best_action]

    def game_step(self, action=None, render=True):
        if action is None: action = self.choose_action()

        if render:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            window.blit(skyline_image, (0, 0))

        self.spawn_pipe()

        # Aggiornamento dei tubi
        for pipe in self.pipes[:]:
            if pipe.update():
                self.pipes.remove(pipe)
            if pipe.pipe_type == 'bottom' and not pipe.passed and self.bird.rect.left > pipe.rect.right:
                pipe.passed = True
                self.score += 1

        # Aggiornamento terreno
        for ground in self.ground:
            ground.update()

        self.bird.update(action)

        # Renderizzazione
        if render:
            for pipe in self.pipes:
                window.blit(pipe.image, pipe.rect)
            for g in self.ground:
                window.blit(g.image, g.rect)
            window.blit(self.bird.image, self.bird.rect)
            score_text = font.render(f'Score: {self.score}  High Score: {self.high_score}', True, (255, 255, 255))
            window.blit(score_text, (20, 20))
            pygame.display.update()

        # Collisioni
        collision = any(self.bird.rect.colliderect(pipe.rect) for pipe in self.pipes) or \
                    any(self.bird.rect.colliderect(g.rect) for g in self.ground)

        if collision:
            self.bird.alive = False

        return not self.bird.alive, self.score

    def spawn_pipe(self):
        if self.pipe_timer <= 0 and self.bird.alive:
            gap = random.randint(90, 130)
            max_gap_center = self.ground_y - gap // 2 - 50
            gap_center = random.randint(150 + gap // 2, max_gap_center)

            top_pipe_height = gap_center - gap // 2
            bottom_pipe_top = gap_center + gap // 2
            bottom_pipe_height = self.ground_y - bottom_pipe_top

            self.pipes.append(Pipe(WIN_WIDTH, 0, top_pipe_image, top_pipe_height, 'top'))
            self.pipes.append(Pipe(WIN_WIDTH, bottom_pipe_top, bottom_pipe_image, bottom_pipe_height, 'bottom'))
            self.pipe_timer = 70
        self.pipe_timer -= 1


if __name__ == "__main__":
    game = simpleSearchFlappy()
    try:
        while True:
            done, score_val = game.game_step()
            if done:
                print(f"Game Over! Score: {score_val}")
                game.reset()
            clock.tick(500)
    except KeyboardInterrupt:
        print("Game interrotto dall'utente.")
    except Exception as e:
        print(f"Errore: {e}")