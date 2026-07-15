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

## Fichiers
- CSV : `cage2_*_final.csv`, `drones_*_final.csv` (dans 02_resultats_bruts/).
- Figures : `03_captures/cage2_boxplots.png`, `03_captures/comparaison_deux_terrains.png`.
- Campagnes terminées : les 5 stratégies sont à n=1000 sur les deux terrains (LLM DroneSwarm bouclé le 15 juillet, ~69 h).
