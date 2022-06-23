import context
import torch
from pacman import RandomAgent, Environment, GameController
from QLearning import QNetwork, Qptimizer, ReplayMemory, utilities
from tqdm import tqdm
from random import random


path = "/".join(__loader__.path.split('/')[:-1])

class SimpleAgent(RandomAgent):

	def __init__(self, qnet : QNetwork, learning_rate = 0.01, gamma = 0.999, epsilon = 0.05, speed = 1):
		super().__init__(speed)
		self.gamma = gamma
		self.epsilon = epsilon
		self.memory = ReplayMemory(100000)

		self.policy_net = qnet
		self.target_net = qnet.clone()
		self.target_net.copy_from(self.policy_net)
		self.target_net.eval()

		# self.optimizer = torch.optim.RMSprop(self.policy_net.parameters(), lr=learning_rate)
		self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=learning_rate)
		self.optimizer = Qptimizer(
			self.memory,
			self.optimizer,
			self.policy_net,
			self.target_net,
			criterion = torch.nn.MSELoss()
		)

	def __call__(self, state):
		roll = random()
		if roll > self.epsilon:
			action = utilities.select_action(self.policy_net, state.unsqueeze(0))
			self.perform_action(action)
		else:
			super().__call__(state)
		#action = utilities.select_epsilon(self.policy_net, state.unsqueeze(0), 0.05) #!

	def save(self, path = "./net"):
		self.policy_net.save(path)

	def load(self, path = "./net"):
		self.policy_net.load(path)

	def feedback(self, state, action, reward, new_state):
		self.memory.push(state, action, reward, new_state)
		self.optimizer(gamma = self.gamma)

	def train(self, episodes = 1, update_frq = 10, live = False, plot = False, ghosts = Environment.default_ghosts):
		Environ = GameController if live else Environment

		score_history = []
		for episode in tqdm(range(episodes)):
			env = Environ(self, ghosts)
			while not env.terminal():
				next(env)
				if live: env.update()
			score_history.append(env.score)
			if episode % update_frq == 0:
				self.target_net.copy_from(self.policy_net)
			if plot:
				self.optimizer.plot_loss_variance()
				self.optimizer.plot_loss()
				utilities.quickplot(score_history, "Score", "./score")