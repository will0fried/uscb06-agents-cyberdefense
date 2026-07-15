# DroneSwarm - le bouton fixe #26 joue sur 40 parties, seed 42, 25 tours. A servi a
# demasquer le faux champion a -93,4 : re-mesure, il retombe a -169,0 (artefact de selection).
# Exploration du 3 juillet. A copier dans ~/CybORG puis : python dix_parties_bouton26.py
import random, statistics
import numpy as np
from CybORG import CybORG
from CybORG.Simulator.Scenarios.DroneSwarmScenarioGenerator import DroneSwarmScenarioGenerator
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper

SEED = 42
random.seed(SEED); np.random.seed(SEED)
env = OpenAIGymWrapper(agent_name='blue_agent_0',
                       env=FixedFlatWrapper(CybORG(DroneSwarmScenarioGenerator(), 'sim')))
env.action_space.seed(SEED)

scores = []
for partie in range(1, 41):
    env.reset(); total = 0
    for _ in range(25):
        _, recompense, fini, _ = env.step(26)
        total += recompense
        if fini: break
    scores.append(total)
    print(f"Partie {partie:2d} : {total:7.1f}")

print("\nMoyenne des 40 :", round(statistics.mean(scores), 1))
print("Meilleure :", max(scores), " | Pire :", min(scores))
