import http.server, socket, socketserver, webbrowser
import os, shutil
import tkinter as tk
from tkinter import messagebox

PORT = 8010
# php -S localhost:8010 -t .
# php -S 127.0.0.1:8010 -t .
# php -S 0.0.0.0:8010          # Disponible depuis d'autre machine par IPv4
# php -S [::0]:8010            # Disponible depuis d'autre machine par IPv6
# python3 -m http.server 8010 --cgi

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

dossier_config = "dist"
chemin_home = os.environ.get('USERPROFILE') or os.environ.get('HOME')
chemin_mandat = os.path.join(os.getcwd(), dossier_config)
chemin_config = os.path.join(chemin_home, chemin_mandat)

if os.environ.get('HOME'):
    print("Dossier home:", os.environ.get('HOME'))
else:
    print("Dossier user:", os.environ.get('USERPROFILE'))

if os.path.exists(chemin_config):
    os.chdir(chemin_config)
    print(f"Mandat vers {chemin_config}")
else:
    print(f"Le dossier config n'a pas été trouvé sous {chemin_config}")

# creating a http request
Handler = http.server.SimpleHTTPRequestHandler
hostname = socket.gethostname()

# finding the IP address of the PC
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
IP = "http://" + s.getsockname()[0] + ":" + str(PORT)

root = tk.Tk()
try:
    with open("../Clientdist.txt", "w") as fichier_client:
        fichier_client.write(IP)
        msg = "L'adresse IP a été écrite dans Clientdist.txt"
except Exception as e:
    msg = f"Une erreur est survenue lors de l'écriture dans le fichier : {e}"
messagebox.showinfo("Adresse IP", msg)
root.destroy()

# continuous stream of data between client and server
with socketserver.TCPServer(("", PORT), UTF8HTTPRequestHandler) as httpd:
    print(f"Serveur sous {IP} (ou {hostname})")
    httpd.serve_forever()