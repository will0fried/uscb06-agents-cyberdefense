# CAGE 2 - agent a REGLES reactives (facon AICA), 100 parties 30 tours, graines 1-100, B_line.
# Regle : serveur COMPROMIS -> Restore ce serveur ; sinon activite suspecte -> Analyse ; sinon Monitor.
# A copier dans ~/cage-challenge-2/CybORG/ puis : python cage2_regles.py
import inspect, csv, statistics, random
import numpy as np
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

PARTIES, TOURS = 100, 30
PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'

# menu lisible : nom -> index reel
_e = ChallengeWrapper(env=CybORG(PATH,'sim',agents={'Red':B_lineAgent}), agent_name='Blue'); _e.reset()
_w = _e.env
while _w is not None and not hasattr(_w, 'possible_actions'):
    _w = getattr(_w, 'env', None)
NOMS = [str(a) for a in _w.possible_actions]
HOTES = [n.split(' ',1)[1] for n in NOMS if n.startswith('Analyse')]
IDX = {n: i for i, n in enumerate(NOMS)}
MONITOR = IDX.get('Monitor', 1)

def ma_regle(obs):
    # 13 serveurs x 4 bits (2 activite, 2 compromission)
    compromis, suspects = [], []
    for k, hote in enumerate(HOTES):
        b = obs[k*4:k*4+4]
        if b[2] or b[3]: compromis.append(hote)
        elif b[0] or b[1]: suspects.append(hote)
    if compromis:
        return IDX.get(f'Restore {compromis[0]}', MONITOR)
    if suspects:
        return IDX.get(f'Analyse {suspects[0]}', MONITOR)
    return MONITOR

scores = []
for graine in range(1, PARTIES + 1):
    random.seed(graine); np.random.seed(graine)
    env = ChallengeWrapper(env=CybORG(PATH,'sim',agents={'Red':B_lineAgent}), agent_name='Blue')
    env.action_space.seed(graine)
    obs = env.reset()
    total = 0
    for _ in range(TOURS):
        obs, r, done, _ = env.step(ma_regle(obs))
        total += r
        if done: break
    scores.append(round(total, 2))

with open('cage2_regles.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['graine', 'score'])
    for g, s in enumerate(scores, 1): w.writerow([g, s])

print(f"=== MA REGLE REACTIVE sur CAGE 2 (100 parties, 30 tours) ===")
print(f"Moyenne : {statistics.mean(scores):.2f} | min {min(scores)} | max {max(scores)}")
print("CSV : cage2_regles.csv")
