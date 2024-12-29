"""
Utilitaires pour interagir avec VeraCrypt en ligne de commande.
"""

import os
import subprocess
from typing import List, Tuple
from . import system
import time
from .sudo_session import sudo_session
import datetime

def get_user_mount_dir() -> str:
    """Retourne le répertoire de montage pour l'utilisateur."""
    return os.path.expanduser('~')

def check_mount_point(mount_point: str) -> Tuple[bool, str]:
    """Vérifie si un point de montage est valide.
    
    Args:
        mount_point: Point de montage à vérifier
        
    Returns:
        Tuple contenant:
        - Un booléen indiquant si le point de montage est valide
        - Un message d'erreur si le point de montage n'est pas valide
    """
    # S'assurer que le point de montage est dans le répertoire utilisateur
    user_dir = get_user_mount_dir()
    if not mount_point.startswith(user_dir):
        return False, f"Le point de montage doit être dans votre répertoire personnel ({user_dir})"
        
    # Vérifier si le répertoire existe
    if os.path.exists(mount_point):
        # Vérifier si le répertoire est vide
        if os.path.isdir(mount_point) and os.listdir(mount_point):
            return False, f"Le répertoire {mount_point} n'est pas vide"
    else:
        # Créer le répertoire
        try:
            os.makedirs(mount_point, exist_ok=True)
        except Exception as e:
            return False, f"Impossible de créer le répertoire {mount_point}: {str(e)}"
            
    return True, ""

def generate_mount_point() -> str:
    """Génère un point de montage unique dans le répertoire utilisateur."""
    # Utiliser un timestamp pour le nom du répertoire
    mount_dir = get_user_mount_dir()
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    mount_point = os.path.join(mount_dir, f"veracrypt_{timestamp}")
    
    # S'assurer que le point de montage n'existe pas déjà
    counter = 0
    while os.path.exists(mount_point):
        counter += 1
        mount_point = os.path.join(mount_dir, f"veracrypt_{timestamp}_{counter}")
        
    return mount_point

def run_veracrypt_command(command: list, need_admin: bool = False) -> Tuple[bool, str, str]:
    """Exécute une commande VeraCrypt.
    
    Args:
        command: Liste contenant la commande et ses arguments
        need_admin: Si True, exécute la commande avec sudo
        
    Returns:
        Tuple contenant:
        - Un booléen indiquant si la commande a réussi
        - La sortie standard
        - La sortie d'erreur
    """
    try:
        if need_admin:
            success, stdout, stderr = sudo_session.run_with_sudo(command)
        else:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
            success = process.returncode == 0
            stdout = process.stdout
            stderr = process.stderr
            
        return success, stdout, stderr
        
    except Exception as e:
        return False, '', str(e)

def list_mounted_volumes() -> List[Tuple[str, str]]:
    """Liste les volumes VeraCrypt montés.
    
    Returns:
        Liste de tuples contenant:
        - Le numéro de slot
        - Le point de montage
    """
    try:
        command = [
            system.Constants.VERACRYPT_PATH,
            '--text',
            '--non-interactive',
            '--list'
        ]
        
        print(f"Exécution de la commande: {' '.join(command)}")
        
        # La liste des volumes ne nécessite pas sudo
        process = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        stdout = process.stdout
        stderr = process.stderr
        
        print(f"Sortie standard:\n{stdout}")
        print(f"Sortie d'erreur:\n{stderr}")
        
        # "No volumes mounted" est une sortie normale quand aucun volume n'est monté
        if "No volumes mounted" in stderr:
            print("Aucun volume monté")
            return []
            
        if process.returncode != 0 and stderr and "No volumes mounted" not in stderr:
            print(f"Erreur lors de la liste des volumes: {stderr}")
            return []
            
        volumes = []
        for line in stdout.splitlines():
            print(f"Analyse de la ligne: {line}")
            if not line.strip():
                continue
                
            # Format: "1: /dev/sdc2 /dev/loop32 /media/jayces/veracrypt_20241226_205820"
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].endswith(':'):
                slot = parts[0].rstrip(':')  # Extraire le numéro de slot
                mount_point = parts[-1] if len(parts) >= 4 else ""  # Le point de montage est le dernier élément
                device = parts[1]  # Le périphérique est le deuxième élément
                if mount_point:
                    print(f"Volume trouvé - slot: {slot}, device: {device}, mount_point: {mount_point}")
                    volumes.append((slot, mount_point))
                    
        print(f"Volumes trouvés: {volumes}")
        return volumes
        
    except Exception as e:
        print(f"Erreur lors de la liste des volumes: {str(e)}")
        return []

