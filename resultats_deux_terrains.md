# Résultats des deux terrains - campagnes finales (1 000 parties)

Relevé du 12 juillet 2026. Source des chiffres pour le chapitre 4.4.
Protocole identique sur les deux terrains : 4 stratégies (hasard, action fixe, règle
réactive, RL/PPO), 1 000 parties de 30 tours, graines 1-1000 appariées, même venv
(.venv, numpy 2.5.0). Stratégies adaptées à chaque terrain (règle, action fixe et
modèle RL propres à chaque environnement). Reproductibilité vérifiée (2 runs identiques).

## CAGE 2 - terrain lisible (attaquant B_line, chemin fixe)

| Stratégie | Moyenne | σ | IC 95 % |
|---|---|---|---|
| RL (PPO) | −4,70 | 3,4 | [−4,91 ; −4,49] |
| Règle réactive | −14,33 | 0,8 | [−14,38 ; −14,28] |
| Action fixe (#135 Restore Enterprise2) | −57,30 | 1,1 | [−57,36 ; −57,23] |
| Hasard | −154,71 | 78,9 | [−159,60 ; −149,82] |
| LLM (llama3.2:3b, n=1000) | −188,42 | 54,38 | [−191,79 ; −185,05] |

(n=1000 remplace la valeur provisoire n=100 de −190,03 [−200,21 ; −179,85], relevée le 13 juil ; CSV cage2_llm_final.csv, 0 invalide.)

Le LLM est significativement pire que le hasard (IC disjoints).
Intervalles tous disjoints : le classement RL > règle > action fixe > hasard
tient sans ambiguïté.

## DroneSwarm - terrain chaotique (attaquant piloté par le simulateur)

| Stratégie | Moyenne | σ | IC 95 % |
|---|---|---|---|
| RL (PPO) | −194,35 | 116,1 | [−201,54 ; −187,15] |
| Action fixe (#12) | −194,38 | 116,4 | [−201,60 ; −187,17] |
| Règle réactive | −197,56 | 112,2 | [−204,52 ; −190,60] |
| Hasard | −205,83 | 107,6 | [−212,50 ; −199,16] |
| LLM (llama3.2:3b, n=1000) | −211,50 | 111,28 | [−218,40 ; −204,61] |

Les intervalles de confiance se chevauchent largement. Mais l'analyse appariée
(la même que sur CAGE 2) détecte des écarts significatifs - le chevauchement des IC ne
prouve pas l'absence de différence :

| Comparaison appariée | Δ moyen | IC 95 % du Δ | Victoires | Verdict |
|---|---|---|---|---|
| RL vs hasard | +11,48 | [+4,07 ; +18,89] | 553/1000 | significatif |
| Règle vs hasard | +8,27 | [+1,11 ; +15,42] | 536/1000 | significatif |
| Action fixe vs hasard | +11,44 | [+4,18 ; +18,71] | 542/1000 | significatif |
| RL vs règle | +3,21 | [−4,69 ; +11,11] | 495/1000 | non significatif |
| RL vs action fixe | +0,04 | [−6,77 ; +6,85] | 460/1000 | non significatif |
| LLM vs hasard | −5,68 | [−12,46 ; +1,11] | 481/1000 | non significatif |

Le RL, la règle et l'action fixe battent le hasard de façon statistiquement
significative mais pratiquement négligeable (~11 points, 55 % des parties) - contre
150 points et 99 % sur CAGE 2. Aucune stratégie ne maîtrise le terrain chaotique.
(Recalculé le 13 juil depuis drones_*_final.csv, graines appariées 1-1000.)

## Le résultat central

Le même algorithme PPO, avec le même code :
- sur CAGE 2, domine tout de façon nette (−4,70, intervalle disjoint) ;
- sur DroneSwarm, ne devance plus le hasard que de façon marginale (+11 pts, 55 % - significatif à l'appariement mais négligeable en pratique).

« Le terrain décide autant que l'algorithme. » La performance d'un agent ne dépend
pas que de sa sophistication, mais de la lisibilité de l'environnement (observabilité,
attaquant prévisible). Démontré avec intervalles de confiance sur les deux terrains.

## Deuxième résultat : le petit LLM échoue partout
Le LLM llama3.2:3b (3 milliards de paramètres, local) est le plus mauvais des
deux côtés : significativement pire que le hasard sur CAGE 2 (IC disjoints), et
le plus bas sur DroneSwarm. Confirme la littérature (Castro et al. [6], CAIBench
[21]) : la connaissance générale d'un LLM n'implique pas la capacité d'agir en
cyberdéfense, surtout à petite taille et exécuté localement.

Attention : les scores ne se comparent pas d'un terrain à l'autre (échelles de
récompense différentes) ; on compare le motif - hiérarchie nette vs chevauchement.

## Validation contre le journal (campagne v2, 100 parties)
- Règle drones : −197,6 (v2) puis −197,56 (1000). Identique.
- Hasard drones : −208,8 puis −205,83 (écart 3, dans le bruit).
- RL drones : −200,0 puis −194,35 (écart 5,6, n=100 côté ancien).
- Action fixe drones : −184,5 (n=50) puis −194,38 (1000) : l'ancienne valeur sur
 50 parties surestimait de ~10 points, illustration de plus de l'importance
 du grand échantillon.

## Contrôle 3 : la graine et la durée d'entraînement (16 juillet)

Le modèle RL DroneSwarm publié est entraîné avec la graine 42 sur des parties de 25 tours.
Trois modèles supplémentaires, un seul facteur modifié à chaque fois, tous évalués sur le
protocole publié (1000 parties de 30 tours, graines appariées 1-1000).

| Modèle | Ce qui change | Moyenne | IC 95 % |
|---|---|---|---|
| publié (g42, 25 tours) | référence | −194,35 | [−201,54 ; −187,15] |
| g43_t25 | graine seule | −194,83 | [−201,95 ; −187,72] |
| g44_t25 | graine seule | −194,10 | [−201,06 ; −187,14] |
| g42_t30 | durée seule | −197,17 | [−204,31 ; −190,03] |

Lecture : trois entraînements indépendants (g42, g43, g44) tiennent en 0,73 point. La graine
n'explique rien. L'entraînement à 30 tours donne 2,8 points d'écart, orienté dans le sens
inverse de l'objection (entraîner à 30 ne rattrape rien).

Les quatre politiques PPO se rangent entre −194 et −197, soit collées à l'action fixe
(−194,38) et à une dizaine de points du hasard (−205,83). Le plafond de DroneSwarm ne
dépend ni de la graine ni de la durée d'entraînement : il tient au terrain.

Script : `01_scripts/controle3_rl_graines_duree.py`. CSV : `controle3_*.csv`.
À faire : comparaison appariée publié vs g42_t30 (les IC se chevauchent, l'appariement
tranchera). Tant qu'elle n'est pas faite, ne pas écrire « non significatif ».

## E1 : robustesse au changement d'adversaire (16 juillet)

Même campagne que CAGE 2, une seule chose modifiée : l'attaquant B_lineAgent (chemin fixe)
remplacé par RedMeanderAgent (exploration). Le PPO n'est PAS réentraîné : il a appris contre
B_line, on le confronte à un adversaire inconnu. Protocole identique : 1000 parties de
30 tours, graines appariées 1-1000. Script : `01_scripts/cage2_campagne_meander.py`.

| Stratégie | B_line | Meander | Écart | σ B_line | σ Meander |
|---|---|---|---|---|---|
| RL (PPO) | −4,70 | **−8,79** | **−4,09** | 3,40 | 2,02 |
| Règle réactive | −14,33 | −12,26 | +2,07 | 0,80 | **0,56** |
| Action fixe #135 | −57,30 | −55,99 | +1,31 | 1,06 | 4,47 |
| Hasard | −154,71 | −34,60 | +120,11 | 78,93 | 16,28 |
| LLM (llama3.2:3b) | −188,42 | −36,11 | **+152,31** | 54,36 | 16,60 |

La ligne LLM a été mesurée séparément (`01_scripts/cage2_llm_meander.py`, prompt identique au
byte près à `cage2_llm_1000.py`, 1000 parties, 0 réponse invalide, 1058 minutes).

Le classement change d'un attaquant à l'autre. Contre B_line : RL > règle > action fixe >
hasard > LLM. Contre Meander : RL > règle > hasard > LLM > action fixe. L'action fixe #135
passe de la 3ᵉ place à la dernière, le LLM remonte de la 5ᵉ à la 4ᵉ, et seuls le RL et la
règle gardent leur rang.

Comparaisons appariées à l'intérieur de Meander (cinq stratégies, dix paires) :

| Comparaison | Δ moyen | IC 95 % du Δ | Victoires | Verdict |
|---|---|---|---|---|
| RL vs règle | +3,48 | [+3,35 ; +3,61] | 96,6 % (4 nuls) | significatif |
| RL vs hasard | +25,81 | [+24,80 ; +26,83] | 99,6 % | significatif |
| RL vs LLM | +27,32 | [+26,28 ; +28,36] | 100,0 % | significatif |
| RL vs action fixe | +47,21 | [+46,90 ; +47,51] | 100,0 % | significatif |
| Règle vs hasard | +22,34 | [+21,33 ; +23,35] | 99,7 % | significatif |
| Règle vs LLM | +23,84 | [+22,82 ; +24,87] | 100,0 % | significatif |
| Règle vs action fixe | +43,73 | [+43,45 ; +44,01] | 100,0 % | significatif |
| **Hasard vs LLM** | **+1,51** | **[+0,06 ; +2,96]** | **54,5 % (2 nuls)** | **significatif, sans portée** |
| Hasard vs action fixe | +21,39 | [+20,35 ; +22,44] | 92,6 % | significatif |
| LLM vs action fixe | +19,89 | [+18,83 ; +20,94] | 91,2 % | significatif |

Lecture, trois points.

1. Meander est un attaquant plus doux sur 30 tours : le hasard gagne 120 points, la règle
   gagne, l'action fixe gagne. **Le RL est le seul à reculer** (−4,09). L'environnement
   devient plus facile pour tout le monde et lui s'aggrave : sur-apprentissage sur
   l'attaquant d'entraînement, montré et non supposé.

2. Le RL ne s'effondre pas, il maigrit : il gagne encore 97 % des parties contre la règle,
   mais son avance passe de **+9,63 à +3,48**, soit −64 %.

3. **Inversion de hiérarchie** : l'action fixe #135 (Restore Enterprise2), choisie parce
   qu'Enterprise2 est sur le chemin de B_line, passe **sous le hasard** (+21,39 pour le
   hasard, 92,6 % des parties). L'ordre devient RL > règle > hasard > action fixe.
   Une stratégie taillée pour un adversaire précis devient pire que le dé face à un autre.

Les variances racontent la même histoire : celle du hasard s'écroule (78,93 → 16,28, B_line
détruit ou pas, Meander fait des dégâts moyens réguliers), celle de l'action fixe augmente
(1,06 → 4,47, son sort dépend maintenant d'où Meander erre), et la règle reste la plus
stable des quatre sur les deux attaquants (σ = 0,56). Matière directe pour le §4.5 :
elle est prévisible même face à un adversaire qu'elle n'a jamais vu.

À compléter : le LLM contre Meander (`cage2_llm_meander.py`, en cours). Sans lui le tableau
a 4 lignes là où les autres en ont 5.

## Fichiers
- CSV : `cage2_*_final.csv`, `drones_*_final.csv` (dans 02_resultats_bruts/).
- Figures : `03_captures/cage2_boxplots.png`, `03_captures/comparaison_deux_terrains.png`.
- Campagnes terminées : les 5 stratégies sont à n=1000 sur les deux terrains (LLM DroneSwarm bouclé le 15 juillet, ~69 h).
