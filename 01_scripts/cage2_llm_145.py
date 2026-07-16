# CAGE 2 - agent LLM (llama3.2:3b), ESPACE D'ACTION COMPLET : les 145 actions.
#
# UN SEUL FACTEUR CHANGE par rapport a cage2_llm_1000.py : le filtre MENU est retire.
# Le LLM voit maintenant les 145 actions (leurres compris), comme le hasard et le PPO.
# Tout le reste est identique au byte pres : meme modele, meme temperature 0, meme
# traduction de l'etat, meme consigne, meme format ACTION=<n>, memes graines 1-1000,
# meme attaquant B_line, memes 30 tours.
#
# Pourquoi : dans la campagne publiee, le LLM choisissait parmi 41 actions quand le
# hasard et le PPO en avaient 145. C'est la seule asymetrie du dispositif sur CAGE 2
# (sur DroneSwarm le LLM joue deja les 56 actions). Cette campagne la mesure au lieu
# de l'argumenter, et permet d'inclure le LLM dans la decomposition de variance.
#
# A surveiller : PAS le taux d'invalides. La fenetre d'acceptation de lire_action est
# 0 <= idx < len(MENU) : en passant de 41 a 145 elle s'ELARGIT, donc les invalides ne
# peuvent que baisser. La vraie question est : QUE joue-t-il ? Utilise-t-il les 104
# actions de leurre qu'on vient de lui rendre ? D'ou le journal des actions ci-dessous.
#
# Le journal des actions est de la pure observation : il n'entre dans aucune decision,
# il ne change aucun facteur. Il ajoute une colonne au CSV et un compteur a l'ecran.
#
# REPREND automatiquement (lit le CSV). A copier dans ~/cage-challenge-2/CybORG/ puis :
#   caffeinate -i python cage2_llm_145.py
import inspect, re, os, csv, time, random
import numpy as np
import ollama
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

MODELE = 'llama3.2:3b'
PARTIES, TOURS = 1000, 30
CSV = 'cage2_llm_145_final.csv'   # NE PAS reutiliser le CSV du v1 : la reprise sauterait tout
PATH = str(inspect.getfile(CybORG))[:-10] + '/Shared/Scenarios/Scenario2.yaml'

# --- construire le menu lisible (une fois) : nom -> index reel ---
_c = CybORG(PATH, 'sim', agents={'Red': B_lineAgent})
_e = ChallengeWrapper(env=_c, agent_name='Blue'); _e.reset()
_w = _e.env
while _w is not None and not hasattr(_w, 'possible_actions'):
    _w = getattr(_w, 'env', None)
NOMS = [str(a) for a in _w.possible_actions]           # 145 noms
# LE SEUL CHANGEMENT DU SCRIPT : aucun filtre. Les 145 actions, leurres compris.
MENU = [(i, n) for i, n in enumerate(NOMS)]
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
    jouees = []                      # journal des actions : pure observation, ne change rien
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
        jouees.append(NOMS[a])
        obs, r, done, _ = env.step(a); total += r
        if done: break
    return round(total, 2), invalides, jouees

# --- reprise ---
faites = set()
if os.path.exists(CSV):
    with open(CSV) as f:
        for row in csv.DictReader(f): faites.add(int(row['graine']))
    print(f">>> reprise : {len(faites)} parties deja faites.", flush=True)

nouveau = not os.path.exists(CSV)
with open(CSV, 'a', newline='') as f:
    w = csv.writer(f)
    if nouveau: w.writerow(['graine', 'score', 'invalides', 'actions'])
    debut = time.time()
    for graine in range(1, PARTIES + 1):
        if graine in faites: continue
        score, invalides, jouees = une_partie(graine)
        w.writerow([graine, score, invalides, '|'.join(jouees)]); f.flush()
        leurres = sum(1 for x in jouees if x.startswith('Decoy'))
        print(f"partie {graine:3d}/{PARTIES} : {score:8.2f}  ({invalides} inval | {leurres}/{len(jouees)} leurres | {(time.time()-debut)/60:.0f} min)", flush=True)

import statistics
scores = []
with open(CSV) as f:
    for row in csv.DictReader(f): scores.append(float(row['score']))
print(f"\n=== LLM sur CAGE 2 ({len(scores)} parties, 30 tours) ===")
print(f"Moyenne : {statistics.mean(scores):.2f} | min {min(scores)} | max {max(scores)}")
print(f"CSV : {CSV}")
