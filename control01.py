from mcesim17 import *
import numpy as np
import tensorflow as tf
from tensorflow import keras
from matplotlib import pyplot

state_size = 160
num_actions = 4
GAMMA = 0.95

# network = keras.Sequential([
#     # keras.layers.Dense(30, activation='relu', kernel_initializer=keras.initializers.he_normal()),
#     keras.layers.Conv1D(64, kernel_size=3, activation='relu', kernel_initializer=keras.initializers.he_normal()),
#     keras.layers.Conv1D(64, kernel_size=3, activation='relu', kernel_initializer=keras.initializers.he_normal()),
#     keras.layers.MaxPool1D((20)),
#     keras.layers.Flatten(),
#     keras.layers.Dense(30, activation='relu', kernel_initializer=keras.initializers.he_normal()),
#     keras.layers.Dense(num_actions, activation='softmax')
# ])
# network.compile(loss='categorical_crossentropy',optimizer=keras.optimizers.Adam())


@dataclass
class deneme:
    def __init__(self, A, B, r):
        self.A = A
        self.B = B
        self.reward = r
        self.input_vector = np.concatenate([self.B, self.A])

    def get_action(self, network, num_actions):
        # #  For CNN
        # softmax_out = network(self.input_vector.reshape((1, -1, 1)))

        # For Dense Layer
        softmax_out = network(self.input_vector.reshape((1, -1)))

        # print('input Shape:', self.input_vector.reshape((1, -1, 1)).shape)
        print(network.layers[0].weights[0][2])
        self.act = np.random.choice(num_actions, p=softmax_out.numpy()[0])
        return self.act

    def update_network(self, network, rewards, states, actions, num_actions):
        reward_sum = 0
        discounted_rewards = []
        for reward in rewards[::-1]:  # reverse buffer r
            reward_sum = reward + GAMMA * reward_sum
            discounted_rewards.append(reward_sum)
        discounted_rewards.reverse()
        discounted_rewards = np.array(discounted_rewards)
        # standardise the rewards
        discounted_rewards -= np.mean(discounted_rewards)
        discounted_rewards /= np.std(discounted_rewards)
        states = np.vstack(states)
        # print("states shape", states.shape,"\n")

        # # For CNN Layer
        # states = states.reshape(-1, 160, 1)
        # print('states shape:', states.shape)
        # loss = network.train_on_batch(states, discounted_rewards)
        onehot_actions = np.array([[1 if a == i else 0 for i in range(4)] for a in actions])
        loss = network.train_on_batch(states, onehot_actions, sample_weight=discounted_rewards)
        # print(network.summary())
        return loss

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
    #             loss = update_network(network, rewards, states, actions, num_actions)
    #             tot_reward = sum(rewards)
    #             print(f"Episode: {episode}, Reward: {tot_reward}, avg loss: {loss:.5f}")
    #             break
    #
    #         state = new_state