# gardenIQ-back
Le projet GardenIQ est un système intelligent d'arrosage de plantes qui utilise des relevés télémétriques pour automatiser l'arrosage en fonction des différents critères.

# API-Rest
L'API de gardenIQ est développée en Python3 avec Django et Django Rest Framework.

---
Pour configurer le projet vous avez deux options disponible :
- Avec un [environnement virtuel](#installation-environnement-virtuel)
- Avec [Docker et docker compose](#docker-et-docker-compose)
--- 

# Installation environnement virtuel
Le projet utilise Python version 3.13.5. Vérifie que la bonne version est bien présente.

Tu peux utiliser `pyenv` pour installer et gérer différente versions de Python.

## 1. Installation de `pipenv`

Une fois que tu as installé `pyenv` et configuré la version Python appropriée (3.13.5), tu peux installer **pipenv** pour gérer les environnements virtuels et les dépendances du projet.

### 1.1. Installation de `pipenv`

### Étapes :

1. **Installer pipenv** en utilisant `pip` (le gestionnaire de paquets Python intégré) :
    
    ```bash
    pip install pipenv
    ```
    
2. **Vérifie l’installation** :
    
    ```bash
    pipenv --version
    ```
    

---

## 2. Installation de l'environnement de développement pour le projet

Une fois `pyenv` et `pipenv` installés, suis ces étapes pour configurer l'environnement du projet :

### 2.1. Cloner le dépôt du projet

Clone le dépôt gardenIQ-back du projet via Git :

```bash
git clone https://github.com/riderflo85/gardenIQ-back.git
cd gardenIQ-back
```

### 2.2. Créer et activer l'environnement virtuel avec `pipenv`

1. **Créer l'environnement virtuel et installer les dépendances** :
    
    ```bash
    pipenv install --dev
    ```
    
    Cette commande va :
    
    - Créer un environnement virtuel basé sur la version Python 3.13.5
    - Installer les dépendances spécifiées dans le fichier `Pipfile`.
2. **Activer l'environnement virtuel** :
    
    ```bash
    pipenv shell
    ```
    
3. **Vérifie que l'environnement est bien activé** :
    
    ```bash
    python --version
    ```
    
    Tu devrais voir `Python 3.13.5`.
    

### 2.3. Lancer le serveur backend

Une fois dans l'environnement virtuel, tu peux exécuter le serveur backend :

```bash
./manage.py runserver
OU
python manage.py runserver
```

---

## 3. Notes supplémentaires

- **Gestion des dépendances** : Si tu as besoin d'ajouter une nouvelle bibliothèque au projet, utilise la commande suivante pour ajouter la dépendance au `Pipfile` :
    
    ```bash
    pipenv install <package>
    ```
    
- **Synchronisation des dépendances** : Pour synchroniser tes dépendances avec celles définies dans le `Pipfile.lock` (par exemple, après un `git pull`), utilise :
    
    ```bash
    pipenv sync
    ```

---

# Docker et docker compose
## 📁 Prérequis

* [Docker](https://www.docker.com/) installé
* [Docker Compose](https://docs.docker.com/compose/) installé
* Python 3.13 pour le script USB
* Un fichier `Pipfile` (et éventuellement `Pipfile.lock`) gérant les dépendances Python

---

## 🧪 Lancer en développement avec hot-reload

### 1. Démarrer le conteneur `web-dev`

```bash
docker compose up web-dev
```

* Accès à l’application : [http://localhost:8000](http://localhost:8000)
* Le code source est monté en volume (`./:/app`), donc les modifications sont rechargées automatiquement.

---

## 🔌 Connexion automatique à un périphérique USB

🧠 Le script Python (`start_usb_docker.py`) détecte automatiquement un périphérique série USB (comme une carte MicroPython), puis :

* 📝 Génère un fichier `docker-compose-usb-override.yml` dynamique
* 🔌 Monte le périphérique dans Docker sous `/dev/ttyUSBCard1`
* 🚀 Lance Docker Compose avec le périphérique monté

### ▶️ Lancer le script

```bash
python start_usb_docker.py
```

Par défaut, il cherche un périphérique dont le **manufacturer** contient `"MicroPython"`.

---

### ⚙️ Options personnalisées

Tu peux utiliser des options CLI pour affiner la détection :

| Option | Description                                                            |
| ------ | ---------------------------------------------------------------------- |
| `-t`   | Type de filtre : `manufacturer` (défaut) ou `hwid`                     |
| `-v`   | Valeur recherchée dans le champ sélectionné (`MicroPython` par défaut) |

**Exemples :**

```bash
python start_usb_docker.py -t manufacturer -v MicroPython
python start_usb_docker.py -t hwid -v "USB VID:PID=1234:ABCD"
```

🛠️ **Astuce** :
Tu peux afficher les valeurs possibles de `manufacturer` ou `hwid` pour tes périphériques connectés à l’aide de la commande suivante :

```bash
python manage.py list_devices --verbose
```

Cela affichera tous les périphériques disponibles avec leurs informations utiles pour le filtrage (fabricant, identifiants, port, etc.).

---

### ✅ Si le périphérique est détecté

Le script affichera :

```
✅ usb card successfully detected !
    Host port is `/dev/ttyUSB1`
    Mounted on docker to `/dev/ttyUSBCard1`

📝 File `docker-compose-usb-override.yml` generated...
🚀 Launch docker compose...
```

---

### ⚠️ Si le périphérique existe mais n’est pas accessible

Le script te suggère la correction :

```
⚠️ Usb card `/dev/ttyUSB1` exist but does not access: Permission denied.
   Add your user to `dialout` group and restart session :
   sudo usermod -aG dialout $USER
```

---

### 🔍 Vérifier que le port USB est bien monté dans le conteneur

Une fois le script exécuté et le conteneur lancé, tu peux t’assurer que le périphérique USB est bien visible à l’intérieur du conteneur.

#### 1. Accéder au conteneur `web-dev`

```bash
docker exec -it <nom_du_conteneur> bash
```

> Remplace `<nom_du_conteneur>` par celui de ton conteneur (tu peux lister les noms avec `docker ps`).
> Exemple courant : `web-dev-1` ou simplement `web-dev`.

#### 2. Lister les périphériques disponibles

Dans le terminal du conteneur, tape :

```bash
ls -l /dev/ttyUSB*
```

Tu devrais voir une sortie du type :

```
crw-rw---- 1 root dialout 188, 0 Jul 17 15:42 /dev/ttyUSBCard1
```

Cela confirme que le périphérique est bien monté avec le bon nom (défini dans le script Python par `DOCKER_USB_PORT`).

#### 3. Vérifier l’accès depuis Python (optionnel)

Tu peux également tester depuis un shell Python dans le conteneur :

```bash
python
>>> import serial
>>> s = serial.Serial("/dev/ttyUSBCard1")
>>> s.close()
```

Aucune erreur = le périphérique est bien monté et accessible.

---

## 🔧 Configuration optionnelle

* Tu peux modifier le port d’écoute de l’application (`8000`, `8001`) dans `docker-compose.yml` si besoin.
