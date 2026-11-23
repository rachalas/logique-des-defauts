"""
formules.py -- Lecture d'une formule écrite au clavier et affichage.

Rôle (cf. énoncé, étape 1) :
  * lire_formule(texte)      : texte -> formule (arbre de tuples) ; ValueError claire si erreur
  * afficher_formule(f)      : formule -> chaîne avec les symboles ¬ ∧ ∨ → ↔
  * variables(formules)      : liste triée des variables / propositions / prédicats

Représentation (tuples, donc hachables et comparables avec ==) :
  ("var", nom) | ("vrai",) | ("faux",) | ("non", f)
  ("et", f, g) | ("ou", f, g) | ("imp", f, g) | ("equiv", f, g)

Syntaxe de saisie (énoncé) :  ~  &  |  ->  <->  true / false
(les symboles unicode ¬ ∧ ∨ → ↔ ⊤ ⊥ sont aussi acceptés en entrée).
Priorités : ~  >  &  >  |  >  ->  >  <->   ( -> associe à droite ).
Un prédicat commence par une majuscule : P(x), Aime(karim, Q). Pour le moteur de
raisonnement, un atome fermé comme P(x) est traité comme une proposition.
Ce module n'a aucune dépendance (ni SymPy, ni tkinter).
"""
import re

# ----------------------------------------------------------------------------
# Constructeurs
# ----------------------------------------------------------------------------
VRAI = ("vrai",)
FAUX = ("faux",)


def Var(nom): return ("var", nom)
def Non(f): return ("non", f)
def Et(f, g): return ("et", f, g)
def Ou(f, g): return ("ou", f, g)
def Imp(f, g): return ("imp", f, g)
def Equiv(f, g): return ("equiv", f, g)


def conjonction(formules):
    """Conjonction d'une liste de formules (VRAI si la liste est vide)."""
    res = VRAI
    for f in formules:
        res = f if res == VRAI else Et(res, f)
    return res


# ----------------------------------------------------------------------------
# Analyse lexicale
# ----------------------------------------------------------------------------
_SYMBOLES = {"~": "NOT", "¬": "NOT", "&": "AND", "∧": "AND", "|": "OR", "∨": "OR",
             "→": "IMP", "↔": "IFF", "⊤": "TRUE", "⊥": "FALSE",
             "(": "LP", ")": "RP", ",": "COMMA"}
_MOTS = {"true": "TRUE", "vrai": "TRUE", "false": "FALSE", "faux": "FALSE"}
_MOT = re.compile(r"\w+")

# This function converts a logical expression into tokens (jetons) so that another part of the program can analyze it.
def _tokeniser(texte):
    """Découpe le texte en jetons (type, texte, position)."""
    jetons, i = [], 0
    while i < len(texte):
        c = texte[i]
        if c.isspace():
            i += 1
        elif texte.startswith("<->", i):
            jetons.append(("IFF", "<->", i)); i += 3
        elif texte.startswith("->", i):
            jetons.append(("IMP", "->", i)); i += 2
        elif c in "<-=>":
            raise ValueError(f"Connecteur inconnu « {c} » (position {i + 1}). "
                             "Connecteurs permis : ~  &  |  ->  <->")
        elif c in _SYMBOLES:
            jetons.append((_SYMBOLES[c], c, i)); i += 1
        else:
            m = _MOT.match(texte, i)
            if not m:
                raise ValueError(f"Caractère inconnu « {c} » (position {i + 1}).")
            mot = m.group()
            jetons.append((_MOTS.get(mot.lower(), "ID"), mot, i))
            i = m.end()
    
    return jetons


# ----------------------------------------------------------------------------
# Analyse syntaxique (descente récursive)
# ----------------------------------------------------------------------------
#  It converts a token list into a formula tuple.
class _Parseur:
    def __init__(self, jetons):
        # self.j = token list, self.k = current index.
        self.j, self.k = jetons, 0
    # peek current token
    def _pk(self):
        return self.j[self.k] if self.k < len(self.j) else None
    
    # advance by one token.
    def _av(self):
        self.k += 1

    def analyser(self):
        if not self.j:
            raise ValueError("Formule vide.")
        f = self._equiv()
        t = self._pk()
        if t is not None:
            if t[0] == "RP":
                raise ValueError(f"Parenthèse fermante « ) » en trop (position {t[2] + 1}).")
            raise ValueError(f"Connecteur manquant avant « {t[1]} » (position {t[2] + 1}).")
        return f

    def _equiv(self):                       # <-> : associatif à gauche
        f = self._imp()
        while self._pk() and self._pk()[0] == "IFF":
            self._av(); f = Equiv(f, self._imp())
        return f

    def _imp(self):                         # -> : associatif à droite
        f = self._ou()
        if self._pk() and self._pk()[0] == "IMP":
            self._av(); f = Imp(f, self._imp())
        return f

    def _ou(self):
        f = self._et()
        while self._pk() and self._pk()[0] == "OR":
            self._av(); f = Ou(f, self._et())
        return f

    def _et(self):
        f = self._non()
        while self._pk() and self._pk()[0] == "AND":
            self._av(); f = Et(f, self._non())
        return f

    def _non(self):
        if self._pk() and self._pk()[0] == "NOT":
            self._av(); return Non(self._non())
        return self._atome()

    def _atome(self):
        t = self._pk()
        if t is None:
            raise ValueError("Formule incomplète : un opérande est attendu à la fin.")
        typ, val, pos = t
        if typ == "LP":
            self._av()
            if self._pk() and self._pk()[0] == "RP":
                raise ValueError(f"Parenthèses vides (position {pos + 1}).")
            f = self._equiv()
            if not self._pk() or self._pk()[0] != "RP":
                raise ValueError(f"Parenthèse fermante manquante (ouverte en position {pos + 1}).")
            self._av()
            return f
        if typ == "TRUE":
            self._av(); return VRAI
        if typ == "FALSE":
            self._av(); return FAUX
        if typ == "ID":
            self._av()
            if val[0].isdigit():
                raise ValueError(f"Nom de symbole invalide « {val} » (ne doit pas commencer par un chiffre).")
            if self._pk() and self._pk()[0] == "LP":
                if not val[0].isupper():
                    raise ValueError(f"« {val} » est suivi de « ( » : un prédicat doit commencer par une "
                                     f"majuscule (sinon il manque un connecteur, position {self._pk()[2] + 1}).")
                return Var(val + "(" + ",".join(self._arguments(val)) + ")")
            return Var(val)
        raise ValueError(f"Opérande manquant avant « {val} » (position {pos + 1}).")
    
    # handles (a, b, c): parse first, then repeatedly , + term, then require ).
    def _arguments(self, nom):
        """Lit « ( t1, t2, ... ) » après un prédicat ; renvoie la liste des termes."""
        self._av()                           # consomme « ( »
        termes = [self._terme(nom)]
        while self._pk() and self._pk()[0] == "COMMA":
            self._av(); termes.append(self._terme(nom))
        if not self._pk() or self._pk()[0] != "RP":
            raise ValueError(f"Parenthèse fermante manquante dans les arguments de « {nom} ».")
        self._av()
        return termes

    # allows nested functional terms like P(f(x)) — if after the term there's (, recurse.
    def _terme(self, nom):
        t = self._pk()
        if t is None or t[0] != "ID":
            raise ValueError(f"Argument attendu dans « {nom}(...) ».")
        self._av()
        if self._pk() and self._pk()[0] == "LP":      # terme fonctionnel f(x)
            return t[1] + "(" + ",".join(self._arguments(t[1])) + ")"
        return t[1]

