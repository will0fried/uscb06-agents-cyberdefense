# Campagne LLM de NUIT - protocole v2 : 1000 parties de 30 tours, graines 1-1000.
# Le LLM n'etant PAS deterministe (controle 2), chaque graine est jouee 1 fois ici
# (la variabilite interne du LLM s'ajoute a celle du monde : on l'assume et on le note).
# REPREND automatiquement la ou il s'est arrete (lit le CSV existant).
# A copier dans ~/CybORG puis lancer :  caffeinate -i python serie_llm_nuit.py
import re, os, csv, time, random
import numpy as np
import ollama
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

MODELE = 'llama3.2:3b'
PARTIES, TOURS = 1000, 30
CSV = 'drones_llm_final.csv'

def resume_etat(cyborg, ips):
    obs = cyborg.get_observation('blue_agent_0')
    lignes = [f"Resultat de ma derniere action : {obs.get('success')}"]
    for nom, d in obs.items():
        if not nom.startswith('drone'): continue
        infos, ip = [], None
        for iface in d.get('Interface', []):
            if iface.get('IP Address'): ip = str(iface['IP Address'])
            if iface.get('blocked_ips'): infos.append(f"bloque {len(iface['blocked_ips'])} IP")
            if iface.get('NetworkConnections'): infos.append(f"{len(iface['NetworkConnections'])} connexions")
        k = ips.index(ip) if ip in ips else None
        lignes.append(f"- {nom}{' (k=%d)'%k if k is not None else ''} : " + (", ".join(infos) if infos else "rien"))
    return "\n".join(lignes)

def lire_action(texte):
    m = re.search(r'ACTION\s*=\s*(\d+)\s*\+\s*(\d+)', texte)
    if m: a = int(m.group(1)) + int(m.group(2))
    elif (m := re.search(r'ACTION\s*=\s*(\d+)', texte)): a = int(m.group(1))
    elif (m := re.search(r'(\d+)\s*\+\s*(\d+)', texte)): a = int(m.group(1)) + int(m.group(2))
    else:
        n = re.findall(r'\d+', texte); a = int(n[-1]) if n else None
    return a if (a is not None and 0 <= a <= 55) else None

def une_partie(graine):
    random.seed(graine); np.random.seed(graine)
    cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim', seed=graine)
    env = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
    env.action_space.seed(graine); env.reset()
    ips = [str(a.ip_address) for a in env.possible_actions[:18]]
    total, invalides = 0, 0
    for tour in range(TOURS):
        prompt = f"""Agent de cyberdefense, essaim de 18 drones (k=0-17). Tour {tour+1}/{TOURS}.
SITUATION :
{resume_etat(cyborg, ips)}
ACTIONS : k=reprendre drone k | 18=nettoyer mon drone | 19+k=bloquer k | 37+k=debloquer k | 55=rien
Termine par : ACTION=<0-55>"""
        rep = ollama.chat(model=MODELE, messages=[{'role':'user','content':prompt}], options={'temperature':0})
        a = lire_action(rep['message']['content'].strip())
        if a is None: a = 55; invalides += 1
        _, r, fini, _ = env.step(a); total += r
        if fini: break
    return total, invalides

# --- reprise : quelles graines sont deja faites ? ---
faites = set()
if os.path.exists(CSV):
    with open(CSV) as f:
        for row in csv.DictReader(f):
            faites.add(int(row['graine']))
    print(f">>> reprise : {len(faites)} parties deja faites, on continue.", flush=True)

nouveau = not os.path.exists(CSV)
with open(CSV, 'a', newline='') as f:
    w = csv.writer(f)
    if nouveau:
        w.writerow(['graine', 'score', 'invalides'])
    debut = time.time()
    for graine in range(1, PARTIES + 1):
        if graine in faites:
            continue
        score, invalides = une_partie(graine)
        w.writerow([graine, score, invalides]); f.flush()   # sauvegarde APRES CHAQUE partie
        ecoule = (time.time() - debut) / 60
        print(f"partie {graine:3d}/{PARTIES} : {score:7.1f}  ({invalides} invalides | {ecoule:.0f} min)", flush=True)

# --- bilan final ---
scores = []
with open(CSV) as f:
    for row in csv.DictReader(f):
        scores.append(float(row['score']))
import statistics
print(f"\n=== AGENT LLM ({MODELE}, {len(scores)} parties, 30 tours, graines 1-1000) ===")
print(f"Moyenne : {statistics.mean(scores):.1f}")
print(f"Meilleure : {max(scores):.1f} | Pire : {min(scores):.1f}")
print(f"CSV : {CSV}")
