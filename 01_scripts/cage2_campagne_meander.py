# CAGE 2 - E1 : la hierarchie survit-elle a un changement d'adversaire ?
# Copie conforme de cage2_campagne.py. UNE SEULE chose change : l'attaquant.
# B_lineAgent (chemin fixe) -> RedMeanderAgent (exploration aleatoire).
#
# Le point important : on NE reentraine PAS le PPO. Il a appris contre B_line et on le
# confronte a un adversaire qu'il n'a jamais vu. C'est un test de generalisation.
# L'action fixe reste #135 (Restore Enterprise2), choisie parce qu'elle est sur le chemin
# de B_line : si elle s'effondre ici, c'est en soi un resultat.
#
# A copier dans ~/cage-challenge-2/CybORG/ puis : caffeinate -i python cage2_campagne_meander.py
# Produit : cage2_hasard_meander.csv, cage2_actionfixe_meander.csv,
#           cage2_regle_meander.csv, cage2_rl_meander.csv
import inspect, csv, statistics, random, time, sys, math
import numpy as np
from stable_baselines3 import PPO
from CybORG import CybORG
from CybORG.Agents import RedMeanderAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

PARTIES, TOURS = 1000, 30          # identique a la campagne publiee
ADVERSAIRE = RedMeanderAgent       # la seule difference avec cage2_campagne.py

PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'
print('CONDITIONS - CybORG:', inspect.getfile(CybORG))
print('adversaire:', ADVERSAIRE.__name__, '| numpy', np.__version__,
      '| python', sys.version.split()[0], flush=True)

_e = ChallengeWrapper(env=CybORG(PATH,'sim',agents={'Red':ADVERSAIRE}), agent_name='Blue'); _e.reset()
_w = _e.env
while _w is not None and not hasattr(_w,'possible_actions'):
    _w = getattr(_w,'env',None)
NOMS = [str(a) for a in _w.possible_actions]
HOTES = [n.split(' ',1)[1] for n in NOMS if n.startswith('Analyse')]
IDX = {n:i for i,n in enumerate(NOMS)}
MONITOR = IDX.get('Monitor',1)
FIXE = IDX.get('Restore Enterprise2', MONITOR)
print('Action fixe =', FIXE, '->', NOMS[FIXE], flush=True)
modele = PPO.load("ppo_cage2")     # modele entraine contre B_line, NON reentraine

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
        env = ChallengeWrapper(env=CybORG(PATH,'sim',agents={'Red':ADVERSAIRE}), agent_name='Blue')
        env.action_space.seed(g); obs = env.reset(); total = 0
        for _ in range(TOURS):
            obs, r, done, _ = env.step(politique(nom, obs, env)); total += r
            if done: break
        sc.append(round(total,2))
        if g % 200 == 0: print(f'  {nom}: {g}/{PARTIES}, {time.time()-t0:.0f}s', flush=True)
    with open(fic,'w',newline='') as f:
        w = csv.writer(f); w.writerow(['graine','score'])
        for i,s in enumerate(sc,1): w.writerow([i,s])
    m = statistics.mean(sc); ic = 1.96*statistics.stdev(sc)/math.sqrt(len(sc))
    print(f'FINI {fic} : moyenne {m:.2f}  IC 95% [{m-ic:.2f} ; {m+ic:.2f}]  (n={len(sc)})'
          f' en {time.time()-t0:.0f}s', flush=True)
    return m

resultats = {}
for nom, fic in [('hasard','cage2_hasard_meander.csv'),('fixe','cage2_actionfixe_meander.csv'),
                 ('regle','cage2_regle_meander.csv'),('rl','cage2_rl_meander.csv')]:
    print(f'--- {nom} ---', flush=True); resultats[nom] = joue(nom, fic)

print('\n=== RECAPITULATIF : B_line (publie) vs Meander (ici) ===', flush=True)
publie = {'rl': -4.70, 'regle': -14.33, 'fixe': -57.30, 'hasard': -154.71}
print(f"  {'strategie':10s} {'B_line':>10s} {'Meander':>10s} {'ecart':>10s}", flush=True)
for nom in ['rl','regle','fixe','hasard']:
    print(f'  {nom:10s} {publie[nom]:10.2f} {resultats[nom]:10.2f} {resultats[nom]-publie[nom]:+10.2f}', flush=True)
print("\n  Lecture : l'ordre RL > regle > fixe > hasard tient-il encore ? Si l'avance du RL", flush=True)
print("  se reduit ou s'inverse, c'est qu'elle etait specifique a B_line (sur-apprentissage).", flush=True)