# lire_defaut uses lire_formule three times (prereq, each justification, consequent). Theorie.ajouter_formule uses lire_formule. The GUI never parses anything itself — it calls lire_formule via theorie.ajouter_formule. That's the "interface does no logic" rule in action.
def lire_formule(texte):
    """Texte -> formule. Lève ValueError (message en français) si la syntaxe est incorrecte."""
    if not isinstance(texte, str):
        raise ValueError("La formule doit être une chaîne de caractères.")
    return _Parseur(_tokeniser(texte)).analyser()


# ----------------------------------------------------------------------------
# Affichage
# ----------------------------------------------------------------------------
_PREC = {"equiv": 1, "imp": 2, "ou": 3, "et": 4, "non": 5}
SYM_UNICODE = {"non": "¬", "et": "∧", "ou": "∨", "imp": "→", "equiv": "↔",
               "vrai": "Vrai", "faux": "Faux"}
SYM_ASCII = {"non": "~", "et": "&", "ou": "|", "imp": "->", "equiv": "<->",
             "vrai": "true", "faux": "false"}

# Its job is to convert the logical formula (tree) back into readable text, while respecting operator priority and parentheses.
def _ecrire(f, S, prec_parent=0):
    op = f[0]
    # If the formula is a variable, simply return its name.
    if op == "var":
        return f[1]
    # Returns the corresponding symbol from dictionary S.
    if op in ("vrai", "faux"):
        return S[op]
    if op == "non":
        return S["non"] + _ecrire(f[1], S, 5)
    # Gets the priority of the current operator from _PREC.
    p = _PREC[op]
    #Implication is right-associative.
    if op == "imp":                          # associatif à droite
        gauche, droite = _ecrire(f[1], S, p + 1), _ecrire(f[2], S, p)
    else:                                    # associatif à gauche
        gauche, droite = _ecrire(f[1], S, p), _ecrire(f[2], S, p + 1)
    # Construct the final expression
    s = gauche + " " + S[op] + " " + droite
    # Decide whether to add parentheses
    return "(" + s + ")" if p < prec_parent else s


def afficher_formule(f):
    """Formule -> chaîne avec les symboles ¬ ∧ ∨ → ↔ (parenthèses minimales)."""
    return _ecrire(f, SYM_UNICODE)


def ecrire_formule(f):
    """Formule -> chaîne en syntaxe de saisie ASCII (relisible par lire_formule) ; sert à la sauvegarde."""
    return _ecrire(f, SYM_ASCII)


# ----------------------------------------------------------------------------
# Variables et évaluation
# ----------------------------------------------------------------------------
# Recursively walk the tuple tree, collecting all atom names into a set acc
def _atomes(f, acc):
    if f[0] == "var":
        acc.add(f[1])
    elif f[0] != "vrai" and f[0] != "faux":
        for sous in f[1:]:
            _atomes(sous, acc)


def variables(formules):
    """Liste triée des variables / propositions / prédicats apparaissant dans les formules
    (accepte une formule seule ou un itérable de formules)."""
    if isinstance(formules, tuple) and formules and isinstance(formules[0], str):
        formules = [formules]
    acc = set()
    for f in formules:
        _atomes(f, acc)
    return sorted(acc)


def evaluer(f, valuation):
    """Valeur de vérité de f sous une valuation {atome: bool} (atome absent = faux)."""
    op = f[0]
    #  missing atoms default to False
    if op == "var": return bool(valuation.get(f[1], False))
    if op == "vrai": return True
    if op == "faux": return False
    if op == "non": return not evaluer(f[1], valuation)
    a, b = evaluer(f[1], valuation), evaluer(f[2], valuation)
    if op == "et": return a and b
    if op == "ou": return a or b
    if op == "imp": return (not a) or b
    return a == b                            # equiv
