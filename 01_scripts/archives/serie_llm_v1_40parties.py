# Serie officielle LLM - prompt v1 (sans conseils), 40 parties de 25 tours.
# A copier dans ~/CybORG puis lancer :  python serie_llm_v1_40parties.py
# Duree estimee : ~1h15 (laisser tourner, ex. pendant le dejeuner).
import re, time, csv, statistics
import ollama
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

MODELE = 'llama3.2:3b'
PARTIES, TOURS = 40, 25
VERSION_PROMPT = 'v1_40parties'

cyborg = CybORG(DroneSwarmScenarioGenerator(), 'sim')
env = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
env.reset()
ips = [str(a.ip_address) for a in env.possible_actions[:18]]

def resume_etat():
    obs = cyborg.get_observation('blue_agent_0')
    lignes = [f"Resultat de ma derniere action : {obs.get('success')}"]
    for nom, d in obs.items():
        if not nom.startswith('drone'):
            continue
        infos, ip = [], None
        for iface in d.get('Interface', []):
            if iface.get('IP Address'):
                ip = str(iface['IP Address'])
            if iface.get('blocked_ips'):
                infos.append(f"bloque {len(iface['blocked_ips'])} IP")
            if iface.get('NetworkConnections'):
                infos.append(f"{len(iface['NetworkConnections'])} connexions reseau")
        k = ips.index(ip) if ip in ips else None
        nom_k = f"{nom} (numero k={k})" if k is not None else nom
        lignes.append(f"- {nom_k} : " + (", ".join(infos) if infos else "rien a signaler"))
    return "\n".join(lignes)

def lire_action(texte):
    m = re.search(r'ACTION\s*=\s*(\d+)\s*\+\s*(\d+)', texte)
    if m:
        action = int(m.group(1)) + int(m.group(2))
    elif (m := re.search(r'ACTION\s*=\s*(\d+)', texte)):
        action = int(m.group(1))
    elif (m := re.search(r'(\d+)\s*\+\s*(\d+)', texte)):
        action = int(m.group(1)) + int(m.group(2))
    else:
        nombres = re.findall(r'\d+', texte)
        action = int(nombres[-1]) if nombres else None
    if action is not None and not (0 <= action <= 55):
        action = None
    return action

def demander_au_llm(resume, tour):
    prompt = f"""Tu es un agent de cyberdefense. Tu proteges un essaim de 18 drones (numeros k = 0 a 17) contre un ver qui se propage de drone en drone. Tour {tour} sur 25.

SITUATION (je ne vois que mes voisins radio) :
{resume}

ACTIONS POSSIBLES :
- k (0 a 17) : reprendre le controle du drone k (echoue 1 fois sur 4)
- 18 : nettoyer mon propre drone
- 19+k : bloquer le trafic venant du drone k
- 37+k : reautoriser le trafic du drone k
- 55 : ne rien faire

Termine ta reponse par exactement : ACTION=<nombre entre 0 et 55>"""
    rep = ollama.chat(model=MODELE,
                      messages=[{'role': 'user', 'content': prompt}],
                      options={'temperature': 0})
    return lire_action(rep['message']['content'].strip())

scores, invalides_total = [], 0
debut_serie = time.time()
for partie in range(1, PARTIES + 1):
    env.reset()
    total = 0
    for tour in range(1, TOURS + 1):
        action = demander_au_llm(resume_etat(), tour)
        if action is None:
            invalides_total += 1
            action = 55
        _, r, fini, _ = env.step(action)
        total += r
        if fini:
            break
    scores.append(total)
    print(f"Partie {partie:2d}/{PARTIES} : {total:7.1f}   (moyenne provisoire : {statistics.mean(scores):7.1f} | {(time.time()-debut_serie)/60:.0f} min)")

nom_csv = f"resultats_llm_{VERSION_PROMPT}.csv"
with open(nom_csv, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['partie', 'score', 'modele', MODELE, 'prompt', VERSION_PROMPT, 'temperature', 0])
    for i, s in enumerate(scores, 1):
        w.writerow([i, s])

print(f"\n=== AGENT LLM ({MODELE}, prompt {VERSION_PROMPT}, temperature 0) ===")
print(f"Moyenne sur {PARTIES} parties : {statistics.mean(scores):.1f}")
print(f"Meilleure : {max(scores):.1f} | Pire : {min(scores):.1f}")
print(f"Reponses invalides : {invalides_total}")
print(f"CSV ecrit : {nom_csv} (a copier dans preuves/02_resultats_bruts/)")
