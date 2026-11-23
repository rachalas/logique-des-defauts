"""
tests_moteur.py -- Tests du moteur (sans interface). Lancer :  python tests_moteur.py
Chaque module est testé indépendamment ; le test de régression est celui de l'énoncé.
"""
from formules import lire_formule, afficher_formule, ecrire_formule, variables
from raisonnement import (est_coherent, consequence, sous_ensemble_incoherent,
                          sous_ensembles_incoherents_minimaux)
from defauts import Theorie, lire_defaut, avertissements
from extensions import (extensions, est_extension, consequence_sceptique,
                        consequence_credule, rapport_extensions, repondre_consequence,
                        appliquer_ordre, ordres_possibles, toutes_permutations,
                        rapport_ordre)

nb = 0
def verifie(cond, msg):
    global nb
    nb += 1
    assert cond, "ÉCHEC : " + msg
    print("  ok  ", msg)

def erreur(fn, *args):
    try: fn(*args)
    except ValueError: return True
    return False

def theorie(W, D):
    t = Theorie()
    for w in W: t.ajouter_formule(w)
    for d in D: t.ajouter_defaut(d)
    return t

print("== formules.py ==")
verifie(afficher_formule(lire_formule("p -> ~v")) == "p → ¬v", "affichage « p -> ~v » = « p → ¬v »")
verifie(afficher_formule(lire_formule("~(a & b) <-> c | d")) == "¬(a ∧ b) ↔ c ∨ d", "priorités et parenthèses")
verifie(lire_formule("¬p ∧ q → r") == lire_formule("~p & q -> r"), "symboles unicode en entrée")
verifie(lire_formule(ecrire_formule(lire_formule("a -> (b -> c) -> d"))) == lire_formule("a -> (b -> c) -> d"), "aller-retour ASCII")
verifie(variables([lire_formule("P(x) & Q -> karim")]) == ["P(x)", "Q", "karim"], "variables triées (prédicat P(x))")
for mauvais, nom in [("(p & q", "parenthèse manquante"), ("p & q)", "parenthèse en trop"), ("p && q", "opérande manquant"),
                     ("p = q", "connecteur inconnu"), ("", "formule vide"), ("p q", "connecteur manquant"), ("p(x)", "prédicat minuscule")]:
    verifie(erreur(lire_formule, mauvais), f"ValueError : {nom} (« {mauvais} »)")

print("== raisonnement.py ==")
verifie(not est_coherent([lire_formule("p"), lire_formule("~p")]), "{p, ¬p} incohérent")
verifie(consequence([lire_formule("p"), lire_formule("p -> q")], lire_formule("q")), "{p, p→q} |= q")
verifie(not consequence([lire_formule("p")], lire_formule("q")), "{p} ⊭ q")
W = [lire_formule(x) for x in ["p", "~p", "q", "q -> r", "~r"]]
verifie(sorted(map(sorted, sous_ensembles_incoherents_minimaux(W))) == [[0, 1], [2, 3, 4]], "incohérents minimaux {p,¬p} et {q,q→r,¬r}")
verifie(len(sous_ensemble_incoherent(W)) in (2, 3), "un sous-ensemble incohérent minimal")

print("== defauts.py ==")
d = lire_defaut(": x / x")
verifie(d.texte() == ": x / x", "prérequis vide autorisé")
verifie(lire_defaut("A(x,y) : B(x,y), c / d").justifications[0] == lire_formule("B(x,y)"), "virgule de P(x,y) non coupée")
for mauvais in ["a b / c", "a : b c", "a / b : c", "a : / c", "a : b / ", "a : b : c / d", "a : (b / c"]:
    verifie(erreur(lire_defaut, mauvais), f"défaut invalide refusé (« {mauvais} »)")
verifie(len(avertissements(lire_defaut("a : x & ~x / x"))) == 1, "avertissement : justification incohérente")
t = theorie(["o", "p -> o"], ["o : v / v"])
t2 = Theorie.depuis_dict(t.en_dict())
verifie(t2.W == t.W and t2.D == t.D, "sauvegarde / chargement JSON (aller-retour)")

print("== extensions.py : TEST DE RÉGRESSION (énoncé) ==")
reg = theorie(["o", "p -> o", "p -> ~v"], ["o : v / v", "a : c / b"])
ex = extensions(reg)
print(rapport_extensions(reg, ex))
verifie(len(ex) == 1, "1 extension")
verifie([afficher_formule(l) for l in ex[0].litteraux] == ["o", "v", "¬p"], "littéraux : o, v, ¬p")
verifie(ex[0].indices == (0,), "défaut appliqué : d1 seulement (d2 : a non dérivable)")
verifie(est_extension(reg, ex[0]), "vérification de Reiter  E = Γ(E)")
reg2 = theorie(["o", "p -> o", "p -> ~v", "v"], ["o : v / v", "a : c / b"])
ex2 = extensions(reg2)
verifie(len(ex2) == 1 and [afficher_formule(l) for l in ex2[0].litteraux] == ["o", "v", "¬p"], "variante W = {o, p→o, p→¬v, v} : même résultat")

