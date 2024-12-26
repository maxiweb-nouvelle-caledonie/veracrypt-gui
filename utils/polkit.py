import subprocess
from typing import Tuple, Optional
import os

def run_privileged_command(command: list) -> Tuple[bool, str, str]:
    """Exécute une commande avec des privilèges élevés via polkit.
    
    Args:
        command: Liste contenant la commande et ses arguments
        
    Returns:
        Tuple contenant:
        - Un booléen indiquant si la commande a réussi
        - La sortie standard
        - La sortie d'erreur
    """
    try:
        # Utiliser pkexec pour exécuter la commande avec des privilèges
        full_command = ['pkexec'] + command
        
        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        success = process.returncode == 0
        
        return success, stdout, stderr
        
    except Exception as e:
        return False, '', str(e)
