# Evaluation de l'agent RL entraine (ppo_droneswarm.zip) : 40 parties de 25 tours,
# meme protocole que le hasard, l'action fixe et le LLM.
# A copier dans ~/CybORG puis lancer :  python evaluation_rl.py
import csv, statistics
import numpy as np
import gymnasium as gymn
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

PARTIES, TOURS = 40, 25

class AdaptateurGymnasium(gymn.Env):
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

modele = PPO.load("ppo_droneswarm")
env = AdaptateurGymnasium()

scores = []
for partie in range(1, PARTIES + 1):
    obs, _ = env.reset()
    total = 0
    for _ in range(TOURS):
        action, _ = modele.predict(obs, deterministic=True)
        obs, r, fini, tronque, _ = env.step(int(action))
        total += r
        if fini or tronque:
            break
    scores.append(total)
    print(f"Partie {partie:2d}/{PARTIES} : {total:7.1f}   (moyenne provisoire : {statistics.mean(scores):7.1f})")

with open('resultats_rl_40parties.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['partie', 'score', 'agent', 'PPO_300k_pas', 'deterministe', True])
    for i, s in enumerate(scores, 1):
        w.writerow([i, s])

print(f"\n=== AGENT RL (PPO, 300 000 pas d'entrainement) ===")
print(f"Moyenne sur {PARTIES} parties : {statistics.mean(scores):.1f}")
print(f"Meilleure : {max(scores):.1f} | Pire : {min(scores):.1f}")
print("CSV ecrit : resultats_rl_40parties.csv (a copier dans preuves/02_resultats_bruts/)")
