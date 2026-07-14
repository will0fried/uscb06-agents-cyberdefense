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

print("\nMoyenne des 10 :", round(statistics.mean(scores), 1))
print("Meilleure :", max(scores), " | Pire :", min(scores))
