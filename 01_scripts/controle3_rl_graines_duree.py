# DroneSwarm - Controle 3 : la graine et la duree d'entrainement changent-elles le resultat du RL ?
# Le modele publie (ppo_droneswarm) est entraine avec la graine 42 sur des parties de 25 tours.
# Deux objections possibles : (1) la graine 42 serait tombee juste, (2) l'entrainement a 25 tours
# alors que l'evaluation est a 30 penaliserait le RL. Ce controle repond aux deux avec des chiffres.
#
# On entraine 3 modeles, on ne change qu'UNE chose a la fois :
#   g43_t25 et g44_t25 -> meme duree que le modele publie, seule la graine change (objection 1)
#   g42_t30            -> meme graine que le modele publie, seule la duree change (objection 2)
# Les 3 sont evalues sur le protocole publie : 1000 parties de 30 tours, graines 1-1000 appariees.
#
# A copier dans ~/CybORG puis : caffeinate -i python controle3_rl_graines_duree.py
# Duree : environ 1 h d'entrainement (3 x 20 min) puis l'evaluation. Peut tourner la nuit.
# Produit : controle3_g43_t25.csv, controle3_g44_t25.csv, controle3_g42_t30.csv

import inspect, csv, statistics, random, time, math
import numpy as np
import gymnasium as gymn
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

print('CONDITIONS - CybORG:', inspect.getfile(CybORG), flush=True)

PAS_TOTAL = 300_000              # identique au modele publie
PARTIES_EVAL, TOURS_EVAL = 1000, 30   # evaluation TOUJOURS a 30 tours (le protocole publie)

# (nom, graine d'entrainement, duree des parties d'entrainement)
CONFIGS = [
    ("g43_t25", 43, 25),
    ("g44_t25", 44, 25),
    ("g42_t30", 42, 30),
]


class AdaptateurGymnasium(gymn.Env):
    """Meme adaptateur que entrainement_rl.py, avec la duree de partie en parametre."""
    def __init__(self, tours):
        self.tours = tours
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
        return (np.asarray(obs, dtype=np.float32).flatten(), float(r),
                bool(done), self.compteur >= self.tours, info)


def entraine(nom, graine, tours):
    print(f"\n=== Entrainement {nom} : graine {graine}, parties de {tours} tours ===", flush=True)
    t = time.time()
    env = AdaptateurGymnasium(tours)
    modele = PPO("MlpPolicy", env, verbose=0, seed=graine)
    modele.learn(total_timesteps=PAS_TOTAL)
    modele.save(f"ppo_droneswarm_{nom}")
    print(f"  termine en {(time.time()-t)/60:.0f} min -> ppo_droneswarm_{nom}.zip", flush=True)


def evalue(nom):
    # exactement le protocole de drones_campagne.py : graines 1-1000 appariees, 30 tours
    modele = PPO.load(f"ppo_droneswarm_{nom}")
    scores, t = [], time.time()
    for g in range(1, PARTIES_EVAL + 1):
        random.seed(g); np.random.seed(g)
        cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim', seed=g)
        env = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
        env.action_space.seed(g)
        obs = env.reset(); total = 0
        for _ in range(TOURS_EVAL):
            o = np.asarray(obs, dtype=np.float32).flatten()
            a, _ = modele.predict(o, deterministic=True)
            obs, r, fini, _ = env.step(int(a)); total += r
            if fini: break
        scores.append(round(total, 2))
        if g % 200 == 0:
            print(f"  {nom}: {g}/{PARTIES_EVAL}, {time.time()-t:.0f}s", flush=True)
    fic = f"controle3_{nom}.csv"
    with open(fic, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['graine', 'score'])
        for i, s in enumerate(scores, 1): w.writerow([i, s])
    m = statistics.mean(scores)
    ic = 1.96 * statistics.stdev(scores) / math.sqrt(len(scores))
    print(f"FINI {fic} : moyenne {m:.2f}  IC 95% [{m-ic:.2f} ; {m+ic:.2f}]  (n={len(scores)})", flush=True)
    return m, ic


for nom, graine, tours in CONFIGS:
    entraine(nom, graine, tours)

print("\n=== EVALUATION des 3 modeles (1000 parties de 30 tours, graines 1-1000) ===", flush=True)
resultats = {}
for nom, _, _ in CONFIGS:
    resultats[nom] = evalue(nom)

print("\n=== RECAPITULATIF ===", flush=True)
print("  modele publie (graine 42, 25 tours) : -194.35  IC 95% [-201.54 ; -187.15]", flush=True)
for nom, (m, ic) in resultats.items():
    print(f"  {nom:10s} : {m:8.2f}  IC 95% [{m-ic:.2f} ; {m+ic:.2f}]", flush=True)
print("\n  Lecture : si les 3 tombent dans l'intervalle du modele publie, ni la graine", flush=True)
print("  ni la duree d'entrainement n'expliquent le resultat. C'est le terrain.", flush=True)
