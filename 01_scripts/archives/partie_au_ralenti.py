import random
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

obs = env.reset()
print("Ce que le défenseur observe : un vecteur de", len(obs), "nombres")
total = 0
for tour in range(1, 26):
    action = env.action_space.sample()          # stratégie : hasard
    obs, recompense, fini, info = env.step(action)
    total += recompense
    print(f"Tour {tour:2d} | bouton #{action:2d} | points ce tour : {recompense:7.1f} | total : {total:8.1f}")
    if fini:
        print("Partie terminée avant la fin.")
        break
print("\nScore final de cette partie :", round(total, 1))
