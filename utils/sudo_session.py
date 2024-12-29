import subprocess
import time
import threading
from typing import Optional
from PyQt6.QtWidgets import QInputDialog, QLineEdit

class SudoSession:
    _instance = None
    _sudo_timestamp = 0
    _refresh_thread = None
    _stop_refresh = False
    _sudo_password = None  # Stockage temporaire du mot de passe
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SudoSession, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._sudo_timestamp = 0
            self._sudo_password = None
            
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
                
            # Tester le mot de passe
            process = subprocess.run(
                ['sudo', '-S', '-v'],
                input=password + '\n',
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                self._sudo_timestamp = time.time()
                self._sudo_password = password  # Stocker le mot de passe
                # Démarrer le thread de rafraîchissement
                self._start_refresh_thread()
                return True
            return False
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la session sudo: {str(e)}")
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
        
    def _refresh_sudo(self):
        """Rafraîchit la session sudo en arrière-plan."""
        while not self._stop_refresh:
            try:
                # Rafraîchir toutes les 4 minutes (la timeout par défaut est 5 minutes)
                if time.time() - self._sudo_timestamp >= 240:
                    subprocess.run(
                        ['sudo', '-S', '-v'],
                        input=self._sudo_password + '\n',
                        capture_output=True
                    )
                    self._sudo_timestamp = time.time()
            except:
                pass
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
            
    def run_with_sudo(self, command: list) -> tuple[bool, str, str]:
        """Exécute une commande avec sudo.
        
        Args:
            command: La commande à exécuter
            
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
                    
            # Exécuter la commande avec sudo
            process = subprocess.run(
                ['sudo', '-S'] + command,
                input=self._sudo_password + '\n',
                capture_output=True,
                text=True
            )
            
            return process.returncode == 0, process.stdout, process.stderr
            
        except Exception as e:
            return False, '', str(e)
            
    def __del__(self):
        """Arrête le thread de rafraîchissement à la destruction."""
        self._stop_refresh = True
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._refresh_thread.join(timeout=1)
            
# Instance globale
sudo_session = SudoSession()
