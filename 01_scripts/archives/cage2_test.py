# Test de survie CAGE 2 : cree l'environnement entreprise, verifie obs/actions,
# joue 3 tours au hasard. A copier dans ~/cage-challenge-2/CybORG/ et lancer.
import inspect
from CybORG import CybORG
from CybORG.Agents import B_lineAgent
from CybORG.Agents.Wrappers import ChallengeWrapper

path = str(inspect.getfile(CybORG))
path = path[:-10] + '/Shared/Scenarios/Scenario2.yaml'
print("scenario:", path)

cyborg = CybORG(path, 'sim', agents={'Red': B_lineAgent})
env = ChallengeWrapper(env=cyborg, agent_name='Blue')

obs = env.reset()
print("observation : vecteur de", len(obs), "nombres")
print("espace d'actions :", env.action_space)

total = 0
for tour in range(3):
    a = env.action_space.sample()
    obs, r, done, info = env.step(a)
    total += r
    print(f"  tour {tour+1} -> action #{a}, recompense {r}, total {total}")

print("\nCAGE 2 OK")
