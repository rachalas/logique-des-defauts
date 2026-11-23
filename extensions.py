"""
extensions.py -- Applicabilité, extensions, conséquences sceptiques et crédules.

Algorithme (processus de Antoniou, équivalent à la définition de Reiter pour une théorie finie) :
  On construit des processus  Π = (d_i1, d_i2, ...)  de défauts distincts. À chaque étape,
      In = W ∪ {conséquents des défauts déjà appliqués}
  et un défaut d = α : β1..βn / γ est APPLICABLE si  In |= α  et  In ⊭ ¬βi  pour tout i.
  Π est FERMÉ  si aucun défaut non appliqué n'est applicable à In,
  Π est RÉUSSI si, pour tout défaut appliqué, In ⊭ ¬βi (les justifications restent consistantes
  avec la base finale : Out ∩ Th(In) = ∅).
  Les extensions sont exactement les Th(In(Π)) des processus fermés et réussis.
  On explore tous les ordres d'application par recherche en profondeur sur les ENSEMBLES de défauts
  appliqués (mémoïsés : In ne dépend que de l'ensemble, pas de l'ordre).
"""
from dataclasses import dataclass
from itertools import permutations

from formules import VRAI, Non, afficher_formule, variables, lire_formule
from raisonnement import consequence, est_coherent, equivalents
from defauts import Theorie


# ----------------------------------------------------------------------------
# Applicabilité
# ----------------------------------------------------------------------------
# when does a default fire
#1.Prerequisite must be derivable
#2.Each justification must remain compatible
def applicable(defaut, base):
    """Le défaut est-il applicable à Th(base) ?  base |= α  et  base ⊭ ¬βi pour tout i."""
    if defaut.prerequis != VRAI and not consequence(base, defaut.prerequis):
        return False
    return all(not consequence(base, Non(b)) for b in defaut.justifications)


# ----------------------------------------------------------------------------
# Extension
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Extension:
    base: tuple          # In = W + consequents of applied defaults
    indices: tuple       # which defaults were applied (sorted indices)
    litteraux: tuple     # positive literals then negative literals
    incoherente: bool    # True if W itself is inconsistent
    #is φ in the extension?
    def contient(self, phi):
        """φ ∈ Th(base) ?"""
        return consequence(self.base, phi)
    #text report
    def decrire(self, numero, theorie):
        """Texte d'affichage : base In, littéraux et défauts appliqués."""
        base = "Th({" + ", ".join(afficher_formule(f) for f in self.base) + "})"
        lits = ("extension inconsistante (contient toutes les formules)" if self.incoherente
                else ", ".join(afficher_formule(l) for l in self.litteraux) or "aucun")
        appl = ", ".join(Theorie.nom_defaut(i) for i in self.indices) or "aucun"
        return (f"E{numero} = {base}\n      littéraux : {lits}\n      défauts appliqués : {appl}")


def _sans_doublons(formules):
    vus = []
    for f in formules:
        if f not in vus:
            vus.append(f)
    return tuple(vus)


def _litteraux(base, atomes):
    pos = [("var", a) for a in atomes if consequence(base, ("var", a))]
    neg = [Non(("var", a)) for a in atomes if consequence(base, Non(("var", a)))]
    return tuple(pos + neg)

#Reiter's algorithm
def extensions(theorie):
    """Liste de toutes les extensions de la théorie (W, D) (liste vide s'il n'y en a pas)."""
    W, D = list(theorie.W), list(theorie.D)
    atomes = variables(W + [x for d in D for x in (d.prerequis, d.consequent, *d.justifications)])
    #vus: memoization set ,resultats = the extensions found.
    vus, resultats = set(), []

    def base_de(ens):
        return W + [D[i].consequent for i in sorted(ens)]
    #A process is successful if, for every applied default, each justification is still consistent with the final base.
    def reussi(ens, base):
        return all(not consequence(base, Non(b)) for i in ens for b in D[i].justifications)

    def explorer(ens):
        #Memoization 
        if ens in vus:
            return
        vus.add(ens)
        #Compute base = W + consequents of ens
        base = base_de(ens)
        #Find candidates
        candidats = [i for i in range(len(D)) if i not in ens and applicable(D[i], base)]
        if candidats:                                  # pas fermé : on étend de toutes les façons
            for i in candidats:
                explorer(ens | {i})
            return
        if not reussi(ens, base):                      # fermé mais échoué
            return
        b = _sans_doublons(base)
        if any(equivalents(e.base, b) for e in resultats):
            return                                     # même théorie déjà trouvée
        incoh = not est_coherent(b)
        resultats.append(Extension(b, tuple(sorted(ens)), () if incoh else _litteraux(b, atomes), incoh))

    explorer(frozenset())
    return sorted(resultats, key=lambda e: e.indices)


