# Balayage complet : les 56 actions fixes, 40 parties de 25 tours chacune (2240 parties).
# A copier dans ~/CybORG puis lancer :  caffeinate -i python experience_complete.py
# Duree estimee : 15 a 45 minutes. Peut tourner la nuit sans surveillance.
import csv, statistics, random
import numpy as np
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

SEED = 42
random.seed(SEED); np.random.seed(SEED)
env = OpenAIGymWrapper(agent_name='blue_agent_0',
                       env=FixedFlatWrapper(CybORG(DroneSwarmScenarioGenerator(), 'sim')))
env.action_space.seed(SEED)
PARTIES, TOURS = 40, 25

resultats = []
for a in range(env.action_space.n):
    scores = []
    for _ in range(PARTIES):
        env.reset(); total = 0
        for _ in range(TOURS):
            _, r, fini, _ = env.step(a)
            total += r
            if fini: break
        scores.append(total)
    m = statistics.mean(scores)
    resultats.append((a, m, scores))
    print(f"Action {a:2d}/55 : moyenne sur {PARTIES} parties = {m:8.1f}")

with open('resultats_56_actions_40parties.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['action', 'moyenne'] + [f'partie_{i+1}' for i in range(PARTIES)])
    for a, m, scores in resultats:
        w.writerow([a, round(m, 1)] + scores)

classement = sorted(resultats, key=lambda x: x[1], reverse=True)
print(f"\n=== Classement final ({PARTIES} parties/action, seed {SEED}) ===")
for a, m, _ in classement[:5]:
    print(f"  action #{a:2d} : {m:.1f}")
print(f"  ... pire : #{classement[-1][0]} : {classement[-1][1]:.1f}")
print("\nCSV ecrit : resultats_56_actions_40parties.csv (a copier dans preuves/02_resultats_bruts/)")
