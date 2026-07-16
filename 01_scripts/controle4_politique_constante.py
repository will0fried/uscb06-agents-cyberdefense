# DroneSwarm - Controle 4 : le PPO a-t-il appris a appuyer toujours sur le meme bouton ?
#
# D'ou vient la question : en comparant les CSV deja produits (1000 parties appariees), le
# PPO publie tombe sur exactement le meme score que l'action fixe dans 12,0 % des cas, et
# que le PPO de la graine 43 dans 9,9 % des cas. Alors qu'entre strategies etrangeres (PPO
# vs regle, PPO vs hasard, regle vs hasard) le taux de scores identiques n'est que de 0,7 a
# 1,7 %. Soupcon : la politique apprise serait quasi constante.
#
# Un score identique ne prouve pas des actions identiques. Ce script regarde les actions.
# Il ne rejoue PAS la campagne : 30 parties suffisent a voir une politique constante.
#
# A copier dans ~/CybORG puis : python controle4_politique_constante.py
# Duree : environ une minute. Ne produit pas de CSV, juste un constat a l'ecran.

import inspect, random
from collections import Counter
import numpy as np
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

print('CONDITIONS - CybORG:', inspect.getfile(CybORG), flush=True)

PARTIES, TOURS = 30, 30       # 30 parties suffisent pour voir une politique constante
MODELES = ['ppo_droneswarm', 'ppo_droneswarm_g43_t25', 'ppo_droneswarm_g44_t25']

def actions_jouees(nom_modele):
    modele = PPO.load(nom_modele)
    toutes, par_partie = [], []
    for g in range(1, PARTIES + 1):
        random.seed(g); np.random.seed(g)
        cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim', seed=g)
        env = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
        env.action_space.seed(g)
        obs = env.reset()
        actions = []
        for _ in range(TOURS):
            o = np.asarray(obs, dtype=np.float32).flatten()
            a, _ = modele.predict(o, deterministic=True)
            actions.append(int(a))
            obs, r, fini, _ = env.step(int(a))
            if fini: break
        toutes.extend(actions)
        par_partie.append(actions)
    return toutes, par_partie

for nom in MODELES:
    try:
        toutes, par_partie = actions_jouees(nom)
    except FileNotFoundError:
        print(f"\n{nom} : fichier absent, ignore.")
        continue
    c = Counter(toutes)
    top, n_top = c.most_common(1)[0]
    # une partie est dite "constante" si le modele y joue toujours la meme action
    constantes = sum(1 for p in par_partie if len(set(p)) == 1)
    print(f"\n=== {nom} ===")
    print(f"  {len(toutes)} decisions sur {PARTIES} parties")
    print(f"  actions differentes utilisees : {len(c)} sur 56 possibles")
    print(f"  action la plus jouee : #{top}, {n_top}/{len(toutes)} fois ({100*n_top/len(toutes):.1f} %)")
    print(f"  parties ou il joue TOUJOURS la meme action : {constantes}/{PARTIES}")
    print(f"  les 5 actions les plus jouees : {c.most_common(5)}")

print("""
  Lecture. Si une seule action represente l'essentiel des decisions, ou si le modele
  joue toujours la meme action d'un bout a l'autre des parties, alors la politique
  apprise est constante : le PPO n'a pas appris a defendre, il a appris a appuyer sur
  un bouton. Cela expliquerait le +0,04 d'ecart avec l'action fixe (-194,35 contre
  -194,38) et les 12 % de scores identiques.
  Si au contraire les actions sont variees et dependent de l'etat, l'hypothese tombe :
  le PPO reagit bien a ce qu'il voit, mais cela ne lui rapporte rien sur ce terrain.
  Les deux resultats sont interessants, et ils ne disent pas la meme chose.
""")
