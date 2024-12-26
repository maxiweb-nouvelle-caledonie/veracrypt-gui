"""
Utilitaires système pour la gestion des fichiers et périphériques.
"""

import os
import subprocess
import stat
from typing import List, Tuple, Optional
from src.utils.constants import Constants  # Importation correcte de Constants

def _is_valid_device(path: str) -> bool:
    """Vérifie si un périphérique est valide."""
    try:
        # Vérifier si le chemin commence par /dev/
        if not path.startswith('/dev/'):
            return False
            
        # Vérifier si le périphérique existe dans /dev/
        if not os.path.exists(path):
            return False
            
        # Vérifier si c'est un périphérique bloc
        return os.path.exists(path) and stat.S_ISBLK(os.stat(path).st_mode)
    except Exception:
        return False

def list_devices() -> List[Tuple[str, str]]:
    """Liste les périphériques disponibles."""
    devices = []
    
    try:
        # Lister les périphériques avec lsblk
        result = subprocess.run(
            ['lsblk', '--pairs', '--paths', '--output', 'NAME,SIZE,TYPE'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                    
                # Parser la sortie au format KEY="VALUE"
                info = {}
                for item in line.split():
                    key, value = item.split('=', 1)
                    info[key] = value.strip('"')
                
                if 'NAME' not in info or 'SIZE' not in info or 'TYPE' not in info:
                    continue
                    
                path = info['NAME']
                size = info['SIZE']
                dev_type = info['TYPE']
                
                # Ne garder que les disques et partitions
                if dev_type in ['disk', 'part']:
                    # Ignorer les petits périphériques (< 10MB)
                    if 'M' in size:
                        try:
                            size_mb = float(size.replace('M', ''))
                            if size_mb < 10:
                                continue
                        except ValueError:
                            continue
                    elif 'K' in size:
                        continue
                        
                    # Vérifier si le périphérique est valide
                    if _is_valid_device(path):
                        name = f"Périphérique {path} ({size})"
                        devices.append((path, name))
    except Exception as e:
        print(f"Erreur lors de la liste des périphériques: {str(e)}")
    
    return devices

def ensure_directory(path: str) -> Tuple[bool, str]:
    """
    S'assure qu'un répertoire existe et est accessible.
    
    Args:
        path: Chemin du répertoire
        
    Returns:
        Tuple (succès, message d'erreur)
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return True, ""
    except Exception as e:
        return False, str(e)

def cleanup_mount_point(mount_point: str) -> Tuple[bool, str]:
    """
    Nettoie un point de montage.
    
    Args:
        mount_point: Chemin du point de montage
        
    Returns:
        Tuple (succès, message d'erreur)
    """
    try:
        if os.path.exists(mount_point):
            os.rmdir(mount_point)
        return True, ""
    except Exception as e:
        return False, str(e)

def cleanup_mount_points() -> Tuple[bool, str]:
    """Nettoie les points de montage non utilisés.
    
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    try:
        base_mount_dir = Constants.BASE_MOUNT_DIR
        
        # Vérifier si le répertoire de base existe
        if not os.path.exists(base_mount_dir):
            return True, "Aucun point de montage à nettoyer"
            
        # Lister les points de montage existants
        mounted = []
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    if base_mount_dir in line:
                        mounted.append(line.split()[1])
        except Exception as e:
            return False, f"Erreur lors de la lecture de /proc/mounts: {str(e)}"
        
        # Parcourir les répertoires dans le dossier de montage
        cleaned = []
        for dir_name in os.listdir(base_mount_dir):
            dir_path = os.path.join(base_mount_dir, dir_name)
            
            # Vérifier si c'est un répertoire et s'il n'est pas monté
            if os.path.isdir(dir_path) and dir_path not in mounted:
                try:
                    # Vérifier si le répertoire est vide
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        cleaned.append(dir_path)
                    else:
                        print(f"Répertoire non vide, ignoré: {dir_path}")
                except Exception as e:
                    print(f"Erreur lors de la suppression de {dir_path}: {str(e)}")
        
        if cleaned:
            return True, f"Points de montage nettoyés: {', '.join(cleaned)}"
        return True, "Aucun point de montage à nettoyer"
        
    except Exception as e:
        return False, f"Erreur lors du nettoyage: {str(e)}"
