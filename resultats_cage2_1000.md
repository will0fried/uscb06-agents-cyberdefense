# Résultats CAGE 2 - campagne finale (1 000 parties)

Relevé du 12 juillet 2026. Source des chiffres pour le chapitre 4.4.

## Dispositif
- Environnement : CybORG 2.1, Scenario2 (CAGE 2), mode simulation, attaquant `B_lineAgent`.
- 1 000 parties de 30 tours, graines 1 à 1000 (appariées : `random`, `numpy`, `action_space`).
- Toutes les stratégies dans le même venv (`.venv`, numpy 2.5.0) - conditions identiques.
- Scripts : ceux de `01_scripts/` (les mêmes que la campagne à 100 parties, relancés à 1 000). CSV : `cage2_*_final.csv`.
- Reproductibilité : run relancé une 2ᵉ fois, chiffres identiques au centième.
- Contrôle venv : hasard = −154,71 aussi bien dans `.venv` que dans `cyborg-env`, donc le venv n'a aucun effet.

## Résultats (moyenne ± IC 95 %)

| Stratégie | n | Moyenne | Écart-type | IC 95 % |
|---|---|---|---|---|
| RL (PPO) | 1000 | −4,70 | 3,40 | [−4,91 ; −4,49] |
| Règle réactive (façon AICA) | 1000 | −14,33 | 0,80 | [−14,38 ; −14,28] |
| Action fixe (#135 Restore Enterprise2) | 1000 | −57,30 | 1,06 | [−57,36 ; −57,23] |
| Hasard | 1000 | −154,71 | 78,93 | [−159,60 ; −149,82] |

Les intervalles de confiance ne se recouvrent pas : le classement
RL > règle > action fixe > hasard tient sans ambiguïté.

## Comparaisons appariées (victoire = score strictement meilleur)

| Comparaison | Victoires | Δ moyen | IC 95 % du Δ |
|---|---|---|---|
| RL vs règle | 979/1000 | +9,63 | [+9,41 ; +9,85] |
| Règle vs hasard | 981/1000 | +140,38 | [+135,48 ; +145,27] |
| RL vs hasard | 993/1000 | +150,01 | [+145,11 ; +154,90] |
| Action fixe vs hasard | 796/1000 | +97,41 | [+92,52 ; +102,31] |

## Lecture pour le mémoire
- Hiérarchie nette et significative : terrain lisible, l'attaquant à chemin fixe est
 contrable ; restaurer le bon serveur (règle) ou apprendre une politique (RL) paie.
- Histoire des variances : règle très stable (σ = 0,80), hasard chaotique (σ = 79).
 La règle n'est pas seulement meilleure, elle est fiable.
- À contraster avec DroneSwarm (terrain chaotique) où aucune stratégie ne domine, ce qui appuie la
 thèse « le terrain décide autant que l'algorithme ».
- Figure : `preuves/03_captures/cage2_boxplots.png`.
- LLM (llama3.2:3b) à 1 000 parties : −188,42 (σ = 54,38 ; IC 95 % [−191,79 ; −185,05]),
 0 invalide. CSV : `cage2_llm_final.csv`. Significativement pire que le hasard
 (IC entièrement inférieur à [−159,60 ; −149,82]). Campagne terminée le 13 juillet 2026.
- DroneSwarm à 1 000 : fait (voir resultats_deux_terrains.md). LLM DroneSwarm : n = 1000 (terminé le 15 juillet, ~69 h de calcul)
 — campagne terminée.
