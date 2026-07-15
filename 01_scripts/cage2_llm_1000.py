# CAGE 2 - agent LLM (llama3.2:3b), 1000 parties de 30 tours, graines 1-1000, attaquant B_line.
# Etat des 13 serveurs traduit en clair ; menu restreint aux actions utiles (Sleep/Monitor/
# Analyse/Remove/Restore par serveur ; leurres exclus, note dans le memoire).
# REPREND automatiquement (lit le CSV). A copier dans ~/cage-challenge-2/CybORG/ puis :
#   caffeinate -i python cage2_llm_nuit.py
import inspect, re, os, csv, time, random
import numpy as np
import ollama
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

MODELE = 'llama3.2:3b'
PARTIES, TOURS = 1000, 30
CSV = 'cage2_llm_final.csv'
PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'

# --- construire le menu lisible (une fois) : nom -> index reel ---
_c = CybORG(PATH, 'sim', agents={'Red': B_lineAgent})
_e = ChallengeWrapper(env=_c, agent_name='Blue'); _e.reset()
_w = _e.env
while _w is not None and not hasattr(_w, 'possible_actions'):
    _w = getattr(_w, 'env', None)
NOMS = [str(a) for a in _w.possible_actions]           # 145 noms
# menu = Sleep, Monitor, + Analyse/Remove/Restore par serveur (pas les Decoy)
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
    env = ChallengeWrapper(env=CybORG(PATH, 'sim', agents={'Red': B_lineAgent}), agent_name='Blue')
    env.action_space.seed(graine)
    obs = env.reset()
    total, invalides = 0, 0
    for tour in range(TOURS):
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
        print(f"partie {graine:3d}/{PARTIES} : {score:8.2f}  ({invalides} inval | {(time.time()-debut)/60:.0f} min)", flush=True)

import statistics
scores = []
with open(CSV) as f:
    for row in csv.DictReader(f): scores.append(float(row['score']))
print(f"\n=== LLM sur CAGE 2 ({len(scores)} parties, 30 tours) ===")
print(f"Moyenne : {statistics.mean(scores):.2f} | min {min(scores)} | max {max(scores)}")
print(f"CSV : {CSV}")
