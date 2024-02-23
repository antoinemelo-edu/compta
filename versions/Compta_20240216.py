# Antoine MELO :: COMPTA :: v0.6 :: 15 février 2024

import tkinter, os, sys, shutil, webbrowser
from tkinter import Text, ttk, messagebox, scrolledtext
from tkinter.scrolledtext import ScrolledText
from itertools import zip_longest
from datetime import datetime, timedelta

tk = tkinter
python_executable = sys.executable

verifier_mandat_vide = ""
label_bienvenue = None
bouton_exercice = None

'''
global f_journaliser, compte_combobox, f_operations_compte,
       nom_entry, entreprise_entry, entreprise_entry_value, dossier_mandat
'''

def ouvrir_pdf():
    chemin_pdf = os.path.join(os.getcwd(), "config", "manuel.pdf")
    webbrowser.open(chemin_pdf)

def lancer_soldes_initiaux():
    if os.path.exists(f"{dossier_mandat}/plan_comptable.txt") and os.path.exists(f"{dossier_mandat}/soldes_initiaux.txt"):
        pc_tri = tri_comptes(f"{dossier_mandat}/plan_comptable.txt")
        lancer_interface(pc_tri, f"{dossier_mandat}/soldes_initiaux.txt")
    else:
        messagebox.showwarning("Problème de configuration", "Sauvegarder votre mandat\n(Configuration, en haut à gauche)")

def lancer_journaliser():
    if os.path.exists(f"{dossier_mandat}/plan_comptable.txt") and os.path.exists(f"{dossier_mandat}/journal.txt"):
        comptes = lire_pc(f"{dossier_mandat}/plan_comptable.txt")
        lancer_interface_ajout_entree(f"{dossier_mandat}/journal.txt", comptes)
    else:
        messagebox.showwarning("Problème de configuration", "Sauvegarder votre mandat\n(Configuration, en haut à gauche)")

def lancer_journal():
    if os.path.exists(f"{dossier_mandat}/journal.txt"):
        afficher_journal(f"{dossier_mandat}/journal.txt")
    else:
        messagebox.showwarning("Problème de configuration", "Sauvegarder votre mandat\n(Configuration, en haut à gauche)")

def lancer_grand_livre():
    if os.path.exists(f"{dossier_mandat}/plan_comptable.txt") and os.path.exists(f"{dossier_mandat}/soldes_initiaux.txt") and os.path.exists(f"{dossier_mandat}/journal.txt"):
        accounts = read_plan_comptable(f"{dossier_mandat}/plan_comptable.txt")
        initial_balances = read_initial_balances(f"{dossier_mandat}/soldes_initiaux.txt")
        account_totals, final_balances = process_journal(f"{dossier_mandat}/journal.txt", accounts, initial_balances)
        afficher_grand_livre(accounts, initial_balances, account_totals, final_balances)
    else:
        messagebox.showwarning("Problème de configuration", "Sauvegarder votre mandat\n(Configuration, en haut à gauche)")

# SOLDES #########################################################################

def tri_comptes(pc):
    with open(pc, 'r', encoding='utf-8') as file:
        comptes = [line.strip().split(' - ') for line in file if line.startswith(('1', '2'))]
        return sorted(comptes, key=lambda x: int(x[0]))

def importer_donnees(entries, si):
    with open(si, 'r', encoding='utf-8') as file:
        for ligne in file:
            compte, montant = ligne.strip().split(' = ')
            if compte in entries:
                entries[compte].delete(0, tk.END)
                entries[compte].insert(0, montant)

def enregistrer_et_quitter(entries, f_quit, si):
    balances = {id_compte: entry.get() for id_compte, entry in entries.items()}
    with open(si, 'w', encoding='utf-8') as file:
        for id_compte, balance in sorted(balances.items(), key=lambda x: int(x[0])):
            balance = float(balance) if balance else 0.0
            file.write(f"{id_compte} = {balance}\n")
    f_quit.destroy()

def lancer_interface(pc_tri, si):
    f_soldes = tk.Tk()
    f_soldes.title("Soldes initiaux")
    entries = {}
    for index, (id_compte, nom_compte) in enumerate(pc_tri):
        label = tk.Label(f_soldes, text=f"{nom_compte} ({id_compte}):", anchor='w')
        entry = tk.Entry(f_soldes)
        label.grid(row=index, column=0, sticky='w', padx=5, pady=2)
        entry.grid(row=index, column=1, sticky='w', padx=5, pady=2)
        entries[id_compte] = entry
    
    nombre_lignes = len(pc_tri)
    if len(pc_tri) == 0:
        label = tk.Label(f_soldes, text="Aucun compte à afficher: les créer sous Configuration.", fg="red", anchor='n')
        label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=2)  # Utiliser columnspan pour centrer le message si nécessaire
    else:
        bouton_importer = tk.Button(f_soldes, text="Soldes actuels", command=lambda: importer_donnees(entries, si))
        bouton_importer.grid(row=nombre_lignes, column=0, padx=5, pady=10)

        bouton_enregistrer = tk.Button(f_soldes, text="Sauvegarder", command=lambda: enregistrer_et_quitter(entries, f_soldes, si))
        bouton_enregistrer.grid(row=nombre_lignes, column=1, pady=10)

    f_soldes.mainloop()

# JOURNALISER #########################################################################

def lire_pc(fichier):
    comptes_dict = {}
    with open(fichier, 'r', encoding='utf-8') as file:
        for line in file.readlines():
            parts = line.strip().split(' - ')
            if len(parts) == 2:
                numero_compte, intitule = parts
                comptes_dict[numero_compte] = intitule
    return comptes_dict

