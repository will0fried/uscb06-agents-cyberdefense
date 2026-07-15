# CAGE 2 - campagne finale : hasard, action fixe (#135 Restore Enterprise2), regle reactive
# et RL (PPO), 1000 parties de 30 tours, graines 1-1000 appariees, attaquant B_line.
# A copier dans ~/cage-challenge-2/CybORG/ puis : caffeinate -i python cage2_campagne.py
# Produit : cage2_hasard_final.csv, cage2_actionfixe_final.csv, cage2_regle_final.csv, cage2_rl_final.csv
import inspect, csv, statistics, random, time, sys
import numpy as np
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

PARTIES, TOURS = 1000, 30
PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'
print('CONDITIONS - CybORG:', inspect.getfile(CybORG))
print('numpy', np.__version__, '| python', sys.version.split()[0], flush=True)

_e = ChallengeWrapper(env=CybORG(PATH,'sim',agents={'Red':B_lineAgent}), agent_name='Blue'); _e.reset()
_w = _e.env
while _w is not None and not hasattr(_w,'possible_actions'):
    _w = getattr(_w,'env',None)
NOMS = [str(a) for a in _w.possible_actions]
HOTES = [n.split(' ',1)[1] for n in NOMS if n.startswith('Analyse')]
IDX = {n:i for i,n in enumerate(NOMS)}
MONITOR = IDX.get('Monitor',1)
FIXE = IDX.get('Restore Enterprise2', MONITOR)
print('Action fixe =', FIXE, '->', NOMS[FIXE], flush=True)
modele = PPO.load("ppo_cage2")

def ma_regle(obs):
    comp, susp = [], []
    for k,h in enumerate(HOTES):
        b = obs[k*4:k*4+4]
        if b[2] or b[3]: comp.append(h)
        elif b[0] or b[1]: susp.append(h)
    if comp: return IDX.get(f'Restore {comp[0]}', MONITOR)
    if susp: return IDX.get(f'Analyse {susp[0]}', MONITOR)
    return MONITOR

def politique(nom, obs, env):
    if nom=='hasard': return env.action_space.sample()
    if nom=='fixe':   return FIXE
    if nom=='regle':  return ma_regle(obs)
    a,_ = modele.predict(np.asarray(obs,dtype=np.float32), deterministic=True); return int(a)

def joue(nom, fic):
    sc, t0 = [], time.time()
    for g in range(1, PARTIES+1):
        random.seed(g); np.random.seed(g)
        env = ChallengeWrapper(env=CybORG(PATH,'sim',agents={'Red':B_lineAgent}), agent_name='Blue')
        env.action_space.seed(g); obs = env.reset(); total = 0
        for _ in range(TOURS):
            obs, r, done, _ = env.step(politique(nom, obs, env)); total += r
            if done: break
        sc.append(round(total,2))
        if g % 200 == 0: print(f'  {nom}: {g}/{PARTIES}, {time.time()-t0:.0f}s', flush=True)
    with open(fic,'w',newline='') as f:
        w = csv.writer(f); w.writerow(['graine','score'])
        for i,s in enumerate(sc,1): w.writerow([i,s])
    print(f'FINI {fic} : moyenne {statistics.mean(sc):.2f} (n={len(sc)}) en {time.time()-t0:.0f}s', flush=True)

for nom, fic in [('hasard','cage2_hasard_final.csv'),('fixe','cage2_actionfixe_final.csv'),
                 ('regle','cage2_regle_final.csv'),('rl','cage2_rl_final.csv')]:
    print(f'--- {nom} ---', flush=True); joue(nom, fic)
print('=== CAMPAGNE TERMINEE ===', flush=True)
