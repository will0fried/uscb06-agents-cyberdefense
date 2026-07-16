# CAGE 2 - E1 : le LLM face a un adversaire qu'il n'a jamais vu (llama3.2:3b).
# Copie conforme de cage2_llm_1000.py. UNE SEULE chose change : l'attaquant.
# B_lineAgent (chemin fixe) -> RedMeanderAgent (exploration aleatoire).
# Le prompt, le menu, la temperature et les graines sont identiques : sinon la comparaison
# B_line vs Meander ne voudrait rien dire.
#
# Complete le tableau E1 : les 4 autres strategies sont deja mesurees contre Meander
# (cage2_campagne_meander.py), il manquait le LLM. C'est aussi la piste 2 de Clement :
# evaluer la generalisation du LLM quand l'environnement change.
#
# REPREND automatiquement (relit le CSV) : si ca coupe, on relance et ca continue.
# A copier dans ~/cage-challenge-2/CybORG/ puis :
#   caffeinate -i python cage2_llm_meander.py
# Duree : longue (30 000 appels a Ollama). Peut tourner plusieurs nuits.
import inspect, re, os, csv, time, random
import numpy as np
import ollama
from CybORG import CybORG
from CybORG.Agents import RedMeanderAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

MODELE = 'llama3.2:3b'
PARTIES, TOURS = 1000, 30
ADVERSAIRE = RedMeanderAgent          # la seule difference avec cage2_llm_1000.py
CSV = 'cage2_llm_meander.csv'
PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'
print('CONDITIONS - CybORG:', inspect.getfile(CybORG))
print('adversaire:', ADVERSAIRE.__name__, '| modele:', MODELE, flush=True)

# --- construire le menu lisible (une fois) : nom -> index reel ---
_c = CybORG(PATH, 'sim', agents={'Red': ADVERSAIRE})
_e = ChallengeWrapper(env=_c, agent_name='Blue'); _e.reset()
_w = _e.env
while _w is not None and not hasattr(_w, 'possible_actions'):
    _w = getattr(_w, 'env', None)
NOMS = [str(a) for a in _w.possible_actions]           # 145 noms
MENU = [(i, n) for i, n in enumerate(NOMS)
        if n in ('Sleep', 'Monitor') or n.startswith(('Analyse', 'Remove', 'Restore'))]
HOTES = [n.split(' ', 1)[1] for i, n in enumerate(NOMS) if n.startswith('Analyse')]  # 13 serveurs

def etat_lisible(obs):
    """52 bits = 13 serveurs x 4 bits (2 activite + 2 compromission)."""
    lignes = []
    for k, hote in enumerate(HOTES):
        b = obs[k*4:k*4+4]
        activite = "activite suspecte" if (b[0] or b[1]) else "RAS"
        compromis = "COMPROMIS" if (b[2] or b[3]) else "sain"
        if activite != "RAS" or compromis != "sain":
            lignes.append(f"- {hote} : {activite}, {compromis}")
    return "\n".join(lignes) if lignes else "- tout le reseau parait sain"

def lire_action(texte):
    m = re.search(r'ACTION\s*=\s*(\d+)', texte)
    if m:
        idx = int(m.group(1))
        if 0 <= idx < len(MENU):
            return MENU[idx][0]     # index du menu -> index reel
    n = re.findall(r'\d+', texte)
    if n and 0 <= int(n[-1]) < len(MENU):
        return MENU[int(n[-1])][0]
    return None

MENU_TXT = "\n".join(f"{j} = {nom}" for j, (i, nom) in enumerate(MENU))

def une_partie(graine):
    random.seed(graine); np.random.seed(graine)
    env = ChallengeWrapper(env=CybORG(PATH, 'sim', agents={'Red': ADVERSAIRE}), agent_name='Blue')
    env.action_space.seed(graine)
    obs = env.reset()
    total, invalides = 0, 0
    for tour in range(TOURS):
        # prompt STRICTEMENT identique a celui de cage2_llm_1000.py
        prompt = f"""Tu es un agent de cyberdefense d'un reseau d'entreprise. Tour {tour+1}/{TOURS}.
ETAT DES SERVEURS :
{etat_lisible(obs)}

ACTIONS POSSIBLES (reponds par le numero) :
{MENU_TXT}

Analyse un serveur suspect, restaure (Restore) un serveur compromis, ou Monitor si tout va bien.
Termine par : ACTION=<numero>"""
        rep = ollama.chat(model=MODELE, messages=[{'role':'user','content':prompt}], options={'temperature':0})
        a = lire_action(rep['message']['content'].strip())
        if a is None: a = 1; invalides += 1     # defaut : Monitor
        obs, r, done, _ = env.step(a); total += r
        if done: break
    return round(total, 2), invalides

# --- reprise ---
faites = set()
if os.path.exists(CSV):
    with open(CSV) as f:
        for row in csv.DictReader(f): faites.add(int(row['graine']))
    print(f">>> reprise : {len(faites)} parties deja faites.", flush=True)

nouveau = not os.path.exists(CSV)
with open(CSV, 'a', newline='') as f:
    w = csv.writer(f)
    if nouveau: w.writerow(['graine', 'score', 'invalides'])
    debut = time.time()
    for graine in range(1, PARTIES + 1):
        if graine in faites: continue
        score, invalides = une_partie(graine)
        w.writerow([graine, score, invalides]); f.flush()
        print(f"partie {graine:4d}/{PARTIES} : {score:8.2f}  ({invalides} inval | {(time.time()-debut)/60:.0f} min)", flush=True)

import statistics, math
scores = []
with open(CSV) as f:
    for row in csv.DictReader(f): scores.append(float(row['score']))
m = statistics.mean(scores)
ic = 1.96 * statistics.stdev(scores) / math.sqrt(len(scores)) if len(scores) > 1 else 0
print(f"\n=== LLM sur CAGE 2 contre Meander ({len(scores)} parties, 30 tours) ===")
print(f"Moyenne : {m:.2f}  IC 95% [{m-ic:.2f} ; {m+ic:.2f}]  | min {min(scores)} | max {max(scores)}")
print(f"Rappel contre B_line : -188,42  IC 95% [-191,79 ; -185,05]")
print(f"Rappel Meander : hasard -34,60 | RL -8,79 | regle -12,26 | fixe -55,99")
print(f"CSV : {CSV}")
