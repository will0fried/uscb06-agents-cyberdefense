# analyse_profondeur.py - à lancer depuis preuves/02_resultats_bruts : python3 ../../analyse_profondeur.py
# Calcule : A) queues de distribution  B) corrélations par graine  C) décomposition de variance graine/stratégie  D) taux de parties catastrophiques
# Aucune dépendance externe (stdlib uniquement). Vérifie mes chiffres sur TA machine avant insertion dans le mémoire.
import csv, math, statistics as st

def load(path):
    with open(path) as f:
        return {int(r['graine']): float(r['score']) for r in csv.DictReader(f)}

C = {'RL': load('cage2_rl_final.csv'), 'Règle': load('cage2_regle_final.csv'),
     'ActionFixe': load('cage2_actionfixe_final.csv'), 'Hasard': load('cage2_hasard_final.csv')}
D = {'RL': load('drones_rl_final.csv'), 'Règle': load('drones_regle_final.csv'),
     'ActionFixe': load('drones_actionfixe_final.csv'), 'Hasard': load('drones_hasard_final.csv')}
CL = load('cage2_llm_final.csv'); DL = load('drones_llm_final.csv')

def pct(vals, p):
    s = sorted(vals); k = (len(s)-1)*p/100; f=int(k); c=min(f+1,len(s)-1)
    return s[f] + (s[c]-s[f])*(k-f)

print("="*70); print("A. QUEUES DE DISTRIBUTION (le pire cas compte en défense)")
for name, data in [("CAGE 2", C), ("DroneSwarm", D)]:
    print(f"\n--- {name} ---")
    print(f"{'strat':<12}{'moy':>9}{'médiane':>9}{'P5(pire5%)':>12}{'min':>9}{'max':>8}")
    for s, d in data.items():
        v = list(d.values())
        print(f"{s:<12}{st.mean(v):>9.2f}{st.median(v):>9.2f}{pct(v,5):>12.2f}{min(v):>9.1f}{max(v):>8.1f}")
llm_c = list(CL.values()); llm_d = list(DL.values())
print(f"{'LLM C2(n=100)':<12}{st.mean(llm_c):>8.2f}{st.median(llm_c):>9.2f}{pct(llm_c,5):>12.2f}{min(llm_c):>9.1f}{max(llm_c):>8.1f}")
print(f"{'LLM Dr(n=100)':<12}{st.mean(llm_d):>8.2f}{st.median(llm_d):>9.2f}{pct(llm_d,5):>12.2f}{min(llm_d):>9.1f}{max(llm_d):>8.1f}")

def pearson(a, b):
    ks = sorted(set(a) & set(b))
    xa=[a[k] for k in ks]; xb=[b[k] for k in ks]
    ma, mb = st.mean(xa), st.mean(xb)
    num = sum((x-ma)*(y-mb) for x,y in zip(xa,xb))
    den = math.sqrt(sum((x-ma)**2 for x in xa)*sum((y-mb)**2 for y in xb))
    return num/den

print("\n"+"="*70); print("B. CORRÉLATIONS PAR GRAINE (même partie difficile pour tous ?)")
for name, data in [("CAGE 2", C), ("DroneSwarm", D)]:
    keys = list(data.keys())
    print(f"\n--- {name} ---")
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            r = pearson(data[keys[i]], data[keys[j]])
            print(f"  {keys[i]:<11} vs {keys[j]:<11}: r = {r:+.3f}")

print("\n"+"="*70); print("C. DÉCOMPOSITION DE VARIANCE (graine vs stratégie, 4 stratégies n=1000)")
for name, data in [("CAGE 2", C), ("DroneSwarm", D)]:
    seeds = sorted(set.intersection(*[set(d) for d in data.values()]))
    strats = list(data.keys())
    allv = [data[s][k] for s in strats for k in seeds]
    grand = st.mean(allv)
    ss_tot = sum((x-grand)**2 for x in allv)
    ss_strat = len(seeds)*sum((st.mean([data[s][k] for k in seeds])-grand)**2 for s in strats)
    ss_seed = len(strats)*sum((st.mean([data[s][k] for s in strats])-grand)**2 for k in seeds)
    ss_res = ss_tot - ss_strat - ss_seed
    print(f"\n--- {name} (n={len(seeds)} graines x {len(strats)} stratégies) ---")
    print(f"  variance expliquée par la STRATÉGIE : {100*ss_strat/ss_tot:5.1f} %")
    print(f"  variance expliquée par la GRAINE    : {100*ss_seed/ss_tot:5.1f} %")
    print(f"  résiduel (interaction)              : {100*ss_res/ss_tot:5.1f} %")

print("\n"+"="*70); print("D. STABILITÉ : % de parties 'catastrophiques' (score < seuil)")
for name, data, thr in [("CAGE 2", C, -100), ("DroneSwarm", D, -300)]:
    print(f"\n--- {name} (seuil {thr}) ---")
    for s, d in data.items():
        v = list(d.values()); bad = sum(1 for x in v if x < thr)
        print(f"  {s:<12}: {bad:>4}/{len(v)} parties sous {thr} ({100*bad/len(v):.1f} %)")
