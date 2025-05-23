import pygame
from sys import exit
import random

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
SCROLL_SPEED = 2
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
        self.vel = 0
        self.flap = False
        self.alive = True

    def update(self, user_input):
        if self.alive:
            self.image_index = (self.image_index + 1) % 30
            self.image = bird_images[self.image_index // 10]

        self.vel = min(self.vel + 0.5, 7)
        if self.rect.y < 500:
            self.rect.y += int(self.vel)
        if self.vel == 0:
            self.flap = False

        angle = max(-30, min(self.vel * -7, 90))
        self.image = pygame.transform.rotate(self.image, angle)

        if user_input[pygame.K_SPACE] and not self.flap and self.rect.y > 0 and self.alive:
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
                return 10
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
            self.pipe_timer = random.randint(70, 100)
        self.pipe_timer -= 1

    def game_step(self):
        reward = 0
        self.quit_game()
        user_input = pygame.key.get_pressed()
        window.blit(skyline_image, (0, 0))

        self.spawn_pipe()
        reward += sum(pipe.update() for pipe in self.pipes)
        self.ground.update()
        self.bird.update(user_input)

        self.pipes.draw(window)
        self.ground.draw(window)
        self.bird.draw(window)

        score_text = font.render(f'Score: {score}  High Score: {high_score}', True, pygame.Color(255, 255, 255))
        window.blit(score_text, (20, 20))

        if pygame.sprite.spritecollide(self.bird.sprite, self.pipes, False) or \
            pygame.sprite.spritecollide(self.bird.sprite, self.ground, False):
            self.bird.sprite.alive = False
            self.reset()
            reward -= 10

        clock.tick(60)
        pygame.display.update()
        return reward, not self.bird.sprite.alive, score

if __name__ == '__main__':
    game = FlappyBirdAI()
    while True:
        reward, gameOver, score = game.game_step()
        print(reward, gameOver, score)
