# CAGE 2 : meilleure action fixe. Balayage des 145 actions sur graines 1-50 (calibration),
# puis test de la meilleure sur graines 51-100 (jamais vues). Attaquant B_line, 30 tours.
# A copier dans ~/cage-challenge-2/CybORG/ puis : python cage2_action_fixe.py
import inspect, csv, statistics, random
import numpy as np
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

TOURS = 30
PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'

def joue_action(action, graines):
    scores = []
    for g in graines:
        random.seed(g); np.random.seed(g)
        env = ChallengeWrapper(env=CybORG(PATH, 'sim', agents={'Red': B_lineAgent}), agent_name='Blue')
        env.action_space.seed(g); env.reset()
        total = 0
        for _ in range(TOURS):
            _, r, done, _ = env.step(action)
            total += r
            if done: break
        scores.append(total)
    return statistics.mean(scores), scores

n_actions = 145
calib = range(1, 51)
print("Balayage des 145 actions sur graines 1-50...", flush=True)
moyennes = []
for a in range(n_actions):
    m, _ = joue_action(a, calib)
    moyennes.append((a, m))
    if a % 20 == 0:
        print(f"  action {a}/{n_actions-1} : {m:.2f}", flush=True)

meilleure = max(moyennes, key=lambda x: x[1])[0]
print(f"\n>>> Meilleure action sur graines 1-50 : #{meilleure} ({dict(moyennes)[meilleure]:.2f})")

# test sur graines neuves 51-100
m_test, scores_test = joue_action(meilleure, range(51, 101))
with open('cage2_action_fixe.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['graine', 'score', 'action', meilleure])
    for g, s in zip(range(51, 101), scores_test): w.writerow([g, s])

print(f"\n=== ACTION FIXE #{meilleure} sur graines 51-100 (neuves) ===")
print(f"Moyenne : {m_test:.2f}")
print("CSV : cage2_action_fixe.csv")
