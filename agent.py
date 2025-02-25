import torch
import random
import numpy as np
from collections import deque
from game import FlappyBirdAI, Bird, Pipe, Ground
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()

        self.model = Linear_QNet(8, 256, 1)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)


    def get_state(self, game):
        #prossimo pipe
        min_distance = float('inf')
        closest_top_pipe = None
        closest_bottom_pipe = None
        for pipe in game.pipes:
            if pipe.rect.x + 26 > game.bird.sprite.rect.x:  # Considera solo le pipe davanti al bird
                distance = pipe.rect.x - game.bird.sprite.rect.x
                if distance <= min_distance:
                    min_distance = distance
                    if pipe.pipe_type == 'bottom':
                        closest_bottom_pipe = pipe
                    else:
                        closest_top_pipe = pipe

    # next_pipe_up_y, next_pipe_down_y, birdSpeed, bird_acceleration (speed-prevSpeed),  in_pipe, y_pos, isFlapping, x_distance_from_pipe
        if closest_bottom_pipe is None or closest_top_pipe is None:
            dist_x = 9999
            bottom_pipe_y = 9999
            top_pipe_y = 9999
            in_pipe = False
        else:
            dist_x = (closest_bottom_pipe.rect.width // 2) - game.bird.sprite.rect.x
            bottom_pipe_y = closest_bottom_pipe.rect.y
            top_pipe_y = closest_top_pipe.rect.y
            in_pipe = (closest_bottom_pipe.rect.x - game.bird.sprite.rect.x) <= 26

        state = [
            dist_x,  # distanza dal prossimo pipe in orizzontale
            bottom_pipe_y,  # altezza pipe basso
            top_pipe_y,  # altezza pipe alto
            in_pipe,  # l'uccello è tra i tubi
            game.bird.sprite.flap,  # l'uccello sta sbattendo le ali
            game.bird.sprite.rect.y,  # posizione verticale dell'uccello
            game.bird.sprite.vel,  # velocità dell'uccello
            game.bird.sprite.vel - game.bird.sprite.prevVel  # accelerazione dell'uccello
        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 80 - self.n_games
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 1)  # Scelta casuale (esplorazione)
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)  # Output della rete neurale
            move = torch.argmax(prediction).item()  # Indice della mossa migliore
        return move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = FlappyBirdAI()
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.game_step(final_move)
        print(reward, done, score)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()