# Entraine 2 agents RL supplementaires (graines 43 et 44), 30 tours/partie,
# pour ne pas dependre d'un seul entrainement (recommandation Henderson/Colas).
# A copier dans ~/CybORG puis lancer :  caffeinate -i python entrainement_rl_multi.py
# Duree : ~20-25 min par modele, ~45 min au total.
import time
import numpy as np
import gymnasium as gymn
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

TOURS = 30
PAS_TOTAL = 300_000

class AdaptateurGymnasium(gymn.Env):
    def __init__(self):
        cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim')
        self.interne = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
        self.compteur = 0
        self.action_space = gymn.spaces.Discrete(self.interne.action_space.n)
        n = int(np.prod(self.interne.observation_space.shape))
        self.observation_space = gymn.spaces.Box(low=-np.inf, high=np.inf, shape=(n,), dtype=np.float32)
    def reset(self, seed=None, options=None):
        obs = self.interne.reset(); self.compteur = 0
        return np.asarray(obs, dtype=np.float32).flatten(), {}
    def step(self, action):
        obs, r, done, info = self.interne.step(int(action))
        self.compteur += 1
        return (np.asarray(obs, dtype=np.float32).flatten(), float(r), bool(done), self.compteur >= TOURS, info)

for graine in [43, 44]:
    print(f"\n===== Entrainement RL graine {graine} (30 tours) =====", flush=True)
    env = AdaptateurGymnasium()
    modele = PPO("MlpPolicy", env, verbose=0, seed=graine)
    t = time.time()
    modele.learn(total_timesteps=PAS_TOTAL)
    modele.save(f"ppo_droneswarm_g{graine}")
    print(f"  termine en {(time.time()-t)/60:.0f} min -> ppo_droneswarm_g{graine}.zip", flush=True)

print("\nOK. 2 modeles supplementaires prets : ppo_droneswarm_g43.zip, ppo_droneswarm_g44.zip")