def compter_enregistrements(journal_path):
    try:
        with open(journal_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            return len(lines) + 1  # Ajoute 1 pour le prochain numéro de pièce
    except FileNotFoundError:
        return 1  # Si le fichier n'existe pas, le premier numéro sera 1

def numero_compte_existe(numero, comptes_dict):
    return numero in comptes_dict

def ajouter_entree(journal_path, debit_account, credit_account, label, amount_entry, comptes_dict):
    entry_number = compter_enregistrements(journal_path)  # Obtenir le numéro de pièce
    debit_selection = debit_account.get()
    credit_selection = credit_account.get()

    debit_parts = debit_selection.split(" - ")
    credit_parts = credit_selection.split(" - ")

    if len(debit_parts) != 2 or len(credit_parts) != 2:
        messagebox.showerror("Erreur", "Veuillez sélectionner des comptes valides.")
        return

    debit_numero, debit_intitule = debit_parts
    credit_numero, credit_intitule = credit_parts

    if not numero_compte_existe(debit_numero, comptes_dict) or not numero_compte_existe(credit_numero, comptes_dict):
        messagebox.showerror("Erreur", "Certains numéros de compte n'existent pas dans le plan comptable.")
        return

    try:
        amount = float(amount_entry.get())
    except ValueError:
        messagebox.showerror("Erreur", "Montant invalide.")
        return

    with open(journal_path, 'a', encoding='utf-8') as file:
        file.write(f"{entry_number}::{debit_numero}::{credit_numero}::{label.get()}::{amount}\n")
    # messagebox.showinfo("Succès", f"L'opération {entry_number} est enregistrée.")

    debit_account.set("")  # Réinitialiser la sélection du compte au débit
    credit_account.set("")  # Réinitialiser la sélection du compte au crédit
    label.delete(0, "end")  # Effacer le libellé
    amount_entry.delete(0, "end")  # Effacer le montant

    def afficher_message_temporaire(message):
        message_label = tk.Label(f_journaliser, text=message, fg="green")
        message_label.grid(row=1, column=1, columnspan=2, sticky="ew")

        def effacer_message():
            message_label.destroy()
        
    afficher_message_temporaire(f"Opération # {entry_number} enregistrée au journal")

def lancer_interface_ajout_entree(journal_path, comptes_dict):
    def update_combobox(event, combobox, values):
        # Récupère le texte actuellement saisi dans le combobox
        current_text = event.widget.get()
        # Filtre les options basées sur le texte saisi
        filtered_options = [option for option in values if current_text.lower() in option.lower()]
        # Met à jour les valeurs du combobox avec les options filtrées, en gardant le texte actuel
        combobox['values'] = filtered_options if filtered_options else values
        combobox.set(current_text)
        combobox.icursor(tk.END)

    global f_journaliser
    f_journaliser = tk.Tk()
    f_journaliser.title("Ajouter une entrée au journal")

    # Tri des comptes par numéro de compte
    comptes_tries = [f"{numero} - {intitule}" for numero, intitule in sorted(comptes_dict.items())]

    # Compte au débit
    frame_debit = ttk.Frame(f_journaliser)
    frame_debit.grid(row=0, column=0, padx=5, pady=5)
    tk.Label(frame_debit, text="Compte au débit:").pack(side="top", anchor="w")
    debit_account = ttk.Combobox(frame_debit, values=comptes_tries)
    debit_account.pack(side="bottom")
    debit_account.bind('<KeyRelease>', lambda event: update_combobox(event, debit_account, comptes_tries))

    # Compte au crédit
    frame_credit = ttk.Frame(f_journaliser)
    frame_credit.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(frame_credit, text="Compte au crédit:").pack(side="top", anchor="w")
    credit_account = ttk.Combobox(frame_credit, values=comptes_tries)
    credit_account.pack(side="bottom")
    credit_account.bind('<KeyRelease>', lambda event: update_combobox(event, credit_account, comptes_tries))

    # Libellé
    frame_label = ttk.Frame(f_journaliser)
    frame_label.grid(row=0, column=2, padx=5, pady=5)
    tk.Label(frame_label, text="Libellé:").pack(side="top", anchor="w")
    label = tk.Entry(frame_label)
    label.pack(side="bottom")

    # Montant
    frame_amount = ttk.Frame(f_journaliser)
    frame_amount.grid(row=0, column=3, padx=5, pady=5)
    tk.Label(frame_amount, text="Montant:").pack(side="top", anchor="w")
    amount_entry = tk.Entry(frame_amount, justify=tk.RIGHT)
    amount_entry.pack(side="bottom")

    bouton_afficher_journal = tk.Button(f_journaliser, text="Journal", command=lancer_journal)
    bouton_afficher_journal.grid(row=1, column=0, padx=10, pady=5, sticky='w')

    # Bouton Ajouter
    bouton_ajouter = tk.Button(f_journaliser, text="Ajouter", command=lambda: ajouter_entree(journal_path, debit_account, credit_account, label, amount_entry, comptes_dict))
    bouton_ajouter.grid(row=1, column=3, columnspan=4, pady=10)

    f_journaliser.mainloop()

# COMPTES #########################################################################

def update_combobox(event, combobox, values):
    current_text = event.widget.get()
    filtered_options = [option for option in values if current_text.lower() in option.lower()]
    combobox['values'] = filtered_options if filtered_options else values
    combobox.set(current_text)
    combobox.icursor(tk.END)

def ouvrir_details_compte():
    compte_selectionne_entier = compte_combobox.get()
    comptes_dict = lire_pc(f"{dossier_mandat}/plan_comptable.txt")  # Recharger les données
    if any(compte_selectionne_entier.startswith(f"{numero} -") for numero in comptes_dict):
        compte_selectionne = compte_selectionne_entier.split(" - ")[0]
        f_details_compte = tk.Toplevel()
        f_details_compte.title(f"Extrait de compte")

        # Utiliser un Frame pour contenir le label et le Text widget
        content_frame = tk.Frame(f_details_compte)
        content_frame.grid(row=0, column=0, sticky="ew")

        text_widget = tk.Text(content_frame, wrap='none', height=20, width=50)  # Définir une taille fixe pour le Text widget
        text_widget.grid(row=1, column=0, sticky="nsew")

        # Configuration pour que le content_frame utilise tout l'espace disponible
        f_details_compte.grid_rowconfigure(0, weight=1)
        f_details_compte.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        solde_initial = somme_debit = somme_credit = 0.0
        lignes_debit = []
        lignes_credit = []

        try:
            with open(f"{dossier_mandat}/soldes_initiaux.txt", 'r', encoding='utf-8') as soldes_file:
                for line in soldes_file:
                    compte, solde = line.strip().split(" = ")
                    if compte == compte_selectionne:
                        solde_initial = float(solde)
                        break
        except FileNotFoundError:
            text_widget.insert(tk.END, f"Le fichier des soldes initiaux n'a pas été trouvé.")

        if compte_selectionne.startswith('1'):
            lignes_debit.append(f"{' ':>2}Si) {str(solde_initial).rjust(10)}")
            somme_debit += solde_initial
        elif compte_selectionne.startswith('2'):
            lignes_credit.append(f"{str(solde_initial).rjust(8)} (Si")
            somme_credit += solde_initial

        try:
            with open(f"{dossier_mandat}/journal.txt", 'r', encoding='utf-8') as journal_file:
                for line in journal_file:
                    no_piece, debit, credit, _, montant = line.strip().split("::")
                    montant = float(montant)
                    if compte_selectionne in (debit, credit):
                        if compte_selectionne == debit:
                            lignes_debit.append(f"{no_piece.rjust(4)}) {str(montant).rjust(10)}")
                            somme_debit += montant
                        else:
                            lignes_credit.append(f"{str(montant).rjust(8)} ({no_piece}")
                            somme_credit += montant
        except FileNotFoundError:
            text_widget.insert(tk.END, f"Le fichier du journal n'a pas été trouvé.")

        # Ajout des lignes de débit et de crédit
        compte_selectionne_tronque = compte_selectionne_entier[:28]
        lo = 24 if len(compte_selectionne_entier) <= 24 else 30
        longueur_titre = lo - len(compte_selectionne_entier)
        longueur_titre = max(3, longueur_titre)
        titre = " "*longueur_titre
        text_widget.insert(tk.END, f"{titre}{compte_selectionne_tronque}\n")
        text_widget.insert(tk.END, "  ------------------------------\n")
        for ligne_debit, ligne_credit in zip_longest(lignes_debit, lignes_credit, fillvalue=" " * 18):
            text_widget.insert(tk.END, f"{ligne_debit.ljust(18)} | {ligne_credit}\n")

        # Ajout des totaux
        text_widget.insert(tk.END, "       ----------  |  ----------\n")
        ligne_totale = f"{str(somme_debit).rjust(16)}   |{str(somme_credit).rjust(10)}\n"
        text_widget.insert(tk.END, ligne_totale)

        dif = "Sf)" if compte_selectionne.startswith('1') or compte_selectionne.startswith('2') else "Vr)"

        difference = abs(somme_debit - somme_credit)
        ligne_difference = ""
        if somme_debit > somme_credit:
            ligne_difference = f"  {dif}{' ':>13} | {difference:>9}\n"
        else:
            ligne_difference = f"  {dif}{' ':>0} {difference:>9} {' ':>2}|\n"

        text_widget.insert(tk.END, ligne_difference)

        text_widget.tag_configure('left', justify='left')

        btn_frame = tk.Frame(f_details_compte)
        btn_frame.grid(row=1, column=0, sticky="ew")
        tk.Button(btn_frame, text="Nouvelle·s opération·s liée·s à ce compte", 
                  command=lambda: saisir_operations_compte(compte_selectionne_entier, f_details_compte, dossier_mandat)).pack(pady=5)
       
        hauteur_fenetre = min(len(text_widget.get(1.0, 'end').split('\n'))*20+30, 400)
        largeur_fenetre = 280
        f_details_compte.geometry(f"{largeur_fenetre}x{hauteur_fenetre}")
    else:
        messagebox.showerror("Erreur", "Ce compte n'existe pas dans le plan comptable.")

def selection_compte(f_compte, comptes_dict):
    frame_selection_compte = tk.Frame(f_compte)
    frame_selection_compte.grid(row=2, column=0, columnspan=2, sticky='w')

    bouton_afficher_details = tk.Button(frame_selection_compte, text="Extrait de compte --->", command=ouvrir_details_compte)
    bouton_afficher_details.pack(side="left", padx=(10, 50), pady=(5, 5))

    global compte_combobox
    comptes_tries = sorted([f"{numero} - {intitule}" for numero, intitule in comptes_dict.items()])
    compte_combobox = ttk.Combobox(frame_selection_compte, values=comptes_tries, width=25, state="readonly")
    compte_combobox.pack(side="left", padx=10)
    compte_combobox.bind('<KeyRelease>', lambda event: update_combobox(event, compte_combobox, comptes_tries))

    if comptes_tries:
        compte_combobox.set(comptes_tries[0])

def saisir_operations_compte(compte_info, fenetre_a_fermer, rep_mandat):
    fenetre_a_fermer.destroy()
    
    global f_operations_compte
    f_operations_compte = tk.Toplevel()

    # Configuration initiale pour utiliser grid
    f_operations_compte.grid_columnconfigure(1, weight=1)

    comptes_facture = modes_facture_tuple(f"{rep_mandat}/facture.txt")
    # True si comptes_facture correspond au compte en cours
    mode_facture = any(compte_info.startswith(element) for element in comptes_facture)

    if mode_facture:
        f_operations_compte.title("Factures ouvertes")
        rep_journal = f"{rep_mandat}"
        dossier_factures = f"{rep_mandat}/factures"
        compte_info_no = compte_info.split(" - ")[0]
        compte_info_text = compte_info.split(" - ")[1]
        afficher_ecritures_journal(f_operations_compte, rep_journal, dossier_factures, compte_info_text, compte_info_no)
        f_operations_compte.mainloop()
    else:
        f_operations_compte.title("Opérations")
        # Afficher les informations du compte
        label_montant = tk.Label(f_operations_compte, text="Montant au ...", font=("", 10, "bold"))
        label_montant.grid(row=0, column=0, sticky="w")

        label_compte_info = tk.Label(f_operations_compte, text=f"{compte_info}", font=("Courier", 12, "bold"))
        label_compte_info.grid(row=0, column=1, sticky="ew")

        # Variables pour les entrées
        montant_debit_var = tk.StringVar()
        montant_credit_var = tk.StringVar()
        libelle_var = tk.StringVar()
        compte_contrepartie_var = tk.StringVar()

        compte_numero = compte_info.split(" - ")[0]
        # Déterminer les signes à ajouter après les labels de débit et de crédit
        if compte_numero.startswith('2') or compte_numero.startswith('3'):
            label_debit_text = "· débit (- - / sortie ou dim.)"
            label_credit_text = "· crédit (++ / entrée ou augm.)"
        else:
            label_debit_text = "· débit (++ / entrée ou augm.)"
            label_credit_text = "· crédit (- - / sortie ou dim.)"

        # Utiliser ces textes pour les labels dans l'interface
        tk.Label(f_operations_compte, text=label_debit_text).grid(row=1, column=0, sticky="w")
        montant_debit_entry = tk.Entry(f_operations_compte, textvariable=montant_debit_var)
        montant_debit_entry.grid(row=1, column=1, sticky="ew")

        tk.Label(f_operations_compte, text=label_credit_text).grid(row=2, column=0, sticky="w")
        montant_credit_entry = tk.Entry(f_operations_compte, textvariable=montant_credit_var)
        montant_credit_entry.grid(row=2, column=1, sticky="ew")

        tk.Label(f_operations_compte, text="Libellé").grid(row=3, column=0, sticky="w")
        libelle_entry = tk.Entry(f_operations_compte, textvariable=libelle_var)
        libelle_entry.grid(row=3, column=1, sticky="ew")

        def update_combobox(event):
            current_text = compte_contrepartie.get()
            compte_info_num = compte_info.split(" - ")[0]
            filtered_options = [option for option in lire_plan_comptable(f"{dossier_mandat}/plan_comptable.txt") if current_text.lower() in option.lower() and not compte_info_num in option]
            compte_contrepartie['values'] = filtered_options if filtered_options else lire_plan_comptable(f"{dossier_mandat}/plan_comptable.txt")
            compte_contrepartie.set(current_text)

        # Assurer que la liste des comptes est ordonnée et ne contient pas le compte actuel
        comptes_tries = sorted([option for option in lire_plan_comptable(f"{dossier_mandat}/plan_comptable.txt") if not compte_info.split(" - ")[0] in option], key=lambda item: item.split(" - ")[0])

        tk.Label(f_operations_compte, text="Contrepartie").grid(row=4, column=0, sticky="w")
        compte_contrepartie = ttk.Combobox(f_operations_compte, textvariable=compte_contrepartie_var, values=comptes_tries)
        compte_contrepartie.grid(row=4, column=1, sticky="ew")
        compte_contrepartie.bind('<KeyRelease>', update_combobox)
        
        tk.Button(f_operations_compte, text="Ajouter", command=lambda: enregistrer_operation_compte(compte_info, montant_debit_var, montant_credit_var, libelle_var, compte_contrepartie.get(), False, "", "", "", "")).grid(row=5, column=0, columnspan=2, sticky="ew")

        # Fonction pour vérifier et désactiver/activer les entrées de montant
        def verifier_montant(*args):
            if montant_debit_var.get():
                montant_credit_entry.config(state="disabled")
            else:
                montant_credit_entry.config(state="normal")

            if montant_credit_var.get():
                montant_debit_entry.config(state="disabled")
            else:
                montant_debit_entry.config(state="normal")

        montant_debit_var.trace("w", verifier_montant)
        montant_credit_var.trace("w", verifier_montant)

        # Ajustement de la configuration de la fenêtre
        for widget in f_operations_compte.winfo_children():
            widget.grid(padx=5, pady=5)
        
def lire_plan_comptable(fichier):
    if not os.path.exists(fichier):
        return []
    with open(fichier, 'r', encoding='utf-8') as f:
        comptes = [ligne.strip() for ligne in f.readlines()]
    return sorted(comptes, key=lambda x: int(x.split(' - ')[0]))

def enregistrer_operation_compte(compte_principal, montant_debit_var, montant_credit_var, libelle_var, compte_contrepartie, facture, date_var, delai_var, piece_impact, paiement_var):
    montant_debit = montant_debit_var.get()
    montant_credit = montant_credit_var.get()
    libelle = libelle_var.get()
    if len(str(date_var)) > 0:
        date_saisie = date_var.get()
    if len(str(delai_var)) > 0:
        delai_saisi = delai_var.get()
    if len(str(piece_impact)) > 0:
        piece_saisie = piece_impact.get()
    if len(str(paiement_var)) > 0:
        paiement = paiement_var.get()
    # Extraire uniquement le numéro de compte depuis compte_principal et compte_contrepartie
    compte_principal_numero = compte_principal.split(" - ")[0] if " - " in compte_principal else compte_principal
    compte_contrepartie_numero = compte_contrepartie.split(" - ")[0] if " - " in compte_contrepartie else compte_contrepartie
    compte_principal_text = compte_principal.split(" - ")[1] if " - " in compte_principal else compte_principal

    montant = 0
    debit = credit = ""

    if montant_debit:
        montant = float(montant_debit)  # Convertir le montant de débit en float
        debit = compte_principal_numero
        credit = compte_contrepartie_numero
    elif montant_credit:
        montant = float(montant_credit)  # Convertir le montant de crédit en float
        debit = compte_contrepartie_numero
        credit = compte_principal_numero
    
    dernier_numero = 0
    try:
        with open(f"{dossier_mandat}/journal.txt", 'r', encoding='utf-8') as f:
            for ligne in f:
                if ligne.strip():
                    dernier_numero = int(ligne.split("::")[0])
    except FileNotFoundError:
        print(f"Le fichier du journal n'a pas été trouvé.")
    except ValueError:
        print("Erreur lors de la lecture du dernier numéro de pièce.")
    nouveau_numero = dernier_numero + 1
        
    if facture:
        numero_modifie = f"0{nouveau_numero}" if nouveau_numero < 10 else nouveau_numero
        nom_fichier = f"{date_saisie}_{numero_modifie}_{delai_saisi}"
        # Création du fichier sans extension
        dos = f"{dossier_mandat}/factures"
        rep = f"{dossier_mandat}"
        fen = "f_operations_compte"
        texte_ref = ""
        if len(piece_saisie) > 0 and paiement == 0:
            piece_saisie = int(piece_saisie)
            numero_modifie = f"0{piece_saisie}" if piece_saisie < 10 else piece_saisie
            texte_ref = f"Réf. # {piece_saisie}"
            nom_fichier = f"_{numero_modifie}_"            
            for fichier in os.listdir(dos):
                chemin_complet = os.path.join(dos, fichier)
                if nom_fichier in fichier and os.path.isfile(chemin_complet):
                    os.remove(chemin_complet)
        else:
            numero_modifie = f"0{nouveau_numero}" if nouveau_numero < 10 else nouveau_numero
            nom_fichier = f"{date_saisie}_{numero_modifie}_{delai_saisi}"
            with open(f"{dos}/{nom_fichier}", 'w') as fichier:
                fichier.write("")
        
        if len(libelle) > 0 and len(texte_ref) > 0:
            libelle = f"{texte_ref} / {libelle}"
        elif len(libelle) == 0 and len(texte_ref) > 0:
            libelle = f"{texte_ref}"

    # Enregistrer dans le fichier journal
    with open(f"{dossier_mandat}/journal.txt", "a", encoding='utf-8') as f:
        f.write(f"{nouveau_numero}::{debit}::{credit}::{libelle}::{montant:.2f}\n")

    if facture:
        afficher_ecritures_journal(fen, rep, dos, compte_principal_text, compte_principal_numero)

    row_message = 1 if facture else 6
    column_message = 1 if facture else 0
    def afficher_message_temporaire(message):
        message_label = tk.Label(f_operations_compte, text=message, fg="green")
        message_label.grid(row=row_message, column=column_message, sticky="w") if facture else message_label.grid(row=row_message, column=column_message, columnspan=2, sticky="ew")

        def effacer_message():
            message_label.destroy()
            
        f_operations_compte.after(7000, effacer_message)  # Effacer après 7 secondes

    afficher_message_temporaire(f"Opération # {nouveau_numero} enregistrée au journal")
    # Réinitialiser les champs d'entrée pour une nouvelle saisie
    montant_debit_var.set("")
    montant_credit_var.set("")
    libelle_var.set("")

# JOURNAL #########################################################################

def afficher_journal(journal_path):
    f_journal = tk.Tk()
    f_journal.title("Journal")

    text_widget = Text(f_journal, wrap='none')
    text_widget.pack(expand=True, fill='both')

    header = "{:>4} {:>10} {:>10} {:>10} {:>35}\n".format("No", " Débit ", " Crédit ", " Libellé ", " Montant ")
    text_widget.insert(tk.END, header)

    # Ajouter le soulignement après le header
    underline = "{:>5} {:>9} {:>10} {:>35} {:>10}\n".format("----", "-------", "--------", "----------------------------------", "---------")
    text_widget.insert(tk.END, underline)
    
    try:
        with open(f"{dossier_mandat}/journal.txt", 'r', encoding='utf-8') as journal_file:
            journal_entries = journal_file.readlines()
            for entry in journal_entries:
                no, debit, credit, label, montant = entry.strip().split("::")
                line = "{:>4} {:>9} {:>10}   {:<33} {:>10.2f}\n".format(no, debit, credit, label, float(montant))
                text_widget.insert(tk.END, line)
    except FileNotFoundError:
        text_widget.insert(tk.END, f"Le fichier du journal n'a pas été trouvé.")

    if os.path.exists("config/config.txt"):
        with open("config/config.txt", "r", encoding='utf-8') as fichier:
            for ligne in fichier:
                if ligne.startswith("Nom:"):
                    nom = ligne.split("Nom:")[1].strip()
                elif ligne.startswith("Entreprise:"):
                    entreprise = ligne.split("Entreprise:")[1].strip()
            if len(nom) > 0 and len(entreprise) > 0:
                txt = f" ---\n {nom} / {entreprise}"
            elif  len(nom) > 0 and len(entreprise) == 0:
                txt = f" ---\n {nom}"
            elif  len(nom) == 0 and len(entreprise) > 0:
                txt = f" ---\n {entreprise}"
            else:
                txt = " ---\n Note: fichiers configuration à éditer"
                
            text_widget.insert(tk.END, txt)

    f_journal.mainloop()

# GRAND LIVRE #########################################################################

def read_plan_comptable(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return {line.split(' - ')[0]: line.split(' - ')[1].strip() for line in file}

def read_initial_balances(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return {line.split(' = ')[0]: float(line.split(' = ')[1].strip()) for line in file}

def process_journal(journal_path, accounts, initial_balances):
    account_totals = {account: {'debit': 0, 'credit': 0} for account in accounts}
    with open(journal_path, 'r', encoding='utf-8') as file:
        for line in file:
            _, debit_account, credit_account, _, amount = line.strip().split('::')
            amount = float(amount)
            if debit_account in account_totals:
                account_totals[debit_account]['debit'] += amount
            if credit_account in account_totals:
                account_totals[credit_account]['credit'] += amount

    final_balances = {}
    for account, totals in account_totals.items():
        initial_balance = initial_balances.get(account, 0)
        final_balance = 0  # Initialiser final_balance
        if account.startswith('1') or account.startswith('4') or account.startswith('5') or account.startswith('6') or account.startswith('7') or account.startswith('8'):
            final_balance = initial_balance + totals['debit'] - totals['credit']
        elif account.startswith('2') or account.startswith('3'):
            final_balance = initial_balance - totals['debit'] + totals['credit']
        final_balances[account] = final_balance
    return account_totals, final_balances


def afficher_grand_livre(accounts, initial_balances, account_totals, final_balances):
    f_grandlivre = tk.Tk()
    f_grandlivre.title("Grand-Livre")

    text_widget = tk.Text(f_grandlivre, wrap='none')
    text_widget.pack(expand=True, fill='both')

    header = "{:<35} {:>10} {:>10} {:>10} {:>10}\n".format("Comptes du GL", "Si  ", "Débit ", "Crédit ", "Sf/Vr ")
    text_widget.insert(tk.END, header)


    # Ajouter le soulignement après le header
    underline = "{:<35} {:>10} {:>10} {:>10} {:>10}\n".format("-----------------------", "------", "--------", "--------", "-------")
    text_widget.insert(tk.END, underline)
    
    for account in sorted(final_balances.keys(), key=int):
        if initial_balances.get(account, 0) != 0 or account_totals[account]['debit'] != 0 or account_totals[account]['credit'] != 0 or final_balances[account] != 0:
            line = "{:<5} {:<29} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}\n".format(
                account,
                accounts[account],
                initial_balances.get(account, 0.0),
                account_totals[account]['debit'],
                account_totals[account]['credit'],
                final_balances[account]
                )
            text_widget.insert(tk.END, line)
    
    nom = entreprise = ""
    if os.path.exists("config/config.txt"):
        with open("config/config.txt", "r", encoding='utf-8') as fichier:
            for ligne in fichier:
                if ligne.startswith("Nom:"):
                    nom = ligne.split("Nom:")[1].strip()
                elif ligne.startswith("Entreprise:"):
                    entreprise = ligne.split("Entreprise:")[1].strip()
            if len(nom) > 0 and len(entreprise) > 0:
                txt = f"---\n{nom} / {entreprise}"
            elif  len(nom) > 0 and len(entreprise) == 0:
                txt = f"---\n{nom}"
            elif  len(nom) == 0 and len(entreprise) > 0:
                txt = f"---\n{entreprise}"
            else:
                txt = f"---\nNote: fichiers configuration à éditer"
            text_widget.insert(tk.END, txt)
            
    f_grandlivre.mainloop()

# INFO #########################################################################

def afficher_texte():
    texte_a_afficher = """Ce petit logiciel de compta est développé avec <3
par Antoine Melo (antoine.melo@edu.ge.ch)
                                        ---
Version βeta 0.6 du 15 février 2024
                                        ---"""
    fenetre_texte = tk.Toplevel()
    fenetre_texte.title("À propos")

    # Afficher le texte normal
    label_texte = tk.Label(fenetre_texte, text=texte_a_afficher, justify=tk.LEFT)
    label_texte.pack()

    # Vérifier si le fichier PDF existe avant de créer le lien
    chemin_pdf = os.path.join(os.getcwd(), "config", "manuel.pdf")
    if os.path.exists(chemin_pdf):
        # Créer un label cliquable pour le PDF
        label_pdf = tk.Label(fenetre_texte, text="Manuel (pdf)", fg="blue", cursor="hand2")
        label_pdf.pack()
        label_pdf.bind("<Button-1>", lambda e: ouvrir_pdf())

# CONFIG #########################################################################
def vider_journal(journal_mandat):
    if len(journal_mandat) > 0:
        dos = f"config/{journal_mandat}"
        open(f"{dos}/journal.txt", "w").close()
        if os.path.exists(f"{dos}/factures"):
            shutil.rmtree(f"{dos}/factures")
    else:
        dos = f"config"
        open(f"{dos}/journal.txt", "w").close()
        if os.path.exists(f"{dos}/factures"):
            shutil.rmtree(f"{dos}/factures")
        
def sauvegarder_config(nom_entry, entreprise_entry, text_widget, fenetre_config, fenetre_principale):
    global verifier_mandat_vide, dossier_mandat
    # Sauvegarde des informations utilisateur
    nom = nom_entry.get()
    entreprise = entreprise_entry.get()
    dossier_mandat = f"config/{nom}"
    chemin_mandat = os.path.join(os.getcwd(), dossier_mandat)
    with open("config/config.txt", "w", encoding='utf-8') as fichier:
        fichier.write(f"Nom: {nom}\n")
        fichier.write(f"Entreprise: {entreprise}")
    fenetre_principale.title(f":: {nom} ::")

    fichiers = ["plan_comptable.txt", "soldes_initiaux.txt", "journal.txt"]
    if not os.path.exists(f"config/{nom}") or len(nom) == 0:
        chemin_a_crer = os.path.join(os.getcwd(), f"config/{nom}")
        if len(nom) == 0:
            nom = "$bac£a£sable$"
        verifier_mandat(chemin_a_crer, fichiers, nom)

    # Sauvegarde du plan comptable
    contenu = text_widget.get("1.0", "end-1c")
    if nom == "$bac£a£sable$":
        chemin_sauvegarde = os.path.join(os.getcwd(), f"config")
    else:
        chemin_sauvegarde = os.path.join(os.getcwd(), f"config/{nom}")
    if verifier_mandat_vide == "":
        with open(f"{chemin_sauvegarde}/plan_comptable.txt", "w", encoding='utf-8') as fichier:
            fichier.write(contenu)
    comptes_dict = lire_pc(f"{chemin_sauvegarde}/plan_comptable.txt")  # Recharger les données
    selection_compte(fenetre_principale, comptes_dict)  # Mettre à jour le ComboBox
    verifier_exercice(fenetre, chemin_mandat, nom)
    # Fermeture de la fenêtre de configuration
    fenetre_config.destroy()

def lire_nom_mandat():
    """Lit le nom du mandat depuis le fichier de configuration."""
    chemin_config = "config/config.txt"
    if os.path.exists(chemin_config):
        with open(chemin_config, "r", encoding='utf-8') as fichier:
            for ligne in fichier:
                if ligne.startswith("Nom:"):
                    return ligne.split("Nom:")[1].strip()
    return ""

def charger_plan_comptable(text_widget, dossier_mandat):
    """Charge et affiche le contenu du fichier plan_comptable.txt pour le mandat sélectionné."""
    if len(dossier_mandat) > 0:
        fichier_plan = f"config/{dossier_mandat}/plan_comptable.txt"
    else:
        fichier_plan = f"config/plan_comptable.txt"
    text_widget.delete('1.0', tk.END)  # Efface le contenu précédent
    if os.path.exists(fichier_plan):
        with open(fichier_plan, "r", encoding='utf-8') as fichier:
            contenu = fichier.read()
            text_widget.insert(tk.END, contenu)

def charger_contenu(text_widget, fichier_path):
    """Charge le contenu d'un fichier dans un widget texte."""
    text_widget.delete('1.0', tk.END)  # Efface le contenu précédent

    if not os.path.exists(fichier_path):
        with open(fichier_path, 'w', encoding='utf-8') as fichier:
            fichier.write("")
            
    if os.path.exists(fichier_path):
        with open(fichier_path, "r", encoding='utf-8') as fichier:
            contenu = fichier.read()
            text_widget.insert(tk.END, contenu)

def sauvegarder_contenu(text_widget, fichier_path):
    """Enregistre le contenu d'un widget texte dans un fichier."""
    contenu = text_widget.get("1.0", "end-1c")
    with open(fichier_path, "w", encoding='utf-8') as fichier:
        fichier.write(contenu)

def ouvrir_fenetre_instructions(nom_mandat):
    fenetre_instructions = tk.Toplevel()
    fenetre_instructions.title(f":: {nom_mandat} ::")
    rep_mandat = f"config/{nom_mandat}"
    
    tk.Label(fenetre_instructions, text="INSTRCUTIONS", font=("Courier", 10, "bold")).grid(row=0, column=0, pady=5, columnspan=2)
    text_instructions = scrolledtext.ScrolledText(fenetre_instructions, height=15, width=80)
    text_instructions.grid(row=1, column=0, columnspan=2, padx=10, pady=0)
    charger_contenu(text_instructions, f"config/{nom_mandat}/exercice.txt")

    tk.Label(fenetre_instructions, text="------------------------------------------------------------------", font=("Courier")).grid(row=2, column=0, columnspan=2)
    tk.Label(fenetre_instructions, text="COMPTES FONCTIONNANT EN MOINS - PLUS (expl*: 2, 3)", font=("Courier", 10, "bold")).grid(row=3, column=0, columnspan=2)
    tk.Label(fenetre_instructions, text="* 2 pour les passifs, 3 pour les produits", font=("Courier", 8, "italic")).grid(row=5, column=0, padx=15, columnspan=2, sticky='w')
    text_moinsplus = tk.Text(fenetre_instructions, height=1, width=80)
    text_moinsplus.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
    charger_contenu(text_moinsplus, f"config/{nom_mandat}/moinsplus.txt")

    tk.Label(fenetre_instructions, text="------------------------------------------------------------------", font=("Courier")).grid(row=6, column=0, columnspan=2)
    tk.Label(fenetre_instructions, text="COMPTES POUR LE SUIVI DE FACTURES (expl*: 11, 20)", font=("Courier", 10, "bold")).grid(row=7, column=0, columnspan=2)
    tk.Label(fenetre_instructions, text="* 11 pour les créances, 20 pour les dettes fournisseurs et autres accomptes", font=("Courier", 8, "italic")).grid(row=9, column=0, padx=15, columnspan=2, sticky='w')
    text_facture = tk.Text(fenetre_instructions, height=1, width=80)
    text_facture.grid(row=8, column=0, columnspan=2, padx=10, pady=5)
    charger_contenu(text_facture, f"config/{nom_mandat}/facture.txt")

    tk.Label(fenetre_instructions, text="------------------------------------------------------------------", font=("Courier")).grid(row=10, column=0, columnspan=2)
    tk.Label(fenetre_instructions, text="AFFICHAGE BILAN ET COMPTES DE RÉSULTAT", font=("Courier", 10, "bold")).grid(row=11, column=0, columnspan=2)
    text_totaux = scrolledtext.ScrolledText(fenetre_instructions, height=20, width=80)
    text_totaux.grid(row=12, column=0, columnspan=2, padx=10, pady=5)
    charger_contenu(text_totaux, f"config/{nom_mandat}/totaux.txt")

    bouton_sauvegarder = tk.Button(fenetre_instructions, text="Sauvegarder", command=lambda: sauvegarder_modifications(fenetre_instructions, text_instructions, text_moinsplus, text_facture, text_totaux, rep_mandat))
    bouton_sauvegarder.grid(row=13, column=0, columnspan=2, pady=5)

def sauvegarder_modifications(fenetre_a_fermer, text_instructions, text_moinsplus, text_facture, text_totaux, rep_mandat):
    sauvegarder_contenu(text_instructions, f"{rep_mandat}/exercice.txt")
    sauvegarder_contenu(text_moinsplus, f"{rep_mandat}/moinsplus.txt")
    sauvegarder_contenu(text_facture, f"{rep_mandat}/facture.txt")
    sauvegarder_contenu(text_totaux, f"{rep_mandat}/totaux.txt")
    fenetre_a_fermer.destroy()

def ouvrir_config(fenetre_principale):
    """Ouvre la fenêtre de configuration et initialise les composants."""
    fenetre_config = tk.Toplevel()
    fenetre_config.title("Configuration")
    
    global nom_entry, entreprise_entry, entreprise_entry_value

    tk.Label(fenetre_config, text="Mandat :").grid(row=0, column=0, padx=10, sticky='w')
    dossiers_mandat = [d for d in os.listdir("config") if os.path.isdir(os.path.join("config", d))]
    dossiers_mandat.sort()
    nom_mandat = lire_nom_mandat()  # Lit le nom du mandat actuel depuis le fichier de configuration
    nom_entry = ttk.Combobox(fenetre_config, values=dossiers_mandat, width=25)
    nom_entry.set(nom_mandat)  # Définit la valeur sélectionnée du combobox
    nom_entry.grid(row=0, column=1, pady=5, sticky='w')

    # Liaison de l'événement de changement de valeur du combobox
    nom_entry.bind("<<ComboboxSelected>>", lambda event: charger_plan_comptable(text_plan_comptable, nom_entry.get()))

    tk.Label(fenetre_config, text="Prénom NOM, ÉCOLE, ENTREPRISE :").grid(row=1, column=0, padx=10, sticky='w')
    entreprise_entry = tk.Entry(fenetre_config, width=28)
    entreprise_entry.grid(row=1, column=1, pady=5, sticky='w')

    if os.path.exists("config/config.txt"):
        with open("config/config.txt", "r", encoding='utf-8') as fichier:
            for ligne in fichier:
                if ligne.startswith("Entreprise: "):
                    entreprise_entry.insert(0, ligne.split("Entreprise: ")[1].strip())
                    entreprise_entry_value = ligne.split("Entreprise: ")[1].strip()

    bouton_sauvegarder = tk.Button(fenetre_config, text="Sauvegarder", command=lambda: sauvegarder_config(nom_entry, entreprise_entry, text_plan_comptable, fenetre_config, fenetre_principale))
    bouton_sauvegarder.grid(row=6, column=0, columnspan=2, pady=5)

    bouton_vider_journal = tk.Button(fenetre_config, text="Effacer les saisies du journal", command=lambda: vider_journal(nom_entry.get()))
    bouton_vider_journal.grid(row=2, column=0, padx=10, pady=5, sticky='w')

    bouton_modifier_instructions = tk.Button(fenetre_config, text="Modifier les instructions", command=lambda: ouvrir_fenetre_instructions(nom_entry.get()))
    bouton_modifier_instructions.grid(row=2, column=1, pady=5, sticky='w')
    
    tk.Label(fenetre_config, text="-------------------------------------------------", font=("Courier")).grid(row=3, column=0, columnspan=2)
    tk.Label(fenetre_config, text="PLAN COMPTABLE (no - libellé du compte", font=("Courier", 10, "bold")).grid(row=4, column=0, sticky='e')
    tk.Label(fenetre_config, text=", expl: 1000 - Actifs)", font=("Courier", 10, "bold")).grid(row=4, column=1, sticky='w')

    text_plan_comptable = tk.Text(fenetre_config, height=10, width=60)
    text_plan_comptable.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

    # Charge initialement le plan comptable si une sélection est déjà présente
    if nom_entry.get():
        charger_plan_comptable(text_plan_comptable, nom_entry.get())
    else:
        charger_plan_comptable(text_plan_comptable, "")

# END CONFIG #########################################################################
def creer_mandat(chemin_m, t_fichiers, message):
    if chemin_m.endswith(':'):
        chemin_m = chemin_m[:-1]    
    if not os.path.exists(chemin_m):
        os.makedirs(chemin_m)
    for fichier in t_fichiers:
        open(os.path.join(chemin_m, fichier), 'w').close()

    # messagebox.showinfo("Mandat créé", f"Le mandat a été créé avec succès sous \"{chemin_m}\".")

def creer_base(t_fichiers):
    chemin_m = os.path.join(os.getcwd(), "config")
    if not os.path.exists(chemin_m):
        os.makedirs(chemin_m)
    for fichier in t_fichiers:
        if not os.path.exists(f"config/{fichier}"):
            open(os.path.join(chemin_m, fichier), 'w').close()

def verifier_mandat(chemin_m, t_fichiers, nom_a_verifier):
    creation = ""
    if len(nom_a_verifier) == 0:
        msg = "Aucun mandat correspondant ne semble exister dans le répertoire de configuration. Voulez-vous créer un exemple de mandat ?"
    elif nom_a_verifier == "$bac£a£sable$":
        for fichier in t_fichiers:
            if not os.path.exists(f"config/{fichier}"):
                creation = "oui"
        if creation == "oui":
            msg = "Un tel mandat (sans nom) n'existe pas encore. C'est tout à fait possible... Souhaitez-vous procéder à sa création ?"
        else:
            creation == "non"
            msg = "Un tel mandat (sans nom) existe déjà. Continuer ?"
    else:
        msg = "Le mandat n'existe pas. Voulez-vous le créer ?"
        
    if messagebox.askyesno("Créer mandat", msg):
        dossier_mandat = "config/Exemple"
        if len(nom_a_verifier) == 0:
            chemin_m = os.path.join(os.getcwd(), f"config/Exemple")
            with open("config/config.txt", "w", encoding='utf-8') as fichier:
                fichier.write(f"Nom: Exemple\n")
                fichier.write(f"Entreprise: {entreprise_entry_value}")
        elif nom_a_verifier == "$bac£a£sable$":
            dossier_mandat = "config"
            chemin_m = os.path.join(os.getcwd(), f"config")
            with open("config/config.txt", "w", encoding='utf-8') as fichier:
                fichier.write(f"Nom: \n")
                fichier.write(f"Entreprise: {entreprise_entry_value}")
            if creation == "oui" or creation == "":
                messagebox.showwarning("Création confirmée", "Un mandat sans nom existe maintenant dans vos dossiers.")
        creer_mandat(chemin_m, t_fichiers, creation)
    else:
        verifier_mandat_vide = "non"
        dossier_mandat = "config"
        creer_base(t_fichiers)
        with open("config/config.txt", "w", encoding='utf-8') as fichier:
            fichier.write(f"Nom: \n")
            fichier.write(f"Entreprise: {entreprise_entry_value}")
        if creation != "non" and nom_a_verifier != "$bac£a£sable$":
            messagebox.showwarning("Création annulée", "Bien que la création du mandat ait été annulée, des fichiers de type 'bac à sable' ont été créés.")

def lire_nom_depuis_config(fichier_config="config/config.txt"):
    nom_titre = "::"  # Valeur par défaut
    if os.path.exists(fichier_config):
        with open(fichier_config, "r", encoding="utf-8") as fichier:
            for ligne in fichier:
                if ligne.startswith("Nom:"):
                    nom_titre = nom_titre, ligne.split("Nom:")[1].strip(), "::"
                    break  # Quitte la boucle après avoir trouvé le nom
    return nom_titre

def afficher_exercice(nom_exercice):
    chemin_exercice = f"{dossier_mandat}/exercice.txt"
    lignes = []
    index_affichage = [0, 4]  # Début et fin initiaux de l'affichage
    dernier_index_affichage = [0, 4]  # Pour mémoriser le dernier état avant "Tout Afficher"

    if os.path.exists(chemin_exercice):
        with open(chemin_exercice, "r", encoding="utf-8") as fichier:
            lignes = fichier.readlines()

        with open("config/config.txt", "r", encoding="utf-8") as fichier:
            for ligne in fichier:
                if ligne.startswith("Nom:"):
                    nom_titre = ligne.split("Nom:")[1].strip()
                    break  # Quitte la boucle après avoir trouvé le nom
                
        fenetre_exercice = tk.Toplevel()
        fenetre_exercice.title(f"Instruction·s  ::  {nom_titre}")
        texte_exercice = ScrolledText(fenetre_exercice, wrap=tk.WORD)
        texte_exercice.pack(expand=True, fill=tk.BOTH)

        # Boutons qui seront alternativement affichés ou cachés
        bouton_tout_afficher = tk.Button(fenetre_exercice, text="Tout afficher")
        bouton_filtrer = tk.Button(fenetre_exercice, text="Filtrer")

        def mettre_a_jour_affichage():
            texte_exercice.config(state=tk.NORMAL)
            texte_exercice.delete(1.0, tk.END)
            texte_exercice.insert(tk.END, ''.join(lignes[index_affichage[0]:index_affichage[1]]))
            texte_exercice.config(state=tk.DISABLED)

        def suivant():
            if index_affichage[1] < len(lignes):
                index_affichage[1] += 2
                mettre_a_jour_affichage()

        def precedent():
            if index_affichage[1] > 4:
                index_affichage[1] -= 2
                mettre_a_jour_affichage()

        def tout_afficher():
            nonlocal dernier_index_affichage
            dernier_index_affichage = list(index_affichage)  # Mémorise l'état actuel
            index_affichage[0] = 0
            index_affichage[1] = len(lignes)
            mettre_a_jour_affichage()
            bouton_tout_afficher.pack_forget()
            bouton_filtrer.pack(side=tk.BOTTOM, pady=5, padx=15)

        def filtrer():
            nonlocal index_affichage
            index_affichage = list(dernier_index_affichage)  # Restaure l'état mémorisé
            mettre_a_jour_affichage()
            bouton_filtrer.pack_forget()
            bouton_tout_afficher.pack(side=tk.BOTTOM, pady=5, padx=15)

        bouton_precedent = tk.Button(fenetre_exercice, text="Précédent", command=precedent)
        bouton_precedent.pack(side=tk.LEFT, pady=5, padx=10)

        bouton_suivant = tk.Button(fenetre_exercice, text="Suivant", command=suivant)
        bouton_suivant.pack(side=tk.RIGHT, pady=5, padx=15)

        bouton_tout_afficher.config(command=tout_afficher)
        bouton_tout_afficher.pack(side=tk.BOTTOM, pady=5, padx=15)

        bouton_filtrer.config(command=filtrer)

        mettre_a_jour_affichage()

def verifier_exercice(fenetre, repertoire_exercice, nom_exercice):
    global label_bienvenue, bouton_exercice

    rep_fichier = f"{repertoire_exercice}/exercice.txt"
    if os.path.exists(rep_fichier) and os.path.getsize(rep_fichier) > 0:
        if label_bienvenue:  # Vérifier si 'label_bienvenue' existe déjà et le cacher le cas échéant
            label_bienvenue.grid_remove()
        if not bouton_exercice:  # Créer le bouton s'il n'existe pas déjà
            bouton_exercice = tk.Button(fenetre, relief="flat", text="Instruction·s", fg="blue", command=lambda: afficher_exercice(nom_exercice))
            bouton_exercice.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        else:
            bouton_exercice.grid()  # Réafficher le bouton s'il était précédemment caché
    else:
        if bouton_exercice:  # Vérifier si 'bouton_exercice' existe déjà et le cacher le cas échéant
            bouton_exercice.grid_remove()
        if not label_bienvenue:  # Créer 'label_bienvenue' s'il n'existe pas déjà
            label_bienvenue = tk.Label(fenetre, text="Bienvenue ;)")
            label_bienvenue.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        else:
            label_bienvenue.grid()  # Réafficher 'label_bienvenue' s'il était précédemment caché

# TOTAUX #########################################################################
def lire_soldes_initiaux(fichier_soldes):
    soldes = {}
    with open(fichier_soldes, 'r') as f:
        for ligne in f:
            compte, montant = ligne.strip().split(' = ')
            soldes[compte] = float(montant)
    return soldes

def lire_journal(fichier_journal):
    operations = []
    with open(fichier_journal, 'r') as f:
        for ligne in f:
            parts = ligne.strip().split('::')
            operations.append(parts)
    return operations

def mode_fonctionnement_compte(num_compte, moinsplus_mandat):
    comptes_moins_plus = modes_moins_plus_liste(f"{moinsplus_mandat}/moinsplus.txt")
    if num_compte[0] in comptes_moins_plus:
        return 'moins-plus'
    else:
        return 'plus-moins'

def calculer_total_par_numero_ou_intervalle(soldes, operations, num_ou_intervalle, moinsplus_mandat):
    total = 0
    comptes_concernes = set()  # Utilisez un ensemble pour éviter les doublons

    # Traitement des intervalles
    if '-' in str(num_ou_intervalle):
        debut, fin = map(int, num_ou_intervalle.split('-'))
        plage = range(debut, fin + 1)
        verifier_compte = lambda c: int(c[:len(str(debut))]) in plage
    else:
        verifier_compte = lambda c: c.startswith(str(num_ou_intervalle))

    # Étendre la liste des comptes concernés pour inclure ceux du journal
    for compte in soldes:
        if verifier_compte(compte):
            comptes_concernes.add(compte)
    for op in operations:
        no_op, deb, cred, label, montant = op
        if verifier_compte(deb):
            comptes_concernes.add(deb)
        if verifier_compte(cred):
            comptes_concernes.add(cred)

    # Initialiser les soldes à zéro pour les nouveaux comptes
    soldes_initiaux = {compte: soldes.get(compte, 0.0) for compte in comptes_concernes}

    # Calcul du total pour les comptes concernés
    for compte in comptes_concernes:
        mode = mode_fonctionnement_compte(compte, moinsplus_mandat)
        solde_initial = soldes_initiaux[compte]
        total_compte = solde_initial if mode == 'plus-moins' else -solde_initial
        
        for op in operations:
            no_op, deb, cred, label, montant = op
            montant = float(montant)
            if compte == deb and mode == 'plus-moins':
                total_compte += montant
            elif compte == cred and mode == 'plus-moins':
                total_compte -= montant
            elif compte == deb and mode == 'moins-plus':
                total_compte += montant
            elif compte == cred and mode == 'moins-plus':
                total_compte -= montant
        total += total_compte

    return total, list(comptes_concernes)

def lire_totaux(fichier_totaux):
    totaux = {}
    if os.path.exists(fichier_totaux) and os.path.getsize(fichier_totaux) > 0:
        with open(fichier_totaux, 'r', encoding='utf-8') as f:
            for ligne in f:
                # Ignore les lignes vides ou les commentaires
                if ligne.strip() and not ligne.startswith("#"):
                    intitule, numeros = ligne.strip().split(": ")
                    # Stocker l'intitulé et les numéros ou intervalles associés dans un dictionnaire
                    totaux[intitule] = numeros.strip()
    else:
        # Valeurs par défaut si le fichier n'existe pas
        totaux = {
            "Liquidités": "10",
            "Créances clients": "11",
            "Autres actifs circulants": "12-13",
            "Actifs immobilisés": "14-19",
            "Traitille-1": "-----------",
            "TOTAL DES ACTIFS": "1",
            "Doubletrait-1": "===========",
            "Dettes à court terme": "20-23",
            "Dettes à long terme": "24-27",
            "Fonds propres": "28-29",
            "Traitille-2": "-----------",
            "TOTAL DES PASSIFS": "2",
            "Doubletrait-2": "===========",
            "Passifs - Actifs": "1-2",
            "Vide-1": "0",
            "Chiffre d'affaires net": "3",
            "VS et charges d'achat": "39-40",
            "Traitille-3": "-----------",
            "Marge brute": "3-4",
            "Charges de personnel": "5",
            "Autres charges": "6-8",
            "Traitille-4": "-----------",
            "Résultat net": "3-8",
            "Doubletrait-3": "===========",
        }
    return totaux

def modes_moins_plus_liste(fichier):
    """Lire le fichier pour déterminer les comptes fonctionnant en mode 'moins-plus'.
    Retourne une liste de ces comptes à partir d'une ligne unique contenant des valeurs séparées par des virgules."""
    if os.path.exists(fichier) and os.path.getsize(fichier) > 0:
        with open(fichier, 'r', encoding='utf-8') as f:
            # Prend la première ligne, la divise selon les virgules, et retire les espaces inutiles
            return [num.strip() for num in f.readline().split(',')]
    else:
        # Si le fichier n'existe pas ou est vide, retourne les valeurs par défaut
        return ['2', '3']
    
def modes_moins_plus_tuple(fichier):
    # Lire le fichier pour déterminer les comptes fonctionnant en mode 'moins-plus'.
    if os.path.exists(fichier) and os.path.getsize(fichier) > 0:
        with open(fichier, 'r', encoding='utf-8') as f:
            # Prend la première ligne, la divise selon les virgules, et retire les espaces inutiles
            return tuple(num.strip() for num in f.readline().split(','))
    else:
        return ('2', '3')

def afficher_totaux(totaux_mandat):
    # Création de la fenêtre pour afficher les totaux
    fenetre_totaux = tk.Toplevel(fenetre)
    fenetre_totaux.title("")
    fenetre_totaux.geometry("400x800")  # Largeur de 400 pixels et hauteur de 600 pixels

    # Texte pour afficher les résultats
    texte_totaux = scrolledtext.ScrolledText(fenetre_totaux, wrap=tk.WORD, height=10, width=50)
    texte_totaux.pack(expand=True, fill=tk.BOTH)
    soldes_initiaux = lire_soldes_initiaux(f"{totaux_mandat}/soldes_initiaux.txt")
    journal = lire_journal(f"{totaux_mandat}/journal.txt")
    
    totaux = lire_totaux(f"{totaux_mandat}/totaux.txt")
    for intitule, num_ou_intervalle in totaux.items():
        if intitule.startswith("Traitille-") == True or intitule.startswith("Doubletrait-") == True or intitule.startswith("Vide-") == True:  # Si l'intitulé est une ligne de séparation
            if intitule.startswith("Vide-") == True:
                texte_totaux.insert(tk.END, "\n"+" #"+"#"*44+"\n\n")
            else:
                if len(num_ou_intervalle) > 15:
                    A, B = 45 - len(num_ou_intervalle), "\n"
                else:
                    A, B = 30, ""
                texte_totaux.insert(tk.END, f" {B} {'':<{A}}{num_ou_intervalle:>15}\n")
            continue  # Passe au prochain élément dans la boucle

        total, comptes_concernes = calculer_total_par_numero_ou_intervalle(soldes_initiaux, journal, num_ou_intervalle, totaux_mandat)

        # Vérifiez si l'intervalle concerne des comptes qui fonctionnent en moins-plus
        comptes_moins_plus = modes_moins_plus_tuple(f"{totaux_mandat}/moinsplus.txt")
        mode_compte = "moins-plus" if any(c.startswith(comptes_moins_plus) for c in comptes_concernes) else "plus-moins"
        if mode_compte == "moins-plus":
            total = -total  # Inversez le signe du total pour ces comptes

        montant_formatte = f" {total:.2f}" if total != 0 else "-.- "
        resultat = f" {intitule:<30}{montant_formatte:>15}\n"
        texte_totaux.insert(tk.END, resultat)

    texte_totaux.config(state=tk.DISABLED)

# FACTURES ###########################################################################
def modes_facture_liste(fichier):
    """Lire le fichier pour déterminer les comptes fonctionnant en mode 'facture'.
    Retourne une liste de ces comptes à partir d'une ligne unique contenant des valeurs séparées par des virgules."""
    if os.path.exists(fichier) and os.path.getsize(fichier) > 0:
        with open(fichier, 'r', encoding='utf-8') as f:
            # Prend la première ligne, la divise selon les virgules, et retire les espaces inutiles
            return [num.strip() for num in f.readline().split(',')]
    else:
        # Si le fichier n'existe pas ou est vide, retourne les valeurs par défaut
        return ['11', '20']
    
def modes_facture_tuple(fichier):
    # Lire le fichier pour déterminer les comptes fonctionnant en mode 'moins-plus'.
    if os.path.exists(fichier) and os.path.getsize(fichier) > 0:
        with open(fichier, 'r', encoding='utf-8') as f:
            # Prend la première ligne, la divise selon les virgules, et retire les espaces inutiles
            return tuple(num.strip() for num in f.readline().split(','))
    else:
        return ('11', '20')

def lire_journal_factures(fichier_journal):
    """Lire les écritures du fichier journal.txt."""
    with open(fichier_journal, 'r', encoding='utf-8') as fichier:
        return fichier.readlines()

def trouver_infos_factures(dossier_factures):
    """Trouver les infos des factures à partir des noms des fichiers."""
    infos_factures = []
    if not os.path.exists(dossier_factures):
        os.makedirs(dossier_factures)
    for nom_fichier in os.listdir(dossier_factures):
        # Le nom de fichier n'a pas d'extension
        date, no_piece, delai = nom_fichier.split("_")
        infos_factures.append((no_piece, date, delai))
    return infos_factures

def filtrer_ecritures_journal(ecritures_journal, infos_factures, no_compte, rep_journal):
    ecritures_filtrees = []
    nom_fichier = "moinsplus.txt"
    chemin_complet = os.path.join(rep_journal, nom_fichier)
    if os.path.exists(chemin_complet):
        moins_plus = modes_moins_plus_liste(chemin_complet)
    else:
        moins_plus = [2]
    
    premier_nombre = no_compte[0]
    type_utilise = ""
    if premier_nombre in moins_plus:
        type_utilise = "credit"
    else:
        type_utilise = "debit"

    for no_piece, date, delai in infos_factures:
        no_piece_modifie = no_piece[1:] if no_piece.startswith("0") else no_piece
        for ecriture in ecritures_journal:
            no, debit, credit, label, montant = ecriture.strip().split("::")
            no_modifie = f"0{no}" if len(no) == 1 else no

            if premier_nombre in moins_plus:
                compte_utilise = credit
            else:
                compte_utilise = debit

            if no_piece == no_modifie and str(compte_utilise) == str(no_compte):
                ecriture_modifiee = f"{date}::{ecriture}::{delai}"
                ecritures_filtrees.append(ecriture_modifiee)

    return ecritures_filtrees, type_utilise, moins_plus

def afficher_ecritures_journal(fenetre, rep_journal, dossier_factures, nom_compte, no_compte):
    ecritures_journal = lire_journal_factures(f"{rep_journal}/journal.txt")
    infos_factures = trouver_infos_factures(dossier_factures)
    ecritures_filtrees, type_utilise, moins_plus = filtrer_ecritures_journal(ecritures_journal, infos_factures, no_compte, rep_journal)

    texte_ecritures = scrolledtext.ScrolledText(f_operations_compte, wrap=tk.WORD, height=10, width=110)
    texte_ecritures.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

    compte_selectionne_entier = f"{no_compte} - {nom_compte}"
    bouton_afficher_ecritures = tk.Button(f_operations_compte, text=f"Nouvelle·s écriture·s {nom_compte.lower()}", command=lambda: saisir_operations_facture(type_utilise, moins_plus, compte_selectionne_entier, rep_journal, False, ecritures_filtrees))
    bouton_afficher_ecritures.grid(row=1, column=0, padx=10, pady=5, sticky='w')

    if len(ecritures_filtrees) > 0:
        if type_utilise == "debit":
            type_inverse = "credit"
        else:
            type_inverse = "debit"
        bouton_paiement = tk.Button(f_operations_compte, text="Paiement", command=lambda: saisir_operations_facture(type_inverse, moins_plus, compte_selectionne_entier, rep_journal, True, ecritures_filtrees))
        bouton_paiement.grid(row=1, column=1, padx=10, pady=5, sticky='e')

    header = "{:>8} {:>7} {:>10} {:>10} {:>10} {:>35} {:>7} {:>10}\n".format("Date", "No", " Débit ", " Crédit ", " Libellé ", " Montant ", "Delai", "Statut")
    texte_ecritures.insert(tk.END, header)

    # Ajouter le soulignement après le header
    underline = "{:>11} {:>5} {:>9} {:>10} {:>35} {:>10} {:>8} {:>10}\n".format("----------", "----", "-------", "--------", "----------------------------------", "---------", "-------", "---------")
    texte_ecritures.insert(tk.END, underline)

    for ecriture in ecritures_filtrees:
        #texte_ecritures.insert(tk.END, ecriture)
        date, no, debit, credit, label, montant, delai = ecriture.strip().split("::")

        date_initiale = datetime.strptime(date, '%Y%m%d')
        date_delai = date_initiale + timedelta(days=int(delai))
        date_aujourdhui = datetime.now()
        date_dif = date_delai - date_aujourdhui
        date_dif = date_dif.days
        if date_dif > 2:
            statut = "ouvert"
        elif date_dif >= 0:
            statut = "à payer"
        else:
            statut = "en retard"

        line = "{:>10} {:>5} {:>8} {:>10}     {:<32} {:>10.2f} {:>6}j. {:>10}\n".format(date, no, debit, credit, label, float(montant), date_dif, statut)
        texte_ecritures.insert(tk.END, line)
    
    if len(ecritures_filtrees) == 0: texte_ecritures.insert(tk.END, f" Aucune facture n'est ouverte pour le compte de {nom_compte.lower()}")
    texte_ecritures.config(state=tk.DISABLED)

def saisir_operations_facture(type_utilise, moins_plus, compte_info, rep_mandat, paiement, no_pieces_facture):
    f_operations_facture = tk.Toplevel()
    # Configuration initiale pour utiliser grid
    f_operations_facture.grid_columnconfigure(1, weight=1)
    comptes_facture = modes_facture_tuple(f"{rep_mandat}/facture.txt")
    # True si comptes_facture correspond au compte en cours
    mode_facture = any(compte_info.startswith(element) for element in comptes_facture)

    f_operations_facture.title("Opérations")
    # Afficher les informations du compte
    label_compte_info = tk.Label(f_operations_facture, text=f"{compte_info}", font=("Courier", 12, "bold"))
    label_compte_info.grid(row=0, column=1, sticky="ew")

    # Variables pour les entrées
    montant_debit_var = tk.StringVar()
    montant_credit_var = tk.StringVar()
    libelle_var = tk.StringVar()
    compte_contrepartie_var = tk.StringVar()
    date_var = tk.StringVar()
    delai_var = tk.StringVar()
    paiement_var = tk.IntVar()
    piece_impact = tk.StringVar()

    compte_numero = compte_info.split(" - ")[0]
    premier_nombre = compte_numero[0]
    
    # Déterminer les signes à ajouter après les labels de débit et de crédit
    if premier_nombre in moins_plus:
        label_debit_text = "Montant au débit (- - / sortie ou dim.)"
        label_credit_text = "Montant au crédit (++ / entrée ou augm.)"
    else:
        label_debit_text = "Montant au débit  (++ / entrée ou augm.)"
        label_credit_text = "Montant au crédit (- - / sortie ou dim.)"

    def verifier_longueur_date(event):
        date_text = date_var.get()  # Récupérer la valeur de la variable liée à l'Entry
        if len(date_text) != 8:
            messagebox.showerror("Erreur de format", "La date doit comporter exactement 8 caractères (YYYYmmdd).")
            f_operations_facture.lift()
            f_operations_facture.focus_set()
            date_entry.focus_set()
        
    if not paiement:
        date_aujourdhui = datetime.now()
        date_aujourdhui_str = date_aujourdhui.strftime('%Y%m%d')
        tk.Label(f_operations_facture, text="Date de la facture").grid(row=1, column=0, sticky="w")
        tk.Label(f_operations_facture, text=f"(format YYYYmmdd, expl: {date_aujourdhui_str})", font=('Courier', 9, "italic")).grid(row=2, column=1, sticky="w")
        date_entry = tk.Entry(f_operations_facture, textvariable=date_var)
        date_entry.grid(row=1, column=1, sticky="ew")
        date_entry.bind("<FocusOut>", verifier_longueur_date)

        tk.Label(f_operations_facture, text="Délai de paiement (en jours)").grid(row=3, column=0, sticky="w")
        delai_entry = tk.Entry(f_operations_facture, textvariable=delai_var)
        delai_entry.grid(row=3, column=1, sticky="ew")

    if type_utilise == "debit":
    # Utiliser ces textes pour les labels dans l'interface
        tk.Label(f_operations_facture, text=label_debit_text).grid(row=4, column=0, sticky="w")
        montant_debit_entry = tk.Entry(f_operations_facture, textvariable=montant_debit_var)
        montant_debit_entry.grid(row=4, column=1, sticky="ew")
    else:
        tk.Label(f_operations_facture, text=label_credit_text).grid(row=5, column=0, sticky="w")
        montant_credit_entry = tk.Entry(f_operations_facture, textvariable=montant_credit_var)
        montant_credit_entry.grid(row=5, column=1, sticky="ew")

    tk.Label(f_operations_facture, text="Libellé").grid(row=6, column=0, sticky="w")
    libelle_entry = tk.Entry(f_operations_facture, textvariable=libelle_var)
    libelle_entry.grid(row=6, column=1, sticky="ew")

    def update_combobox(event, no_filtre):
        current_text = compte_contrepartie.get()
        filtered_options = [option for option in lire_plan_comptable(f"{dossier_mandat}/plan_comptable.txt")
                            if current_text.lower() in option.lower()
                            and ((option.startswith(no_filtre) if isinstance(no_filtre, str) else any(option.startswith(nf) for nf in no_filtre)))
                            and not compte_info_num in option]       
        compte_contrepartie['values'] = filtered_options if filtered_options else [option for option in lire_plan_comptable(f"{dossier_mandat}/plan_comptable.txt") if isinstance(no_filtre, str) and option.startswith(no_filtre) or (not isinstance(no_filtre, str) and any(option.startswith(nf) for nf in no_filtre))]
        compte_contrepartie.set(current_text)

    compte_info_num = compte_info.split(" - ")[0]
    
    if compte_info_num.startswith('1') and type_utilise == "debit":
        no_filtre = '3'
    elif compte_info_num.startswith('1') and type_utilise == "credit":
        no_filtre = '10'
    elif compte_info_num.startswith('2') and type_utilise == "debit":
        no_filtre = '10'
    elif compte_info_num.startswith('2') and type_utilise == "credit":
        no_filtre = ['4', '5', '6', '7', '8']
    elif compte_info_num.startswith('1') and type_utilise == "":
        no_filtre = '3'
        type_utilise == "debit"
    elif compte_info_num.startswith('2') and type_utilise == "":
        no_filtre = ['4', '5', '6', '7', '8']
        type_utilise == "credit"
    else:
        no_filtre = ['0']

    comptes_tries = sorted([option for option in lire_plan_comptable(f"{dossier_mandat}/plan_comptable.txt")
                                if not compte_info_num in option
                                and ((option.startswith(no_filtre) if isinstance(no_filtre, str) else any(option.startswith(nf) for nf in no_filtre)))],
                               key=lambda item: item.split(" - ")[0])

    tk.Label(f_operations_facture, text="Contrepartie").grid(row=7, column=0, sticky="w")
    compte_contrepartie = ttk.Combobox(f_operations_facture, textvariable=compte_contrepartie_var, values=comptes_tries)
    compte_contrepartie.grid(row=7, column=1, sticky="ew")
    compte_contrepartie.bind('<KeyRelease>', lambda event: update_combobox(event, no_filtre))

    if paiement:
        tk.Label(f_operations_facture, text="Pièce comptable impactée").grid(row=8, column=0, sticky="w")
        piece_impact_entry = tk.Entry(f_operations_facture, textvariable=piece_impact)
        piece_impact_entry.grid(row=8, column=1, sticky="ew")

        case_a_cocher = tk.Checkbutton(f_operations_facture, text="Paiement partiel", variable=paiement_var)
        case_a_cocher.grid(row=9, column=0, columnspan=2, sticky="ew")

    tk.Button(f_operations_facture, text="Ajouter", command=lambda: enregistrer_operation_compte(compte_info, montant_debit_var, montant_credit_var, libelle_var, compte_contrepartie.get(), True, date_var, delai_var, piece_impact, paiement_var)).grid(row=10, column=0, columnspan=2, sticky="ew")

    # Ajustement de la configuration de la fenêtre
    for widget in f_operations_facture.winfo_children():
        widget.grid(padx=5, pady=5)
    
    f_operations_facture.mainloop()

# FIN FACTURES #########################################################################

chemin_config = "config"
base_config = "config.txt"
base_plan = "plan_comptable.txt"

if not os.path.exists(chemin_config):
    os.makedirs(chemin_config)
    if not os.path.exists(f"{chemin_config}/{base_config}"):
        open(f"{chemin_config}/{base_config}", 'w').close()
    if not os.path.exists(f"{chemin_config}/{base_plan}"):
        open(f"{chemin_config}/{base_plan}", 'w').close()

if not os.path.exists(f"{chemin_config}/{base_config}"):
    open(f"{chemin_config}/{base_config}", 'w').close()

if not os.path.exists(f"{chemin_config}/{base_plan}"):
    open(f"{chemin_config}/{base_plan}", 'w').close()

fichiers = ["plan_comptable.txt", "soldes_initiaux.txt", "journal.txt"]

fenetre = tk.Tk()
titre_fenetre = lire_nom_depuis_config()
if len(titre_fenetre) <= 2:
    titre_fenetre = "Créer un mandat sous: Configuration"
fenetre.title(titre_fenetre)
#fenetre.geometry("420x125")
global dossier_mandat
nom_mandat = titre_fenetre[1]
chemin_mandat = os.path.join(os.getcwd(), chemin_config, nom_mandat)
if chemin_mandat.endswith(':'):
    chemin_mandat = chemin_mandat[:-1]
    
if nom_mandat == "O":
    nom_mandat = ""
    for fichier in fichiers:
        if not os.path.exists(f"{chemin_config}/{fichier}"):
            open(fichier, 'w').close()
elif len(nom_mandat) == 0:
    dossier_mandat = chemin_config
else:
    dossier_mandat = f"{chemin_config}/{nom_mandat}"

if not os.path.exists(chemin_mandat):
    verifier_mandat(chemin_mandat, fichiers, nom_mandat)

bouton_lancer_soldes = tk.Button(fenetre, text="Soldes initiaux", command=lancer_soldes_initiaux)
bouton_lancer_soldes.grid(row=1, column=1, padx=10, pady=5, sticky='w')

bouton_lancer_journal = tk.Button(fenetre, text="Journalisation", command=lancer_journaliser)
bouton_lancer_journal.grid(row=3, column=0, padx=10, pady=5, sticky='w')

bouton_afficher_grand_livre = tk.Button(fenetre, text="Grand Livre", command=lancer_grand_livre)
bouton_afficher_grand_livre.grid(row=3, column=1, padx=10, pady=5, sticky='w')

bouton_config = tk.Button(fenetre, text="Configuration", command=lambda: ouvrir_config(fenetre))
bouton_config.grid(row=1, column=0, padx=10, pady=5, sticky='w')

nom_pour_dico = ""
if os.path.exists("config/config.txt"):
    with open("config/config.txt", "r", encoding='utf-8') as fichier:
        for ligne in fichier:
            if ligne.startswith("Nom:"):
                nom_pour_dico = ligne.split("Nom:")[1].strip()
                if len(nom_pour_dico) > 0:
                    dossier_mandat = os.path.join(os.getcwd(), f"config/{nom_pour_dico}")
                else:
                    dossier_mandat = os.path.join(os.getcwd(), f"config")

if dossier_mandat.endswith(':'):
    dossier_mandat = dossier_mandat[:-1]
comptes_dict = lire_pc(f"{dossier_mandat}/plan_comptable.txt")
selection_compte(fenetre, comptes_dict)

verifier_exercice(fenetre, dossier_mandat, nom_pour_dico)

bouton_totaux = tk.Button(fenetre, text="Bilan et comptes de résultat", command=lambda: afficher_totaux(dossier_mandat))
bouton_totaux.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky='ew')

bouton_about = tk.Button(fenetre, relief="flat", text="À propos", command=afficher_texte)
bouton_about.grid(row=0, column=1, padx=10, pady=5, sticky='w')

fenetre.mainloop()
