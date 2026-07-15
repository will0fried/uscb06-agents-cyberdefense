# Entraine un agent RL (PPO) sur CAGE 2 (Scenario2, reseau d'entreprise), attaquant B_line.
# A copier dans ~/cage-challenge-2/CybORG/ puis :  caffeinate -i python cage2_entrainement_rl.py
# Duree : ~20-30 min. Surveille ep_rew_mean : si ca MONTE, il apprend le terrain.
import inspect, time
import numpy as np
import gymnasium as gymn
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

TOURS = 30                 # identique a l evaluation finale (cage2_campagne.py)
PAS_TOTAL = 300_000

class Env(gymn.Env):
    def __init__(self):
        path = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'
        cyborg = CybORG(path, 'sim', agents={'Red': B_lineAgent})
        self.interne = ChallengeWrapper(env=cyborg, agent_name='Blue')
        self.compteur = 0
        self.action_space = gymn.spaces.Discrete(self.interne.action_space.n)
        obs = self.interne.reset()
        self.observation_space = gymn.spaces.Box(low=-np.inf, high=np.inf,
                                                 shape=(len(obs),), dtype=np.float32)
    def reset(self, seed=None, options=None):
        self.compteur = 0
        return np.asarray(self.interne.reset(), dtype=np.float32), {}
    def step(self, action):
        obs, r, done, info = self.interne.step(int(action))
        self.compteur += 1
        return np.asarray(obs, dtype=np.float32), float(r), bool(done), self.compteur >= TOURS, info

print("Entrainement PPO sur CAGE 2 (attaquant B_line)...", flush=True)
env = Env()
modele = PPO("MlpPolicy", env, verbose=1, seed=42)
t = time.time()
modele.learn(total_timesteps=PAS_TOTAL)
modele.save("ppo_cage2")
print(f"\nTermine en {(time.time()-t)/60:.0f} min -> ppo_cage2.zip", flush=True)
