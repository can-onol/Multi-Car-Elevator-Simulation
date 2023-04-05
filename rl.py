# import numpy as np
# import tensorflow as tf
# from tensorflow import keras
# from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.optimizers import Adam
# from matplotlib import pyplot
# from mcesim17 import *
#
# class Agent:
#     def __init__(self, state_size, action_size):
#         self.n_actions = action_size
#         # we define some parameters and hyperparameters:
#         # "lr" : learning rate
#         # "gamma": discounted factor
#         # "exploration_proba_decay": decay of the exploration probability
#         # "batch_size": size of experiences we sample to train the DNN
#         self.lr = 0.001
#         self.gamma = 0.99
#         self.exploration_proba = 1.0
#         self.exploration_proba_decay = 0.005
#         self.batch_size = 32
#
#
#         # We define our memory buffer where we will store our experiences
#         # We stores only the 2000 last time steps
#         self.memory_buffer = list()
#         self.max_memory_buffer = 2000
#
#         self.model = Sequential([
#             Dense(units=24, input_dim=state_size, activation='relu'),
#             Dense(units=24, activation='relu'),
#             Dense(units=action_size, activation='linear')
#         ])
#         self.model.compile(loss="mse",
#                            optimizer=Adam(lr=self.lr))
#
#         def compute_action(self, current_state):
#             # We sample a variable uniformly over [0,1]
#             # if the variable is less than the exploration probability
#             #     we choose an action randomly
#             # else
#             #     we forward the state through the DNN and choose the action
#             #     with the highest Q-value.
#             if np.random.uniform(0, 1) < self.exploration_proba:
#                 return np.random.choice(range(self.n_actions))
#             q_values = self.model.predict(current_state)[0]
#             return np.argmax(q_values)
#
#         # when an episode is finished, we update the exploration probability using
#         # espilon greedy algorithm
#         def update_exploration_probability(self):
#             self.exploration_proba = self.exploration_proba * np.exp(-self.exploration_proba_decay)
#             print(self.exploration_proba)
#
#         # At each time step, we store the corresponding experience
#         def store_episode(self, current_state, action, reward, next_state, done):
#             # We use a dictionnary to store them
#             self.memory_buffer.append({
#                 "current_state": current_state,
#                 "action": action,
#                 "reward": reward,
#                 "next_state": next_state,
#                 "done": done
#             })
#
