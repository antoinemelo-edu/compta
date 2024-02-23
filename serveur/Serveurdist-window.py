import tkinter as tk
from tkinter import messagebox
import os, threading, http.server, socket, socketserver, webbrowser


PORT = 8010
httpd = None
server_thread = None

class UTF8HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_response(self, code, message=None):
        super().send_response(code, message=message)
    
    def end_headers(self):
        super().end_headers()
    
    def do_GET(self):
        chemin_fichier = self.translate_path(self.path)
        
        if os.path.isfile(chemin_fichier):
            # Déterminer le type de contenu basé sur l'extension du fichier
            if chemin_fichier.endswith('.exe'):
                content_type = 'application/octet-stream'
            else:
                content_type = 'text/plain; charset=utf-8'
                
            try:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                
                with open(chemin_fichier, 'rb') as fichier:
                    # Lire et envoyer le fichier en binaire sans décodage
                    self.wfile.write(fichier.read())
            except FileNotFoundError:
                self.send_error(404, "Fichier non trouvé")
            except Exception as e:
                self.send_error(500, f"Erreur interne du serveur: {str(e)}")
        else:
            super().do_GET()

def serveur_thread(httpd):
    httpd.serve_forever()

def demarrer_serveur():
    global httpd, server_thread
    if not httpd:
        Handler = UTF8HTTPRequestHandler
        httpd = socketserver.TCPServer(("", PORT), Handler)
        server_thread = threading.Thread(target=serveur_thread, args=(httpd,))
        server_thread.daemon = True
        server_thread.start()

        # Trouver l'adresse IP du PC
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        IP = "http://" + s.getsockname()[0] + ":" + str(PORT)
        s.close()  # Il est important de fermer le socket après utilisation

        # Écrire l'adresse IP dans Clientdist.txt
        try:
            with open("Clientdist.txt", "w") as fichier_client:
                fichier_client.write(IP)
                msg = "L'adresse IP a été écrite dans Clientdist.txt"
        except Exception as e:
            msg = f"Une erreur est survenue lors de l'écriture dans le fichier : {e}"

        # Afficher le message dans une boîte de dialogue
        messagebox.showinfo("Adresse IP", msg)

        print(f"Serveur démarré à {IP}")

def arreter_serveur(fenetre):
    global httpd
    if httpd:
        httpd.shutdown()
        httpd.server_close()
        httpd = None
        messagebox.showinfo("Serveur arrêté", "Le serveur a été arrêté avec succès.")
        fenetre.destroy()  # Ferme la fenêtre principale
    else:
        messagebox.showinfo("Serveur", "Le serveur n'est pas en cours d'exécution.")


def lancer_interface():
    fenetre = tk.Tk()
    fenetre.title("Web")

    tk.Button(fenetre, text="Arrêter le serveur", command=lambda: arreter_serveur(fenetre)).pack(pady=20, padx=10)

    fenetre.mainloop()

if __name__ == "__main__":
    demarrer_serveur()  # Démarrer le serveur dès le lancement du script
    lancer_interface()  # Lancer l'interface graphique
