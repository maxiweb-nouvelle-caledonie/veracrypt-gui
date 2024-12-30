# VeraCrypt GUI

Une interface graphique moderne pour VeraCrypt écrite en Python avec PyQt6.

## Fonctionnalités

- Création de volumes VeraCrypt avec une interface intuitive
- Montage/démontage de volumes VeraCrypt
- Gestion des favoris pour un accès rapide aux volumes fréquemment utilisés
- Support des périphériques (clés USB, disques externes)
- Interface en français
- Collecte d'entropie interactive pour une meilleure sécurité
- Montage automatique après la création d'un volume
- Gestion des points de montage dans le répertoire personnel

## Prérequis

- Python 3.6 ou supérieur
- VeraCrypt installé sur le système
- PyQt6
- Droits sudo pour les opérations de montage/démontage

## Installation de VeraCrypt sous Linux

### Méthode 1 : Via le dépôt officiel (Ubuntu/Debian)

1. Ajouter le dépôt VeraCrypt :
```bash
sudo add-apt-repository ppa:unit193/encryption
sudo apt update
```

2. Installer VeraCrypt :
```bash
sudo apt install veracrypt
```

### Méthode 2 : Via le fichier .deb (Recommandé)

1. Télécharger le dernier fichier .deb depuis le site officiel :
   - Visiter [https://www.veracrypt.fr/en/Downloads.html](https://www.veracrypt.fr/en/Downloads.html)
   - Télécharger la version "Debian et Ubuntu"

2. Installer les dépendances requises :
```bash
sudo apt install libwxgtk3.0-gtk3-0v5 libwxbase3.0-0v5
```

3. Installer le fichier .deb :
```bash
sudo dpkg -i veracrypt-*-setup.deb
```

4. Corriger les dépendances si nécessaire :
```bash
sudo apt -f install
```

### Méthode 3 : Compilation depuis les sources

1. Installer les dépendances de compilation :
```bash
sudo apt install build-essential pkg-config libfuse-dev wx-common libwxgtk3.0-gtk3-dev
```

2. Télécharger et extraire les sources depuis [https://www.veracrypt.fr/en/Downloads.html](https://www.veracrypt.fr/en/Downloads.html)

3. Compiler et installer :
```bash
tar xvf VeraCrypt_*_Source.tar.bz2
cd VeraCrypt_*_Source
make
sudo make install
```

### Vérification de l'installation

Pour vérifier que VeraCrypt est correctement installé :
```bash
veracrypt --version
```

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-username/veracrypt-gui.git
cd veracrypt-gui
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

1. Lancer l'application :
```bash
python main.py
```

2. Création d'un volume :
   - Cliquer sur "Volumes" > "Créer un volume"
   - Suivre l'assistant de création
   - Le volume sera automatiquement monté après sa création

3. Montage d'un volume :
   - Cliquer sur "Monter un fichier"
   - Sélectionner le volume à monter
   - Entrer le mot de passe
   - Le volume apparaîtra dans la liste des volumes montés

4. Gestion des favoris :
   - Ajouter des volumes fréquemment utilisés aux favoris
   - Option pour sauvegarder le mot de passe
   - Montage rapide depuis la liste des favoris

## Structure du projet

- `gui/` : Contient tous les composants de l'interface graphique
  - `main_window.py` : Fenêtre principale de l'application
  - `create_volume_wizard.py` : Assistant de création de volume
  - `mount_dialog.py` : Dialogue de montage
  - `progress_dialog.py` : Dialogue de progression
  
- `utils/` : Utilitaires et fonctions communes
  - `veracrypt.py` : Interface avec l'exécutable VeraCrypt
  - `entropy_collector.py` : Collecte d'entropie pour la création de volume
  - `favorites.py` : Gestion des favoris
  - `constants.py` : Constantes de l'application

## Sécurité

- Les mots de passe ne sont jamais stockés en clair
- Utilisation de la collecte d'entropie pour une meilleure qualité de chiffrement
- Support de plusieurs algorithmes de chiffrement (AES, Serpent, Twofish)
- Support de différents systèmes de fichiers (FAT, exFAT, NTFS, EXT4)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## Contact

contact@maxiweb.nc
