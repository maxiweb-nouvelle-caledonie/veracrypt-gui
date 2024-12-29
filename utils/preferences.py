"""
Gestion des préférences de l'application.
"""

import json
import os
from typing import Dict, Any

class Preferences:
    def __init__(self):
        self.preferences_file = os.path.expanduser('~/.veracrypt/preferences.json')
        self._ensure_preferences_dir()
        self.preferences = self._load_preferences()
        
    def _ensure_preferences_dir(self):
        """S'assure que le répertoire des préférences existe."""
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
        
    def _load_preferences(self) -> Dict[str, Any]:
        """Charge les préférences depuis le fichier."""
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._get_default_preferences()
        return self._get_default_preferences()
        
    def _save_preferences(self) -> bool:
        """Sauvegarde les préférences dans le fichier."""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des préférences : {e}")
            return False
            
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Retourne les préférences par défaut."""
        return {
            'auto_clean_mount_points': True,  # Nettoyer automatiquement les points de montage vides
            'check_mount_points_on_start': True,  # Vérifier l'intégrité des points de montage au démarrage
            'default_mount_dir': os.path.expanduser('~/veracrypt'),  # Répertoire de montage par défaut
            'show_notifications': True,  # Afficher les notifications
            'theme': 'Système',  # Thème de l'application
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une préférence."""
        return self.preferences.get(key, default)
        
    def set(self, key: str, value: Any) -> bool:
        """Définit une préférence."""
        self.preferences[key] = value
        return self._save_preferences()
        
# Instance globale
preferences = Preferences()
