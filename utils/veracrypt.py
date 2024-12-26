"""
Utilitaires pour interagir avec VeraCrypt en ligne de commande.
"""

import subprocess
from typing import Tuple, List, Optional
from ..constants import Constants

def execute_veracrypt_command(cmd: List[str], password: Optional[str] = None, timeout: int = Constants.MOUNT_TIMEOUT) -> Tuple[bool, str, str]:
    """
    Exécute une commande VeraCrypt et retourne le résultat.
    
    Args:
        cmd: Liste des arguments de la commande
        password: Mot de passe optionnel
        timeout: Timeout en secondes
        
    Returns:
        Tuple (succès, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            input=f"{password}\n" if password else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return False, "", "Le processus a expiré"

def list_mounted_volumes() -> List[Tuple[str, str]]:
    """Liste les volumes VeraCrypt montés.
    Returns:
        Liste de tuples (slot, point_de_montage)
    """
    cmd = [
        'sudo',
        Constants.VERACRYPT_PATH,
        '--text',
        '--list'
    ]
    success, stdout, stderr = execute_veracrypt_command(cmd)
    
    if not success:
        print(f"Erreur lors de la liste des volumes: {stderr}")
        return []
    
    print(f"Sortie de veracrypt --list:\n{stdout}")
    
    volumes = []
    for line in stdout.split('\n'):
        line = line.strip()
        if line and ":" in line:
            # Format: "1: /chemin/source /dev/mapper/veracrypt1 /point/de/montage"
            parts = line.split(':', 1)
            if len(parts) == 2:
                slot = parts[0].strip()
                # Prendre le dernier élément (point de montage)
                volume_info = parts[1].strip().split()
                if volume_info:
                    mount_point = volume_info[-1]  # Dernier élément = point de montage
                    volumes.append((slot, mount_point))
    
    print(f"Volumes trouvés (slot, point de montage): {volumes}")
    return volumes

def mount_volume(volume_path: str, mount_point: str, password: str) -> Tuple[bool, str]:
    """Monte un volume VeraCrypt."""
    cmd = [
        'sudo',
        Constants.VERACRYPT_PATH,
        '--text',
        '--non-interactive',
        '--verbose',
        '--stdin',
        '--protect-hidden=no',
        volume_path,
        mount_point
    ]
    success, stdout, stderr = execute_veracrypt_command(cmd, password)
    return success, stderr if not success else stdout

def unmount_volume(mount_path: str) -> Tuple[bool, str]:
    """Démonte un volume VeraCrypt."""
    # Construire la commande avec le point de montage
    cmd = [
        'sudo',
        Constants.VERACRYPT_PATH,
        '--text',
        '--dismount',
        mount_path,  # Utiliser le point de montage au lieu du slot
        '--force'
    ]
    
    # Afficher la commande pour exécution manuelle
    cmd_str = ' '.join(cmd)
    print(f"\nCommande de démontage à exécuter manuellement:\n{cmd_str}\n")
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=Constants.MOUNT_TIMEOUT
        )
        
        print(f"Sortie de la commande:")
        print(f"  stdout: {result.stdout}")
        print(f"  stderr: {result.stderr}")
        print(f"  code retour: {result.returncode}")
        
        if result.returncode == 0:
            return True, "Volume démonté avec succès"
        else:
            # Essayer avec --all si le premier essai échoue
            print("\nEssai avec --all...")
            cmd_all = [
                'sudo',
                Constants.VERACRYPT_PATH,
                '--text',
                '--dismount',
                '--all',
                '--force'
            ]
            print(f"Commande alternative: {' '.join(cmd_all)}")
            
            result_all = subprocess.run(
                cmd_all,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=Constants.MOUNT_TIMEOUT
            )
            
            print(f"Sortie de la commande --all:")
            print(f"  stdout: {result_all.stdout}")
            print(f"  stderr: {result_all.stderr}")
            print(f"  code retour: {result_all.returncode}")
            
            if result_all.returncode == 0:
                return True, "Tous les volumes ont été démontés"
            return False, f"Erreur: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Le processus a expiré"
    except Exception as e:
        return False, f"Erreur inattendue: {str(e)}"
