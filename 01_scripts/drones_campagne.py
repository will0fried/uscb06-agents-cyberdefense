# DroneSwarm - campagne finale : hasard, action fixe (#12), regle reactive et RL (PPO),
# 1000 parties de 30 tours, graines 1-1000 appariees, attaquant pilote par le simulateur.
# A copier dans ~/CybORG puis : caffeinate -i python drones_campagne.py
# Produit : drones_hasard_final.csv, drones_actionfixe_final.csv, drones_regle_final.csv, drones_rl_final.csv
import inspect, csv, statistics, random, time, sys
import numpy as np
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

PARTIES, TOURS = 1000, 30
FIXE = 12
print('CONDITIONS - CybORG:', inspect.getfile(CybORG))
print('numpy', np.__version__, '| python', sys.version.split()[0], flush=True)
modele = PPO.load("ppo_droneswarm")

def regle(cyborg):
    obs = cyborg.get_observation('blue_agent_0')
    return 0 if str(obs.get('success')) == 'FALSE' else 55

def joue(nom, fic):
    sc, t0 = [], time.time()
    for g in range(1, PARTIES+1):
        random.seed(g); np.random.seed(g)
        cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim', seed=g)
        env = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
        env.action_space.seed(g)
        obs = env.reset(); total = 0
        for _ in range(TOURS):
            if   nom=='hasard': a = env.action_space.sample()
            elif nom=='fixe':   a = FIXE
            elif nom=='regle':  a = regle(cyborg)
            else:
                o = np.asarray(obs, dtype=np.float32).flatten()
                a,_ = modele.predict(o, deterministic=True); a = int(a)
            obs, r, fini, _ = env.step(int(a)); total += r
            if fini: break
        sc.append(round(total,2))
        if g % 200 == 0: print(f'  {nom}: {g}/{PARTIES}, {time.time()-t0:.0f}s', flush=True)
    with open(fic,'w',newline='') as f:
        w=csv.writer(f); w.writerow(['graine','score'])
        for i,s in enumerate(sc,1): w.writerow([i,s])
    print(f'FINI {fic} : moyenne {statistics.mean(sc):.2f} (n={len(sc)}) en {time.time()-t0:.0f}s', flush=True)

for nom,fic in [('hasard','drones_hasard_final.csv'),('fixe','drones_actionfixe_final.csv'),
                ('regle','drones_regle_final.csv'),('rl','drones_rl_final.csv')]:
    print(f'--- {nom} ---', flush=True); joue(nom,fic)
print('=== CAMPAGNE DRONES TERMINEE ===', flush=True)
