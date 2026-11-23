"""
interface.py -- Interface graphique minimaliste (thème clair).

RÈGLE DE L'ÉNONCÉ : l'interface ne fait AUCUN calcul logique. Elle lit ce que l'utilisateur a saisi,
appelle les fonctions des modules (defauts, raisonnement, extensions) et affiche leurs résultats.

Disposition : barre d'outils en haut, deux colonnes (gauche 40 % : la théorie W / D ;
droite 60 % : actions et résultats), barre d'état en bas.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from defauts import Theorie, lister_exemples
from formules import afficher_formule
from raisonnement import rapport_coherence
from extensions import (rapport_extensions, repondre_consequence,
                        appliquer_ordre, toutes_permutations, rapport_ordre)

# ═══════════════════════════════════════════════════════════════════════════
# Palette très sobre
# ═══════════════════════════════════════════════════════════════════════════
BG       = "#ffffff"   # fond
PANEL    = "#f4f6f8"   # panneaux
TEXT     = "#333333"   # texte
MUTED    = "#8a929b"   # texte secondaire
BORDER   = "#d5d9de"   # bordures discrètes
ACCENT   = "#005b9f"   # bleu du bouton principal
ACCENT_H = "#0a70bd"   # bleu au survol
LIST_BG  = "#fafafa"   # fond des listes
RES_BG   = "#f8f9fa"   # fond des résultats
ERR_BG, ERR_FG = "#fde8e8", "#b3261e"

FONT_UI   = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 11)

PAD = 15


class Application:
    def __init__(self, racine):
        self.racine = racine
        self.theorie = Theorie()
        self.fichier = None

        racine.title("Logique des défauts")
        racine.geometry("1180x720")
        racine.minsize(900, 560)
        racine.configure(bg=BG)

        self._style()
        self._construire()
        self._rafraichir()
        self._statut("Prêt")

    # ── style ──────────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self.racine)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass

        s.configure(".", background=BG, foreground=TEXT, font=FONT_UI, borderwidth=0)
        s.configure("TFrame", background=BG)
        s.configure("Panel.TFrame", background=PANEL)
        s.configure("TLabel", background=BG, foreground=TEXT)
        s.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
        s.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        s.configure("Status.TLabel", background=PANEL, foreground=MUTED, padding=(PAD, 6))

        s.configure("TLabelframe", background=BG, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, borderwidth=1, relief="solid")
        s.configure("TLabelframe.Label", background=BG, foreground=TEXT, font=FONT_BOLD)

        s.configure("TButton", background=PANEL, foreground=TEXT, padding=(12, 6),
                    bordercolor=BORDER, lightcolor=PANEL, darkcolor=PANEL, borderwidth=1)
        s.map("TButton", background=[("active", "#e8ecf0"), ("pressed", "#dde2e7")])

        s.configure("Toolbar.TButton", background=BG, padding=(10, 6), borderwidth=0)
        s.map("Toolbar.TButton", background=[("active", PANEL)])
        s.configure("Toolbar.TMenubutton", background=BG, foreground=TEXT,
                    padding=(10, 6), borderwidth=0, arrowcolor=MUTED)
        s.map("Toolbar.TMenubutton", background=[("active", PANEL)])

        s.configure("Accent.TButton", background=ACCENT, foreground="#ffffff",
                    padding=(16, 10), font=FONT_BOLD, bordercolor=ACCENT,
                    lightcolor=ACCENT, darkcolor=ACCENT)
        s.map("Accent.TButton",
              background=[("active", ACCENT_H), ("pressed", ACCENT_H)],
              foreground=[("active", "#ffffff")])

        s.configure("TEntry", fieldbackground="#ffffff", foreground=TEXT, padding=5,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, borderwidth=1)
        s.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])

        s.configure("TCombobox", fieldbackground="#ffffff", background=PANEL,
                    foreground=TEXT, padding=5, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, arrowcolor=MUTED)
        s.map("TCombobox", fieldbackground=[("readonly", "#ffffff")])

        s.configure("TSeparator", background=BORDER)
        s.configure("Vertical.TScrollbar", background=PANEL, troughcolor=BG,
                    bordercolor=BG, arrowcolor=MUTED)

    # ── construction ───────────────────────────────────────────────────────
    def _construire(self):
        root = self.racine
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        self._barre_outils(root)
        ttk.Separator(root, orient="horizontal").grid(row=0, column=0, sticky="sew")

        main = ttk.Frame(root, padding=PAD)
        main.grid(row=1, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=2, uniform="col")   # 40 %
        main.columnconfigure(1, weight=3, uniform="col")   # 60 %

        self._colonne_gauche(main)
        self._colonne_droite(main)

        self.lbl_statut = ttk.Label(root, text="Prêt", style="Status.TLabel", anchor="w")
        self.lbl_statut.grid(row=2, column=0, sticky="ew")

    def _barre_outils(self, root):
        bar = ttk.Frame(root, padding=(PAD - 5, 8))
        bar.grid(row=0, column=0, sticky="ew")

        ttk.Button(bar, text="Nouveau", style="Toolbar.TButton",
                   command=self.nouveau).pack(side="left", padx=5)
        ttk.Button(bar, text="Ouvrir", style="Toolbar.TButton",
                   command=self.ouvrir).pack(side="left", padx=5)
        ttk.Button(bar, text="Enregistrer", style="Toolbar.TButton",
                   command=self.enregistrer).pack(side="left", padx=5)

        mb = ttk.Menubutton(bar, text="Exemples ▾", style="Toolbar.TMenubutton")
        menu = tk.Menu(mb, tearoff=0, bg=BG, fg=TEXT, activebackground=PANEL,
                       activeforeground=TEXT, relief="flat", font=FONT_UI)
        for nom, chemin in lister_exemples():
            menu.add_command(label=nom, command=lambda c=chemin: self.charger_fichier(c))
        mb["menu"] = menu
        mb.pack(side="left", padx=5)

    # ── helpers de widgets ─────────────────────────────────────────────────
    @staticmethod
    def _liste(parent, hauteur=5):
        """Listbox à fond gris très clair, bordure discrète et barre de défilement."""
        cadre = tk.Frame(parent, bg=LIST_BG, highlightbackground=BORDER, highlightthickness=1)
        cadre.rowconfigure(0, weight=1)
        cadre.columnconfigure(0, weight=1)
        lb = tk.Listbox(cadre, height=hauteur, selectmode="extended", exportselection=False,
                        font=FONT_MONO, bg=LIST_BG, fg=TEXT, relief="flat", borderwidth=0,
                        highlightthickness=0, activestyle="none",
                        selectbackground=ACCENT, selectforeground="#ffffff")
        sb = ttk.Scrollbar(cadre, command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        sb.grid(row=0, column=1, sticky="ns")
        return cadre, lb

    # ── colonne gauche : la théorie ────────────────────────────────────────
    def _colonne_gauche(self, parent):
        gauche = ttk.Frame(parent)
        gauche.grid(row=0, column=0, sticky="nsew", padx=(0, PAD // 2))
        gauche.columnconfigure(0, weight=1)
        gauche.rowconfigure(0, weight=1)
        gauche.rowconfigure(1, weight=1)

        # ── Monde W ──
        cw = ttk.LabelFrame(gauche, text=" Monde W ", padding=PAD)
        cw.grid(row=0, column=0, sticky="nsew", pady=(0, PAD))
        cw.columnconfigure(0, weight=1)
        cw.rowconfigure(2, weight=1)

        ligne = ttk.Frame(cw)
        ligne.grid(row=0, column=0, sticky="ew")
        ligne.columnconfigure(0, weight=1)
        self.e_formule = ttk.Entry(ligne)
        self.e_formule.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.e_formule.bind("<Return>", lambda e: self.ajouter_formule())
        ttk.Button(ligne, text="Ajouter", command=self.ajouter_formule).grid(row=0, column=1)

        ttk.Label(cw, text="Exemple :  p -> ~v", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 8))

        cadre, self.l_formules = self._liste(cw)
        cadre.grid(row=2, column=0, sticky="nsew")

        bas = ttk.Frame(cw)
        bas.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(bas, text="Supprimer", command=self.supprimer_formule).pack(side="left")
        ttk.Button(bas, text="Vérifier la cohérence",
                   command=self.verifier_coherence).pack(side="left", padx=8)

        # ── Défauts D ──
        cd = ttk.LabelFrame(gauche, text=" Défauts D ", padding=PAD)
        cd.grid(row=1, column=0, sticky="nsew")
        cd.columnconfigure(0, weight=1)
        cd.rowconfigure(2, weight=1)

        form = ttk.Frame(cd)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        self.e_pre = self._champ(form, 0, "Prérequis")
        self.e_just = self._champ(form, 1, "Justifications")
        self.e_cons = self._champ(form, 2, "Conséquent")
        self.e_cons.bind("<Return>", lambda e: self.ajouter_defaut())

        ttk.Label(cd, text="Forme :  α : β₁, β₂ / γ", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 8))

        cadre_d, self.l_defauts = self._liste(cd)
        cadre_d.grid(row=2, column=0, sticky="nsew")

        bas_d = ttk.Frame(cd)
        bas_d.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(bas_d, text="Ajouter", command=self.ajouter_defaut).pack(side="left")
        ttk.Button(bas_d, text="Supprimer", command=self.supprimer_defaut).pack(side="left", padx=8)

    @staticmethod
    def _champ(parent, r, libelle):
        ttk.Label(parent, text=libelle).grid(row=r, column=0, sticky="w", padx=(0, 12), pady=4)
        e = ttk.Entry(parent)
        e.grid(row=r, column=1, sticky="ew", pady=4)
        return e

    # ── colonne droite : actions + résultats ───────────────────────────────
    def _colonne_droite(self, parent):
        droite = ttk.Frame(parent)
        droite.grid(row=0, column=1, sticky="nsew", padx=(PAD // 2, 0))
        droite.columnconfigure(0, weight=1)
        droite.rowconfigure(1, weight=1)

        # zone d'actions
        act = ttk.Frame(droite, style="Panel.TFrame", padding=PAD)
        act.grid(row=0, column=0, sticky="ew", pady=(0, PAD))
        act.columnconfigure(0, weight=1)
        act.columnconfigure(1, weight=1)

        ttk.Button(act, text="Générer les extensions", style="Accent.TButton",
                   command=self.generer).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(act, text="Simuler un ordre", command=self.simuler_ordre).grid(
            row=0, column=1, sticky="ew", padx=(8, 0), ipady=4)

        phi = ttk.Frame(act, style="Panel.TFrame")
        phi.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(PAD, 0))
        phi.columnconfigure(1, weight=1)
        ttk.Label(phi, text="φ", style="Panel.TLabel", font=FONT_BOLD).grid(
            row=0, column=0, padx=(0, 8))
        self.e_phi = ttk.Entry(phi)
        self.e_phi.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.e_phi.bind("<Return>", lambda e: self.consequence("sceptique"))
        ttk.Button(phi, text="Sceptique ?",
                   command=lambda: self.consequence("sceptique")).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(phi, text="Crédule ?",
                   command=lambda: self.consequence("credule")).grid(row=0, column=3)

        # résultats : grande zone de texte
        res = ttk.LabelFrame(droite, text=" Résultats ", padding=PAD)
        res.grid(row=1, column=0, sticky="nsew")
        res.columnconfigure(0, weight=1)
        res.rowconfigure(0, weight=1)

        cadre = tk.Frame(res, bg=RES_BG, highlightbackground=BORDER, highlightthickness=1)
        cadre.grid(row=0, column=0, sticky="nsew")
        cadre.rowconfigure(0, weight=1)
        cadre.columnconfigure(0, weight=1)

        self.t_res = tk.Text(cadre, wrap="word", font=FONT_MONO, state="disabled",
                             bg=RES_BG, fg=TEXT, insertbackground=TEXT, relief="flat",
                             borderwidth=0, padx=14, pady=12, spacing3=3,
                             selectbackground=ACCENT, selectforeground="#ffffff")
        sb = ttk.Scrollbar(cadre, command=self.t_res.yview)
        self.t_res.configure(yscrollcommand=sb.set)
        self.t_res.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.t_res.tag_configure("erreur", foreground=ERR_FG)

    # ── helpers d'affichage ────────────────────────────────────────────────
    def _statut(self, msg):
        self.lbl_statut.configure(text=msg)

    def _afficher(self, texte, erreur=False):
        self.t_res.configure(state="normal")
        self.t_res.delete("1.0", "end")
        self.t_res.insert("end", texte, "erreur" if erreur else ())
        self.t_res.configure(state="disabled")

    def _rafraichir(self):
        self.l_formules.delete(0, "end")
        for ligne in self.theorie.lignes_formules():
            self.l_formules.insert("end", ligne)
        self.l_defauts.delete(0, "end")
        for ligne in self.theorie.lignes_defauts():
            self.l_defauts.insert("end", ligne)
        titre = "Logique des défauts"
        if self.fichier or self.theorie.nom:
            titre += "  —  " + (os.path.basename(self.fichier) if self.fichier
                                else self.theorie.nom)
        self.racine.title(titre)

    # ── fichiers ───────────────────────────────────────────────────────────
    def nouveau(self):
        if (self.theorie.W or self.theorie.D) and not messagebox.askyesno(
                "Nouveau", "Effacer la théorie courante ?"):
            return
        self.theorie.vider()
        self.fichier = None
        self._rafraichir()
        self._afficher("")
        self._statut("Nouvelle théorie vide")

    def ouvrir(self):
        chemin = filedialog.askopenfilename(
            title="Ouvrir une théorie",
            filetypes=[("Théorie JSON", "*.json"), ("Tous", "*.*")])
        if chemin:
            self.charger_fichier(chemin)

    def charger_fichier(self, chemin):
        try:
            nouvelle = Theorie.charger(chemin)
        except (OSError, ValueError) as e:
            messagebox.showerror("Ouvrir", f"Impossible de charger le fichier :\n{e}")
            return
        self.theorie.remplacer_par(nouvelle)
        self.fichier = chemin
        self._rafraichir()
        self._afficher(self.theorie.description or
                       f"Théorie chargée : {os.path.basename(chemin)}")
        self._statut(f"Théorie chargée — {len(self.theorie.W)} formule(s), "
                     f"{len(self.theorie.D)} défaut(s)")

    def enregistrer(self):
        chemin = filedialog.asksaveasfilename(
            title="Enregistrer la théorie", defaultextension=".json",
            filetypes=[("Théorie JSON", "*.json")])
        if not chemin:
            return
        try:
            self.theorie.sauvegarder(chemin)
        except OSError as e:
            messagebox.showerror("Enregistrer", f"Échec de l'enregistrement :\n{e}")
            return
        self.fichier = chemin
        self._rafraichir()
        self._afficher(f"Théorie enregistrée dans {chemin}")
        self._statut(f"Enregistré : {os.path.basename(chemin)}")

    # ── édition de W ───────────────────────────────────────────────────────
    def ajouter_formule(self):
        try:
            self.theorie.ajouter_formule(self.e_formule.get())
        except ValueError as e:
            messagebox.showerror("Formule invalide", str(e))
            return
        self.e_formule.delete(0, "end")
        self._rafraichir()
        self._statut(f"Formule ajoutée — W contient {len(self.theorie.W)} formule(s)")

    def supprimer_formule(self):
        sel = list(self.l_formules.curselection())
        if not sel:
            messagebox.showinfo("Supprimer", "Sélectionnez d'abord une formule.")
            return
        for i in reversed(sel):
            self.theorie.supprimer_formule(i)
        self._rafraichir()
        self._statut(f"Formule(s) supprimée(s) — W : {len(self.theorie.W)}")

    def verifier_coherence(self):
        coherent, texte, a_surligner = rapport_coherence(self.theorie.W)
        self._rafraichir()
        for i in a_surligner:
            self.l_formules.itemconfigure(i, background=ERR_BG, foreground=ERR_FG)
        self._afficher(texte, erreur=not coherent)
        self._statut("W est cohérent" if coherent
                     else "W est INCOHÉRENT — formules fautives surlignées")

    # ── édition de D ───────────────────────────────────────────────────────
    def ajouter_defaut(self):
        texte = f"{self.e_pre.get()} : {self.e_just.get()} / {self.e_cons.get()}"
        try:
            _, avert = self.theorie.ajouter_defaut(texte)
        except ValueError as e:
            messagebox.showerror("Défaut invalide", str(e))
            return
        for c in (self.e_pre, self.e_just, self.e_cons):
            c.delete(0, "end")
        self._rafraichir()
        self._statut(f"Défaut ajouté — D contient {len(self.theorie.D)} défaut(s)")
        if avert:
            messagebox.showwarning("Avertissement", "\n".join(avert))

    def supprimer_defaut(self):
        sel = list(self.l_defauts.curselection())
        if not sel:
            messagebox.showinfo("Supprimer", "Sélectionnez d'abord un défaut.")
            return
        for i in reversed(sel):
            self.theorie.supprimer_defaut(i)
        self._rafraichir()
        self._statut(f"Défaut(s) supprimé(s) — D : {len(self.theorie.D)}")

    # ── raisonnement ───────────────────────────────────────────────────────
    def generer(self):
        texte = rapport_extensions(self.theorie)
        self._afficher(texte)
        if texte.startswith("Aucune"):
            self._statut("Aucune extension générée")
        else:
            premiere = texte.split("\n", 1)[0].rstrip(":")
            self._statut(f"{premiere} générée(s)" if premiere.startswith("1 ")
                         else f"{premiere} générées")

    def consequence(self, mode):
        try:
            texte = repondre_consequence(self.theorie, self.e_phi.get(), mode)
        except ValueError as e:
            messagebox.showerror("Formule φ invalide", str(e))
            return
        self._afficher(texte)
        self._statut(f"Conséquence {mode} évaluée")

    # ── dialogue : simuler un ordre ────────────────────────────────────────
    def simuler_ordre(self):
        if not self.theorie.D:
            messagebox.showinfo("Simuler un ordre", "Aucun défaut dans D.")
            return

        dlg = tk.Toplevel(self.racine)
        dlg.title("Simuler un ordre")
        dlg.geometry("560x430")
        dlg.minsize(440, 360)
        dlg.configure(bg=BG)
        dlg.transient(self.racine)
        dlg.grab_set()

        cont = ttk.Frame(dlg, padding=20)
        cont.pack(fill="both", expand=True)
        cont.columnconfigure(0, weight=1)
        cont.rowconfigure(1, weight=1)

        ttk.Label(cont, text="Défauts à ordonner", font=FONT_BOLD).grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        cadre, lb = self._liste(cont)
        cadre.grid(row=1, column=0, sticky="nsew")
        for ligne in self.theorie.lignes_defauts():
            lb.insert("end", ligne)

        ttk.Label(cont, text="Ordre d'application  (✔ extension, ✘ échec)",
                  font=FONT_BOLD).grid(row=2, column=0, sticky="w", pady=(15, 8))
        combo = ttk.Combobox(cont, state="readonly")
        combo.grid(row=3, column=0, sticky="ew")

        compte = ttk.Label(cont, text="", style="Muted.TLabel")
        compte.grid(row=4, column=0, sticky="w", pady=(6, 15))

        cache = {"sel": None, "perms": []}

        def _maj(_e=None):
            sel = tuple(sorted(lb.curselection()))
            if sel == cache["sel"]:
                return
            cache["sel"] = sel
            perms = toutes_permutations(self.theorie, sel)
            cache["perms"] = perms
            labels = []
            for perm, res in perms:
                nom = (" → ".join(Theorie.nom_defaut(i) for i in perm)
                       if perm else "(ordre vide)")
                labels.append(nom + ("  ✔" if res.extension is not None else "  ✘"))
            combo["values"] = labels
            if labels:
                combo.current(0)
            else:
                combo.set("")
            k = sum(1 for _, r in perms if r.extension is not None)
            compte.configure(text=f"{k} ordre(s) sur {len(perms)} produisent une extension.")

        lb.bind("<<ListboxSelect>>", _maj)
        _maj()

        def _lancer():
            idx = combo.current()
            if idx < 0 or idx >= len(cache["perms"]):
                messagebox.showinfo("Simuler", "Choisissez un ordre dans la liste.")
                return
            ordre, _ = cache["perms"][idx]
            res = appliquer_ordre(self.theorie, ordre)
            self._afficher(rapport_ordre(self.theorie, res))
            self._statut("Simulation terminée — " +
                         ("extension obtenue" if res.extension is not None
                          else "pas d'extension"))
            dlg.destroy()

        bas = ttk.Frame(cont)
        bas.grid(row=5, column=0, sticky="ew")
        ttk.Button(bas, text="Simuler", style="Accent.TButton",
                   command=_lancer).pack(side="left")
        ttk.Button(bas, text="Annuler", command=dlg.destroy).pack(side="left", padx=10)


def lancer():
    racine = tk.Tk()
    Application(racine)
    racine.mainloop()
