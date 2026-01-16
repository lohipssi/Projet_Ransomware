# Ransomware Pédagogique - Projet Python - Lohan et Melvin

## 📋 Fonctionnalités implémentées

### Partie obligatoire ✅

**Côté Client (malware):**
- ✅ Génération de clé de chiffrement depuis `/dev/urandom` avec lettres A-Z uniquement
- ✅ Identification unique de la machine via UUID (`/proc/sys/kernel/random/uuid`)
- ✅ Chiffrement XOR réversible des fichiers
- ✅ Parcours récursif du répertoire cible
- ✅ Exfiltration des informations (UUID + clé) vers le serveur C2
- ✅ Réception et exécution de commandes à distance
- ✅ Commande de déchiffrement des fichiers
- ✅ Exécution de commandes système sans privilèges admin
- ✅ Upload de fichiers (client → serveur)
- ✅ Download de fichiers (serveur → client)

**Côté Serveur (C2):**
- ✅ Acceptation de connexions TCP multiples
- ✅ Réception et stockage persistant de l'UUID et de la clé
- ✅ Envoi de commandes aux clients connectés
- ✅ Menu interactif pour contrôler les victimes
- ✅ Base de données des victimes (fichier texte)

### Partie bonus ✅

- ✅ **Système de logs** : Horodatage avec niveaux (INFO, ERROR, SUCCESS, WARNING)
- ✅ **Multithreading** : Le serveur peut gérer plusieurs clients simultanément
- ✅ **Gestion d'erreurs** : Try/except pour gérer les erreurs réseau et système

## 🏗️ Architecture globale

Le projet suit une architecture **client-serveur** classique d'un ransomware :

```
┌─────────────────┐                    ┌─────────────────┐
│   CLIENT        │                    │   SERVEUR C2    │
│   (Victime)     │                    │   (Attaquant)   │
├─────────────────┤                    ├─────────────────┤
│ 1. Génère UUID  │                    │ 1. Écoute TCP   │
│ 2. Génère clé   │ ──── TCP ───────→  │ 2. Reçoit infos │
│ 3. Exfiltre     │                    │ 3. Stocke DB    │
│ 4. Attend ordre │ ←──── CMD ───────  │ 4. Menu interac │
│ 5. Chiffre XOR  │                    │ 5. Logs events  │
└─────────────────┘                    └─────────────────┘
```

### Flux d'exécution

1. **Phase d'initialisation** : Le client génère un UUID unique et une clé de 16 lettres A-Z
2. **Phase de connexion** : Établissement d'une connexion TCP avec le serveur C2
3. **Phase d'exfiltration** : Envoi immédiat de l'UUID et de la clé au serveur
4. **Phase de contrôle** : Boucle infinie d'attente et d'exécution des commandes
5. **Phase d'action** : Chiffrement/déchiffrement, exécution de commandes, transferts de fichiers

## 🚀 Comment lancer le projet

### Prérequis

- Python 3.x (aucune dépendance externe requise)
- Système Linux (pour `/dev/urandom` et `/proc/sys/kernel/random/uuid`)
- VM de test pour le client (obligatoire!)

### Étape 1 : Démarrer le serveur C2

Sur ta machine hôte ou une VM serveur :

```bash
python3 server.py
```

Tu devrais voir :
```
[2026-01-16 10:00:00] [INFO] Démarrage du serveur C2 sur 0.0.0.0:9526
[2026-01-16 10:00:00] [INFO] Serveur en écoute, en attente de connexions...
```

### Étape 2 : Lancer le client (dans une VM)

Sur la VM victime :

```bash
python3 client.py
```

Le client va automatiquement :
- Se connecter au serveur
- Envoyer son UUID et sa clé
- Attendre les ordres

### Étape 3 : Contrôler la victime

Dans le terminal du serveur, tu peux maintenant taper des commandes :

```bash
Action (chiffrer/dechiffrer/system/upload/download/exit) > chiffrer
```

