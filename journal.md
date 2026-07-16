# Journal de bord - mémoire USCB06

Une ligne par séance, écrite au fil de l'eau. C'est la matière brute du chapitre 4 : les résultats, mais aussi les erreurs, parce qu'elles comptent autant.

## Avant de reprendre proprement

Mesure du hasard sur DroneSwarm, 40 parties, seed 42 : -164,2. Balayage des 56 actions fixes, 10 parties chacune : moyenne -161,2, la meilleure (#26) à -93,4, la pire (#44) à -236,2. Leçon retenue tôt : un premier essai à 5 parties m'avait sorti un faux « miracle » à -44 - corrigé en moyennant sur plus de parties et en fixant la graine.

## 2 juillet

Repris tout à zéro pour vraiment comprendre. Environnement recréé : venv Python 3.12.13, `pip install -r Requirements.txt`, `pip install -e .`, plus setuptools parce que gym cassait (« No module named distutils »). CybORG tourne. Au passage un avertissement « gym non maintenu » : je le garde comme exemple de vieillissement des outils pour le chapitre 4.

`partie_au_ralenti.py` : une partie hasard affichée tour par tour. L'observation, c'est un vecteur de 11 293 nombres, et il y a 56 actions. Score -8 sur cette partie, un coup de chance (l'attaquant s'est peu propagé). Les dégâts se concentrent en fin de partie.

`dix_parties.py` : 10 parties hasard, seed 42, moyenne -158,2, avec une dispersion énorme (-31 à -260). Cohérent avec le -164,2 de référence, donc la ligne « hasard » du tableau est comprise et reproduite.

`dix_parties_bouton26.py` : le bouton fixe #26 sur 10 parties donne -186,9, alors que le chiffre « officiel » était -93,4. Ça sent le « gagnant du loto ». À trancher : relancer le bouton 26 sur 40 parties.

Testé `env.render()` : pas implémenté dans CybORG 3.1 (NotImplementedError). Un outil de recherche inachevé, à citer au chapitre 4.

Partie accidentelle de 45 tours (-562). Leçon : c'est le script qui fixe la durée, pas le simulateur. Je ne compare que des parties de même longueur (25 tours partout).

Observation en fin de partie : -17/-18 par tour une fois saturé, avec un essaim d'environ 18 drones. Hypothèse à vérifier dans le code : à peu près -1 par drone en mauvais état et par tour, et bloquer du trafic pénalise aussi les communications légitimes.

## 3 juillet

Verdict pour le bouton 26 : re-mesuré sur 40 parties (seed 42, 25 tours ; sur des échantillons de 10 parties j'avais eu -186,9 puis -172,7), résultat -169,0. Le -93,4 ne se reproduit pas - c'est un artefact de sélection : on garde le meilleur parmi 56 mesures bruitées, donc on récolte surtout le plus chanceux. Conclusion corrigée : aucune action fixe repérée ne bat le hasard (-164). Une défense statique ne protège pas l'essaim, il faut s'adapter.

Branché le LLM sur CybORG (`agent_llm.py`) : un traducteur d'état (résumé en texte), la règle du menu (k / 18 / 19+k / 37+k / 55), l'appel à Ollama llama3.2:3b, et un filet de sécurité. Première partie à -30, mais j'ai découvert un bug d'interface : le parseur lisait le premier nombre, donc « ACTION=19+3 » était joué comme 19. Corrigé avec une étiquette ACTION=, le calcul des sommes, et temperature 0. J'ai gardé un exemple dans `echange_exemple_llm.txt`.

Partie test après correction : le LLM sur-bloque (BlockTraffic presque à chaque tour), -173. « Défendre a un coût » : le modèle générique s'auto-asphyxie en coupant les communications légitimes.

Première série LLM (prompt v1) : 10 parties, 25 tours, temperature 0, moyenne -139,3 (de -25 à -325), 0 réponse invalide, environ 1,5 min par partie. Mieux que le hasard en tendance, mais l'écart n'est pas concluant à 10 parties.

Série LLM v2 (mêmes conditions, seul le prompt change : conseils sur le coût du blocage, privilégier RetakeControl, sinon ne rien faire) : -153,4 (de -66 à -267), 0 invalide. L'écart v1/v2 est dans le bruit - les conseils n'améliorent pas vraiment un modèle 3B.

Balayage complet : 56 actions × 40 parties = 2 240 parties. RetakeControl domine le classement, les blocages/déblocages derrière, Sleep (-185) est presque le pire geste. Un nouveau « champion » apparent sort à #13, -115,5.

Vérifié le champion #13 sur 40 parties neuves : -157,3, à peu près le hasard. C'était le troisième « gagnant du loto » de la journée. Conclusion : aucune action fixe ne bat le hasard, même mesurée à 40 parties, dès qu'on sélectionne le meilleur parmi 56. Le protocole en deux temps (balayer, puis vérifier sur un échantillon neuf) est validé.

## 5 juillet

Contrôle 1 (appariement) : même graine rejouée deux fois en Sleep, sur 3 graines, résultat identique 3/3 (-94 / -244 / -379). L'appariement par graine est valide, le monde CybORG est déterministe à graine fixée.

Contrôle 2 (déterminisme du LLM) : même partie (graine 1) rejouée 3 fois à temperature 0, -361 / -193 / -318, un écart de 168. Le LLM n'est pas reproductible même à temperature 0, il diverge dès le tour 4 alors que le monde est identique. Conséquence : je devrai le moyenner sur des répétitions, pas l'apparier en une passe.

Agent à règles que j'ai écrit (`agent_regles.py`) : « si dernière action = FALSE, RetakeControl(0), sinon Sleep ». 100 parties, 30 tours, graines 1-100, -197,6 (de 0 à -434). Le mécanisme façon AICA (alerte, puis action) réagit au bon signal mais vise parfois le mauvais drone (le sien, pas le compromis).

Hasard sur les mêmes 100 parties appariées : -208,8. Comparaison appariée règle contre hasard : 54 victoires, 0 nul, 46 défaites - à peu près pile ou face, écart non significatif. La règle simple ne se distingue pas du hasard, cohérent avec la difficulté de DroneSwarm.

Choix de l'action fixe des drones, puisque #13 est tombée : j'ai pris la deuxième du balayage, #12 (-126,2). Je note tout de suite la faiblesse, elle est la même que pour #13 : quand on sélectionne le meilleur parmi 56 mesures bruitées, le deuxième est contaminé exactement comme le premier. Et ça se vérifie, -126,2 au balayage puis -184,5 sur 50 parties. Je la garde quand même, mais comme témoin : sur ce terrain aucune action fixe ne se détache, l'intérêt n'est pas qu'elle soit bonne, c'est d'avoir une stratégie sans mémoire ni regard à comparer aux autres. Contrairement à CAGE 2 où #135 tient ses promesses en calibration et en test, ici je n'ai pas de championne à présenter, et c'est un résultat en soi.

RL DroneSwarm réévalué sur 100 parties appariées, 30 tours : -200,0. Et le LLM llama3.2:3b, 100 parties de 30 tours (de nuit) : -215,6, 0 invalide sur 3000 décisions. Tableau drones : action fixe #12 -184,5, règle -197,6, RL -200, hasard -208,8, LLM -215,6. Tout tient dans environ 30 points, personne ne domine.

Deuxième terrain : CAGE 2 (Scenario2, réseau d'entreprise) installé dans un venv séparé (~/cage-challenge-2, CybORG 2.1). Observation de 52 nombres, 145 actions, échelle de récompense différente (~-0,1 par tour), attaquant B_line. Contrôles : monde quasi déterministe (une action fixe donne le même score sur toutes les graines) ; le hasard n'est reproductible qu'avec action_space.seed. RL entraîné en 6 min : ep_rew_mean passe de -171 à -4,15, explained_variance de 0 à 0,79 - là il apprend, contrairement aux drones.

Résultat clé CAGE 2 : 100 parties de 30 tours, B_line, hasard -158,07 contre RL -4,52, le RL bat le hasard 100 fois sur 100. Un facteur d'environ 35. C'est le contraste au cœur du mémoire : le même PPO, le même code, échoue sur DroneSwarm (à peu près le hasard) et triomphe sur l'entreprise (quasi parfait). Attention, les scores CAGE 2 ne se comparent pas à ceux de DroneSwarm (échelles différentes) - je compare les stratégies à l'intérieur d'un même terrain.

Action fixe CAGE 2 : balayage des 145 actions, calibration 1-50 puis test 51-100. La meilleure est #135 (Restore Enterprise2), -57,29 en calibration et -57,43 en test (cohérent, pas d'artefact). Restaurer en boucle un serveur clé du chemin d'attaque bat déjà largement le hasard.

LLM CAGE 2 : llama3.2:3b, 100 parties de 30 tours, menu de 41 actions utiles (Sleep / Monitor / Analyse / Remove / Restore par serveur, leurres exclus), état de 52 bits traduit en clair, -190,03 (0 invalide sur 3000). Pire que le hasard (-158), comme sur les drones. Le petit LLM 3B échoue sur les deux terrains ; le RL, lui, dépend du terrain.

Règle réactive CAGE 2 que j'ai écrite : serveur compromis, Restore ce serveur ; sinon activité suspecte, Analyse ; sinon Monitor. 100 parties, 30 tours, -14,46 (min -16, max -13, très stable). Deuxième derrière le RL, loin devant le reste. Sur un terrain lisible, une règle simple qui vise juste rivalise avec l'apprentissage - ça rejoint le vainqueur de CAGE 3 (Hicks et al., où une heuristique experte passe devant le RL). Tableau CAGE 2 complet : RL -4,5, règle -14,5, action fixe -57,4, hasard -158,1, LLM -190,0.

Bilan des deux terrains (5 stratégies chacun). Drones (chaotique) : tout dans environ 30 points, personne ne domine, le RL et la règle valent le hasard. Entreprise (lisible) : hiérarchie nette, RL puis règle puis action fixe puis hasard puis LLM. Ce que j'en tire : le petit LLM échoue partout ; le RL et les règles dépendent du terrain ; le terrain décide autant que l'algorithme ; et une règle simple bien ciblée peut rivaliser avec le RL sur un terrain lisible. Tous les CSV sont dans `02_resultats_bruts`.

## 3 juillet - notes RL et LLM (ajoutées après coup)

Entraînement RL : PPO (stable-baselines3), 300 000 pas (environ 12 000 parties), 21 min, seed 42 (modèle `ppo_droneswarm.zip`). ep_rew_mean de -165 à -147, entropie de -4,0 à -1,8 (il a acquis des préférences). Apprentissage modeste mais réel.

Évaluation RL : 40 parties, 25 tours, politique déterministe, -147,4 (de -7 à -381). La meilleure moyenne du tableau, +17 par rapport au hasard, mais l'écart vaut environ un écart-type : une tendance, pas une preuve.

Mesure de référence LLM : prompt v1, 40 parties, temperature 0, environ 1 h, -177,0 (de -20 à -376), 2 réponses invalides sur 1000 décisions. Le -139,3 vu à 10 parties ne tient pas à 40 : troisième artefact de petit échantillon du projet (après le -44 à 5 parties et le -93,4 sélectionné). Le LLM 3B générique ne bat pas le hasard (-177 contre -164). Hypothèses à discuter au chapitre 4 : modèle trop petit, observation pauvre en signal (on ne voit que 4 voisins sur 18 drones), un seul défenseur pour 18 drones. Cette limite vaut pour toutes les stratégies, donc la comparaison reste équitable.

## 15 juillet

Fin de la campagne LLM sur DroneSwarm à 1000 parties : moyenne -211,50 (écart-type 111,3, IC 95 % [-218,40 ; -204,61]), 0 invalide sur les 1000. Le run a tourné presque 69 heures d'affilée, environ 4 min par partie. Meilleure partie -4, pire -476 : la dispersion reste énorme, comme d'habitude sur ce terrain.

La valeur à 100 parties donnait -215,6, à 1000 on trouve -211,5. L'écart est dans le bruit, donc la mesure tenait déjà. Comparaison appariée avec le hasard : -5,68 en moyenne, IC 95 % [-12,46 ; +1,11], 481 victoires sur 1000. L'intervalle contient zéro, donc le LLM n'est pas significativement pire que le hasard sur DroneSwarm, il reste simplement le plus bas. Sur CAGE 2 il l'était significativement ; ici non.

Piège du jour : l'en-tête affiché à la fin du run disait « 1000 parties, graines 1-100 ». C'était juste le texte du print resté figé après le passage de PARTIES à 1000. Vérifié dans le CSV avant de toucher au mémoire : 1000 lignes, graines 1 à 1000, toutes uniques. Le libellé mentait, pas les données. Encore une fois : ne jamais recopier un chiffre sans ouvrir le fichier.

Avec cette campagne, les cinq stratégies sont à 1000 parties sur les deux terrains. Plus d'asymétrie dans le mémoire.

Audit complet du dossier de preuves dans la foulée, avant d'attaquer CAGE 4. Je voulais partir sur une base saine plutôt que traîner des trucs bancals. Bien m'en a pris.

Le gros problème : les scripts que j'avais copiés dans preuves/ étaient les versions à 100 parties, alors que les campagnes finales ont tourné à 1000. Les vrais scripts de campagne (cage2_campagne.py, drones_campagne.py, cage2_llm_1000.py) étaient restés sur la machine, jamais recopiés. Autrement dit, aucun de mes 10 CSV finaux n'était reproductible depuis le dépôt. Ils y sont maintenant, et les 10 remontent chacun à leur script. Il manquait aussi ppo_droneswarm.zip, que drones_campagne.py charge pour rejouer la ligne RL.

Quatre libellés mentaient. cage2_llm_1000.py et serie_llm_nuit.py annonçaient « 100 parties, graines 1-100 » alors que le code tourne à 1000 : c'est exactement ce qui m'a fait douter de mon propre résultat ce soir. dix_parties_bouton26.py affichait « Moyenne des 10 » en jouant 40 parties. Et entrainement_rl.py disait « même durée de partie que tout le reste du protocole » avec TOURS = 25, alors que tout le reste est passé à 30.

Ce dernier n'est pas qu'un commentaire faux. Le RL DroneSwarm est bien entraîné sur des parties de 25 tours et évalué sur 30, alors que CAGE 2 est à 30 des deux côtés. L'écart est réel. Il est maintenant écrit noir sur blanc dans le code, et il ira dans les limites du mémoire.

La leçon est la même que celle du gagnant du loto, version code : un libellé n'est pas une mesure. J'ai ouvert le CSV avant de toucher au mémoire, les données étaient bonnes, c'est l'étiquette qui mentait. Ne jamais recopier ce qu'un script affiche sans regarder le fichier.

Les anciens résultats à 100 parties restent en archives. Ils prouvent le -184,5 qui rejoint le peloton à -194 une fois mesuré sur 1000, et les trois faux champions. Ce sont des preuves, pas des déchets.

## 16 juillet

Contrôle 3, lancé hier soir, fini cette nuit. Deux objections m'attendaient à la soutenance et je préférais y répondre avec des chiffres plutôt qu'avec des arguments : la graine 42 serait tombée juste, et l'entraînement à 25 tours face à une évaluation à 30 aurait handicapé le RL. Trois modèles réentraînés, un seul facteur qui change à chaque fois, et les trois évalués sur le protocole publié à l'identique (1000 parties de 30 tours, graines appariées 1-1000).

Graines 43 et 44, durée inchangée : -194,83 et -194,10, contre -194,35 pour le modèle publié. Moins d'un point d'écart entre trois entraînements indépendants. La graine n'explique rien. Durée portée à 30 tours, graine inchangée : -197,17, soit 2,8 points. L'écart est petit, et surtout il va dans le sens inverse de l'objection : entraîner à 30 ne rattrape rien.

Ce que ça donne au total : quatre politiques PPO entraînées différemment atterrissent toutes entre -194 et -197, c'est-à-dire collées à l'action fixe (-194,38) et à une dizaine de points du hasard (-205,83). Ce n'est donc pas un entraînement raté, c'est un plafond. Le terrain plafonne tout le monde au même endroit, et changer la façon d'entraîner ne fait pas bouger le mur. L'objection « votre RL est mal réglé » ne tient plus.

Deux erreurs en route, aucune n'a coûté de calcul. Le script a d'abord planté sur CybORG.__file__ : dans mes scripts je fais `from CybORG import CybORG`, donc j'importe la classe et pas le module, et une classe n'a pas de __file__. Corrigé avec inspect.getfile. Plus embêtant : ma première version faisait varier la graine avec TOURS = 30, alors que le modèle publié est entraîné à 25. J'aurais changé deux choses à la fois et je n'aurais pas su laquelle expliquait quoi. Repéré avant de lancer, en relisant. C'est exactement le genre de détail qui ruine un contrôle sans qu'on s'en aperçoive.

Reste à faire : la comparaison appariée entre le modèle publié et g42_t30, graine par graine. Les intervalles se chevauchent mais l'appariement est plus fin, il tranchera vraiment. Tant que je ne l'ai pas faite, je n'écris pas « non significatif » dans le mémoire.

E1 dans la foulée, pendant que le contrôle 3 finissait. Question : la hiérarchie de CAGE 2 survit-elle si on change d'attaquant ? Même campagne, même protocole, une seule chose modifiée : B_line remplacé par RedMeanderAgent. Le PPO n'est pas réentraîné, c'est tout l'intérêt : il a appris contre B_line et je le confronte à un adversaire qu'il n'a jamais vu.

Résultats (B_line puis Meander) : RL -4,70 -> -8,79. Règle -14,33 -> -12,26. Action fixe -57,30 -> -55,99. Hasard -154,71 -> -34,60.

Ce que ça dit, et je ne m'y attendais pas dans ce sens : Meander est un attaquant beaucoup plus doux sur 30 tours. Le hasard gagne 120 points, la règle gagne, l'action fixe gagne. Tout le monde profite du changement. Sauf le RL, qui est le seul à s'aggraver et double ses dégâts. L'environnement devient plus facile pour tous et lui recule : c'est du sur-apprentissage, montré au lieu d'être supposé.

Deux chiffres à retenir. L'avance du RL sur la règle passe de +9,63 à +3,47, elle perd 64 %. Et l'action fixe #135 (Restore Enterprise2), choisie parce qu'Enterprise2 est sur le chemin de B_line, passe sous le hasard : la hiérarchie devient RL > règle > hasard > fixe. L'ordre change, contre un adversaire qui ne passe plus par là.

Le kit E1 que j'avais préparé le 14 était périmé : il visait cage2_regles.py et cage2_hasard_et_rl.py, les versions à 100 parties que l'audit du 15 a rangées en archives. Les suivre aurait produit des CSV hors protocole. Refait depuis cage2_campagne.py : cage2_campagne_meander.py. Leçon : un kit vieillit dès qu'on touche au dépôt.

Reste à faire avant d'écrire : la comparaison appariée RL vs règle à l'intérieur de Meander. Les moyennes suffisent à voir le sens, pas à écrire « significatif ».

Le §4.7 se termine encore par « Vérifier cette hypothèse en changeant d'adversaire constitue le prolongement le plus direct de ce travail ». C'est fait. La phrase doit devenir un résultat.
