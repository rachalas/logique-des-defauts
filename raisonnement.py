"""
raisonnement.py -- Cohérence, conséquence logique, formules incohérentes.

Logique classique propositionnelle (les atomes P(x) sont traités comme des propositions).
Test de satisfiabilité par dépliage de Shannon avec simplification des constantes :
sans dépendance externe, largement suffisant pour des théories de taille de TD.
"""
from itertools import combinations

from formules import (VRAI, FAUX, Non, conjonction, variables, evaluer,
                      afficher_formule)


# ----------------------------------------------------------------------------
# Satisfiabilité
# ----------------------------------------------------------------------------
# smart negation
def _non(g):
    if g == VRAI: return FAUX
    if g == FAUX: return VRAI
    return g[1] if g[0] == "non" else ("non", g)

# smart binary operation
def _bin(op, a, b):
    """Construit (a op b) en simplifiant les constantes Vrai / Faux."""
    if op == "et":
        if a == FAUX or b == FAUX: return FAUX
        if a == VRAI: return b
        if b == VRAI: return a
    elif op == "ou":
        if a == VRAI or b == VRAI: return VRAI
        if a == FAUX: return b
        if b == FAUX: return a
    elif op == "imp":
        if a == FAUX or b == VRAI: return VRAI
        if a == VRAI: return b
        if b == FAUX: return _non(a)
    else:  # equiv
        if a == VRAI: return b
        if a == FAUX: return _non(b)
        if b == VRAI: return a
        if b == FAUX: return _non(a)
    return (op, a, b)

#  substitute one variable
def _subst(f, v, val):
    """Remplace l'atome v par la constante val et simplifie."""
    op = f[0]
    if op == "var":
        return (VRAI if val else FAUX) if f[1] == v else f
    if op in ("vrai", "faux"):
        return f
    if op == "non":
        return _non(_subst(f[1], v, val))
    return _bin(op, _subst(f[1], v, val), _subst(f[2], v, val))


def satisfiable(f):
    """La formule f admet-elle un modèle ?"""
    if f == VRAI: return True
    if f == FAUX: return False
    # If no variables remain → evaluer
    vs = variables([f])
    if not vs:
        return evaluer(f, {})
    return satisfiable(_subst(f, vs[0], True)) or satisfiable(_subst(f, vs[0], False))

# Build f₁ ∧ f₂ ∧ … ∧ fₙ
def est_coherent(formules):
    """L'ensemble de formules est-il cohérent (satisfiable) ? L'ensemble vide l'est."""
    return satisfiable(conjonction(list(formules)))

# si toutes les prémisses sont vraies, est-ce que la conclusion est forcément vraie ?
def consequence(formules, f):
    """formules |= f ?  (vrai ssi formules ∪ {¬f} est incohérent)"""
    return not est_coherent(list(formules) + [Non(f)])


def est_tautologie(f):
    return consequence([], f)


def equivalents(formules1, formules2):
    """Th(formules1) = Th(formules2) ?"""
    return (all(consequence(formules1, f) for f in formules2) and
            all(consequence(formules2, f) for f in formules1))


# ----------------------------------------------------------------------------
# Sous-ensembles incohérents
# ----------------------------------------------------------------------------
# The algorithm tries to remove formulas one by one.
# - If removing a formula makes the remaining set coherent → keep that formula.
# - If removing it still leaves the set incoherent → permanently remove it.
def sous_ensemble_incoherent(formules):
    """Indices d'UN sous-ensemble incohérent minimal (liste vide si cohérent).
    Algorithme de suppression : on retire chaque formule dont le retrait laisse l'incohérence."""
    formules = list(formules)
    if est_coherent(formules):
        return []
    idx = list(range(len(formules)))
    for i in list(idx):
        reste = [j for j in idx if j != i]
        if not est_coherent([formules[j] for j in reste]):
            idx = reste
    return idx


def sous_ensembles_incoherents_minimaux(formules, max_formules=16):
    """Liste de TOUS les sous-ensembles incohérents minimaux (chacun = liste d'indices).
    Énumération par taille croissante ; au-delà de max_formules on ne renvoie qu'un seul sous-ensemble."""
    formules = list(formules)
    if est_coherent(formules):
        return []
    n = len(formules)
    if n > max_formules:
        return [sous_ensemble_incoherent(formules)]
    trouves = []
    for taille in range(1, n + 1):
        for idx in combinations(range(n), taille):
            s = set(idx)
            if any(set(m) <= s for m in trouves):
                continue                      # contient déjà un minimal : pas minimal
            if not est_coherent([formules[i] for i in idx]):
                trouves.append(list(idx))
    return trouves

# which formulas to highlight in red
def formules_incoherentes(formules):
    """Indices des formules qui participent à au moins une incohérence minimale."""
    return sorted({i for m in sous_ensembles_incoherents_minimaux(formules) for i in m})

# text report for the GUI
def rapport_coherence(formules):
    """(coherent, texte, indices_a_surligner) — utilisé par le bouton « Vérifier la cohérence de W »."""
    formules = list(formules)
    minimaux = sous_ensembles_incoherents_minimaux(formules)
    if not minimaux:
        return True, "W est cohérent.", []
    lignes = [f"W est INCOHÉRENT : {len(minimaux)} sous-ensemble(s) incohérent(s) minimal(aux) :"]
    for k, m in enumerate(minimaux, 1):
        lignes.append(f"  {k}. {{" + ", ".join(afficher_formule(formules[i]) for i in m) + "}"
                      + "   (formules n° " + ", ".join(str(i + 1) for i in m) + ")")
    return False, "\n".join(lignes), sorted({i for m in minimaux for i in m})