def check_mount_points() -> List[Tuple[str, str]]:
    """Vérifie l'intégrité des points de montage.
    
    Returns:
        Liste de tuples (point de montage, erreur)
    """
    issues = []
    mounted_volumes = list_mounted_volumes()
    
    # Récupérer tous les points de montage
    mount_points = [mount_point for _, mount_point in mounted_volumes]
    
    # Vérifier chaque point de montage
    for _, mount_point in mounted_volumes:
        # Vérifier si le point de montage existe
        if not os.path.exists(mount_point):
            issues.append((mount_point, "Le point de montage n'existe pas"))
            continue
            
        # Vérifier si le point de montage est accessible
        try:
            os.listdir(mount_point)
        except Exception as e:
            issues.append((mount_point, f"Le point de montage n'est pas accessible : {str(e)}"))
            
    return issues

def clean_empty_mount_points() -> List[str]:
    """Nettoie les points de montage vides.
    
    Returns:
        Liste des points de montage nettoyés
    """
    cleaned = []
    user_dir = get_user_mount_dir()
    
    # Parcourir les répertoires de montage
    for item in os.listdir(user_dir):
        mount_point = os.path.join(user_dir, item)
        if os.path.isdir(mount_point) and item.startswith("veracrypt_"):
            try:
                # Vérifier si le répertoire est vide et n'est pas monté
                if not os.listdir(mount_point) and not any(mp == mount_point for _, mp in list_mounted_volumes()):
                    os.rmdir(mount_point)
                    cleaned.append(mount_point)
            except Exception as e:
                print(f"Erreur lors du nettoyage de {mount_point}: {e}")
                
    return cleaned

def mount_volume(volume_path: str, mount_point: str, password: str) -> Tuple[bool, str]:
    """Monte un volume VeraCrypt.
    
    Args:
        volume_path: Chemin vers le volume à monter
        mount_point: Point de montage
        password: Mot de passe du volume
        
    Returns:
        Tuple contenant:
        - Un booléen indiquant si le montage a réussi
        - Un message d'erreur si le montage a échoué
    """
    try:
        print(f"Tentative de montage du volume {volume_path} sur {mount_point}")
        
        # Vérifier que le volume existe
        if not os.path.exists(volume_path):
            return False, f"Le volume {volume_path} n'existe pas"
            
        # Vérifier le point de montage
        valid, error = check_mount_point(mount_point)
        if not valid:
            return False, error
            
        # Vérifier si le volume est déjà monté
        mounted_volumes = list_mounted_volumes()
        for _, existing_mount in mounted_volumes:
            if os.path.exists(existing_mount):
                try:
                    # Vérifier si le volume est déjà monté quelque part
                    if os.path.samefile(volume_path, existing_mount):
                        return False, f"Le volume {volume_path} est déjà monté sur {existing_mount}"
                except OSError:
                    # Ignorer les erreurs de comparaison de fichiers
                    pass
                    
            # Vérifier si le point de montage est déjà utilisé
            if os.path.exists(mount_point) and os.path.samefile(existing_mount, mount_point):
                return False, f"Le point de montage {mount_point} est déjà utilisé"
            
        # Monter le volume
        command = [
            system.Constants.VERACRYPT_PATH,
            '--text',  # Mode texte
            '--non-interactive',  # Mode non interactif
            '--mount',  # Action de montage
            volume_path,  # Chemin du volume
            mount_point,  # Point de montage
            '--password', password,  # Mot de passe
            '--verbose'  # Plus de détails dans la sortie
        ]
        
        print(f"Exécution de la commande: {' '.join(command)}")
        
        # Le montage nécessite sudo
        success, stdout, stderr = sudo_session.run_with_sudo(command)
        
        print(f"Sortie standard du montage:\n{stdout}")
        print(f"Sortie d'erreur du montage:\n{stderr}")
        
        if success:
            print("Montage réussi")
            return True, ''
        else:
            # Nettoyer le point de montage en cas d'erreur
            try:
                if os.path.exists(mount_point) and not os.listdir(mount_point):
                    os.rmdir(mount_point)
            except:
                pass
                
            # Extraire le message d'erreur pertinent
            error_msg = stderr.strip()
            if "already mounted" in error_msg.lower():
                return False, "Le volume est déjà monté"
            elif "incorrect password" in error_msg.lower():
                return False, "Mot de passe incorrect"
            else:
                return False, error_msg
            
    except Exception as e:
        print(f"Exception lors du montage: {str(e)}")
        return False, str(e)

def unmount_volume(mount_point: str) -> Tuple[bool, str]:
    """Démonte un volume VeraCrypt.
    
    Args:
        mount_point: Point de montage du volume à démonter
        
    Returns:
        Tuple contenant:
        - Un booléen indiquant si le démontage a réussi
        - Un message d'erreur si le démontage a échoué
    """
    try:
        command = [
            system.Constants.VERACRYPT_PATH,
            '--text',
            '--non-interactive',
            '--dismount',
            mount_point
        ]
        
        # Le démontage nécessite sudo
        success, stdout, stderr = sudo_session.run_with_sudo(command)
        
        if success:
            # Supprimer le répertoire de montage s'il est vide
            try:
                os.rmdir(mount_point)
            except:
                pass
            return True, ''
        else:
            return False, stderr
            
    except Exception as e:
        return False, str(e)
