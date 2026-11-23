LOGIQUE DES DÉFAUTS — Mini-projet 1 (RCR, 4-ING-IA, USTHB)
===========================================================

1. Installation
---------------
* Python 3.8 ou plus récent.
* AUCUNE bibliothèque externe à installer : le moteur logique est écrit en Python pur
  (pas de SymPy) et l'interface utilise tkinter, fourni avec Python.
* Linux (Debian/Ubuntu) uniquement, si « import tkinter » échoue :
      sudo apt install python3-tk
  (Windows et macOS : tkinter est inclus avec l'installateur officiel de Python.)

2. Lancer l'application
-----------------------
Dans le dossier du projet :
      python main.py          (ou  python3 main.py  sous Linux/macOS)

3. Lancer les tests (sans interface)
------------------------------------
      python tests_moteur.py
Ce script exécute, entre autres, le test de régression de l'énoncé
(W = {o, p -> o, p -> ~v}, D = {o : v / v ; a : c / b}  =>  1 extension, littéraux o, v, ~p).

4. Syntaxe de saisie
--------------------
  Connecteur :  ¬    ∧    ∨    →     ↔     Vrai / Faux
  Saisie     :  ~    &    |    ->    <->   true / false
  (les symboles unicode sont aussi acceptés à la saisie)
  Priorités : ~ > & > | > -> > <->.   Exemple :  p -> ~v ,  P(x) & Q -> karim
  Variables en minuscules (p, karim), propositions / prédicats en majuscules (P, Q, P(x,y)).
  Un défaut se saisit par 3 champs : prérequis, justifications (séparées par des virgules),
  conséquent. Le prérequis peut être vide (défaut « : x / x »).

5. Organisation des fichiers
----------------------------
  formules.py       lecture (texte -> formule), affichage ¬ ∧ ∨ → ↔, variables
  raisonnement.py   cohérence, conséquence logique, sous-ensembles incohérents
  defauts.py        classes Defaut et Theorie, lecture d'un défaut, sauvegarde / chargement JSON
  extensions.py     applicabilité, extensions, conséquences sceptiques et crédules
  interface.py      fenêtre tkinter (AUCUN calcul logique)
  main.py           point d'entrée
  tests_moteur.py   tests du moteur
  exemples/         8 théories d'exemple (menu « Exemples »), au format JSON

6. Utilisation rapide
---------------------
  Exemples > « Exemple de l'énoncé » puis « Générer les extensions ».
  Saisir φ (ex. v) dans la zone « φ » puis « Sceptique ? » ou « Crédule ? ».
  Exemples > « W incohérent » puis « Vérifier la cohérence de W » : les formules fautives
  sont surlignées en rouge.

7. Simulation d'un ordre d'application
--------------------------------------
  Le bouton « Simuler un ordre » ouvre une boîte de dialogue : sélectionnez un sous-ensemble
  de défauts (Listbox multi-sélection), choisissez un ordre valide dans la Combobox
  (seules les permutations qui produisent un processus fermé et réussi sont proposées),
  puis cliquez « Simuler ». Le panneau RÉSULTATS affiche les défauts appliqués / ignorés,
  la fermeture, le succès et les littéraux de l'extension obtenue. Un avertissement apparaît
  si certaines permutations de la sélection ne donnent pas d'extension.
  Côté moteur : appliquer_ordre(theorie, ordre) et ordres_possibles(theorie, indices)
  dans extensions.py (l'interface ne fait aucun calcul logique).
