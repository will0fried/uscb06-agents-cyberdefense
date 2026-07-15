# Entrainement d'un agent RL (PPO) sur CybORG DroneSwarm.
# A copier dans ~/CybORG puis lancer :  caffeinate -i python entrainement_rl.py
# (caffeinate empeche le Mac de s'endormir pendant l'entrainement)
# Duree estimee : 30 min a 2 h selon la machine. Surveille la colonne ep_rew_mean :
# c'est la moyenne des scores recents - si elle monte, l'agent apprend.
import time
import numpy as np
import gymnasium as gymn
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

TOURS = 25                 # herite du protocole v1. ATTENTION : l evaluation finale
                           # (drones_campagne.py) se fait a 30 tours. Ecart assume et
                           # signale dans le memoire (section limites).
PAS_TOTAL = 300_000        # nombre de coups d'entrainement (~12 000 parties)

class AdaptateurGymnasium(gymn.Env):
    """Pont entre le vieux format 'gym' de CybORG et le format moderne
    'gymnasium' qu'attend stable-baselines3. Il coupe aussi chaque partie
    a 25 tours, comme dans toutes nos mesures."""
    def __init__(self):
        cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim')
        self.interne = OpenAIGymWrapper(agent_name='blue_agent_0',
                                        env=FixedFlatWrapper(cyborg))
        self.compteur = 0
        self.action_space = gymn.spaces.Discrete(self.interne.action_space.n)
        n = int(np.prod(self.interne.observation_space.shape))
        self.observation_space = gymn.spaces.Box(low=-np.inf, high=np.inf,
                                                 shape=(n,), dtype=np.float32)
    def reset(self, seed=None, options=None):
        obs = self.interne.reset()
        self.compteur = 0
        return np.asarray(obs, dtype=np.float32).flatten(), {}
    def step(self, action):
        obs, r, done, info = self.interne.step(int(action))
        self.compteur += 1
        tronque = self.compteur >= TOURS
        return (np.asarray(obs, dtype=np.float32).flatten(),
                float(r), bool(done), tronque, info)

env = AdaptateurGymnasium()
print("Environnement pret. Debut de l'entrainement PPO...")
print("(la colonne a surveiller : ep_rew_mean - si elle monte, il apprend)\n")

modele = PPO("MlpPolicy", env, verbose=1, seed=42)
debut = time.time()
modele.learn(total_timesteps=PAS_TOTAL)
duree = (time.time() - debut) / 60

modele.save("ppo_droneswarm")
print(f"\nEntrainement termine en {duree:.0f} minutes.")
print("Modele sauvegarde : ppo_droneswarm.zip")
print("Prochaine etape : evaluer ce modele sur 40 parties, meme protocole que les autres.")
