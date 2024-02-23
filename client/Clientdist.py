import requests, os, shutil
import tkinter as tk
from bs4 import BeautifulSoup
from datetime import datetime
from tkinter import messagebox
from urllib.parse import urljoin

def sauvegarder_repertoires_locaux():
    chemin_local = os.getcwd()
    nom_repertoire_backups = "backups"
    chemin_backups = os.path.join(chemin_local, nom_repertoire_backups)

    os.makedirs(chemin_backups, exist_ok=True)
    nom_sous_repertoire = "backup_" + datetime.now().strftime("%Y%m%d-%H%M%S")
    chemin_sous_repertoire = os.path.join(chemin_backups, nom_sous_repertoire)
    
    os.makedirs(chemin_sous_repertoire, exist_ok=True)
    for nom in os.listdir(chemin_local):
        chemin_complet = os.path.join(chemin_local, nom)
        if os.path.isdir(chemin_complet) and nom != nom_repertoire_backups:
            destination = os.path.join(chemin_sous_repertoire, nom)
            shutil.copytree(chemin_complet, destination)

def nettoyer_chemin(chemin):
    # Remplacer les caractères non désirés par des underscores ou d'autres substitutions valides
    for char in [':', '?', '*', '"', '<', '>', '|', 'http:', 'https:']:
        chemin = chemin.replace(char, '_')
    return chemin

def telecharger_fichier(url_fichier, chemin_fichier_local):
    reponse = requests.get(url_fichier, stream=True)
    if reponse.status_code == 200:
        with open(chemin_fichier_local, 'wb') as fichier:
            for chunk in reponse.iter_content(chunk_size=8192):
                fichier.write(chunk)
        #print(f"Fichier téléchargé et sauvegardé : {chemin_fichier_local}")
    else:
        messagebox.showerror("Erreur de téléchargement", f"Erreur lors du téléchargement de {url_fichier}: Status {reponse.status_code}")

def obtenir_temps_derniere_modification(url_complet):
    try:
        reponse = requests.head(url_complet)
        last_modified = reponse.headers.get('Last-Modified')
        if last_modified:
            temps_distant = time.mktime(datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S GMT').timetuple())
            return temps_distant
    except Exception as e:
        print(f"Erreur lors de l'obtention du temps de la dernière modification : {e}")
    return None

def creer_fichier_local(fichier_info, spec):
    # Extraction des informations
    url_complet = fichier_info['url_complet']
    nom_fichier = fichier_info['nom_fichier']
    url_repertoire = fichier_info['url_base']
    partie_chemin = url_repertoire.split('//')[1]  # Enlève le schéma (http, https)
    partie_chemin = partie_chemin.split(':')[1]  # Enlève l'url
    partie_chemin = partie_chemin[5:]  # Enlève les 5 premiers caractères
    chemin_specifique_repertoire = nettoyer_chemin(partie_chemin)
    chemin_de_base_local = os.path.join(os.getcwd(), chemin_specifique_repertoire)

    nom_fichier_nettoye = nettoyer_chemin(nom_fichier)
    chemin_local_complet = os.path.join(chemin_de_base_local, nom_fichier_nettoye)

    doit_telecharger = False
    if os.path.exists(chemin_local_complet):
        temps_local = os.path.getmtime(chemin_local_complet)
        temps_distant = obtenir_temps_derniere_modification(url_complet)
        if temps_distant > temps_local:
            doit_telecharger = True

    if not os.path.exists(chemin_local_complet) and spec == "racine":
        os.makedirs(os.path.dirname(chemin_local_complet), exist_ok=True)
        telecharger_fichier(url_complet, chemin_local_complet)
    elif doit_telecharger and spec == "racine":
        os.makedirs(os.path.dirname(chemin_local_complet), exist_ok=True)
        telecharger_fichier(url_complet, chemin_local_complet)
    elif spec == "dossier":
        os.makedirs(os.path.dirname(chemin_local_complet), exist_ok=True)
        telecharger_fichier(url_complet, chemin_local_complet)

def lister_repertoires(url, liste_repertoires=[], chemin_actuel=""):
    reponse = requests.get(url)
    if reponse.status_code == 200:
        soup = BeautifulSoup(reponse.text, 'html.parser')
        for lien in soup.find_all('a'):
            href = lien.get('href')
            if href.endswith('/') and not href.startswith('?') and not href.startswith('/') and not href == "../":
                sous_chemin = urljoin(chemin_actuel + '/', href)
                url_complet = urljoin(url, sous_chemin)
                
                if url_complet not in liste_repertoires:
                    liste_repertoires.append(url_complet)
                
                lister_repertoires(url_complet, liste_repertoires, sous_chemin)
    return liste_repertoires

def lister_fichiers_dans_repertoire(url):
    fichiers = []
    reponse = requests.get(url)
    if reponse.status_code == 200:
        soup = BeautifulSoup(reponse.text, 'html.parser')
        for lien in soup.find_all('a'):
            href = lien.get('href')
            if not href.endswith('/') and not href.startswith('?') and not href.startswith('/') and not href == "../":
                url_fichier_complet = urljoin(url, href)
                # Ajouter un dictionnaire contenant l'URL complète, l'URL de base, et le nom du fichier
                fichiers.append({
                    "url_complet": url_fichier_complet,
                    "url_base": url,
                    "nom_fichier": href
                })
    return fichiers

def afficher_message_fin(fenetre):
    fin = tk.Tk()
    fin.withdraw()  # Cacher la fenêtre sous-jacente
    messagebox.showinfo("Terminé", "Tâche terminée avec succès.")
    fenetre.destroy()
    fin.destroy()  # Fermer l'interface graphique après l'affichage du message

def telecharger_contenu(fenetre):
    try:
        sauvegarder_repertoires_locaux()
        with open('Clientdist.txt', 'r') as file:
            url_base = file.read().strip()

        fichiers_racine = lister_fichiers_dans_repertoire(url_base)
        spec = "racine"
        for fichier in fichiers_racine:
            creer_fichier_local(fichier, spec)
            
        repertoires = lister_repertoires(url_base)
        chemin_de_base_local = url_base.split('//')[-1]
        for repertoire in repertoires:
            fichiers = lister_fichiers_dans_repertoire(repertoire)
            spec = "dossier"
            for fichier in fichiers:
                creer_fichier_local(fichier,spec)
        afficher_message_fin(fenetre)
    except Exception as e:
        messagebox.showerror("Erreur de téléchargement", f"Une erreur est survenue: {e}")

fenetre = tk.Tk()
fenetre.title("Web")

bouton_telecharger = tk.Button(fenetre, text="Télécharger les mandats", command=lambda: telecharger_contenu(fenetre))
bouton_telecharger.pack(pady=20, padx=10)

fenetre.mainloop()