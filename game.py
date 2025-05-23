import os

import pygame
from sys import exit
import random
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

clock = pygame.time.Clock()


# Window
WIN_HEIGHT = 720
WIN_WIDTH = 551
window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

# Images
bird_images = [pygame.image.load("assets/bird_down.png"),
               pygame.image.load("assets/bird_mid.png"),
               pygame.image.load("assets/bird_up.png")]
skyline_image = pygame.image.load("assets/background.png")
ground_image = pygame.image.load("assets/ground.png")
top_pipe_image = pygame.image.load("assets/pipe_top.png")
bottom_pipe_image = pygame.image.load("assets/pipe_bottom.png")

# Game Constants
SCROLL_SPEED = 5
BIRD_START_POSITION = (100, 250)
score = 0
high_score = 0
font = pygame.font.SysFont('Segoe', 26)

class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = bird_images[0]
        self.rect = self.image.get_rect(center=BIRD_START_POSITION)
        self.image_index = 0
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
        if self.rect.y < 500:
            self.rect.y += int(self.vel)
        if self.vel == 0:
            self.flap = False

        angle = max(-30, min(self.vel * -7, 45))
        self.image = pygame.transform.rotate(self.image, angle)

        if action[0] == 1 and not self.flap and self.rect.y > 0 and self.alive:
            self.flap = True
            self.vel = -7

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, image, pipe_type):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pipe_type = pipe_type
        self.passed = False

    def update(self):
        global score
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.kill()

        if self.pipe_type == 'bottom' and not self.passed:
            if BIRD_START_POSITION[0] > self.rect.left:
                self.passed = True
                score += 1
                return 2
        return 0

class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = ground_image
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.rect.x = WIN_WIDTH

class FlappyBirdAI:
    def __init__(self):
        self.reset()
        self.consecutive_jumps = 0

    def reset(self):
        global score, high_score
        if score > high_score:
            high_score = score
        score = 0

        self.bird = pygame.sprite.GroupSingle(Bird())
        self.pipe_timer = 0
        self.pipes = pygame.sprite.Group()
        self.ground = pygame.sprite.Group(Ground(0, 520), Ground(WIN_WIDTH, 520))

    def quit_game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

    def spawn_pipe(self):
        if self.pipe_timer <= 0 and self.bird.sprite.alive:
            y_top = random.randint(-600, -480)
            y_bottom = y_top + random.randint(90, 130) + bottom_pipe_image.get_height()
            self.pipes.add(Pipe(WIN_WIDTH, y_top, top_pipe_image, 'top'))
            self.pipes.add(Pipe(WIN_WIDTH, y_bottom, bottom_pipe_image, 'bottom'))
            self.pipe_timer = 70
        self.pipe_timer -= 1

    def game_step(self, action):
        reward = 1
        self.quit_game()
        # todo window.blit(skyline_image, (0, 0))

        self.spawn_pipe()
        reward += sum(pipe.update() for pipe in self.pipes)
        self.ground.update()
        self.bird.update(action)

        #todo self.pipes.draw(window)
        #todo self.ground.draw(window)
        #todo self.bird.draw(window)

        # reward in intervallo
        min_distance = float('inf')
        closest_top_pipe = None
        closest_bottom_pipe = None
        for pipe in self.pipes:
            if pipe.rect.x + 26 > self.bird.sprite.rect.x:  # Considera solo le pipe davanti al bird
                distance = pipe.rect.x - self.bird.sprite.rect.x
                if distance <= min_distance:
                    min_distance = distance
                    if pipe.pipe_type == 'bottom':
                        closest_bottom_pipe = pipe
                    else:
                        closest_top_pipe = pipe

        # Penalità progressiva per salti consecutivi
        if action[0] == 1:
            reward -= 0.05 * self.consecutive_jumps
            self.consecutive_jumps += 1
        else:
            self.consecutive_jumps = max(0, self.consecutive_jumps - 1)

        # Se il bird è vicino all altezza ottimale rewardalo linearmente in base alla distanza
        if closest_top_pipe and closest_bottom_pipe:
            gap_top = closest_top_pipe.rect.bottom
            gap_bottom = closest_bottom_pipe.rect.top
            bird_y = self.bird.sprite.rect.y

            if gap_top < bird_y < gap_bottom:
                # Nel gap, calcola quanto è vicino al centro del gap
                optimal_y = (gap_top + gap_bottom) / 2
                y_dev = abs(bird_y - optimal_y) / (gap_bottom - gap_top)
                # Più è vicino al centro, più reward (massimo +0.2)
                reward += (1 - y_dev) * 0.2
            else:
                # Fuori dal gap, penalità proporzionale alla distanza
                if bird_y < gap_top:
                    y_dev = (gap_top - bird_y) / WIN_HEIGHT
                else:
                    y_dev = (bird_y - gap_bottom) / WIN_HEIGHT
                reward -= y_dev * 0.4  # Penalità più pesante

        #todo score_text = font.render(f'Score: {score}  High Score: {high_score}', True, pygame.Color(255, 255, 255))
        #todo window.blit(score_text, (20, 20))

        # Controllo di collisione con i tubi o il suolo
        if pygame.sprite.spritecollide(self.bird.sprite, self.pipes, False) or \
            pygame.sprite.spritecollide(self.bird.sprite, self.ground, False):
            self.bird.sprite.alive = False
            reward -= 5
            return reward, True, score

        # todo pygame.display.update()
        return reward, not self.bird.sprite.alive, score
