import subprocess
from typing import Tuple, Optional
import os
import signal
import time

class AuthAgent:
    _instance = None
    _agent_process = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthAgent, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._start_agent()
            
    def _start_agent(self):
        """Démarre l'agent d'authentification."""
        try:
            if self._agent_process is None:
                # Démarrer l'agent avec pkexec pour avoir les droits root
                self._agent_process = subprocess.Popen(
                    ['pkexec', 'bash', '-c', 'while true; do sleep 1; done'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(1)  # Attendre que l'agent soit prêt
                
        except Exception as e:
            print(f"Erreur lors du démarrage de l'agent: {str(e)}")
            
    def _ensure_agent_running(self):
        """S'assure que l'agent est en cours d'exécution."""
        if self._agent_process is None or self._agent_process.poll() is not None:
            self._start_agent()
            
    def run_command(self, command: list) -> Tuple[bool, str, str]:
        """Exécute une commande avec les privilèges de l'agent.
        
        Args:
            command: Liste contenant la commande et ses arguments
            
        Returns:
            Tuple contenant:
            - Un booléen indiquant si la commande a réussi
            - La sortie standard
            - La sortie d'erreur
        """
        self._ensure_agent_running()
        
        try:
            # Utiliser sudo avec l'agent
            full_command = ['sudo', '-n'] + command
            
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
            
    def __del__(self):
        """Nettoie l'agent à la destruction."""
        if self._agent_process:
            try:
                self._agent_process.terminate()
                self._agent_process.wait(timeout=1)
            except:
                try:
                    self._agent_process.kill()
                except:
                    pass
                    
# Instance globale
auth_agent = AuthAgent()
