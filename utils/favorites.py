"""
Gestion des favoris VeraCrypt.
"""

import json
import os
from typing import List, Dict, Optional

class Favorites:
    def __init__(self):
        self.favorites_file = os.path.expanduser('~/.veracrypt/favorites.json')
        self._ensure_favorites_dir()
        self.favorites = self._load_favorites()
    
    def _ensure_favorites_dir(self):
        """S'assure que le répertoire des favoris existe."""
        os.makedirs(os.path.dirname(self.favorites_file), exist_ok=True)
    
    def _load_favorites(self) -> List[Dict]:
        """Charge les favoris depuis le fichier."""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []
    
    def _save_favorites(self):
        """Sauvegarde les favoris dans le fichier."""
        try:
            print(f"Sauvegarde des favoris : {self.favorites}")  # Debug
            with open(self.favorites_file, 'w') as f:
                json.dump(self.favorites, f, indent=2)
            print(f"Favoris sauvegardés dans {self.favorites_file}")  # Debug
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des favoris : {e}")
            return False
    
    def add_favorite(self, name: str, path: str, is_device: bool, mount_point: str = None) -> bool:
        """Ajoute un favori.
        
        Args:
            name: Nom du favori
            path: Chemin du volume/périphérique
            is_device: True si c'est un périphérique, False si c'est un fichier
            mount_point: Point de montage préféré (optionnel)
            
        Returns:
            True si l'ajout a réussi, False sinon
        """
        print(f"Ajout du favori {name} ({path})")  # Debug
        # Vérifier si le favori existe déjà
        if any(f['volume_path'] == path for f in self.favorites):
            print(f"Le favori existe déjà : {path}")  # Debug
            return False
            
        favorite = {
            'name': name,
            'volume_path': path,
            'is_device': is_device
        }
        
        if mount_point:
            favorite['mount_point'] = mount_point
            
        print(f"Ajout du favori : {favorite}")  # Debug
        self.favorites.append(favorite)
        return self._save_favorites()
    
    def remove_favorite(self, path: str) -> bool:
        """Supprime un favori.
        
        Args:
            path: Chemin du volume/périphérique
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        initial_length = len(self.favorites)
        self.favorites = [f for f in self.favorites if f['volume_path'] != path]
        if len(self.favorites) != initial_length:
            self._save_favorites()
            return True
        return False
    
    def get_favorites(self) -> List[Dict]:
        """Retourne la liste des favoris."""
        print(f"Lecture des favoris : {self.favorites}")  # Debug
        return self.favorites.copy()  # Retourner une copie pour éviter les modifications accidentelles
    
    def get_favorite(self, path: str) -> Optional[Dict]:
        """Retourne un favori par son chemin."""
        for favorite in self.favorites:
            if favorite['volume_path'] == path:
                return favorite
        return None