print("== extensions.py : autres théories ==")
nixon = Theorie.charger("exemples/02_diamant_de_nixon.json")
en = extensions(nixon)
verifie(len(en) == 2 and all(est_extension(nixon, e) for e in en), "Nixon : 2 extensions valides")
pac = lire_formule("Pacifiste(nixon)")
verifie(consequence_credule(nixon, pac)[0] and not consequence_sceptique(nixon, pac)[0], "Nixon : Pacifiste crédule mais pas sceptique")
verifie(consequence_sceptique(nixon, lire_formule("Quaker(nixon)"))[0], "Nixon : Quaker sceptique")
tw = Theorie.charger("exemples/03_tweety_pingouin.json")
verifie(len(extensions(tw)) == 1 and consequence_sceptique(tw, lire_formule("~Vole(tweety)"))[0], "Tweety : ¬Vole sceptique")
na = Theorie.charger("exemples/04_aucune_extension.json")
verifie(extensions(na) == [], "théorie sans extension")
verifie("Aucune extension" in repondre_consequence(na, "p", "credule"), "message clair sans extension")
pv = Theorie.charger("exemples/05_prerequis_vide.json")
verifie(len(extensions(pv)) == 2, "prérequis vide : 2 extensions")
inc = Theorie.charger("exemples/06_monde_incoherent.json")
ei = extensions(inc)
verifie(len(ei) == 1 and ei[0].incoherente, "W incohérent : unique extension inconsistante")
ch = Theorie.charger("exemples/07_chaine_de_defauts.json")
verifie([afficher_formule(l) for l in extensions(ch)[0].litteraux] == ["a", "b", "c", "¬d"], "chaîne de défauts")
for nom in ["01_exemple_enonce", "02_diamant_de_nixon", "03_tweety_pingouin", "05_prerequis_vide", "07_chaine_de_defauts"]:
    th = Theorie.charger(f"exemples/{nom}.json")
    verifie(all(est_extension(th, e) for e in extensions(th)), f"{nom} : toutes les extensions vérifient E = Γ(E)")


print("== extensions.py : ordres imposés ==")
reg = theorie(["o", "p -> o", "p -> ~v"], ["o : v / v", "a : c / b"])
r0 = appliquer_ordre(reg, (0,))
verifie(r0.reussi and r0.ferme and r0.extension is not None, "ordre (0,) réussi et fermé")
verifie(r0.appliques == (0,) and r0.ignores == (), "ordre (0,) : d1 appliqué")
r1 = appliquer_ordre(reg, (1,))
verifie(not r1.reussi or not r1.ferme or r1.extension is None, "ordre (1,) échoue (a non dérivable)")
verifie(r1.appliques == () and r1.ignores == (1,), "ordre (1,) : d2 ignoré")
# Théorie à 3 défauts où certaines permutations échouent
trois = theorie(["a"], [": a / b", "b : c / c", ": ~c / d"])
reussis, echoues = ordres_possibles(trois, (0, 1, 2))
print(f"  ordres valides pour 3 défauts : {len(reussis)} / 6  (échoués : {len(echoues)})")
verifie(len(reussis) < 6, "moins de 3! ordres produisent une extension")
verifie(len(reussis) + len(echoues) == 6, "toutes les permutations sont classées")
verifie(all(appliquer_ordre(trois, o).extension is not None for o in reussis),
        "chaque ordre réussi produit bien une Extension")
verifie(all(appliquer_ordre(trois, o).extension is None for o in echoues),
        "chaque ordre échoué ne produit pas d'Extension")
# sélection vide / singleton
r_vide, e_vide = ordres_possibles(reg, ())
verifie(isinstance(r_vide, list) and isinstance(e_vide, list), "sélection vide gérée")
r_un, e_un = ordres_possibles(reg, (0,))
verifie(len(r_un) == 1 and r_un[0] == (0,), "singleton (0,) est un ordre valide")


# toutes_permutations retourne TOUTES les permutations, pas seulement les valides
trois = theorie(["a"], [": a / b", "b : c / c", ": ~c / d"])
perms = toutes_permutations(trois, (0, 1, 2))
verifie(len(perms) == 6, "toutes_permutations renvoie les 3! = 6 permutations")
reussis = [p for p, r in perms if r.extension is not None]
echoues = [p for p, r in perms if r.extension is None]
verifie(len(reussis) + len(echoues) == 6, "chaque permutation est classée réussie OU échouée")
verifie(len(reussis) < 6, "moins de 6 permutations produisent une extension")
# Le tri est déterministe
verifie([p for p, _ in perms] == sorted(p for p, _ in perms),
        "permutations triées pour le déterminisme")
# Un ordre échoué reste simulable (résultat non None, extension None)
p_echec = echoues[0]
r = appliquer_ordre(trois, p_echec)
verifie(r.extension is None, "l'ordre échoué renvoie bien extension None")
verifie(isinstance(rapport_ordre(trois, r), str) and "Aucune extension générée" in rapport_ordre(trois, r),
        "rapport_ordre décrit l'échec sans planter")

print(f"\n{nb} vérifications réussies.")
