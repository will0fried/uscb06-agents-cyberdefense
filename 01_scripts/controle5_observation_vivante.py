# DroneSwarm - Controle 5 : que voit reellement l'agent, et le reseau y reagit-il ?
#
# D'ou vient la question : le controle 4 montre que les 3 PPO jouent une action constante
# (900/900 decisions, 30/30 parties). Deux lectures possibles, et elles ne disent pas du
# tout la meme chose :
#   (A) l'observation evolue, et le reseau sort quand meme toujours la meme action
#       -> la politique ignore l'etat. Resultat sur l'apprentissage.
#   (B) l'observation n'evolue pas
#       -> il n'y a rien a lire. Une politique constante est alors la seule possible,
#          et le constat porte sur l'OBSERVATION livree par le wrapper, pas sur l'agent.
#
# ATTENTION AU PIEGE (une premiere version de ce script y est tombee) : comparer la
# reponse du reseau au tour 1 et au tour 30 ne prouve rien si ces deux observations sont
# quasi identiques. Il faut le tester sur des observations REELLEMENT differentes, donc
# issues de parties differentes.
#
# A copier dans ~/CybORG puis : python controle5_observation_vivante.py
# Duree : moins d'une minute. Ne produit pas de CSV, juste un constat a l'ecran.

import inspect, random
import numpy as np
import torch
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

print('CONDITIONS - CybORG:', inspect.getfile(CybORG), flush=True)

MODELES = ['ppo_droneswarm', 'ppo_droneswarm_g43_t25', 'ppo_droneswarm_g44_t25']

def obs_partie(graine, tours=30):
    """Rejoue une partie au hasard et renvoie la suite des observations."""
    random.seed(graine); np.random.seed(graine)
    cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim', seed=graine)
    env = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
    env.action_space.seed(graine)
    obs = env.reset()
    suite = [np.asarray(obs, dtype=np.float32).flatten()]
    for _ in range(tours):
        obs, r, fini, _ = env.step(env.action_space.sample())
        suite.append(np.asarray(obs, dtype=np.float32).flatten())
        if fini: break
    return np.array(suite)

# ---------------------------------------------------------------- 1. dans une partie
print("\n=== 1. L'observation evolue-t-elle PENDANT une partie ? ===")
O = obs_partie(1)
varie = (O.std(axis=0) > 0).sum()
distincts = len({o.tobytes() for o in O})
print(f"  {O.shape[0]} observations de {O.shape[1]} valeurs (graine 1)")
print(f"  dimensions qui varient au cours de la partie : {varie} / {O.shape[1]}"
      f"  ({100*varie/O.shape[1]:.2f} %)")
print(f"  vecteurs d'observation distincts             : {distincts} / {O.shape[0]}")

# ---------------------------------------------------------------- 2. entre parties
print("\n=== 2. L'observation change-t-elle d'une partie a l'autre ? ===")
GRAINES = list(range(1, 31))
depart = np.array([obs_partie(g, tours=0)[0] for g in GRAINES])   # etat initial de 30 parties
d_init = len({o.tobytes() for o in depart})
varie_p = (depart.std(axis=0) > 0).sum()
print(f"  etats initiaux distincts sur {len(GRAINES)} parties : {d_init} / {len(GRAINES)}")
print(f"  dimensions qui varient d'une partie a l'autre : {varie_p} / {depart.shape[1]}"
      f"  ({100*varie_p/depart.shape[1]:.2f} %)")

# ---------------------------------------------------------------- 3. le vrai test
print("\n=== 3. Le reseau reagit-il a des observations VRAIMENT differentes ? ===")
print("  On lui soumet les etats initiaux de 30 parties differentes (pas 2 tours voisins).")
for nom in MODELES:
    try:
        m = PPO.load(nom)
    except FileNotFoundError:
        print(f"\n  --- {nom} : absent, ignore."); continue
    with torch.no_grad():
        p = m.policy.get_distribution(torch.as_tensor(depart)).distribution.probs.numpy()
    argmax = p.argmax(axis=1)
    ecart_max = float(np.abs(p - p[0]).sum(axis=1).max())   # distance L1 max a la 1re distribution
    ent = float(-(p[0] * np.log(p[0] + 1e-12)).sum())
    print(f"\n  --- {nom}")
    print(f"    actions choisies sur les {len(depart)} parties : {sorted(set(argmax.tolist()))}")
    print(f"    proba de l'action choisie : de {p.max(axis=1).min():.4f} a {p.max(axis=1).max():.4f}")
    print(f"    ecart L1 MAXIMUM entre deux distributions : {ecart_max:.6f}")
    print(f"    entropie de la politique : {ent:.4f}  (maximum possible : {np.log(p.shape[1]):.4f})")

print("""
  Lecture.
  Point 1 : si tres peu de dimensions varient et si les vecteurs distincts se comptent
  sur les doigts, l'observation est quasi figee PENDANT la partie : l'agent ne percoit
  pas l'attaque se derouler. Une politique constante devient alors la seule possible,
  et c'est un constat sur l'observation, pas sur l'agent.
  Point 3 : c'est le test qui tranche. Si l'ecart L1 maximum entre distributions reste
  proche de 0 alors que les 30 parties sont bien differentes (point 2), la politique
  ignore l'etat. S'il est grand, le reseau reagit bien a ce qu'il voit, et la constance
  du controle 4 vient de ce que les etats se ressemblent trop, pas du reseau.
  Rappel utile : stable-baselines3 met ent_coef = 0.0 par defaut, donc aucun bonus
  d'entropie ne s'oppose a ce que la politique se fige.
""")
