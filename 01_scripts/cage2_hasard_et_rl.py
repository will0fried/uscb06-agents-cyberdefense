# CAGE 2 : hasard vs RL entraine, 100 parties de 30 tours, graines communes, attaquant B_line.
# A copier dans ~/cage-challenge-2/CybORG/ puis :  python cage2_hasard_et_rl.py
import inspect, csv, statistics, random
import numpy as np
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

PARTIES, TOURS = 100, 30
PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'

def joue(politique):
    scores = []
    for graine in range(1, PARTIES + 1):
        random.seed(graine); np.random.seed(graine)
        cyborg = CybORG(PATH, 'sim', agents={'Red': B_lineAgent})
        env = ChallengeWrapper(env=cyborg, agent_name='Blue')
        env.action_space.seed(graine)   # controle le tirage du hasard
        obs = env.reset()
        total = 0
        for _ in range(TOURS):
            a = politique(obs, env)
            obs, r, done, info = env.step(a)
            total += r
            if done: break
        scores.append(round(total, 2))
    return scores

# --- hasard ---
scores_hasard = joue(lambda obs, env: env.action_space.sample())

# --- RL entraine ---
modele = PPO.load("ppo_cage2")
def politique_rl(obs, env):
    a, _ = modele.predict(np.asarray(obs, dtype=np.float32), deterministic=True)
    return int(a)
scores_rl = joue(politique_rl)

# --- sauvegarde + comparaison appariee ---
with open('cage2_hasard.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['graine', 'score'])
    for g, s in enumerate(scores_hasard, 1): w.writerow([g, s])
with open('cage2_rl.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['graine', 'score'])
    for g, s in enumerate(scores_rl, 1): w.writerow([g, s])

victoires_rl = sum(1 for h, r in zip(scores_hasard, scores_rl) if r > h)
print(f"\n=== CAGE 2 (100 parties de 30 tours, attaquant B_line) ===")
print(f"Hasard : moyenne {statistics.mean(scores_hasard):.2f}")
print(f"RL     : moyenne {statistics.mean(scores_rl):.2f}")
print(f"Comparaison appariee : le RL bat le hasard sur {victoires_rl}/100 parties")
print("CSV : cage2_hasard.csv, cage2_rl.csv")
