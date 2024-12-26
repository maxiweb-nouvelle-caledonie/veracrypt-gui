"""
Utilitaires pour interagir avec VeraCrypt en ligne de commande.
"""

import os
import subprocess
from typing import Tuple, List, Optional
from . import system
from . import polkit
from .auth_agent import auth_agent

def execute_veracrypt_command(command: List[str], need_password: bool = False) -> Tuple[bool, str, str]:
    """Exécute une commande veracrypt.
    
    Args:
        command: Liste contenant la commande et ses arguments
        need_password: Si True, la commande nécessite un mot de passe
        
    Returns:
        Tuple contenant:
        - Un booléen indiquant si la commande a réussi
        - La sortie standard
        - La sortie d'erreur
    """
    try:
        # Ajouter l'option --stdin si nécessaire
        if need_password and '--stdin' not in command:
            command.insert(-1, '--stdin')
            
        # Exécuter la commande avec polkit
        success, stdout, stderr = polkit.run_privileged_command(command)
        
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
        
        # Exécuter la commande avec l'agent
        success, stdout, stderr = auth_agent.run_command(command)
        
        print(f"Sortie standard:\n{stdout}")
        print(f"Sortie d'erreur:\n{stderr}")
        
        if not success:
            print(f"Erreur lors de la liste des volumes: {stderr}")
            return []
            
        volumes = []
        for line in stdout.splitlines():
            print(f"Analyse de la ligne: {line}")
            # Format: "1: /dev/sdc2 /dev/loop32 /media/jayces/veracrypt_20241226_205820"
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0].endswith(':'):
                slot = parts[0].rstrip(':')  # Extraire le numéro de slot
                mount_point = parts[-1]  # Le point de montage est le dernier élément
                print(f"Volume trouvé - slot: {slot}, mount_point: {mount_point}")
                volumes.append((slot, mount_point))
                    
        print(f"Volumes trouvés: {volumes}")
        return volumes
        
    except Exception as e:
        print(f"Erreur lors de la liste des volumes: {str(e)}")
        return []

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
        # Vérifier que le volume existe
        if not os.path.exists(volume_path):
            return False, f"Le volume {volume_path} n'existe pas"
            
        # Créer le point de montage si nécessaire
        if not os.path.exists(mount_point):
            os.makedirs(mount_point, exist_ok=True)
            
        # Monter le volume
        command = [
            system.Constants.VERACRYPT_PATH,
            '--text',  # Mode texte
            '--non-interactive',  # Mode non interactif
            '--password', password,  # Mot de passe en argument
            '--mount',
            volume_path,
            mount_point
        ]
        
        # Exécuter la commande avec l'agent
        success, stdout, stderr = auth_agent.run_command(command)
        
        if success:
            return True, ''
        else:
            return False, stderr
            
    except Exception as e:
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
        
        # Exécuter la commande avec l'agent
        success, stdout, stderr = auth_agent.run_command(command)
        
        if success:
            return True, ''
        else:
            return False, stderr
            
    except Exception as e:
        return False, str(e)
