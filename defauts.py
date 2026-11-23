"""
defauts.py -- Classes Defaut et Theorie, lecture d'un défaut, sauvegarde / chargement.

Un défaut s'écrit  prérequis : just1, just2 / conséquent   (prérequis vide autorisé :  ": x / x").
Une théorie des défauts est un couple T = (W, D).
"""
import json
import os
from dataclasses import dataclass

from formules import (VRAI, lire_formule, afficher_formule, ecrire_formule)
from raisonnement import est_coherent

FORMAT_FICHIER = "logique-des-defauts-v1"


# ----------------------------------------------------------------------------
# Défaut
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Defaut:
    """d = prérequis : justifications / conséquent.  Prérequis vide  <=>  VRAI."""
    prerequis: tuple
    justifications: tuple      # tuple de formules (au moins une)
    consequent: tuple

    #display / save
    def texte(self, ascii_=False):
        """Écriture « α : β1, β2 / γ » (unicode par défaut, ASCII pour la sauvegarde)."""
        ecr = ecrire_formule if ascii_ else afficher_formule
        pre = "" if self.prerequis == VRAI else ecr(self.prerequis) + " "
        return pre + ": " + ", ".join(ecr(j) for j in self.justifications) + " / " + ecr(self.consequent)

    def __str__(self):
        return self.texte()

# only split on commas outside parentheses
def _separer_virgules(texte):
    """Découpe sur les virgules de niveau 0 (celles de P(x,y) sont conservées)."""
    morceaux, prof, debut = [], 0, 0
    for i, c in enumerate(texte):
        if c == "(": prof += 1
        elif c == ")": prof -= 1
        elif c == "," and prof == 0:
            morceaux.append(texte[debut:i]); debut = i + 1
    morceaux.append(texte[debut:])
    return morceaux


def _lire_partie(texte, nom):
    try:
        return lire_formule(texte)
    except ValueError as e:
        raise ValueError(f"{nom} invalide : {e}") from None

#all validation happens here
def lire_defaut(texte):
    """Texte « prérequis : just1, just2 / conséquent » -> Defaut. Lève ValueError sinon."""
    if texte.count(":") != 1:
        raise ValueError("Un défaut doit contenir exactement un « : » (forme « prérequis : just1, just2 / conséquent »).")
    if texte.count("/") != 1:
        raise ValueError("Un défaut doit contenir exactement un « / » (forme « prérequis : just1, just2 / conséquent »).")
    if texte.index(":") > texte.index("/"):
        raise ValueError("Le « : » doit venir avant le « / » (forme « prérequis : just1, just2 / conséquent »).")
    pre_txt, reste = texte.split(":")
    just_txt, cons_txt = reste.split("/")
    prerequis = VRAI if pre_txt.strip() == "" else _lire_partie(pre_txt, "Prérequis")
    justs = []
    for k, morceau in enumerate(_separer_virgules(just_txt), 1):
        if morceau.strip() == "":
            raise ValueError(f"Justification n°{k} vide (au moins une justification est requise, séparées par des virgules).")
        justs.append(_lire_partie(morceau, f"Justification n°{k}"))
    if cons_txt.strip() == "":
        raise ValueError("Conséquent vide.")
    return Defaut(prerequis, tuple(justs), _lire_partie(cons_txt, "Conséquent"))

# The assignment explicitly says: "a justification that is itself incoherent gives a warning, because the default will never be applicable"
def avertissements(defaut):
    """Avertissements (non bloquants) : une justification incohérente rend le défaut inapplicable."""
    return [f"La justification « {afficher_formule(j)} » est incohérente : "
            "ce défaut ne sera jamais applicable."
            for j in defaut.justifications if not est_coherent([j])]


