# Evaluation de l'agent RL (ppo_droneswarm.zip) sur le protocole v2 :
# 100 parties de 30 tours, graines 1-100, APPARIEES avec les autres strategies.
# A copier dans ~/CybORG puis lancer :  python eval_rl_v2.py
import csv, statistics, random
import numpy as np
import gymnasium as gymn
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

PARTIES, TOURS = 100, 30

# meme adaptateur que pour l'entrainement, mais ici on FIXE la graine de chaque partie
class Env30:
    def __init__(self, graine):
        random.seed(graine); np.random.seed(graine)
        cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim', seed=graine)
        self.interne = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
        self.interne.action_space.seed(graine)
    def reset(self):
        return np.asarray(self.interne.reset(), dtype=np.float32).flatten()
    def step(self, action):
        obs, r, done, info = self.interne.step(int(action))
        return np.asarray(obs, dtype=np.float32).flatten(), float(r), bool(done)

modele = PPO.load("ppo_droneswarm")

scores = []
for graine in range(1, PARTIES + 1):
    env = Env30(graine)
    obs = env.reset()
    total = 0
    for _ in range(TOURS):
        action, _ = modele.predict(obs, deterministic=True)
        obs, r, fini = env.step(int(action))
        total += r
        if fini: break
    scores.append(total)
    print(f"partie {graine:3d}/{PARTIES} : {total:7.1f}", flush=True)

with open('resultats_rl_v2.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['graine', 'score'])
    for g, s in enumerate(scores, 1):
        w.writerow([g, s])

print(f"\n=== AGENT RL (PPO, graines 1-100, 30 tours) ===")
print(f"Moyenne : {statistics.mean(scores):.1f}")
print(f"Meilleure : {max(scores):.1f} | Pire : {min(scores):.1f}")
print("CSV : resultats_rl_v2.csv")
