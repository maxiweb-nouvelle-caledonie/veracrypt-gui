"""
Utilitaires de chiffrement pour les mots de passe.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .sudo_session import sudo_session

class PasswordEncryption:
    """Classe pour gérer le chiffrement/déchiffrement des mots de passe."""
    
    SALT_FILE = os.path.expanduser('~/.veracrypt/.salt')
    ITERATIONS = 100000
    
    @classmethod
    def _get_or_create_salt(cls) -> bytes:
        """Récupère ou crée le sel de chiffrement."""
        try:
            # Créer le dossier .veracrypt s'il n'existe pas
            os.makedirs(os.path.dirname(cls.SALT_FILE), exist_ok=True)
            
            if os.path.exists(cls.SALT_FILE):
                with open(cls.SALT_FILE, 'rb') as f:
                    return f.read()
            else:
                # Générer un nouveau sel
                salt = os.urandom(16)
                # Sauvegarder le sel
                with open(cls.SALT_FILE, 'wb') as f:
                    f.write(salt)
                return salt
        except Exception as e:
            raise Exception(f"Erreur lors de la gestion du sel: {str(e)}")
    
    @classmethod
    def _get_key(cls) -> bytes:
        """Génère la clé de chiffrement basée sur le mot de passe sudo."""
        try:
            # Utiliser le mot de passe sudo comme base
            sudo_password = sudo_session.get_sudo_password()
            if not sudo_password:
                raise Exception("Pas de mot de passe sudo disponible")
                
            # Récupérer le sel
            salt = cls._get_or_create_salt()
            
            # Dériver la clé
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=cls.ITERATIONS,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(sudo_password.encode()))
            return key
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération de la clé: {str(e)}")
    
    @classmethod
    def encrypt_password(cls, password: str) -> str:
        """Chiffre un mot de passe.
        
        Args:
            password: Le mot de passe à chiffrer
            
        Returns:
            Le mot de passe chiffré en base64
        """
        try:
            key = cls._get_key()
            f = Fernet(key)
            encrypted = f.encrypt(password.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise Exception(f"Erreur lors du chiffrement: {str(e)}")
    
    @classmethod
    def decrypt_password(cls, encrypted_password: str) -> str:
        """Déchiffre un mot de passe.
        
        Args:
            encrypted_password: Le mot de passe chiffré en base64
            
        Returns:
            Le mot de passe en clair
        """
        try:
            key = cls._get_key()
            f = Fernet(key)
            decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_password))
            return decrypted.decode()
        except Exception as e:
            raise Exception(f"Erreur lors du déchiffrement: {str(e)}")
