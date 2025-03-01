import torch
import random
import numpy as np
from collections import deque
from game import FlappyBirdAI, WIN_HEIGHT, WIN_WIDTH
from model import Linear_QNet, QTrainer
from helper import plot

BATCH_SIZE = 512
LR = 0.001
GAMMA = 0.98
MAX_MEMORY = 50_000


class Agent:

    def __init__(self, loadbestmodel=False):
        self.n_games = 0
        self.epsilon = 0 if loadbestmodel else 100  # randomness
        self.gamma = GAMMA  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()

        self.model = Linear_QNet(7, 2)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game):
        #prossimo pipe
        min_distance = float('inf')
        closest_top_pipe = None
        closest_bottom_pipe = None
        for pipe in game.pipes:
            if pipe.pipe_type == 'top' and pipe.rect.right > game.bird.sprite.rect.left:  # Considera solo le pipe davanti al bird
                distance = pipe.rect.left - game.bird.sprite.rect.right
                if distance < min_distance:
                    min_distance = distance
                    closest_top_pipe = pipe

        if closest_top_pipe:
            for p in game.pipes:
                if p.pipe_type == 'bottom' and p.rect.centerx == closest_top_pipe.rect.centerx:
                    closest_bottom_pipe = p
                    break

        # next_pipe_up_y, next_pipe_down_y, birdSpeed, bird_acceleration (speed-prevSpeed),  in_pipe, y_pos, isFlapping, x_distance_from_pipe
        if closest_bottom_pipe is None or closest_top_pipe is None:
            optimal_y = WIN_HEIGHT / 3
            dist_x = WIN_WIDTH
            bottom_pipe_y = WIN_HEIGHT
            top_pipe_y = 0
            in_pipe = False
        else:
            optimal_y = (closest_top_pipe.rect.bottom + closest_bottom_pipe.rect.top) / 2
            dist_x = closest_bottom_pipe.rect.left.__int__() - game.bird.sprite.rect.right.__int__()
            bottom_pipe_y = closest_bottom_pipe.rect.top.__int__()
            top_pipe_y = closest_top_pipe.rect.bottom.__int__()
            in_pipe = (closest_bottom_pipe.rect.x.__int__() - game.bird.sprite.rect.x.__int__()) <= 26

        state = [
            # optimal_y / WIN_HEIGHT,  #Altezza ottimale
            dist_x / WIN_WIDTH,  # Distanza orizzontale normalizzata
            bottom_pipe_y / WIN_HEIGHT,  # Altezza tubo inferiore normalizzata
            top_pipe_y / WIN_HEIGHT,  # Altezza tubo superiore normalizzata
            # float(in_pipe),  # Indicatore se l'uccello è tra i tubi
            float(game.bird.sprite.flap),  # Indicatore se l'uccello sta sbattendo le ali
            game.bird.sprite.rect.y / WIN_HEIGHT,  # Posizione verticale normalizzata
            (game.bird.sprite.vel + 7) / 14, # Velocità dell uccello normalizzata tra 0 e 1
            (game.bird.sprite.vel - game.bird.sprite.prevVel + 7) / 14 #Accellerazione dell'uccello normalizzata tra 0 e 1
        ]

        return np.array(state, dtype=np.float32)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))  # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)  # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        # 1 0 salta, 0 1 non salta
        final_move = [0, 0]
        self.epsilon = max(5.0, self.epsilon * 0.995)
        if random.randint(0, 100) < self.epsilon:
            move = random.randint(0, 10)
            if move >= 9:  # Scelta casuale (esplorazione)
                move = 1  #salta
            else:
                move = 0  #non salta
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)  # Output della rete neurale
            move = torch.argmax(prediction).item()  # Indice della mossa migliore
        final_move[move] = 1
        return final_move


def train():
    plot_scores = deque(maxlen=100)  # Mantiene solo gli ultimi 100 giochi
    plot_mean_scores = deque(maxlen=100)
    total_score = 0
    update_interval = 50
    record = 0
    game = FlappyBirdAI()
    loadBestModel = input("Caricare modello? (s/n): ").strip().lower() == 's'
    agent = Agent(loadBestModel)
    if loadBestModel:
        modelNo = input("Quale modello vuoi caricare? (record modello): ").strip()
        try:
            agent.model.load(modelNo)
            print("Miglior modello caricato con successo!")
        except FileNotFoundError:
            print("Nessun modello trovato, si inizia da zero.")

    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.game_step(final_move)

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
                agent.model.save(record)

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)

            if agent.n_games % update_interval == 0:  #Aggiorna il grafico ogni 50 giochi
                plot(list(plot_scores), list(plot_mean_scores))


if __name__ == '__main__':
    train()