# ----------------------------------------------------------------------------
# Théorie
# ----------------------------------------------------------------------------
class Theorie:
    """Théorie des défauts T = (W, D). W : liste de formules ; D : liste de Defaut."""

    def __init__(self, W=None, D=None, nom="", description=""):
        self.W, self.D = list(W or []), list(D or [])
        self.nom, self.description = nom, description

    # --- édition --------------------------------------------------------------
    def ajouter_formule(self, texte):
        """Ajoute une formule à W (ValueError si syntaxe incorrecte ou doublon). Renvoie la formule."""
        f = lire_formule(texte)
        if f in self.W:
            raise ValueError("Cette formule est déjà dans W.")
        self.W.append(f)
        return f

    def ajouter_defaut(self, texte):
        """Ajoute un défaut à D. Renvoie (defaut, liste_d_avertissements)."""
        d = lire_defaut(texte)
        if d in self.D:
            raise ValueError("Ce défaut est déjà dans D.")
        self.D.append(d)
        return d, avertissements(d)

    def supprimer_formule(self, i): del self.W[i]
    def supprimer_defaut(self, i): del self.D[i]

    def vider(self):
        self.W, self.D, self.nom, self.description = [], [], "", ""

    # --- affichage ------------------------------------------------------------
    @staticmethod
    def nom_defaut(i): return f"d{i + 1}"

    def lignes_formules(self):
        return [f"{i + 1}. {afficher_formule(f)}" for i, f in enumerate(self.W)]

    def lignes_defauts(self):
        return [f"{self.nom_defaut(i)} : {d.texte()}" for i, d in enumerate(self.D)]

    # --- sauvegarde / chargement (JSON) --------------------------------------
    #serialize to a dict
    def en_dict(self):
        return {"format": FORMAT_FICHIER, "nom": self.nom, "description": self.description,
                "W": [ecrire_formule(f) for f in self.W],
                "D": [d.texte(ascii_=True) for d in self.D]}
    #deserialize from a dict
    @classmethod
    def depuis_dict(cls, data):
        if not isinstance(data, dict) or "W" not in data or "D" not in data:
            raise ValueError("Fichier invalide : clés « W » et « D » attendues.")
        if not (isinstance(data["W"], list) and isinstance(data["D"], list)):
            raise ValueError("Fichier invalide : « W » et « D » doivent être des listes.")
        t = cls(nom=str(data.get("nom", "")), description=str(data.get("description", "")))
        for k, txt in enumerate(data["W"], 1):
            try: t.W.append(lire_formule(str(txt)))
            except ValueError as e: raise ValueError(f"W, formule n°{k} : {e}") from None
        for k, txt in enumerate(data["D"], 1):
            try: t.D.append(lire_defaut(str(txt)))
            except ValueError as e: raise ValueError(f"D, défaut n°{k} : {e}") from None
        return t

    def sauvegarder(self, chemin):
        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump(self.en_dict(), fichier, ensure_ascii=False, indent=2)

    @classmethod
    def charger(cls, chemin):
        try:
            with open(chemin, encoding="utf-8") as fichier:
                return cls.depuis_dict(json.load(fichier))
        except json.JSONDecodeError as e:
            raise ValueError(f"Fichier JSON invalide : {e}") from None
    #load into existing instance
    def remplacer_par(self, autre):
        """Remplace le contenu de cette théorie par celui d'une autre (sert à Ouvrir / Exemples)."""
        self.W, self.D, self.nom, self.description = autre.W, autre.D, autre.nom, autre.description


def lister_exemples(dossier=None):
    """Liste [(nom, chemin)] des théories d'exemple du dossier exemples/ (menu « Exemples »)."""
    dossier = dossier or os.path.join(os.path.dirname(os.path.abspath(__file__)), "exemples")
    res = []
    if os.path.isdir(dossier):
        for fichier in sorted(os.listdir(dossier)):
            if fichier.endswith(".json"):
                chemin = os.path.join(dossier, fichier)
                try:
                    res.append((Theorie.charger(chemin).nom or fichier, chemin))
                except (OSError, ValueError):
                    pass
    return res