def est_extension(theorie, ext):
    """Vérification INDÉPENDANTE par la définition de Reiter : E = Γ(E) ?
    Γ(E) = plus petit ensemble contenant W, clos par conséquence, et par : si α ∈ Γ(E) et ¬β ∉ E
    pour tout β, alors γ ∈ Γ(E)."""
    S, changement = list(theorie.W), True
    while changement:
        changement = False
        for d in theorie.D:
            if d.consequent in S:
                continue
            if (d.prerequis == VRAI or consequence(S, d.prerequis)) and \
               all(not ext.contient(Non(b)) for b in d.justifications):
                S.append(d.consequent); changement = True
    return equivalents(S, ext.base)


# ----------------------------------------------------------------------------
# Conséquences sceptique et crédule
# ----------------------------------------------------------------------------
def consequence_sceptique(theorie, phi, exts=None):
    """(vrai, indices des extensions contenant φ). Sceptique : φ est dans TOUTES les extensions
    (vrai par convention s'il n'y a aucune extension)."""
    exts = extensions(theorie) if exts is None else exts
    avec = [i for i, e in enumerate(exts) if e.contient(phi)]
    return len(avec) == len(exts), avec


def consequence_credule(theorie, phi, exts=None):
    """(vrai, indices des extensions contenant φ). Crédule : φ est dans AU MOINS une extension."""
    exts = extensions(theorie) if exts is None else exts
    avec = [i for i, e in enumerate(exts) if e.contient(phi)]
    return len(avec) > 0, avec


# ----------------------------------------------------------------------------
# Rapports textuels (affichés tels quels par l'interface)
# ----------------------------------------------------------------------------
def rapport_extensions(theorie, exts=None):
    exts = extensions(theorie) if exts is None else exts
    if not exts:
        return ("Aucune extension : la théorie n'admet pas d'extension "
                "(tout défaut applicable finit par contredire sa propre justification).")
    titre = "1 extension :" if len(exts) == 1 else f"{len(exts)} extensions :"
    return titre + "\n" + "\n".join(f"  {e.decrire(k, theorie)}" for k, e in enumerate(exts, 1))


def repondre_consequence(theorie, phi_texte, mode):
    """mode = 'sceptique' ou 'credule'. Lève ValueError si φ est mal écrite."""
    phi = lire_formule(phi_texte)
    exts = extensions(theorie)
    fonction = consequence_sceptique if mode == "sceptique" else consequence_credule
    vrai, avec = fonction(theorie, phi, exts)
    nom, n = afficher_formule(phi), len(exts)
    noms = lambda idx: ", ".join(f"E{i + 1}" for i in idx)
    if n == 0:
        conv = ("OUI (par convention : condition sur zéro extension)" if mode == "sceptique"
                else "NON (il n'existe aucune extension)")
        return f"Aucune extension. « {nom} » est-elle conséquence {mode} ? {conv}."
    sans = [i for i in range(n) if i not in avec]
    if mode == "sceptique":
        if vrai:
            return f"« {nom} » est conséquence SCEPTIQUE : OUI — présente dans les {n} extension(s) ({noms(avec)})."
        return (f"« {nom} » est conséquence SCEPTIQUE : NON — présente dans {noms(avec) or 'aucune extension'}, "
                f"absente de {noms(sans)}.")
    if vrai:
        return f"« {nom} » est conséquence CRÉDULE : OUI — présente dans {noms(avec)}."
    return f"« {nom} » est conséquence CRÉDULE : NON — absente des {n} extension(s)."


# ----------------------------------------------------------------------------
# Application ordonnée de défauts (simulation d'un ordre imposé) the creativity feature
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class ResultatOrdre:
    """Résultat de la simulation d'un ordre d'application de défauts."""
    ordre: tuple          # indices demandés (dans l'ordre essayé)
    appliques: tuple      # indices effectivement appliqués
    ignores: tuple        # indices de l'ordre non applicables au moment de leur tour
    base: tuple           # In final (W + conséquents appliqués, sans doublon)
    reussi: bool          # justifications des défauts appliqués encore consistantes avec In
    ferme: bool           # aucun défaut hors des appliqués n'est encore applicable à In
    extension: object     # Extension si reussi et ferme, sinon None