**Commandes disponibles :**
- `chiffrer` : Chiffre tous les fichiers du dossier cible
- `dechiffrer` : Déchiffre les fichiers (restaure l'original)
- `system` : Exécute une commande shell (ex: `ls -la`, `whoami`)
- `upload` : Envoie un fichier du serveur vers le client
- `download` : Récupère un fichier depuis le client
- `exit` : Déconnecte le client proprement

## 🔌 Fonctionnement du protocole

### Format des messages

Le protocole utilise **TCP sur le port 9526** avec des messages en texte brut.

#### 1. Enregistrement initial (Client → Serveur)

```
UUID:a1b2c3d4-e5f6-7890-abcd-ef1234567890 | CLE:XYZABCDEFGHIJKLM
```

#### 2. Commandes (Serveur → Client)

Les commandes sont envoyées sous forme de mots-clés simples :

```
chiffrer
dechiffrer
system
upload
download
exit
```

#### 3. Protocole de transfert de fichiers

**Upload (Serveur → Client) :**
```
1. Serveur envoie : "upload"
2. Serveur envoie : nom du fichier
3. Serveur envoie : taille sur 16 octets (ex: "1024            ")
4. Serveur envoie : données brutes du fichier
5. Client répond : "Fichier reçu avec succès"
```

**Download (Client → Serveur) :**
```
1. Serveur envoie : "download"
2. Serveur envoie : nom du fichier demandé
3. Client envoie : taille sur 16 octets OU "ERREUR          "
4. Client envoie : données brutes (si fichier existe)
```

#### 4. Réponses (Client → Serveur)

```
"Chiffrement effectué sur 42 fichiers"
"Déchiffrement effectué sur 42 fichiers"
"Commande exécutée" (ou sortie de la commande)
```

### Pourquoi ce protocole est simple

- Pas de JSON ou XML pour rester léger
- Messages texte faciles à débugger
- Taille fixe de 16 octets pour les métadonnées de fichiers (évite la désynchronisation)
- Pas d'authentification (pour la simplicité pédagogique)

## ⚠️ Limites et faiblesses du ransomware

### Faiblesses cryptographiques

1. **XOR est très faible** : L'algorithme XOR peut être cassé facilement par analyse de fréquence
2. **Clé stockée en mémoire** : Un dump mémoire révèle la clé en clair
3. **Clé aléatoire mais courte** : 16 caractères seulement parmi 26 possibilités (26^16 combinaisons)
4. **Pas de dérivation de clé** : Pas de PBKDF2 ou Argon2

### Faiblesses réseau

5. **Communication en clair** : Aucun chiffrement TLS/SSL sur le réseau
6. **Pas d'authentification** : N'importe qui peut se connecter au serveur C2
7. **Adresse IP hardcodée** : Facile à bloquer par un firewall
8. **Port fixe** : Le port 9526 peut être détecté facilement

### Faiblesses de conception

9. **Pas de persistance** : Le malware s'arrête si on ferme le terminal
10. **Dossier cible limité** : Seulement `~/Documents/CIBLE` au lieu du home complet
11. **Ignore les fichiers .py** : Détection facile par analyse comportementale
12. **Connexion unique** : Si le serveur tombe, le malware est inutile
13. **Logs verbeux** : Le serveur laisse des traces claires de ses actions

### Détection facile

14. **Pas d'obfuscation** : Le code Python est lisible en clair
15. **Comportement prévisible** : Connexion immédiate au C2
16. **Pas d'évasion antivirus** : Aucune technique d'anti-debugging

## 📚 Ce qu'on apprend avec ce projet

Malgré ses faiblesses, ce ransomware permet de comprendre :

- ✅ Comment fonctionne un malware client/serveur
- ✅ Les bases du chiffrement symétrique (XOR)
- ✅ La manipulation de fichiers en Python
- ✅ Les sockets TCP et la communication réseau
- ✅ L'exécution de commandes système
- ✅ L'importance de la sécurité (en voyant toutes les failles!)

## 📁 Structure des fichiers

```
ransomware-pedagogique/
├── README.md                    # Ce fichier
├── client.py                    # Le malware (à exécuter dans la VM)
├── server.py                    # Le serveur C2 (attaquant)
├── base_victimes.txt            # DB des victimes (généré auto)
├── serveur_logs.txt             # Logs du serveur (généré auto)
└── DL_*                         # Fichiers téléchargés (préfixe DL_)
```




