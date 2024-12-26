import subprocess
from typing import Tuple, Optional
import time
import os

class SudoSession:
    _instance = None
    _timestamp = None
    _timeout = 300  # 5 minutes en secondes
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SudoSession, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            
    def _validate_session(self) -> bool:
        """Valide ou renouvelle la session sudo."""
        try:
            # Utiliser sudo -v pour valider/renouveler la session
            result = subprocess.run(
                ['sudo', '-v'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                input='',  # Pour éviter le message "sudo: no tty present"
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Erreur lors de la validation sudo: {str(e)}")
            return False
            
    def run_command(self, command: list) -> Tuple[bool, str, str]:
        """Exécute une commande avec sudo.
        
        Args:
            command: Liste contenant la commande et ses arguments
            
        Returns:
            Tuple contenant:
            - Un booléen indiquant si la commande a réussi
            - La sortie standard
            - La sortie d'erreur
        """
        # Valider la session avant d'exécuter la commande
        if not self._validate_session():
            return False, '', 'Session sudo invalide'
            
        try:
            # Utiliser sudo pour exécuter la commande
            full_command = ['sudo'] + command
            
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
            
# Instance globale
sudo = SudoSession()