def appliquer_ordre(theorie, ordre):
    """Simule l'application des défauts dans l'ordre donné (tuple d'indices dans D).

    Pour chaque i ∈ ordre : si applicable(D[i], In) alors In ← In ∪ {γi} et i est appliqué,
    sinon i est ignoré. À la fin on vérifie fermeture et succès, et on construit une
    Extension si les deux conditions sont réunies.
    """
    W, D = list(theorie.W), list(theorie.D)
    ordre = tuple(ordre)
    In = list(W)
    appliques, ignores = [], []

    for i in ordre:
        if i < 0 or i >= len(D):
            raise ValueError(f"Index de défaut invalide : {i} (D contient {len(D)} défaut(s)).")
        if applicable(D[i], In):
            In.append(D[i].consequent)
            appliques.append(i)
        else:
            ignores.append(i)

    base = _sans_doublons(In)
    # Réussi : pour tout défaut appliqué, aucune justification n'est contredite par In final
    reussi = all(not consequence(base, Non(b)) for i in appliques for b in D[i].justifications)
    # Fermé : aucun défaut non appliqué n'est encore applicable à In final
    appliques_set = set(appliques)
    ferme = all(not applicable(D[i], base) for i in range(len(D)) if i not in appliques_set)

    extension = None
    if reussi and ferme:
        atomes = variables(W + [x for d in D for x in (d.prerequis, d.consequent, *d.justifications)])
        incoh = not est_coherent(base)
        extension = Extension(
            base,
            tuple(sorted(appliques)),
            () if incoh else _litteraux(base, atomes),
            incoh,
        )

    return ResultatOrdre(
        ordre=ordre,
        appliques=tuple(appliques),
        ignores=tuple(ignores),
        base=base,
        reussi=reussi,
        ferme=ferme,
        extension=extension,
    )


def ordres_possibles(theorie, indices):
    """Toutes les permutations de `indices` qui produisent un processus réussi et fermé.

    Retourne (ordres_reussis, ordres_echoues) : listes de tuples d'indices, triées
    pour le déterminisme. Les ordres échoués (non fermés ou non réussis) sont fournis
    pour les tests et le diagnostic, mais ne sont pas proposés dans l'interface.
    """
    indices = tuple(indices)
    if not indices:
        # Ordre vide : process réussi et fermé ssi aucun défaut n'est applicable à W
        res = appliquer_ordre(theorie, ())
        if res.reussi and res.ferme:
            return [()], []
        return [], [()]

    reussis, echoues = [], []
    for perm in permutations(indices):
        res = appliquer_ordre(theorie, perm)
        if res.reussi and res.ferme:
            reussis.append(perm)
        else:
            echoues.append(perm)
    return sorted(reussis), sorted(echoues)



def toutes_permutations(theorie, indices):
    """Toutes les permutations de `indices`, chacune étiquetée par sa réussite.

    Retourne une liste de tuples (permutation, ResultatOrdre) triée par permutation.
    L'appelant peut filtrer sur resultat.extension is not None s'il veut les ordres valides.
    """
    res = []
    for perm in permutations(tuple(indices)):
        res.append((perm, appliquer_ordre(theorie, perm)))
    return sorted(res, key=lambda t: t[0])


def rapport_ordre(theorie, resultat):
    """Texte d'affichage structuré du résultat d'une simulation d'ordre (pour l'interface)."""
    fleche = lambda idx: " → ".join(Theorie.nom_defaut(i) for i in idx) or "(aucun)"
    liste = lambda idx: ", ".join(Theorie.nom_defaut(i) for i in idx) or "(aucun)"

    lignes = [
        "=== SIMULATION DE L'ORDRE ===",
        f"Ordre demandé : {fleche(resultat.ordre)}",
        "",
        f"Défauts appliqués : {liste(resultat.appliques)}",
        f"Défauts ignorés   : {liste(resultat.ignores)}",
        "",
        "Statut du processus :",
    ]
    if resultat.ferme:
        lignes.append("  - Fermé  : Oui (aucun autre défaut n'est applicable)")
    else:
        lignes.append("  - Fermé  : Non (d'autres défauts restent applicables)")
    if resultat.reussi:
        lignes.append("  - Réussi : Oui (les justifications restent valides)")
    else:
        lignes.append("  - Réussi : Non (justification(s) invalidée(s) par la base finale)")

    lignes += ["", "=== RÉSULTAT ==="]
    if resultat.extension is not None:
        ext_ = resultat.extension
        base = ", ".join(afficher_formule(f) for f in ext_.base)
        if ext_.incoherente:
            lits = "extension inconsistante (contient toutes les formules)"
        else:
            lits = ", ".join(afficher_formule(l) for l in ext_.litteraux) or "aucun"
        lignes += [
            "Extension générée :",
            f"  Base : {{{base}}}",
            f"  Littéraux : {lits}",
        ]
    else:
        raisons = []
        if not resultat.ferme:
            raisons.append("non fermé")
        if not resultat.reussi:
            raisons.append("justification invalidée")
        raison = " / ".join(raisons) if raisons else "échec"
        lignes.append(f"Aucune extension générée. Raison : {raison}")
    return "\n".join(lignes)
