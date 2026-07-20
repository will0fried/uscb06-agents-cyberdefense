# Experience complementaire : PPO avec observation NORMALISEE sur DroneSwarm.
#
# Question : le plafond du PPO sur DroneSwarm (-194,35, a peine mieux que le hasard) tient-il
# a la representation - une observation brute de 11 293 valeurs donnee telle quelle a une
# MlpPolicy - ou au terrain lui-meme ? Cette experience change UN SEUL facteur par rapport a
# entrainement_rl.py : l'observation est normalisee (VecNormalize). Meme reseau, meme budget
# (300 000 pas), meme graine (42), meme duree d'entrainement (25 tours).
#
# Portee : ce test porte sur la NORMALISATION (l'echelle des valeurs), pas sur une
# representation structuree (graphe). Si le plafond survit a la normalisation, il ne tient pas
# a un simple probleme d'echelle ; une representation par graphes (King et al. [9]) reste le
# prolongement nomme au chapitre 4.
#
# A copier dans ~/CybORG puis : caffeinate -i python entrainement_rl_normalise.py
# Produit : ppo_droneswarm_norm.zip, norm_stats.npz, et drones_rl_norm_final.csv (protocole
# apparie identique a drones_campagne.py : 1000 parties de 30 tours, graines 1-1000).

import time, csv, statistics, random, sys
import numpy as np
import gymnasium as gymn
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

TOURS_ENTRAINEMENT = 25
PAS_TOTAL = 300_000


class AdaptateurGymnasium(gymn.Env):
    """Identique a entrainement_rl.py : pont gym -> gymnasium, coupe a 25 tours."""
    def __init__(self):
        cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim')
        self.interne = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
        self.compteur = 0
        self.action_space = gymn.spaces.Discrete(self.interne.action_space.n)
        n = int(np.prod(self.interne.observation_space.shape))
        self.observation_space = gymn.spaces.Box(low=-np.inf, high=np.inf, shape=(n,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        obs = self.interne.reset()
        self.compteur = 0
        return np.asarray(obs, dtype=np.float32).flatten(), {}

    def step(self, action):
        obs, r, done, info = self.interne.step(int(action))
        self.compteur += 1
        tronque = self.compteur >= TOURS_ENTRAINEMENT
        return np.asarray(obs, dtype=np.float32).flatten(), float(r), bool(done), tronque, info


# --- Entrainement avec observation normalisee ---
venv = DummyVecEnv([lambda: AdaptateurGymnasium()])
venv = VecNormalize(venv, norm_obs=True, norm_reward=False, clip_obs=10.0)

modele = PPO("MlpPolicy", venv, verbose=1, seed=42)
print("Entrainement PPO avec observation NORMALISEE (surveille ep_rew_mean)...", flush=True)
t0 = time.time()
modele.learn(total_timesteps=PAS_TOTAL)
print(f"Entrainement termine en {(time.time()-t0)/60:.0f} min", flush=True)
modele.save("ppo_droneswarm_norm")

# On fige les statistiques de normalisation apprises, pour les rejouer a l'evaluation.
mean = venv.obs_rms.mean.astype(np.float32)
var = venv.obs_rms.var.astype(np.float32)
eps = float(venv.epsilon)
clip = float(venv.clip_obs)
np.savez("norm_stats.npz", mean=mean, var=var, eps=eps, clip=clip)


def normalise(o):
    return np.clip((o - mean) / np.sqrt(var + eps), -clip, clip).astype(np.float32)


# --- Evaluation : protocole apparie identique a drones_campagne.py ---
PARTIES, TOURS = 1000, 30
print(f"\nEvaluation sur {PARTIES} parties de {TOURS} tours (graines appariees 1-{PARTIES})...", flush=True)
sc, td = [], time.time()
for g in range(1, PARTIES + 1):
    random.seed(g); np.random.seed(g)
    cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim', seed=g)
    env = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
    env.action_space.seed(g)
    obs = env.reset(); total = 0
    for _ in range(TOURS):
        o = np.asarray(obs, dtype=np.float32).flatten()
        a, _ = modele.predict(normalise(o), deterministic=True)
        obs, r, fini, _ = env.step(int(a)); total += r
        if fini: break
    sc.append(round(total, 2))
    if g % 200 == 0:
        print(f'  {g}/{PARTIES}, {time.time()-td:.0f}s', flush=True)

with open('drones_rl_norm_final.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['graine', 'score'])
    for i, s in enumerate(sc, 1):
        w.writerow([i, s])

print(f"\nFINI drones_rl_norm_final.csv : moyenne {statistics.mean(sc):.2f} (n={len(sc)})", flush=True)
print("RAPPEL pour comparer : PPO brut -194,35 | action fixe -194,38 | hasard -205,83 | regle -197,56", flush=True)
