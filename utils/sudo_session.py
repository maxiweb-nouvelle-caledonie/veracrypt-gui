"""
Gestion de la session sudo.
"""

import subprocess
import time
import threading
import logging
import os
from typing import Optional
from PyQt6.QtWidgets import QInputDialog, QLineEdit

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.veracrypt/veracrypt.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('veracrypt.sudo_session')

class SudoSession:
    _instance = None
    _sudo_timestamp = 0
    _refresh_thread = None
    _stop_refresh = False
    _sudo_password = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SudoSession, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._sudo_timestamp = 0
            
    def initialize_session(self) -> bool:
        """Initialise la session sudo en demandant le mot de passe.
        
        Returns:
            bool: True si la session est initialisée avec succès
        """
        try:
            # Demander le mot de passe sudo via une boîte de dialogue
            password, ok = QInputDialog.getText(
                None,
                "Authentification sudo",
                "Entrez votre mot de passe sudo :",
                QLineEdit.EchoMode.Password
            )
            
            if not ok or not password:
                return False
                
            logger.debug("Tentative d'initialisation de la session sudo")
            
            # Tester le mot de passe
            process = subprocess.run(
                ['sudo', '-S', '-v'],
                input=password + '\n',
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                self._sudo_timestamp = time.time()
                self._sudo_password = password
                # Démarrer le thread de rafraîchissement
                self._start_refresh_thread()
                logger.info("Session sudo initialisée avec succès")
                return True
            else:
                logger.error(f"Échec de l'initialisation sudo : {process.stderr}")
                return False
                
        except Exception as e:
            logger.exception("Erreur lors de l'initialisation de la session sudo")
            return False
            
    def get_sudo_password(self) -> Optional[str]:
        """Retourne le mot de passe sudo.
        
        Returns:
            Le mot de passe sudo ou None si pas disponible
        """
        if self._sudo_password is None or time.time() - self._sudo_timestamp > 300:
            if not self.initialize_session():
                return None
        return self._sudo_password
        
    def run_with_sudo(self, command: list, stdin: bytes = None) -> tuple[bool, str, str]:
        """Exécute une commande avec sudo.
        
        Args:
            command: La commande à exécuter
            stdin: Données à envoyer sur l'entrée standard
            
        Returns:
            Tuple contenant:
            - Un booléen indiquant si la commande a réussi
            - La sortie standard
            - La sortie d'erreur
        """
        try:
            # Vérifier si la session est active
            if time.time() - self._sudo_timestamp > 300:  # 5 minutes
                if not self.initialize_session():
                    return False, '', 'Session sudo expirée'
                    
            # Construire l'entrée standard
            input_data = self._sudo_password + '\n'
            if stdin:
                input_data += stdin.decode('utf-8')
                
            logger.debug(f"Exécution de la commande sudo : {' '.join(command)}")
            logger.debug(f"Données stdin (longueur) : {len(input_data)} caractères")
            
            # Exécuter la commande avec sudo
            process = subprocess.run(
                ['sudo', '-S'] + command,
                input=input_data,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                logger.debug("Commande exécutée avec succès")
            else:
                logger.error(f"Échec de la commande : {process.stderr}")
                
            return process.returncode == 0, process.stdout, process.stderr
            
        except Exception as e:
            logger.exception("Erreur lors de l'exécution de la commande sudo")
            return False, '', str(e)
            
    def _refresh_sudo(self):
        """Rafraîchit la session sudo en arrière-plan."""
        while not self._stop_refresh:
            try:
                # Rafraîchir toutes les 4 minutes (la timeout par défaut est 5 minutes)
                if time.time() - self._sudo_timestamp >= 240:
                    logger.debug("Rafraîchissement de la session sudo")
                    process = subprocess.run(
                        ['sudo', '-S', '-v'],
                        input=self._sudo_password + '\n',
                        capture_output=True
                    )
                    if process.returncode == 0:
                        self._sudo_timestamp = time.time()
                        logger.debug("Session sudo rafraîchie avec succès")
                    else:
                        logger.error("Échec du rafraîchissement de la session sudo")
            except Exception as e:
                logger.exception("Erreur lors du rafraîchissement de la session sudo")
            time.sleep(30)  # Vérifier toutes les 30 secondes
            
    def _start_refresh_thread(self):
        """Démarre le thread de rafraîchissement de la session sudo."""
        if self._refresh_thread is None or not self._refresh_thread.is_alive():
            self._stop_refresh = False
            self._refresh_thread = threading.Thread(
                target=self._refresh_sudo,
                daemon=True
            )
            self._refresh_thread.start()
            
    def __del__(self):
        """Arrête le thread de rafraîchissement à la destruction."""
        self._stop_refresh = True
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._refresh_thread.join(timeout=1)
            
# Instance globale
sudo_session = SudoSession()
