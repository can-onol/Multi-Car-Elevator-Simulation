from mcesim17 import *
import numpy as np
import tensorflow as tf
from tensorflow import keras
from matplotlib import pyplot

state_size = 160
num_actions = 4
GAMMA = 0.95

network = keras.Sequential([
    keras.layers.Dense(30, activation='relu', kernel_initializer=keras.initializers.he_normal()),
    keras.layers.Dense(30, activation='relu', kernel_initializer=keras.initializers.he_normal()),
    keras.layers.Dense(num_actions, activation='softmax')
])
network.compile(loss='categorical_crossentropy',optimizer=keras.optimizers.Adam())


@dataclass
class deneme:
    def __init__(self, A, B, r):
        self.A = A
        self.B = B
        self.reward = r
        self.input_vector = np.concatenate([self.B, self.A])

    def get_action(self, network, num_actions):
        softmax_out = network(self.input_vector.reshape((1, -1)))
        s = np.random.choice(num_actions, p=softmax_out.numpy()[0])
        return s

    # def update_network(network, rewards, states, actions, num_actions):
    #     reward_sum = 0
    #     discounted_rewards = []
    #     for reward in rewards[::-1]:  # reverse buffer r
    #         reward_sum = reward + GAMMA * reward_sum
    #         discounted_rewards.append(reward_sum)
    #     discounted_rewards.reverse()
    #     discounted_rewards = np.array(discounted_rewards)
    #     # standardise the rewards
    #     discounted_rewards -= np.mean(discounted_rewards)
    #     discounted_rewards /= np.std(discounted_rewards)
    #     states = np.vstack(states)
    #     loss = network.train_on_batch(states, discounted_rewards)
    #     return loss
    #
    # num_episodes = 10000000
    #
    # for episode in range(num_episodes):
    #     rewards = []
    #     states = []
    #     actions = []
    #     while True:
    #         action = get_action(network, state, num_actions)
    #         new_state, reward, done, _ = env.step(action)
    #         states.append(state)
    #         rewards.append(reward)
    #         actions.append(action)
    #
    #         if done:
    #             loss = update_network(network, rewards, states)
    #             tot_reward = sum(rewards)
    #             print(f"Episode: {episode}, Reward: {tot_reward}, avg loss: {loss:.5f}")
    #             break
    #
    #         state = new_state